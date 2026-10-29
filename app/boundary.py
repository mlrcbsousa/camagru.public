"""Checked edges for sqlite rows, posted forms, and the WSGI environ.

The standard-library stubs type those values as Any. This module is the only
place that reads them. Each read is cast to object, then checked. A column or
header of the wrong type raises ValueError. The request handler already turns
that into the short 500 page, which is the same outcome as a bad row used to
reach later.

A missing form field, or a value that is not text, becomes "". A repeated
field keeps its last value. `frames` stays a list of text. That is what
parse_qs produces.
"""

import sqlite3  # https://docs.python.org/3/library/sqlite3.html
from typing import TypedDict, cast  # https://docs.python.org/3/library/typing.html
from urllib.parse import (
    parse_qs,  # https://docs.python.org/3/library/urllib.parse.html#urllib.parse.parse_qs
)
from wsgiref.types import (
    WSGIEnvironment,  # https://docs.python.org/3/library/wsgiref.html
)


class User(TypedDict):
    id: int
    username: str
    email: str
    password: str
    session_version: int
    confirmed: int
    mail_ok: int


class SessionUser(User):
    csrf: str


class Letter(TypedDict):
    subject: str
    plain: str
    html: str


class SignupForm(TypedDict):
    username: str
    email: str
    password: str


class SignupQuery(TypedDict):
    notice: str
    username: str
    email: str


class LoginForm(TypedDict):
    username: str
    password: str


class LoginQuery(TypedDict):
    notice: str
    username: str


class ResetForm(TypedDict):
    email: str
    token: str
    action: str
    password: str


class ResetQuery(TypedDict):
    notice: str
    email: str


class ProfileForm(TypedDict):
    csrf: str
    username: str
    email: str
    password: str
    mail_ok: str


class EditorForm(TypedDict):
    csrf: str
    upload_b64: str
    use_sample: str
    gif: str
    snap0: str
    snap1: str
    snap2: str


class EditorQuery(TypedDict):
    error: str
    notice: str


class GalleryQuery(TypedDict):
    page: str
    notice: str
    fragment: str


class LikeForm(TypedDict):
    csrf: str
    page: str
    xhr: str


class CommentForm(TypedDict):
    csrf: str
    body: str
    page: str
    xhr: str


class CsrfForm(TypedDict):
    csrf: str
    xhr: str


class Comment(TypedDict):
    body: str
    username: str


class GalleryRow(TypedDict):
    id: int
    user_id: int
    created_at: int
    username: str
    email: str
    mail_ok: int
    likes: int


class GalleryCard(GalleryRow):
    comments: list[Comment]
    url: str


class Thumb(TypedDict):
    id: int
    user_id: int


class PictureFile(TypedDict):
    image_bytes: bytes
    user_id: int


class PictureAuthor(TypedDict):
    id: int
    username: str
    email: str
    mail_ok: int


Header = tuple[str, str]
Response = tuple[str, list[Header], bytes]
Parsed = dict[str, list[str]]


def one(cursor: sqlite3.Cursor) -> sqlite3.Row | None:
    raw = cast(object, cursor.fetchone())  # pyright: ignore[reportAny]

    if raw is None:
        return None

    if isinstance(raw, sqlite3.Row):
        return raw

    raise ValueError("row")


def many(cursor: sqlite3.Cursor) -> list[sqlite3.Row]:
    raw = cast(list[object], cursor.fetchall())  # pyright: ignore[reportAny]
    rows: list[sqlite3.Row] = []

    for item in raw:
        if not isinstance(item, sqlite3.Row):
            raise TypeError("row")

        rows.append(item)

    return rows


def require_str(row: sqlite3.Row, key: str | int) -> str:
    value = cast(object, row[key])  # pyright: ignore[reportAny]

    if isinstance(value, str):
        return value

    raise ValueError(str(key))


def require_int(row: sqlite3.Row, key: str | int) -> int:
    value = cast(object, row[key])  # pyright: ignore[reportAny]

    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(str(key))

    return value


def require_bytes(row: sqlite3.Row, key: str | int) -> bytes:
    value = cast(object, row[key])  # pyright: ignore[reportAny]

    if isinstance(value, bytes):
        return value

    raise ValueError(str(key))


def user_from_row(row: sqlite3.Row) -> User:
    return {
        "id": require_int(row, "id"),
        "username": require_str(row, "username"),
        "email": require_str(row, "email"),
        "password": require_str(row, "password"),
        "session_version": require_int(row, "session_version"),
        "confirmed": require_int(row, "confirmed"),
        "mail_ok": require_int(row, "mail_ok"),
    }


def session_user(user: User, csrf: str) -> SessionUser:
    return {
        "id": user["id"],
        "username": user["username"],
        "email": user["email"],
        "password": user["password"],
        "session_version": user["session_version"],
        "confirmed": user["confirmed"],
        "mail_ok": user["mail_ok"],
        "csrf": csrf,
    }


def comment_from_row(row: sqlite3.Row) -> Comment:
    return {
        "body": require_str(row, "body"),
        "username": require_str(row, "username"),
    }


def gallery_row(row: sqlite3.Row) -> GalleryRow:
    return {
        "id": require_int(row, "id"),
        "user_id": require_int(row, "user_id"),
        "created_at": require_int(row, "created_at"),
        "username": require_str(row, "username"),
        "email": require_str(row, "email"),
        "mail_ok": require_int(row, "mail_ok"),
        "likes": require_int(row, "likes"),
    }


def gallery_card(row: GalleryRow, comments: list[Comment], url: str) -> GalleryCard:
    return {
        "id": row["id"],
        "user_id": row["user_id"],
        "created_at": row["created_at"],
        "username": row["username"],
        "email": row["email"],
        "mail_ok": row["mail_ok"],
        "likes": row["likes"],
        "comments": comments,
        "url": url,
    }


def thumb_from_row(row: sqlite3.Row) -> Thumb:
    return {
        "id": require_int(row, "id"),
        "user_id": require_int(row, "user_id"),
    }


def picture_file(row: sqlite3.Row) -> PictureFile:
    return {
        "image_bytes": require_bytes(row, "image_bytes"),
        "user_id": require_int(row, "user_id"),
    }


def author_from_row(row: sqlite3.Row) -> PictureAuthor:
    return {
        "id": require_int(row, "id"),
        "username": require_str(row, "username"),
        "email": require_str(row, "email"),
        "mail_ok": require_int(row, "mail_ok"),
    }


def env_str(environ: WSGIEnvironment, key: str, default: str = "") -> str:
    value = cast(object, environ.get(key, default))  # pyright: ignore[reportAny]

    if isinstance(value, str):
        return value

    return default


def request_body(environ: WSGIEnvironment, length: int) -> bytes:
    stream = cast(object, environ["wsgi.input"])  # pyright: ignore[reportAny]
    read = getattr(stream, "read", None)

    if not callable(read):
        raise TypeError("body")

    raw = read(length)

    if isinstance(raw, bytes):
        return raw

    raise ValueError("body")


def content_length(environ: WSGIEnvironment) -> int:
    raw = cast(object, environ.get("CONTENT_LENGTH"))  # pyright: ignore[reportAny]

    if raw is None or raw == "":
        return 0

    if isinstance(raw, str):
        return int(raw or "0")

    raise ValueError("CONTENT_LENGTH")


def _last(parsed: dict[str, list[str]], key: str) -> str:
    values = parsed.get(key, [])

    if not values:
        return ""

    return values[-1]


def parsed_query(environ: WSGIEnvironment) -> Parsed:
    return parse_qs(env_str(environ, "QUERY_STRING", ""), keep_blank_values=True)


def parsed_body(environ: WSGIEnvironment) -> Parsed:
    raw = request_body(environ, content_length(environ)).decode("utf-8", "replace")

    return parse_qs(raw, keep_blank_values=True)


def allow(parsed: Parsed, keys: tuple[str, ...]) -> dict[str, str]:
    return {key: _last(parsed, key) for key in keys}


def allow_many(parsed: Parsed, key: str) -> list[str]:
    return list(parsed.get(key, []))


def signup_form(parsed: Parsed) -> SignupForm:
    fields = allow(parsed, ("username", "email", "password"))

    return {
        "username": fields["username"],
        "email": fields["email"],
        "password": fields["password"],
    }


def signup_query(parsed: Parsed) -> SignupQuery:
    fields = allow(parsed, ("notice", "username", "email"))

    return {"notice": fields["notice"], "username": fields["username"], "email": fields["email"]}


def login_form(parsed: Parsed) -> LoginForm:
    fields = allow(parsed, ("username", "password"))

    return {"username": fields["username"], "password": fields["password"]}


def login_query(parsed: Parsed) -> LoginQuery:
    fields = allow(parsed, ("notice", "username"))

    return {"notice": fields["notice"], "username": fields["username"]}


def reset_form(parsed: Parsed) -> ResetForm:
    fields = allow(parsed, ("email", "token", "action", "password"))

    return {
        "email": fields["email"],
        "token": fields["token"],
        "action": fields["action"],
        "password": fields["password"],
    }


def reset_query(parsed: Parsed) -> ResetQuery:
    fields = allow(parsed, ("notice", "email"))

    return {"notice": fields["notice"], "email": fields["email"]}


def profile_form(parsed: Parsed) -> ProfileForm:
    fields = allow(parsed, ("csrf", "username", "email", "password", "mail_ok"))

    return {
        "csrf": fields["csrf"],
        "username": fields["username"],
        "email": fields["email"],
        "password": fields["password"],
        "mail_ok": fields["mail_ok"],
    }


def editor_form(parsed: Parsed) -> EditorForm:
    fields = allow(parsed, ("csrf", "upload_b64", "use_sample", "gif", "snap0", "snap1", "snap2"))

    return {
        "csrf": fields["csrf"],
        "upload_b64": fields["upload_b64"],
        "use_sample": fields["use_sample"],
        "gif": fields["gif"],
        "snap0": fields["snap0"],
        "snap1": fields["snap1"],
        "snap2": fields["snap2"],
    }


def editor_query(parsed: Parsed) -> EditorQuery:
    fields = allow(parsed, ("error", "notice"))

    return {"error": fields["error"], "notice": fields["notice"]}


def gallery_query(parsed: Parsed) -> GalleryQuery:
    fields = allow(parsed, ("page", "notice", "fragment"))

    return {"page": fields["page"], "notice": fields["notice"], "fragment": fields["fragment"]}


def like_form(parsed: Parsed) -> LikeForm:
    fields = allow(parsed, ("csrf", "page", "xhr"))

    return {"csrf": fields["csrf"], "page": fields["page"], "xhr": fields["xhr"]}


def comment_form(parsed: Parsed) -> CommentForm:
    fields = allow(parsed, ("csrf", "body", "page", "xhr"))

    return {
        "csrf": fields["csrf"],
        "body": fields["body"],
        "page": fields["page"],
        "xhr": fields["xhr"],
    }


def csrf_form(parsed: Parsed) -> CsrfForm:
    fields = allow(parsed, ("csrf", "xhr"))

    return {"csrf": fields["csrf"], "xhr": fields["xhr"]}
