"""Sensitive-data guard for chat messages.

Runs in plain Python *before* a message reaches the model provider or the database, so a
card number, SSN or password typed into the chat is never sent out or stored. This doesn't
rely on the model following its prompt.
"""

import re

CARD_CANDIDATE = re.compile(r"\b(?:\d[ -]?){12,18}\d\b")  # 13-19 digits, optional spaces/dashes
SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
# "my password is hunter2", "password: hunter2", "pwd=hunter2" (needs is / : / = so "password policy" is safe)
PASSWORD = re.compile(r"(?i)\b(password|passcode|passwd|pwd)(\s*(?:is|:|=)\s*)(\S+)")

NOTICES = {
    "card": "a card number",
    "ssn": "a Social Security number",
    "password": "a password",
}


def _luhn_ok(digits: str) -> bool:
    """Checksum every real card number passes; avoids flagging order numbers or phone numbers."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d = d * 2 - 9 if d > 4 else d * 2
        total += d
    return total % 10 == 0


def redact(text: str) -> tuple[str, list[str]]:
    """Return (text with sensitive data masked, kinds found)."""
    found: list[str] = []

    def card(m: re.Match) -> str:
        digits = re.sub(r"\D", "", m.group())
        if 13 <= len(digits) <= 19 and _luhn_ok(digits):
            found.append("card")
            return "[card number removed]"
        return m.group()

    text = CARD_CANDIDATE.sub(card, text)
    text, n = SSN.subn("[SSN removed]", text)
    if n:
        found.append("ssn")
    text, n = PASSWORD.subn(lambda m: f"{m.group(1)}{m.group(2)}[password removed]", text)
    if n:
        found.append("password")
    return text, list(dict.fromkeys(found))


def warning(kinds: list[str]) -> str:
    what = " and ".join(NOTICES[k] for k in kinds)
    return (
        f"🔒 For your safety I removed {what} from your message. It wasn't sent to our assistant "
        "or saved. Please never share payment details or passwords in chat.\n\n"
    )
