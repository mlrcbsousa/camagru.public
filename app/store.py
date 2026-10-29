"""Users and one-time links in sqlite.

Passwords are the salted hashes from app.passwords.
A token row stores the SHA-256 of the link, never the link.
https://docs.python.org/3/library/hashlib.html#hashlib.sha256
https://docs.python.org/3/library/secrets.html#secrets.token_urlsafe
"""

import hashlib  # https://docs.python.org/3/library/hashlib.html#hashlib.sha256
import os  # https://docs.python.org/3/library/os.html
import secrets  # https://docs.python.org/3/library/secrets.html#secrets.token_urlsafe
import sqlite3  # https://docs.python.org/3/library/sqlite3.html
import time  # https://docs.python.org/3/library/time.html#time.time

from app.boundary import (
    Comment,
    GalleryRow,
    PictureAuthor,
    PictureFile,
    Thumb,
    User,
    author_from_row,
    comment_from_row,
    gallery_row,
    many,
    one,
    picture_file,
    require_int,
    thumb_from_row,
    user_from_row,
)
from app.passwords import hash_password, verify_password

SCHEMA = """
create table if not exists users (
    id integer primary key,
    username text not null,
    email text not null,
    password text not null,
    session_version integer not null default 1,
    confirmed integer not null default 0,
    mail_ok integer not null default 1
);
create table if not exists pictures (
    id integer primary key,
    user_id integer not null,
    image_bytes blob not null,
    created_at integer not null
);
create table if not exists likes (
    user_id integer not null,
    picture_id integer not null,
    unique (user_id, picture_id)
);
create table if not exists comments (
    id integer primary key,
    picture_id integer not null,
    user_id integer not null,
    body text not null
);
create table if not exists tokens (
    user_id integer not null,
    kind text not null,
    token_hash text not null,
    expires_at integer not null
);
create unique index if not exists users_username_lower on users (lower(username));
create unique index if not exists users_email_lower on users (lower(email));
"""

TOKEN_TTL = 3600


def connect() -> sqlite3.Connection:
    """Open the sqlite file and create the tables when they are missing.

    https://docs.python.org/3/library/sqlite3.html#sqlite3.connect
    """
    path = os.environ.get("DATABASE_PATH", "data/camagru.sqlite3")
    parent = os.path.dirname(path)

    if parent:
        os.makedirs(parent, exist_ok=True)

    conn = sqlite3.connect(path)
    # Row: row["email"] instead of a numeric index.
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)

    return conn


def find_user(conn: sqlite3.Connection, username: str) -> User | None:
    row = one(
        conn.execute(
            "select * from users where lower(username) = lower(?)",
            (username,),
        )
    )

    if row is None:
        return None

    return user_from_row(row)


def find_user_id(conn: sqlite3.Connection, user_id: int) -> User | None:
    row = one(conn.execute("select * from users where id = ?", (user_id,)))

    if row is None:
        return None

    return user_from_row(row)


def username_taken(conn: sqlite3.Connection, username: str) -> bool:
    return find_user(conn, username) is not None


def email_taken(conn: sqlite3.Connection, email: str) -> bool:
    row = one(
        conn.execute(
            "select id from users where lower(email) = lower(?)",
            (email,),
        )
    )

    return row is not None


def insert_user(conn: sqlite3.Connection, username: str, email: str, password: str) -> int | None:
    """Insert one unconfirmed user. Return the id, or None if the name or email is taken.

    The unique indexes on lower(username) and lower(email) close the race
    the lookup in the request handler cannot see.
    """
    stored = hash_password(password)

    try:
        cursor = conn.execute(
            """
            insert into users (username, email, password, session_version, confirmed, mail_ok)
            values (?, ?, ?, 1, 0, 1)
            """,
            (username, email, stored),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()

        return None

    return cursor.lastrowid


def password_matches(user: User, password: str) -> bool:
    return verify_password(password, user["password"])


def issue_token(
    conn: sqlite3.Connection,
    user_id: int,
    kind: str,
    now: int | None = None,
) -> str:
    """Return a new mail-link token and store only its hash. Not the CSRF field.

    Kinds are confirm and reset. The previous token of this kind is deleted.
    """
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


def consume_token(
    conn: sqlite3.Connection,
    kind: str,
    token: str,
    now: int | None = None,
) -> int | None:
    """Return the user id and delete the token, so the link works once. None if it is unknown or expired."""
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


def confirm_user(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("update users set confirmed = 1 where id = ?", (user_id,))
    conn.commit()


def set_password(conn: sqlite3.Connection, user_id: int, password: str) -> None:
    """Store a new hash, bump session_version, and mark the account confirmed."""
    stored = hash_password(password)
    conn.execute(
        """
        update users
        set password = ?, session_version = session_version + 1, confirmed = 1
        where id = ?
        """,
        (stored, user_id),
    )
    conn.commit()


def end_session(conn: sqlite3.Connection, user_id: int) -> None:
    """Bump session_version so every cookie issued before this logout stops working."""
    conn.execute(
        "update users set session_version = session_version + 1 where id = ?",
        (user_id,),
    )
    conn.commit()


def insert_picture(conn: sqlite3.Connection, user_id: int, image_bytes: bytes, now: float) -> int | None:
    """Store one picture file for this member and return its id."""
    cursor = conn.execute(
        "insert into pictures (user_id, image_bytes, created_at) values (?, ?, ?)",
        (user_id, image_bytes, int(now)),
    )
    conn.commit()

    return cursor.lastrowid


def list_pictures(conn: sqlite3.Connection, user_id: int) -> list[Thumb]:
    """The member's pictures, newest first. The page shows them as thumbnails."""
    rows = many(
        conn.execute(
            "select id, user_id from pictures where user_id = ? order by id desc",
            (user_id,),
        )
    )

    return [thumb_from_row(row) for row in rows]


def picture_bytes(conn: sqlite3.Connection, picture_id: int) -> PictureFile | None:
    """The stored PNG and its owner, or None."""
    row = one(conn.execute("select image_bytes, user_id from pictures where id = ?", (picture_id,)))

    if row is None:
        return None

    return picture_file(row)


def delete_picture(conn: sqlite3.Connection, picture_id: int, user_id: int) -> bool:
    """Delete the picture only when this member owns it. True when a row went away."""
    cursor = conn.execute(
        "delete from pictures where id = ? and user_id = ?",
        (picture_id, user_id),
    )
    conn.commit()

    return cursor.rowcount == 1


def update_profile(
    conn: sqlite3.Connection,
    user: User,
    username: str,
    email: str,
    password: str,
    mail_ok: bool,
) -> int | None:
    """Save the profile. Return the new session version, or None if the name or email is taken.

    The version moves only when the password changes, which logs out other sessions.
    """
    version = user["session_version"]
    stored = user["password"]

    if password:
        stored = hash_password(password)
        version = version + 1

    try:
        conn.execute(
            """
            update users
            set username = ?, email = ?, password = ?, session_version = ?, mail_ok = ?
            where id = ?
            """,
            (username, email, stored, version, 1 if mail_ok else 0, user["id"]),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()

        return None

    return version


def picture_count(conn: sqlite3.Connection) -> int:
    row = one(conn.execute("select count(*) as n from pictures"))

    if row is None:
        raise ValueError("count")

    return require_int(row, "n")


def gallery_rows(conn: sqlite3.Connection, page_number: int, size: int) -> list[GalleryRow]:
    offset = (int(page_number) - 1) * int(size)
    rows = many(
        conn.execute(
            """
            select pictures.id, pictures.user_id, pictures.created_at,
                   users.username, users.email, users.mail_ok,
                   (select count(*) from likes where likes.picture_id = pictures.id) as likes
            from pictures
            join users on users.id = pictures.user_id
            order by pictures.created_at desc, pictures.id desc
            limit ? offset ?
            """,
            (int(size), offset),
        )
    )

    return [gallery_row(row) for row in rows]


def picture_author(conn: sqlite3.Connection, picture_id: int) -> PictureAuthor | None:
    row = one(
        conn.execute(
            """
            select pictures.id, users.username, users.email, users.mail_ok
            from pictures
            join users on users.id = pictures.user_id
            where pictures.id = ?
            """,
            (picture_id,),
        )
    )

    if row is None:
        return None

    return author_from_row(row)


def like_count(conn: sqlite3.Connection, picture_id: int) -> int:
    row = one(conn.execute("select count(*) as n from likes where picture_id = ?", (picture_id,)))

    if row is None:
        return 0

    return require_int(row, "n")


def like_once(conn: sqlite3.Connection, user_id: int, picture_id: int) -> None:
    conn.execute(
        "insert or ignore into likes (user_id, picture_id) values (?, ?)",
        (user_id, picture_id),
    )
    conn.commit()


def add_comment(conn: sqlite3.Connection, picture_id: int, user_id: int, body: str) -> None:
    conn.execute(
        "insert into comments (picture_id, user_id, body) values (?, ?, ?)",
        (picture_id, user_id, body),
    )
    conn.commit()


def comments_for(conn: sqlite3.Connection, picture_id: int) -> list[Comment]:
    """Each comment with the username of the member who wrote it, oldest first."""
    rows = many(
        conn.execute(
            """
            select comments.body, users.username
            from comments
            join users on users.id = comments.user_id
            where comments.picture_id = ?
            order by comments.id
            """,
            (picture_id,),
        )
    )

    return [comment_from_row(row) for row in rows]
