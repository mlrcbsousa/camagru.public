"""Login cookie and CSRF token. Both are HMAC-SHA256, keyed by CAMAGRU_SECRET.

There is no session table. The server trusts the cookie only after it checks the signature.
https://docs.python.org/3/library/hmac.html#hmac.new
"""

import hashlib  # https://docs.python.org/3/library/hashlib.html
import hmac  # https://docs.python.org/3/library/hmac.html#hmac.new

MAX_AGE = 12 * 3600


def server_listens(secret: str | None) -> bool:
    """False when the signing key is missing. An empty key would let anyone sign a cookie."""
    return bool(secret)


def issue_cookie(user_id: int, session_version: int, secret: str, now: int) -> str:
    """Return user_id.version.expiry.signature. The signature covers the first three parts."""
    expiry = int(now) + MAX_AGE
    payload = f"{int(user_id)}.{int(session_version)}.{expiry}"
    signature = _sign(secret, payload)

    return payload + "." + signature


def read_session(cookie: str, secret: str, now: int, session_version: int) -> int | None:
    """Return the user id, or None if the signature, the expiry, or the version fails.

    The version check is what makes logout and a password change kill a copied cookie.
    """
    parsed = _parse(cookie, secret)

    if parsed is None:
        return None

    user_id, version, expiry = parsed

    # Expired, or a logout or password change bumped the version after this cookie.
    if int(now) > expiry or version != int(session_version):
        return None

    return user_id


def csrf_token(user_id: int, session_version: int, secret: str) -> str:
    """HMAC of user_id.version. Stable for the life of that session, not per request."""
    payload = f"{int(user_id)}.{int(session_version)}"

    return _sign(secret, payload)


def csrf_accepts(token: str, user_id: int, session_version: int, secret: str) -> bool:
    """Constant-time check of the form token. Another site cannot compute it without the secret.

    https://docs.python.org/3/library/hmac.html#hmac.compare_digest
    """
    if not token or not secret:
        return False

    expected = csrf_token(user_id, session_version, secret)

    return hmac.compare_digest(expected, token)


def _sign(secret: str, payload: str) -> str:
    """HMAC-SHA256 of payload, hex encoded. https://docs.python.org/3/library/hmac.html#hmac.new"""
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()


def _parse(cookie: str, secret: str) -> tuple[int, int, int] | None:
    """Return (user id, version, expiry) after the signature matches, else None."""
    if not cookie or not secret:
        return None

    parts = cookie.split(".")

    if len(parts) != 4:
        return None

    user_id, version, expiry, signature = parts
    payload = f"{user_id}.{version}.{expiry}"
    expected = _sign(secret, payload)

    if not hmac.compare_digest(expected, signature):
        return None

    return int(user_id), int(version), int(expiry)
