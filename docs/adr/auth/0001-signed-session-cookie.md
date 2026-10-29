# ADR 0001: Signed session cookie

Date: 2026-10-21

## Status

Accepted

## Context

v4.1 printed page 7 requires login with username and password, logout in one click, and profile edits. Printed page 6 says a plain or unencrypted password is not secure and that an outside form must not edit private data, and the introduction names CSRF as a notion to learn. The subject names no session store and no password algorithm, and it does not define the "minimum level of complexity" on printed page 7. A reversible cipher would let anyone with the database read the password back, and clearing a cookie on logout does not invalidate a copy another party already holds. PHP's `hash_pbkdf2` and `hash_equals` are standard library, and Python's matches are `hashlib.pbkdf2_hmac` and `hmac.compare_digest`.

## Decision

I will store a salted SHA-256 PBKDF2 hash with 600000 iterations, never the password, with the salt beside the hash in `sqlite3`. I will accept a password only when it has 8 to 128 characters, at least one ASCII letter, and at least one digit, so `password`, `12345678`, and `AAAAAAAA` fail and `Password1` passes.

I will keep login state in one HMAC-SHA256 cookie, HttpOnly and SameSite=Lax, whose payload is the user id, a `session_version` integer, and an expiry unix time. The signing key is `CAMAGRU_SECRET`, which also signs the CSRF token, and if that variable is missing or empty the process exits before it listens. The cookie is marked Secure only when `CAMAGRU_BASE_URL` starts with `https`; `make up` defaults to an `http` URL, so the flag is off there. Max age is 12 hours.

Each user row has a `session_version` that starts at 1 and goes up on logout, on a password change, and on a completed reset. A request is logged in only when the signature matches, the expiry is in the future, and `session_version` equals the row. Logout is a POST that carries the CSRF token, and it also clears the cookie.

Authenticated forms carry a hidden token equal to the HMAC of the user id and `session_version`, compared with `hmac.compare_digest`. Signup, login, and the reset request have no session, so those forms rely on SameSite=Lax instead of a second token. Login matches the username case-insensitively, and the page shows the stored spelling.

A reset or confirmation token is 32 bytes from `secrets`, stored as SHA-256, and expires after 1 hour. Using it once deletes it, and issuing a new token of the same kind replaces the previous one.

## Consequences

There is no session table and no auth package. A copied cookie dies on logout and on a password change, because the version has moved. The defense shows `hashlib.pbkdf2_hmac` against `hash_pbkdf2`, and `hmac.compare_digest` against `hash_equals`. A stricter password rule, a requirement to store a reversible cipher, or an HTTPS-only defense reopens this ADR. The routes that depend on it are in [the spec](../../SPEC.md).
