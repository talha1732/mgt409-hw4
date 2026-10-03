"""Tools the Campus Customs agent can call, plus the shared catalogue/stock lookups.

Every tool here is read-only and touches only `catalogue` and `inventory`.
Nothing in this file reads `users`, `sessions` or `chat_messages`, so the agent
has no path to passwords or other shoppers' data.
"""

import json
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from pydantic_ai import ModelRetry, RunContext

from models import (
    CustomerInfo,
    PageInfo,
    ProductDescription,
    ProductPrice,
    ProductSummary,
    SearchResults,
    SimilarProducts,
    SizeStock,
    StockResult,
)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DB_PATH = DATA_DIR / "campus_customs.db"
SIZE_ORDER = ["XS", "S", "M", "L", "XL", "XXL"]
MAX_RESULTS = 12  # matches the most cards the website shows per reply


@dataclass
class AgentDeps:
    """Per-request context built by main.py for each chat message.

    `customer` comes from the session cookie (never from the chat text), so a shopper can't
    claim to be someone else. `page` comes from the browser's current path; the product on
    it is looked up here on the server.
    """

    customer: CustomerInfo = field(default_factory=lambda: CustomerInfo(logged_in=False))
    page: PageInfo = field(default_factory=lambda: PageInfo(path="/", page_type="home"))


# ---------- Shared DB helpers (also used by main.py for the product pages) ----------

def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


PRODUCT_SQL = """
    SELECT c.*, COALESCE(SUM(i.quantity), 0) AS total_stock
    FROM catalogue c
    LEFT JOIN inventory i ON i.product_id = c.product_id
"""


def product_from_row(row: sqlite3.Row) -> dict:
    """Catalogue row -> API dict."""
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "garment_type": row["garment_type"],
        "description": row["description"],
        "colors": json.loads(row["colors"]),
        "search_tags": json.loads(row["search_tags"]),
        "price": row["price"],
        "image_url": f"/images/{Path(row['image_file_path']).name}",
        "total_stock": row["total_stock"],
    }


def load_stock(conn: sqlite3.Connection) -> dict[str, dict[str, int]]:
    stock: dict[str, dict[str, int]] = {}
    for r in conn.execute("SELECT product_id, size, quantity FROM inventory"):
        stock.setdefault(r["product_id"], {})[r["size"]] = r["quantity"]
    return stock


def size_rows(sizes: dict[str, int]) -> list[dict]:
    return [{"size": s, "quantity": sizes[s], "in_stock": sizes[s] > 0} for s in SIZE_ORDER if s in sizes]


def load_all_products() -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(PRODUCT_SQL + " GROUP BY c.product_id ORDER BY c.name").fetchall()
        stock = load_stock(conn)
    products = [product_from_row(r) for r in rows]
    for p in products:
        p["inventory"] = size_rows(stock.get(p["product_id"], {}))
    return products


def load_product(product_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            PRODUCT_SQL + " WHERE c.product_id = ? GROUP BY c.product_id", (product_id,)
        ).fetchone()
        if row is None:
            return None
        sizes = {
            r["size"]: r["quantity"]
            for r in conn.execute("SELECT size, quantity FROM inventory WHERE product_id = ?", (product_id,))
        }
    product = product_from_row(row)
    product["inventory"] = size_rows(sizes)
    return product


# ---------- Loose text matching (garment_type and tags are messy) ----------

SYNONYMS = {
    "tee": "tshirt", "tees": "tshirt", "shirt": "tshirt", "shirts": "tshirt",
    "hoody": "hoodie", "hoodies": "hoodie", "hood": "hoodie", "hooded": "hoodie",
    "crew": "crewneck", "crewnecks": "crewneck", "sweatshirts": "sweatshirt",
    "quarter": "quarterzip", "jackets": "jacket", "fleeces": "fleece", "grey": "gray",
}
STOPWORDS = {
    "a", "an", "the", "and", "or", "for", "with", "in", "of", "to", "do", "you", "have", "any",
    "i", "me", "my", "want", "need", "looking", "show", "some", "something", "is", "are", "it",
    "yale", "campus", "customs", "college",  # appear on nearly every product, so they don't help rank
}


def normalize(text: str) -> list[str]:
    text = text.lower().replace("t-shirt", "tshirt").replace("t shirt", "tshirt")
    text = text.replace("1/4", "quarter").replace("quarter-zip", "quarterzip").replace("quarter zip", "quarterzip")
    words = re.findall(r"[a-z0-9]+", text)
    out = []
    for w in words:
        w = SYNONYMS.get(w, w)
        if len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
            w = w[:-1]
        if w not in STOPWORDS:
            out.append(w)
    return out


def score(product: dict, terms: list[str]) -> float:
    fields = [
        (product["name"], 3.0),
        (" ".join(product["search_tags"]), 3.0),
        (product["garment_type"], 2.0),
        (" ".join(product["colors"]), 2.0),
        (product["description"], 1.0),
    ]
    total = 0.0
    for term in terms:
        for text, weight in fields:
            if term in normalize(text):
                total += weight
    return total


def summarize(p: dict) -> ProductSummary:
    return ProductSummary(
        product_id=p["product_id"],
        name=p["name"],
        garment_type=p["garment_type"],
        price=p["price"],
        colors=p["colors"],
        sizes_in_stock=[s["size"] for s in p["inventory"] if s["in_stock"]],
        total_stock=p["total_stock"],
    )


# ---------- Page context ----------

STATIC_PAGES = {
    "/": "home", "/products": "products", "/about": "about",
    "/login": "login", "/create-account": "create_account",
}


def build_page_info(path: str) -> PageInfo:
    """Browser path -> PageInfo. Unknown products or odd paths are treated as 'other', never trusted."""
    path = (path or "/").split("?")[0].split("#")[0].rstrip("/") or "/"
    m = re.fullmatch(r"/products/([a-z0-9-]{1,120})", path)
    if m:
        p = load_product(m.group(1))
        if p:
            return PageInfo(path=path, page_type="product_detail", product=summarize(p))
        return PageInfo(path=path, page_type="other")
    return PageInfo(path=path, page_type=STATIC_PAGES.get(path, "other"))


# ---------- Agent tools ----------

def search_products(
    ctx: RunContext[AgentDeps],
    query: str = "",
    garment_type: str | None = None,
    color: str | None = None,
    max_price: float | None = None,
    size: str | None = None,
) -> SearchResults:
    """Search the Campus Customs catalogue. Returns the 12 best matches (price, colors, sizes in stock) and total_matches.

    Args:
        query: What the shopper wants in plain words, e.g. "hockey hoodie", "Morse College", "The Game".
        garment_type: Optional loose type filter, e.g. "hoodie", "crewneck", "t-shirt", "quarter-zip", "jacket".
        color: Optional color the item must come in, e.g. "navy", "gray".
        max_price: Optional price ceiling in USD.
        size: Optional size that must currently be in stock: XS, S, M, L, XL or XXL. This HIDES products
            that are sold out in that size, so don't use it to check stock for a specific named product;
            search by name instead and then call check_stock.
    """
    products = load_all_products()

    if garment_type:
        wanted = set(normalize(garment_type))
        products = [p for p in products if wanted & set(normalize(p["garment_type"] + " " + p["name"]))]
    if color:
        wanted = set(normalize(color))
        products = [p for p in products if wanted & set(normalize(" ".join(p["colors"])))]
    if max_price is not None:
        products = [p for p in products if p["price"] <= max_price]
    if size:
        size = size.strip().upper()
        if size not in SIZE_ORDER:
            raise ModelRetry(f"size must be one of {', '.join(SIZE_ORDER)}")
        products = [p for p in products if any(s["size"] == size and s["in_stock"] for s in p["inventory"])]

    terms = normalize(query)
    full: list[dict] = []
    if terms:
        # Prefer items matching every word ("hockey hoodie" = hockey AND hoodie); only fall back to
        # partial matches when nothing matches them all. Keeps total_matches honest.
        full = [p for p in products if all(score(p, [t]) > 0 for t in terms)]
        pool = full or products
        scored = [(score(p, terms), p) for p in pool]
        products = [p for s, p in sorted(scored, key=lambda x: -x[0]) if s > 0]
    return SearchResults(
        total_matches=len(products),
        matched_all_terms=not terms or bool(full),
        products=[summarize(p) for p in products[:MAX_RESULTS]],
    )


def _require_product(product_id: str) -> dict:
    p = load_product(product_id.strip())
    if p is None:
        raise ModelRetry(f"No product with id {product_id!r}. Call search_products first and use an id it returns.")
    return p


def get_product_description(ctx: RunContext[AgentDeps], product_id: str) -> ProductDescription:
    """The full product description (fit, graphic, features), garment type and available colors.

    Args:
        product_id: The exact product_id from a search_products result.
    """
    p = _require_product(product_id)
    return ProductDescription(
        product_id=p["product_id"],
        name=p["name"],
        garment_type=p["garment_type"],
        description=p["description"],
        colors=p["colors"],
    )


def get_product_price(ctx: RunContext[AgentDeps], product_id: str) -> ProductPrice:
    """The exact current price of a product in USD, straight from the database.

    Args:
        product_id: The exact product_id from a search_products result.
    """
    p = _require_product(product_id)
    return ProductPrice(product_id=p["product_id"], name=p["name"], price=p["price"])


def check_stock(ctx: RunContext[AgentDeps], product_id: str, size: str | None = None) -> StockResult:
    """How many units are in stock, per size. Pass `size` when the shopper asks about one size.

    Args:
        product_id: The exact product_id from a search_products result.
        size: Optional size the shopper asked about: XS, S, M, L, XL or XXL.
    """
    p = _require_product(product_id)
    sizes = [SizeStock(**s) for s in p["inventory"]]
    in_stock = [s.size for s in sizes if s.in_stock]

    qty: int | None = None
    if size:
        size = size.strip().upper()
        if size not in SIZE_ORDER:
            raise ModelRetry(f"size must be one of {', '.join(SIZE_ORDER)}")
        qty = next((s.quantity for s in sizes if s.size == size), 0)
        summary = f"Size {size}: {qty} in stock." if qty > 0 else f"Size {size} is OUT OF STOCK."
    elif p["total_stock"] == 0:
        summary = "OUT OF STOCK in every size."
    else:
        summary = f"In stock in {', '.join(in_stock)} ({p['total_stock']} units total)."
    if size and qty == 0 and in_stock:
        summary += f" In stock in: {', '.join(in_stock)}."

    return StockResult(
        product_id=p["product_id"],
        name=p["name"],
        size_requested=size,
        requested_size_quantity=qty,
        requested_size_in_stock=(qty > 0) if size else None,
        sizes=sizes,
        sizes_in_stock=in_stock,
        total_stock=p["total_stock"],
        summary=summary,
    )


def category(p: dict) -> str:
    """Group messy garment_type values (same buckets as the Products page filter)."""
    t = f"{p['garment_type']} {p['name']}".lower()
    if "hood" in t:
        return "hoodie"
    if "quarter" in t or "1 4 zip" in t:
        return "quarter-zip"
    if "jacket" in t or "fleece" in t:
        return "jacket"
    if "t-shirt" in t or "t shirt" in t or "tee" in t:
        return "t-shirt"
    if "crew" in t or "sweatshirt" in t or "mockneck" in t:  # before "shirt": "sweatshirt" contains it
        return "crewneck"
    return "t-shirt" if "shirt" in t else "other"


GENERIC_TAGS = {"yale", "campus", "custom", "college", "apparel", "merch", "gray", "navy"}


def find_similar_products(
    ctx: RunContext[AgentDeps], product_id: str, size: str | None = None
) -> SimilarProducts:
    """Up to 4 in-stock alternatives to a product: same kind of garment, shared themes (college, sport,
    graphic) and a similar price. Use when an item or size is out of stock, or the shopper asks for
    "something similar" / "other options like this".

    Args:
        product_id: The product to find alternatives for.
        size: Optional size every suggestion must be in stock in (XS, S, M, L, XL, XXL).
    """
    base = _require_product(product_id)
    if size:
        size = size.strip().upper()
        if size not in SIZE_ORDER:
            raise ModelRetry(f"size must be one of {', '.join(SIZE_ORDER)}")

    base_cat = category(base)
    base_tags = set(normalize(" ".join(base["search_tags"]))) - GENERIC_TAGS

    def similarity(p: dict) -> float:
        tags = set(normalize(" ".join(p["search_tags"]))) - GENERIC_TAGS
        shared = len(base_tags & tags) / max(len(base_tags | tags), 1)
        price_gap = abs(p["price"] - base["price"]) / base["price"]
        return 3.0 * (category(p) == base_cat) + 4.0 * shared - 1.0 * min(price_gap, 1.0)

    def available(p: dict) -> bool:
        if size:
            return any(s["size"] == size and s["in_stock"] for s in p["inventory"])
        return p["total_stock"] > 0

    candidates = [p for p in load_all_products() if p["product_id"] != base["product_id"] and available(p)]
    best = sorted(candidates, key=similarity, reverse=True)[:4]
    return SimilarProducts(based_on=base["name"], size=size, products=[summarize(p) for p in best])


def get_customer_info(ctx: RunContext[AgentDeps]) -> CustomerInfo:
    """Who you are chatting with: logged_in, first_name, last_name, email. All empty for guests."""
    return ctx.deps.customer


def get_current_page(ctx: RunContext[AgentDeps]) -> PageInfo:
    """The page the shopper is on right now. On a product page, includes that product (id, name, price,
    colors, sizes in stock). Use it when the shopper says "this", "it" or "this one"."""
    return ctx.deps.page


TOOLS = [
    search_products,
    get_product_description,
    get_product_price,
    check_stock,
    find_similar_products,
    get_customer_info,
    get_current_page,
]
