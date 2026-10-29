# 05 store

Line by line for [app/store.py](../../app/store.py). This is the model: `server.py` decides what to do, and this file reads and writes sqlite.

## Open

```python
def connect() -> sqlite3.Connection:
    path = os.environ.get("DATABASE_PATH", "data/camagru.sqlite3")
    parent = os.path.dirname(path)

    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    return conn
```

`DATABASE_PATH` is the file, defaulting to `data/camagru.sqlite3` outside Docker, and `makedirs` creates its parent directory. `row_factory = sqlite3.Row` makes a row readable by column name, `row["email"]`, not only by position. `executescript` runs the schema, and because every statement is `create table if not exists` or `create unique index if not exists`, opening the file again does not wipe any rows.

A production app usually keeps schema changes in ordered migration files that run once. This subject wants one command and no setup step, so the tables are created on open instead, and there is no migration history. Adding a column later means a new `create` or an `alter` that is safe to run every time.

https://docs.python.org/3/library/sqlite3.html#sqlite3.connect
https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.row_factory
https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.executescript

## Tables

```sql
create table if not exists users (
    id integer primary key,
    username text not null,
    email text not null,
    password text not null,
    session_version integer not null default 1,
    confirmed integer not null default 0,
    mail_ok integer not null default 1
);
create table if not exists tokens (
    user_id integer not null,
    kind text not null,
    token_hash text not null,
    expires_at integer not null
);
create unique index if not exists users_username_lower on users (lower(username));
create unique index if not exists users_email_lower on users (lower(email));
```

These are the account tables. The same `SCHEMA` string also creates `pictures`, `likes`, and `comments`; the `pictures` table is walked in [15-pictures.md](15-pictures.md) and the `likes` uniqueness rule in [19-gallery-query.md](19-gallery-query.md).

SQLite has no boolean storage; the SQL keywords `TRUE` and `FALSE` are aliases for the integers 1 and 0, so these flag columns are integers. Python treats 0 as falsy and 1 as truthy, which is why `if row["confirmed"]` works without a real boolean type. https://www.sqlite.org/datatype3.html

`password` holds the `salt$hash` string, never the password. `confirmed` stays 0 until the mail link is consumed. `mail_ok` is the comment-mail preference: 1, the default, means a new comment emails the author. The profile form writes it and the gallery reads it before sending the letter.

The two indexes make `Bob` and `bob` the same username, and likewise for email, so a second insert raises `IntegrityError`, which `insert_user` catches and turns into `None`. `find_user` and `email_taken` compare with `lower(?)`, and the value stays a bound parameter, so a quote in a password or a name is data, not SQL.

https://docs.python.org/3/library/sqlite3.html#sqlite3.IntegrityError

## Users

`insert_user` hashes the password, then inserts the row with `session_version` 1, `confirmed` 0, and `mail_ok` 1. `password_matches` is `verify_password` against the stored string.

`confirm_user` sets `confirmed` to 1. `set_password` stores a new hash, adds 1 to `session_version`, and sets `confirmed` to 1, so a finished reset also confirms the account. `end_session` only adds 1 to the version. `update_profile` is walked with `_profile` in [02-server.md](02-server.md).

## One-time links

`TOKEN_TTL` is 3600 seconds, one hour.

```python
def issue_token(
    conn: sqlite3.Connection,
    user_id: int,
    kind: str,
    now: int | None = None,
) -> str:
    moment = int(time.time()) if now is None else int(now)
    token = secrets.token_urlsafe(32)
    digest = hashlib.sha256(token.encode()).hexdigest()

    conn.execute("delete from tokens where user_id = ? and kind = ?", (user_id, kind))
    conn.execute(
        """
        insert into tokens (user_id, kind, token_hash, expires_at)
        values (?, ?, ?, ?)
        """,
        (user_id, kind, digest, moment + TOKEN_TTL),
    )
    conn.commit()

    return token
```

`token_urlsafe(32)` is the secret that goes in the mail, and the row stores only its `sha256`, so a stolen database contains no usable link. The delete before the insert drops the previous token of the same kind, which means a second signup mail or a second reset mail replaces the first. `kind` is `"confirm"` or `"reset"`, and signup and the reset request are the only callers.

Neither function is CSRF. The CSRF field is the HMAC of the user id and `session_version`, checked on every member form, and it has no row in this table. A mail link is a different secret: random bytes, stored as a hash, and deleted when used.

```python
def consume_token(
    conn: sqlite3.Connection,
    kind: str,
    token: str,
    now: int | None = None,
) -> int | None:
    moment = int(time.time()) if now is None else int(now)
    digest = hashlib.sha256(token.encode()).hexdigest()
    row = one(
        conn.execute(
            """
            select user_id from tokens
            where kind = ? and token_hash = ? and expires_at >= ?
            """,
            (kind, digest, moment),
        )
    )

    if row is None:
        return None

    conn.execute(
        "delete from tokens where kind = ? and token_hash = ?",
        (kind, digest),
    )
    conn.commit()

    return require_int(row, "user_id")
```

`one` and `require_int` come from `app/boundary.py`: `one` returns the first row or `None`, and `require_int` reads `user_id` and raises unless it is an integer. The delete removes just that one row, this kind and this hash, so a confirm click does not delete a reset token or the other way around. `None` means the link is unknown, already used, or older than an hour. `_confirm` and the new-password step of `_reset` are the only callers.

https://docs.python.org/3/library/secrets.html#secrets.token_urlsafe
https://docs.python.org/3/library/hashlib.html#hashlib.sha256
