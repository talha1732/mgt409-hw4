"""Password hashing and login sessions for Campus Customs.

Passwords are never stored. We keep only a salted PBKDF2-SHA256 hash:
  new accounts:   pbkdf2_sha256$<iterations>$<salt>$<hex digest>
  seed accounts:  pbkdf2_sha256$<salt>$<hex digest>   (iterations from LEGACY_ITERATIONS)
Sessions are random tokens sent in an HttpOnly cookie; the DB stores only a SHA-256 of the token.
"""

import hashlib
import hmac
import os
import secrets
import sqlite3
import time
from datetime import datetime, timedelta, timezone

ALGORITHM = "pbkdf2_sha256"
ITERATIONS = 600_000  # OWASP 2023+ recommendation for PBKDF2-SHA256
# Iteration count used by the seed accounts' 3-part hashes. Not documented in the course data, so it
# must be set (env var CC_LEGACY_PBKDF2_ITERATIONS) before seed accounts like the test user can log in.
_legacy = os.environ.get("CC_LEGACY_PBKDF2_ITERATIONS")
LEGACY_ITERATIONS = int(_legacy) if _legacy else None
SESSION_COOKIE = "cc_session"
SESSION_DAYS = 7
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60


def _pbkdf2(password: str, salt: str, iterations: int) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), iterations).hex()


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    return f"{ALGORITHM}${ITERATIONS}${salt}${_pbkdf2(password, salt, ITERATIONS)}"


def verify_password(password: str, stored: str) -> bool:
    parts = stored.split("$")
    if parts[0] != ALGORITHM:
        return False
    if len(parts) == 4:
        _, iterations, salt, digest = parts
        iterations = int(iterations)
    elif len(parts) == 3:
        if LEGACY_ITERATIONS is None:
            return False
        _, salt, digest = parts
        iterations = LEGACY_ITERATIONS
    else:
        return False
    return hmac.compare_digest(_pbkdf2(password, salt, iterations), digest)


# A real hash to check against when the email doesn't exist, so response time doesn't reveal it.
_DUMMY_HASH = hash_password(secrets.token_hex(8))


# The assignment's published demo login. Its seed hash uses the 3-part legacy format with an
# undocumented iteration count, so it can't be verified as shipped in data.zip.
DEMO_EMAIL = "test@campuscustoms.yale.edu"
DEMO_PASSWORD = "password"  # published in the assignment brief, not a secret


def ensure_demo_account(conn: sqlite3.Connection) -> bool:
    """One-time fix so the published demo login works on a fresh data pack.

    Re-hashes ONLY the demo account, and only while its hash is still in the unverifiable
    3-part legacy format. After that (or if CC_LEGACY_PBKDF2_ITERATIONS is set) it does nothing.
    Returns True if it changed the row.
    """
    row = conn.execute("SELECT id, password_hash FROM users WHERE lower(email) = ?", (DEMO_EMAIL,)).fetchone()
    if row is None:
        return False
    parts = row[1].split("$")
    if not (len(parts) == 3 and parts[0] == ALGORITHM and LEGACY_ITERATIONS is None):
        return False
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (hash_password(DEMO_PASSWORD), row[0]))
    return True


def ensure_sessions_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """CREATE TABLE IF NOT EXISTS sessions (
            token_hash TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            expires_at TEXT NOT NULL
        )"""
    )


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_session(conn: sqlite3.Connection, user_id: int) -> str:
    token = secrets.token_urlsafe(32)
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    conn.execute(
        "INSERT INTO sessions (token_hash, user_id, expires_at) VALUES (?, ?, ?)",
        (_token_hash(token), user_id, expires.strftime("%Y-%m-%d %H:%M:%S")),
    )
    return token


def user_id_for_session(conn: sqlite3.Connection, token: str | None) -> int | None:
    if not token:
        return None
    row = conn.execute(
        "SELECT user_id FROM sessions WHERE token_hash = ? AND expires_at > datetime('now')",
        (_token_hash(token),),
    ).fetchone()
    return row[0] if row else None


def delete_session(conn: sqlite3.Connection, token: str | None) -> None:
    if token:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


# In-memory brute-force guard: email -> list of recent failure timestamps.
_failures: dict[str, list[float]] = {}


def is_locked_out(email: str) -> bool:
    now = time.time()
    recent = [t for t in _failures.get(email, []) if now - t < LOCKOUT_SECONDS]
    _failures[email] = recent
    return len(recent) >= MAX_FAILED_LOGINS


def record_failure(email: str) -> None:
    _failures.setdefault(email, []).append(time.time())


def clear_failures(email: str) -> None:
    _failures.pop(email, None)
