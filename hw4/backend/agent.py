"""Campus Customs agent -- entry point / wiring.

Builds the PydanticAI agent once (prompt file + model + tools) and exposes
`run_chat()` for the FastAPI chat route in main.py.
"""

import logging
import os
import time
from functools import lru_cache
from pathlib import Path

os.environ.setdefault("PYDANTIC_AI_NO_BANNER", "1")

from openai import AsyncOpenAI
from pydantic_ai import Agent, ModelRetry, RunContext, capture_run_messages
from pydantic_ai.exceptions import ModelHTTPError, UsageLimitExceeded
from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.usage import UsageLimits

import audit
from models import ChatReply, HistoryMessage
from tools import TOOLS, AgentDeps, get_conn

BACKEND_DIR = Path(__file__).resolve().parent
PROMPT_PATH = BACKEND_DIR / "prompts" / "prompt.md"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
# Caps one chat turn so a confused model can't loop on tool calls.
USAGE_LIMITS = UsageLimits(request_limit=8)


def load_env() -> None:
    """Read the nearest .env walking up from backend/ (the course folder keeps one shared .env).

    Uses setdefault, so a real environment variable always wins over the file.
    """
    for folder in (BACKEND_DIR, *BACKEND_DIR.parents):
        env_path = folder / ".env"
        if not env_path.exists():
            continue
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
        return


load_env()
MODEL = os.getenv("OPENAI_MODEL", "gpt-5.6-luna")


@lru_cache(maxsize=1)
def build_agent() -> Agent[AgentDeps, ChatReply]:
    api_key = os.getenv("PORTKEY_API_KEY")
    if not api_key:
        raise RuntimeError("PORTKEY_API_KEY is missing from the environment or .env")

    client = AsyncOpenAI(
        api_key=api_key,
        base_url=PORTKEY_BASE_URL,
        default_headers={"x-portkey-api-key": api_key},
    )
    model = OpenAIChatModel(MODEL, provider=OpenAIProvider(openai_client=client))

    agent = Agent(
        model,
        deps_type=AgentDeps,
        output_type=ChatReply,
        # `instructions` (not system_prompt) so the prompt is sent on every turn, even with history.
        instructions=PROMPT_PATH.read_text(encoding="utf-8").strip(),
        tools=TOOLS,
        retries=2,
    )

    @agent.instructions
    def session_context(ctx: RunContext[AgentDeps]) -> str:
        """Fresh every turn: who is chatting and what page they're on (built in code, not by the shopper)."""
        c, page = ctx.deps.customer, ctx.deps.page
        if c.logged_in:
            who = f"Logged in as {c.first_name} {c.last_name} ({c.email})."
        else:
            who = "Guest (not logged in). You don't know their name or email; don't guess."
        if page.product:
            p = page.product
            where = (
                f"Viewing the product page for **{p.name}** (product_id `{p.product_id}`). "
                f'If they say "this", "it" or "this one" without naming another item, they mean this product.'
            )
        else:
            where = f"On the {page.page_type.replace('_', ' ')} page ({page.path}). No specific product is open."
        return f"## Current session (from the server)\n- Shopper: {who}\n- Page: {where}"

    @agent.output_validator
    def known_products_only(ctx: RunContext[AgentDeps], output: ChatReply) -> ChatReply:
        """Reject product cards for IDs that aren't in the catalogue (i.e. made up)."""
        if output.product_ids:
            with get_conn() as conn:
                placeholders = ",".join("?" * len(output.product_ids))
                found = {
                    r[0]
                    for r in conn.execute(
                        f"SELECT product_id FROM catalogue WHERE product_id IN ({placeholders})",
                        output.product_ids,
                    )
                }
            unknown = [pid for pid in output.product_ids if pid not in found]
            if unknown:
                raise ModelRetry(f"These product_ids don't exist: {unknown}. Only use IDs returned by a tool.")
        return output

    return agent


def to_model_history(history: list[HistoryMessage]) -> list[ModelMessage]:
    """Website chat history (plain text) -> PydanticAI message history."""
    messages: list[ModelMessage] = []
    for m in history:
        if m.role == "user":
            messages.append(ModelRequest(parts=[UserPromptPart(content=m.content)]))
        else:
            messages.append(ModelResponse(parts=[TextPart(content=m.content)]))
    return messages


async def run_chat(
    message: str, history: list[HistoryMessage], deps: AgentDeps, redactions: list[str] | None = None
) -> ChatReply:
    """Run one chat turn and append what the agent loop did to output/audit_trail.json."""
    model_history = to_model_history(history)
    started = time.perf_counter()
    entry: dict = {
        "time": audit.now_iso(),
        "model": MODEL,
        "shopper": "logged_in" if deps.customer.logged_in else "guest",
        "page": deps.page.path,
        "message": audit._short(message),  # already guard-redacted by main.py
        "history_messages": len(model_history),
        "guard_redactions": redactions or [],
    }
    with capture_run_messages() as messages:
        try:
            result = await build_agent().run(
                message, message_history=model_history, deps=deps, usage_limits=USAGE_LIMITS
            )
            u = result.usage  # a property in PydanticAI 2.x
            entry.update(
                stop_reason="final_output",
                output={"reply": audit._short(result.output.reply), "product_ids": result.output.product_ids},
                usage={"requests": u.requests, "tool_calls": u.tool_calls,
                       "input_tokens": u.input_tokens, "output_tokens": u.output_tokens},
            )
            return result.output
        except UsageLimitExceeded as e:
            entry.update(stop_reason="usage_limit", error=audit._short(str(e)))
            raise
        except ModelHTTPError as e:
            blocked = "content_filter" in str(e.body)
            entry.update(stop_reason="blocked_by_provider_filter" if blocked else f"model_http_error_{e.status_code}")
            raise
        except Exception as e:
            entry.update(stop_reason="error", error=f"{type(e).__name__}: {audit._short(str(e))}")
            raise
        finally:
            # Only this run's messages (skip the replayed history).
            entry["steps"] = audit.steps_from(messages[len(model_history):])
            entry["duration_ms"] = round((time.perf_counter() - started) * 1000)
            try:
                audit.record(entry)
            except Exception:  # auditing must never break the shopper's chat
                logging.getLogger("campus_customs").exception("Could not write audit trail")
