# 04 passwords

Line by line for [app/passwords.py](../../app/passwords.py). The one-paragraph version of the salt is in [02-server.md](02-server.md).

For the defense, these map to PHP: `hashlib.pbkdf2_hmac` is `hash_pbkdf2`, and `hmac.compare_digest` is `hash_equals`.

https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac
https://www.php.net/manual/en/function.hash-pbkdf2.php
https://docs.python.org/3/library/hmac.html#hmac.compare_digest
https://www.php.net/manual/en/function.hash-equals.php

## The rule

The subject says a simple lowercase word is refused but does not define the rest, so the rule we defend is 8 to 128 characters, one ASCII letter, and one digit. The 128 cap stops a huge string from spending the hash budget.

```python
def password_codes(password: object) -> list[str]:
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
```

A value that is not text fails like a password with no letter and no digit. `short` and `long` are separate codes, so a 10-character word is not told it has the wrong length. The page lists only the codes that came back, under `Invalid password.`, so `Passwordzz` returns `["digit"]`. `accept_password` is true when the list is empty.

## Storing

```python
ITERATIONS = 600000
DIGEST = "sha256"
```

```python
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(DIGEST, password.encode(), salt, ITERATIONS)

    return salt.hex() + "$" + digest.hex()
```

`token_bytes(16)` is 16 random bytes, a new salt on every call, so two users with the same password do not get the same stored string.

PBKDF2 runs SHA-256 over the password and the salt, then feeds the result back in, 600000 times. That count is the cost, and it is what keeps a stolen database from being guessed quickly. 600000 is the OWASP figure for PBKDF2-SHA256.

`hex` turns the bytes into text, and the `$` is our separator, not part of either value, so the column looks like `salt_hex$hash_hex`.

https://docs.python.org/3/library/secrets.html#secrets.token_bytes
https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac

## Checking

```python
def verify_password(password: str, stored: str) -> bool:
    salt_hex, digest_hex = stored.split("$", 1)
    digest = hashlib.pbkdf2_hmac(
        DIGEST,
        password.encode(),
        bytes.fromhex(salt_hex),
        ITERATIONS,
    )

    return hmac.compare_digest(digest.hex(), digest_hex)
```

`split("$", 1)` cuts at the first `$`, leaving the salt on the left and the stored hash on the right. `bytes.fromhex` turns the salt text back into the 16 bytes. The same function, salt, and iteration count either reproduce the stored hash or they do not.

`compare_digest` is the constant-time compare. A plain `==` can finish early when the first bytes differ, which leaks how close a guess was.

https://docs.python.org/3/library/stdtypes.html#bytes.fromhex
https://docs.python.org/3/library/hmac.html#hmac.compare_digest

The password from the form is only the input to this function and is then discarded; it is never written to the row, the cookie, or a log.

## `not []`

An empty list is falsy, so `not []` is `True`, while a non-empty list is truthy, so `not ["digit"]` is `False`. `accept_password` is that one expression: true only when `password_codes` returned nothing.

## HMAC

HMAC means hash-based message authentication code. It is not a hash of the message alone: it mixes the message with a secret key, so someone without the key cannot produce the same result.

`hmac.new` builds that code, while `hmac.compare_digest` only compares two strings in constant time; they are not two strengths of hash. This file uses `compare_digest` in `verify_password`, on the line that returns. The cookie uses `hmac.new` in `session._sign`, walked in [03-session.md](03-session.md).

https://docs.python.org/3/library/hmac.html

## SHA-256, PBKDF2, OWASP

SHA-256 means Secure Hash Algorithm 2 with a 256-bit result. It is one hash function, which turns bytes into a 32-byte digest quickly, and the same input always gives the same digest.

PBKDF2 means Password-Based Key Derivation Function 2. It is a recipe that calls a hash function many times; here that function is SHA-256, and the recipe also takes the salt and the iteration count. SHA-256 alone would be a bad password store, because it is built to be fast and a stolen database could be guessed quickly. PBKDF2 exists to be slow on purpose.

OWASP means the Open Worldwide Application Security Project, which publishes the cheat sheets this iteration count comes from. 600000 is their figure for PBKDF2-HMAC-SHA256, not a number from the subject.

https://docs.python.org/3/library/hashlib.html#hashlib.sha256
https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

The string `"sha256"` is not a secret, and hiding it would not help. Both calls must pass the same name or every password check would fail, so it lives in `DIGEST` next to `ITERATIONS`. The constant is there so the two calls cannot drift, not to hide the algorithm.

## `fromhex`

`secrets.token_bytes(16)` returns raw bytes, and `.hex()` turns them into text so they can sit in the column. `bytes.fromhex` is the inverse of `.hex()`, not of `token_bytes`: it turns the stored salt text back into the 16 bytes PBKDF2 needs.

## A leaked database

The iterations re-hash the previous result that many times, so guessing one password from a stolen file costs 600000 hashes instead of one. A leak is still serious, because the slowdown is not encryption: anyone with the file can guess offline, with no rate limit from our server, until a weak password falls out. The salt sits in that file next to the hash and is not a secret; it only stops one guess from being reused on every user. `CAMAGRU_SECRET` is not in the database, so a stolen sqlite file does not reveal the key that signs cookies.
