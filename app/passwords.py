"""Password rule and storage.

The defense maps these to PHP's standard library:
hash_pbkdf2 https://www.php.net/manual/en/function.hash-pbkdf2.php
hash_equals https://www.php.net/manual/en/function.hash-equals.php
"""

import hashlib  # https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac
import hmac  # https://docs.python.org/3/library/hmac.html#hmac.compare_digest
import secrets  # https://docs.python.org/3/library/secrets.html#secrets.token_bytes

ITERATIONS = 600000
DIGEST = "sha256"


def password_codes(password: object) -> list[str]:
    """The rules this password fails. Empty means it is acceptable.

    short and long are separate so a 10-character word is not told it has the wrong length.
    """
    # A missing or non-text value fails like a password with no letter and no digit.
    if not isinstance(password, str):
        return ["letter", "digit"]

    codes: list[str] = []

    if len(password) < 8:
        codes.append("short")

    if len(password) > 128:
        codes.append("long")

    if not any("a" <= char.lower() <= "z" for char in password):
        codes.append("letter")

    if not any(char.isdigit() for char in password):
        codes.append("digit")

    return codes


def accept_password(password: object) -> bool:
    """True when password_codes is empty."""
    return not password_codes(password)


def hash_password(password: str) -> str:
    """Return salt$hash. A new 16-byte salt means equal passwords store differently.

    PBKDF2-SHA256, 600000 iterations:
    https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac
    Salt: https://docs.python.org/3/library/secrets.html#secrets.token_bytes
    """
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(DIGEST, password.encode(), salt, ITERATIONS)

    return salt.hex() + "$" + digest.hex()


def verify_password(password: str, stored: str) -> bool:
    """Re-derive the hash with the stored salt and compare in constant time.

    https://docs.python.org/3/library/hmac.html#hmac.compare_digest
    PHP: hash_equals. A plain == would leak how much of the hash matched.
    """
    salt_hex, digest_hex = stored.split("$", 1)
    digest = hashlib.pbkdf2_hmac(
        DIGEST,
        password.encode(),
        bytes.fromhex(salt_hex),
        ITERATIONS,
    )

    return hmac.compare_digest(digest.hex(), digest_hex)
