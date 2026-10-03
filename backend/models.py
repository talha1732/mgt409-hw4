"""Pydantic / PydanticAI structured types for the Campus Customs chatbot."""

from pydantic import BaseModel, Field


# ---------- What the tools hand the agent ----------

class SizeStock(BaseModel):
    size: str
    quantity: int
    in_stock: bool


class ProductSummary(BaseModel):
    """Compact search result, so a search over 102 products stays cheap in tokens."""

    product_id: str
    name: str
    garment_type: str
    price: float
    colors: list[str]
    sizes_in_stock: list[str]
    total_stock: int


class SearchResults(BaseModel):
    """search_products result: the top matches plus how many matched overall (so the agent can say "we have 18")."""

    total_matches: int
    matched_all_terms: bool = Field(
        description="False means nothing matched every word of the query, so these are only partial "
        "matches (e.g. 'pink hoodie' -> hoodies that aren't pink). Say so instead of presenting them as matches."
    )
    products: list[ProductSummary]


class ProductDescription(BaseModel):
    """Answer to "tell me about this item": what it is and what it looks like. No price or stock."""

    product_id: str
    name: str
    garment_type: str
    description: str
    colors: list[str]


class ProductPrice(BaseModel):
    """Answer to "how much is it?". The exact DB price, never estimated."""

    product_id: str
    name: str
    price: float
    currency: str = "USD"


class StockResult(BaseModel):
    """Answer to "is it in stock (in size M)?". Spells out out-of-stock so the model can't miss it."""

    product_id: str
    name: str
    size_requested: str | None = Field(description="The size asked about, or None if no size was given.")
    requested_size_quantity: int | None = Field(description="Units in the requested size; None if no size given.")
    requested_size_in_stock: bool | None
    sizes: list[SizeStock] = Field(description="Every size with its quantity, XS to XXL.")
    sizes_in_stock: list[str]
    total_stock: int
    summary: str = Field(description="One plain-English line, e.g. 'Size L is OUT OF STOCK.'")


class SimilarProducts(BaseModel):
    """In-stock alternatives to one product, e.g. when the shopper's size is sold out."""

    based_on: str = Field(description="Name of the product the suggestions are similar to.")
    size: str | None = Field(description="If set, every suggestion is in stock in this size.")
    products: list[ProductSummary]


class CustomerInfo(BaseModel):
    """Who is chatting. Comes from the session cookie on the server, never from what the shopper types."""

    logged_in: bool
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None


class PageInfo(BaseModel):
    """What the shopper is looking at right now, so "this" / "it" can be resolved."""

    path: str = Field(description="Website path, e.g. '/products/morse-1-4-zip' or '/products'.")
    page_type: str = Field(description="home, products, product_detail, about, login, create_account or other")
    product: ProductSummary | None = Field(
        default=None, description="The product on the page when page_type is product_detail."
    )


# ---------- What the agent must return ----------

class ChatReply(BaseModel):
    """The agent's structured answer. Validated before it reaches the website."""

    reply: str = Field(description="Message to the shopper, in Markdown. Short and friendly.")
    product_ids: list[str] = Field(
        default_factory=list,
        description="product_id of each item to show as a product card on the website, best match first "
        "(max 12). Only IDs returned by a tool in this conversation. Empty if no products fit.",
        max_length=12,
    )


# ---------- What the API sends to / receives from the front end ----------

class HistoryMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(max_length=4000)


class PageContext(BaseModel):
    """Sent by the browser with every chat message. Only a path; the server looks up the product itself."""

    path: str = Field(default="/", max_length=200)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    # Used for guests only. For logged-in shoppers the server loads history from chat_messages.
    history: list[HistoryMessage] = Field(default_factory=list, max_length=40)
    page: PageContext = Field(default_factory=PageContext)


class ProductCard(BaseModel):
    """One card the website renders for a chat search result. Built from the DB, not from the model's text."""

    product_id: str
    name: str
    garment_type: str
    price: float
    image_url: str
    description: str
    colors: list[str] = Field(default_factory=list)
    total_stock: int


class ChatResponse(BaseModel):
    reply: str
    products: list[ProductCard]
