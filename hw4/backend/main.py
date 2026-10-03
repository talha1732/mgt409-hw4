"""Campus Customs API: products, images, auth and the chat agent.

Run from the backend/ folder:
    uvicorn main:app --reload --port 8000
"""

import json
import logging
import sqlite3

from fastapi import Cookie, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pydantic_ai.exceptions import ModelHTTPError

import auth
import guard
from agent import run_chat
from models import ChatReply, ChatRequest, ChatResponse, CustomerInfo, HistoryMessage, ProductCard
from tools import DATA_DIR, AgentDeps, build_page_info, get_conn, load_all_products, load_product

log = logging.getLogger("campus_customs")

app = FastAPI(title="Campus Customs API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)
# Images are stored as "products/x.jpg" relative to data/, so mount products/ at /images.
app.mount("/images", StaticFiles(directory=DATA_DIR / "products"), name="images")

with get_conn() as _conn:
    auth.ensure_sessions_table(_conn)
    if auth.ensure_demo_account(_conn):
        log.warning("Converted the demo account (%s) to the current password-hash format.", auth.DEMO_EMAIL)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/products")
def list_products():
    return load_all_products()


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    product = load_product(product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


# ---------- Auth ----------

class SignupRequest(BaseModel):
    first_name: str
    last_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def public_user(row: sqlite3.Row) -> dict:
    """The only user fields ever sent to the browser (never password_hash)."""
    return {
        "id": row["id"],
        "first_name": row["first_name"] or row["name"].split(" ")[0],
        "last_name": row["last_name"] or "",
        "email": row["email"],
    }


def set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        auth.SESSION_COOKIE,
        token,
        max_age=auth.SESSION_DAYS * 86400,
        httponly=True,  # JavaScript (and any injected script) can't read it
        samesite="lax",
        # secure=True once served over HTTPS
    )


@app.post("/api/auth/signup")
def signup(req: SignupRequest, response: Response):
    first, last = req.first_name.strip(), req.last_name.strip()
    email = req.email.strip().lower()
    if not first or not last:
        raise HTTPException(400, "First and last name are required.")
    if "@" not in email or "." not in email.split("@")[-1]:
        raise HTTPException(400, "Please enter a valid email address.")
    if len(req.password) < 8:
        raise HTTPException(400, "Password must be at least 8 characters.")
    with get_conn() as conn:
        if conn.execute("SELECT 1 FROM users WHERE lower(email) = ?", (email,)).fetchone():
            raise HTTPException(409, "An account with this email already exists.")
        cur = conn.execute(
            "INSERT INTO users (name, first_name, last_name, email, password_hash) VALUES (?, ?, ?, ?, ?)",
            (f"{first} {last}", first, last, email, auth.hash_password(req.password)),
        )
        row = conn.execute("SELECT * FROM users WHERE id = ?", (cur.lastrowid,)).fetchone()
        set_session_cookie(response, auth.create_session(conn, row["id"]))
    return public_user(row)


@app.post("/api/auth/login")
def login(req: LoginRequest, response: Response):
    email = req.email.strip().lower()
    if auth.is_locked_out(email):
        raise HTTPException(429, "Too many failed attempts. Please try again in 15 minutes.")
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM users WHERE lower(email) = ?", (email,)).fetchone()
        stored = row["password_hash"] if row else auth._DUMMY_HASH
        if not auth.verify_password(req.password, stored) or row is None:
            auth.record_failure(email)
            # Same message whether the email or the password was wrong.
            raise HTTPException(401, "Invalid email or password.")
        auth.clear_failures(email)
        set_session_cookie(response, auth.create_session(conn, row["id"]))
    return public_user(row)


@app.post("/api/auth/logout")
def logout(response: Response, cc_session: str | None = Cookie(default=None)):
    with get_conn() as conn:
        auth.delete_session(conn, cc_session)
    response.delete_cookie(auth.SESSION_COOKIE)
    return {"ok": True}


@app.get("/api/auth/me")
def me(cc_session: str | None = Cookie(default=None)):
    with get_conn() as conn:
        user_id = auth.user_id_for_session(conn, cc_session)
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone() if user_id else None
    # Guests get null (not a 401): not being logged in is a normal state, not an error.
    return public_user(row) if row else None


# ---------- Chat ----------

def current_user(conn: sqlite3.Connection, token: str | None) -> sqlite3.Row | None:
    user_id = auth.user_id_for_session(conn, token)
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone() if user_id else None


HISTORY_TURNS = 20  # messages of saved history replayed to the agent


def load_history(conn: sqlite3.Connection, user_id: int) -> list[HistoryMessage]:
    """The shopper's last HISTORY_TURNS saved messages, oldest first."""
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT ?",
        (user_id, HISTORY_TURNS),
    ).fetchall()
    return [HistoryMessage(role=r["role"], content=r["content"][:4000]) for r in reversed(rows)]


def to_card(p: dict) -> ProductCard:
    card = {k: p[k] for k in ProductCard.model_fields}
    # Older seed messages stored images as /media/products/x.jpg; this app serves them at /images/x.jpg.
    card["image_url"] = "/images/" + card["image_url"].rsplit("/", 1)[-1]
    return ProductCard(**card)


@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, cc_session: str | None = Cookie(default=None)):
    # Mask card numbers / SSNs / passwords before anything reaches the model or the DB.
    message, flagged = guard.redact(req.message)

    with get_conn() as conn:
        user = current_user(conn, cc_session)
        # Logged in: memory comes from our DB (source of truth), not from what the browser sends.
        if user:
            history = load_history(conn, user["id"])
        else:
            history = [h.model_copy(update={"content": guard.redact(h.content)[0]}) for h in req.history]

    if user:
        u = public_user(user)
        customer = CustomerInfo(
            logged_in=True, first_name=u["first_name"], last_name=u["last_name"], email=u["email"]
        )
    else:
        customer = CustomerInfo(logged_in=False)
    deps = AgentDeps(customer=customer, page=build_page_info(req.page.path))

    try:
        out = await run_chat(message, history, deps, redactions=flagged)
    except ModelHTTPError as e:
        if "content_filter" not in str(e.body):
            log.exception("Agent run failed")
            raise HTTPException(502, "The assistant is having trouble right now. Please try again.")
        # The model provider's safety filter blocked the message (e.g. a jailbreak attempt).
        log.warning("Message blocked by provider content filter")
        out = ChatReply(
            reply="Sorry, I can't help with that. I'm happy to help you find Campus Customs gear, though! "
            "What are you shopping for?"
        )
    except Exception:
        log.exception("Agent run failed")
        raise HTTPException(502, "The assistant is having trouble right now. Please try again.")

    products = [p for pid in dict.fromkeys(out.product_ids) if (p := load_product(pid))]
    reply = (guard.warning(flagged) + out.reply) if flagged else out.reply

    # Logged-in shoppers keep their conversation (and the cards shown) in chat_messages.
    if user:
        with get_conn() as conn:
            conn.execute(
                "INSERT INTO chat_messages (user_id, role, content) VALUES (?, 'user', ?)",
                (user["id"], message),  # the redacted text, never the original
            )
            conn.execute(
                "INSERT INTO chat_messages (user_id, role, content, products_json) VALUES (?, 'assistant', ?, ?)",
                (user["id"], reply, json.dumps(products) if products else None),
            )

    return ChatResponse(reply=reply, products=[to_card(p) for p in products])


@app.get("/api/chat/history")
def chat_history(cc_session: str | None = Cookie(default=None)):
    """The logged-in shopper's own past messages (last 40). Guests get an empty list."""
    with get_conn() as conn:
        user = current_user(conn, cc_session)
        if user is None:
            return []
        rows = conn.execute(
            "SELECT role, content, products_json FROM chat_messages WHERE user_id = ? ORDER BY id DESC LIMIT 40",
            (user["id"],),
        ).fetchall()
    return [
        {
            "role": r["role"],
            "content": r["content"],
            "products": [to_card(p).model_dump() for p in json.loads(r["products_json"] or "[]")],
        }
        for r in reversed(rows)
    ]
