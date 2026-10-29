# 03 session

Line by line for [app/session.py](../../app/session.py). The subject sentence for the cookie is in [02-server.md](02-server.md); this file is where that cookie and the CSRF field are built.

## The signature

Both values are HMAC-SHA256, keyed by `CAMAGRU_SECRET`, over the payload string, with the result in hex.

```python
def _sign(secret: str, payload: str) -> str:
    return hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
```

`encode` turns the strings into bytes, which is what HMAC requires. `compare_digest` compares two hex strings in constant time, so a wrong guess does not finish faster when more of its prefix matches.

https://docs.python.org/3/library/hmac.html#hmac.new
https://docs.python.org/3/library/hmac.html#hmac.compare_digest
https://docs.python.org/3/library/hashlib.html#hashlib.sha256

## Issuing

```python
MAX_AGE = 12 * 3600
```

```python
def issue_cookie(user_id: int, session_version: int, secret: str, now: int) -> str:
    expiry = int(now) + MAX_AGE
    payload = f"{int(user_id)}.{int(session_version)}.{expiry}"
    signature = _sign(secret, payload)

    return payload + "." + signature
```

`MAX_AGE` is twelve hours in seconds, and `now` is the unix time the caller passes in. The cookie text is four dot-separated fields:

```text
user_id.session_version.expiry.signature
```

That layout is ours, not a standard. HTTP only standardises `name=value` plus attributes such as `HttpOnly` and `Max-Age`, so the four fields inside the value are a choice. JWT also uses dots, but this is not JWT.

The signature covers only the first three fields, so changing the user id, the version, or the expiry breaks it. `int(...)` refuses to sign a value that is not a whole number.

## Reading

```python
def _parse(cookie: str, secret: str) -> tuple[int, int, int] | None:
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
```

```python
def read_session(cookie: str, secret: str, now: int, session_version: int) -> int | None:
    parsed = _parse(cookie, secret)

    if parsed is None:
        return None

    user_id, version, expiry = parsed

    if int(now) > expiry or version != int(session_version):
        return None

    return user_id
```

`_parse` checks the signature and nothing else. `read_session` then rejects an expiry in the past and any version that is not the one on the user row. A copied cookie still parses, but it fails on the version line once a logout or a password change has moved the row, so there is no list of cookies to delete.

`server_listens` is `bool(secret)`. An empty secret never gets this far, because `main` exits before it listens, and that matters because an empty key would let anyone compute `_sign`. The secret is not in the git tree, Compose has no default for it, and `.env` is gitignored, since a committed secret would let anyone sign a login cookie.

## CSRF field

```python
def csrf_token(user_id: int, session_version: int, secret: str) -> str:
    payload = f"{int(user_id)}.{int(session_version)}"

    return _sign(secret, payload)


def csrf_accepts(token: str, user_id: int, session_version: int, secret: str) -> bool:
    if not token or not secret:
        return False

    expected = csrf_token(user_id, session_version, secret)

    return hmac.compare_digest(expected, token)
```

The field is the HMAC of `user_id.version` only, so it is the same for every form in that session and changes when the version bumps, which means a logout also kills a form that was already open. Another site can make the browser send the cookie, but it cannot produce this field.

https://developer.mozilla.org/en-US/docs/Glossary/CSRF
