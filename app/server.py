import base64  # https://docs.python.org/3/library/base64.html
import binascii  # https://docs.python.org/3/library/binascii.html
import json  # https://docs.python.org/3/library/json.html#json.dumps
import os  # https://docs.python.org/3/library/os.html#os.environ
import smtplib  # https://docs.python.org/3/library/smtplib.html
import sqlite3  # https://docs.python.org/3/library/sqlite3.html
import time  # https://docs.python.org/3/library/time.html#time.time
from email.message import (  # https://docs.python.org/3/library/email.message.html
    EmailMessage,
)
from urllib.parse import (  # https://docs.python.org/3/library/urllib.parse.html
    quote,
    urlparse,
)
from wsgiref.types import (  # https://docs.python.org/3/library/wsgiref.html
    StartResponse,
    WSGIEnvironment,
)

from app.boundary import (
    CommentForm,
    EditorForm,
    EditorQuery,
    GalleryCard,
    GalleryQuery,
    Header,
    Letter,
    LikeForm,
    LoginForm,
    LoginQuery,
    Parsed,
    ProfileForm,
    ResetForm,
    ResetQuery,
    Response,
    SessionUser,
    SignupForm,
    SignupQuery,
    User,
    allow,
    allow_many,
    comment_form,
    csrf_form,
    editor_form,
    editor_query,
    env_str,
    gallery_card,
    gallery_query,
    like_form,
    login_form,
    login_query,
    one,
    parsed_body,
    parsed_query,
    profile_form,
    reset_form,
    reset_query,
    session_user,
    signup_form,
    signup_query,
    user_from_row,
)
from app.compose import composite, open_base, save_gif
from app.mail import comment as comment_mail
from app.mail import confirmation, reset
from app.pages import (
    editor_page,
    escape,
    gallery_page,
    login_page,
    plain_page,
    profile_page,
    reset_page,
    signup_page,
)
from app.passwords import accept_password, password_codes
from app.session import csrf_accepts, csrf_token, issue_cookie, read_session
from app.store import (
    add_comment,
    comments_for,
    confirm_user,
    connect,
    consume_token,
    delete_picture,
    email_taken,
    end_session,
    find_user,
    find_user_id,
    gallery_rows,
    insert_picture,
    insert_user,
    issue_token,
    like_count,
    like_once,
    list_pictures,
    password_matches,
    picture_author,
    picture_bytes,
    picture_count,
    set_password,
    update_profile,
    username_taken,
)

STATIC = {
    "/app.css": "app.css",
    "/shell.html": "shell.html",
    "/base.png": "base.png",
    "/frames/a.png": "frames/a.png",
    "/frames/b.png": "frames/b.png",
}


def application(environ: WSGIEnvironment, start_response: StartResponse) -> list[bytes]:
    """WSGI entry. environ is the request. start_response sends the status line.

    A locked database or any other error becomes a short 500, and nothing is printed.
    https://peps.python.org/pep-3333/#the-application-framework-side
    https://docs.python.org/3/library/sqlite3.html#sqlite3.OperationalError
    """
    secret = os.environ.get("CAMAGRU_SECRET", "")

    try:
        status, headers, body = handle(environ, secret)
    except sqlite3.OperationalError:
        status = "500 Internal Server Error"
        headers = [("Content-Type", "text/html; charset=utf-8")]
        body = b"database is locked"
    except Exception as exc:  # noqa: BLE001
        status = "500 Internal Server Error"
        headers = [("Content-Type", "text/html; charset=utf-8")]
        detail = ""

        # Local debugging only: name the exception type in the 500 body.
        if os.environ.get("CAMAGRU_DEBUG"):
            detail = " " + escape(type(exc).__name__)

        body = f"something went wrong{detail}".encode()

    start_response(status, headers)

    return [body]


def handle(environ: WSGIEnvironment, secret: str) -> Response:
    """Route one request. Static files skip the database.

    PATH_INFO is the path. REQUEST_METHOD is GET or POST.
    https://peps.python.org/pep-3333/#environ-variables

    localhost and 127.0.0.1 are different sites. A cookie set on one is invisible
    on the other. Every request is sent to CAMAGRU_BASE_URL first.
    """
    canonical = _canonical(environ)

    if canonical is not None:
        return canonical

    path = env_str(environ, "PATH_INFO", "/") or "/"
    method = env_str(environ, "REQUEST_METHOD", "GET").upper()
    query = parsed_query(environ)
    static = _static(path)

    if static is not None:
        return static

    conn = connect()

    try:
        user = _user(conn, environ, secret)
        form = parsed_body(environ) if method == "POST" else {}

        if path == "/signup":
            return _signup(conn, method, signup_form(form), signup_query(query))

        if path == "/login":
            return _login(conn, secret, method, login_form(form), user, login_query(query))

        if path == "/logout" and method == "POST":
            return _logout(conn, user, csrf_form(form)["csrf"], secret)

        if path == "/reset" or path.startswith("/reset/"):
            return _reset(conn, method, reset_form(form), path, reset_query(query))

        if path == "/profile":
            return _profile(conn, secret, method, profile_form(form), user, allow(query, ("notice",))["notice"])

        if path == "/confirm/" or path.startswith("/confirm/"):
            return _confirm(conn, path)

        # Test-only route: Playwright empties the gallery. Off unless CAMAGRU_E2E is set.
        if os.environ.get("CAMAGRU_E2E") and path == "/e2e/reset" and method == "POST":
            conn.execute("delete from comments")
            conn.execute("delete from likes")
            conn.execute("delete from pictures")
            conn.commit()

            return _redirect("/")

        if path == "/editor":
            return _editor(
                conn,
                secret,
                method,
                editor_form(form),
                user,
                editor_query(query),
                allow_many(form, "frames"),
            )

        if path.startswith("/pictures/"):
            return _picture(conn, secret, method, form, user, path)

        return _gallery(conn, user, gallery_query(query))
    finally:
        conn.close()


def _signup(conn: sqlite3.Connection, method: str, form: SignupForm, query: SignupQuery) -> Response:
    """Create an unconfirmed user and mail one link. A taken name or email does not say which.

    Every result redirects. The address bar is then a GET, so refresh does not send the form again.
    """
    notice = query["notice"]
    username = form["username"] or query["username"]
    email = form["email"] or query["email"]
    password = form["password"]

    if method != "POST":
        text = _notice(notice) if notice == "sent" else ""

        return _html(signup_page(username, email, _phrases(notice), text))

    codes = _signup_codes(conn, username, email, password)

    if codes:
        return _redirect(_signup_target(codes, username, email))

    user_id = insert_user(conn, username, email, password)

    # The unique index caught a name or email taken after the check above.
    if user_id is None:
        return _redirect(_signup_target(["taken"], username, email))

    token = issue_token(conn, user_id, "confirm")
    link = _base() + "/confirm/" + token
    _send(email, confirmation(username, email, link))

    return _redirect("/signup?notice=sent")


def _login(
    conn: sqlite3.Connection,
    secret: str,
    method: str,
    form: LoginForm,
    user: SessionUser | None,
    query: LoginQuery,
) -> Response:
    """Set the cookie only when the password matches and the account is confirmed.

    A failure redirects. Refreshing the login page is a GET and does not send the password again.
    """
    notice = query["notice"]
    username = query["username"]

    if method != "POST":
        return _html(login_page(user, username, _login_error(notice), _notice(notice)))

    username = form["username"]
    password = form["password"]
    found = find_user(conn, username)
    target = "/login?username=" + quote(username)

    if found is None:
        return _redirect(target + "&notice=unknown")

    if not password_matches(found, password):
        return _redirect(target + "&notice=badpw")

    if not found["confirmed"]:
        return _redirect(target + "&notice=unconfirmed")

    return _redirect("/", _cookie(found, secret))


def _logout(
    conn: sqlite3.Connection,
    user: SessionUser | None,
    csrf: str,
    secret: str,
) -> Response:
    """End the session on the server, then drop the browser cookie.

    The CSRF field is the outside-form check. Max-Age=0 deletes the cookie.
    An empty value alone does not. See docs/code/02-server.md.
    https://developer.mozilla.org/en-US/docs/Glossary/CSRF
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie#max-agenumber
    """
    if user is None or not csrf_accepts(csrf, user["id"], user["session_version"], secret):
        return _html(login_page(user))

    end_session(conn, user["id"])

    return _redirect("/login", ("Set-Cookie", "camagru=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"))


def _reset(
    conn: sqlite3.Connection,
    method: str,
    form: ResetForm,
    path: str,
    query: ResetQuery,
) -> Response:
    """Two pages. /reset asks for the email. /reset/<token> sets the password.

    The token is the only proof the person read the mail. An email address is not.
    A weak password does not burn the token. An empty email does not pretend a mail was sent.
    """
    notice = query["notice"]
    token = path[len("/reset/") :] if path.startswith("/reset/") else form["token"]
    email = form["email"] or query["email"]
    action = path if token else "/reset"

    if method != "POST":
        text = ""

        if notice == "sent":
            text = "If that email has an account, a reset link is on its way."

        return _html(reset_page(
            email,
            _phrases(notice),
            token,
            action,
            text,
        ))

    # Step one: mail a link. Known and unknown emails get the same answer.
    if form["action"] == "request" and not token:
        email = email.strip()

        if not _email_ok(email):
            return _redirect("/reset?notice=bademail&email=" + quote(email))

        found_row = one(
            conn.execute(
                "select * from users where lower(email) = lower(?)",
                (email,),
            )
        )

        if found_row is not None:
            found = user_from_row(found_row)
            issued = issue_token(conn, found["id"], "reset")
            link = _base() + "/reset/" + issued
            _send(email, reset(found["username"], email, link))

        return _redirect("/reset?notice=sent&email=" + quote(email))

    password = form["password"]

    # Step two needs the mailed token. A new password without it is refused.
    if not token:
        return _html(reset_page(email, "Open the link from the mail to choose a password."))

    if not accept_password(password):
        return _redirect(action + "?notice=" + ",".join(password_codes(password)))

    user_id = consume_token(conn, "reset", token)

    if user_id is None:
        return _html(reset_page(email, "that reset link is not valid"))

    set_password(conn, user_id, password)

    return _redirect("/login?notice=reset")


def _profile(
    conn: sqlite3.Connection,
    secret: str,
    method: str,
    form: ProfileForm,
    user: SessionUser | None,
    notice: str = "",
) -> Response:
    """Change the username, email, or password. A blank password keeps the current hash.

    The CSRF field is required. A new password bumps session_version, and the
    redirect sends a new cookie so this browser stays logged in.
    """
    if user is None:
        return _html(plain_page(None, "<p>Log in to edit your profile.</p>"))

    if method != "POST":
        return _html(profile_page(user, user["csrf"], notice=_notice(notice)))

    if not csrf_accepts(form["csrf"], user["id"], user["session_version"], secret):
        return _html(profile_page(user, user["csrf"], "the form was refused"))

    username = form["username"]
    email = form["email"]
    password = form["password"]
    error = _profile_error(conn, user, username, email, password)

    if error:
        return _html(profile_page(user, user["csrf"], error))

    mail_ok = form["mail_ok"] == "1"
    version = update_profile(conn, user, username, email, password, mail_ok)

    # The unique index caught a name or email taken after _profile_error ran.
    if version is None:
        return _html(profile_page(user, user["csrf"], "that username or email is taken"))

    updated = find_user_id(conn, user["id"])

    # The row was deleted mid-request. The 500 handler answers.
    if updated is None:
        raise ValueError("profile")

    return _redirect("/profile?notice=saved", _cookie(updated, secret))


def _confirm(conn: sqlite3.Connection, path: str) -> Response:
    token = path[len("/confirm/") :]
    user_id = consume_token(conn, "confirm", token)

    if user_id is None:
        return _html(login_page(None))

    confirm_user(conn, user_id)

    return _redirect("/login?notice=confirmed")


def _editor(
    conn: sqlite3.Connection,
    secret: str,
    method: str,
    form: EditorForm,
    user: SessionUser | None,
    query: EditorQuery,
    frames: list[str],
) -> Response:
    """The workspace. A visitor who is not logged in is sent to the login page.

    A save always redirects, so a refresh reloads the page and does not post the picture again.
    """
    if user is None:
        return _redirect("/login")

    if method != "POST":
        error = _editor_error(query["error"])
        notice = _notice(query["notice"])

        return _html(
            editor_page(
                user,
                error,
                list_pictures(conn, user["id"]),
                notice,
            )
        )

    if not csrf_accepts(form["csrf"], user["id"], user["session_version"], secret):
        return _redirect("/editor?error=refused")

    # Bonus: three snaps become one GIF instead of a still PNG.
    if form["gif"] == "1":
        error = _store_gif(conn, user, form, frames)

        return _redirect("/editor?error=" + error if error else "/editor?notice=gif")

    code = _save_picture(conn, user, form["upload_b64"], form["use_sample"], frames)

    if code:
        return _redirect("/editor?error=" + code)

    return _redirect("/editor?notice=picture")


def _gallery(
    conn: sqlite3.Connection,
    user: SessionUser | None,
    query: GalleryQuery,
) -> Response:
    raw_page = query["page"] or "1"
    notice = _notice(query["notice"])
    page_number = int(raw_page) if raw_page.isdigit() and int(raw_page) > 0 else 1
    size = 5
    total = picture_count(conn)
    last = 1 if total == 0 else (total + size - 1) // size

    # Past the last page: redirect there instead of showing an empty page.
    if page_number > last:
        code = query["notice"] if notice else ""

        return _redirect(_gallery_address(str(last), code, query["fragment"] == "1"))

    rows: list[GalleryCard] = []

    for row in gallery_rows(conn, page_number, size):
        rows.append(
            gallery_card(
                row,
                comments_for(conn, row["id"]),
                _base() + "/pictures/" + str(row["id"]),
            )
        )

    has_next = page_number * size < total

    return _html(
        gallery_page(
            user,
            rows,
            page_number,
            has_next,
            notice,
            query["fragment"] == "1",
        )
    )


def _picture(
    conn: sqlite3.Connection,
    secret: str,
    method: str,
    form: Parsed,
    user: SessionUser | None,
    path: str,
) -> Response:
    rest = path[len("/pictures/") :]

    if rest.endswith("/like") and method == "POST":
        return _like(conn, user, like_form(form), secret, rest[: -len("/like")])

    if rest.endswith("/comment") and method == "POST":
        return _comment(conn, user, comment_form(form), secret, rest[: -len("/comment")])

    if rest.endswith("/delete") and method == "POST":
        posted = csrf_form(form)

        # The page script deletes in place and reads JSON, not a redirect.
        if posted["xhr"] == "1":
            picture_id = rest[: -len("/delete")]
            deleted = (
                user is not None
                and picture_id.isdigit()
                and csrf_accepts(posted["csrf"], user["id"], user["session_version"], secret)
                and delete_picture(conn, int(picture_id), user["id"])
            )

            return _json({"ok": deleted})

        if user is None:
            return _redirect("/login")

        picture_id = rest[: -len("/delete")]
        token = posted["csrf"]
        deleted = (
            picture_id.isdigit()
            and csrf_accepts(token, user["id"], user["session_version"], secret)
            and delete_picture(conn, int(picture_id), user["id"])
        )

        if not deleted:
            return _redirect("/editor?error=notyours")

        return _redirect("/editor?notice=deleted")

    # /pictures/<id> serves the stored bytes. Captured images are public, so no login check.
    if rest.isdigit():
        row = picture_bytes(conn, int(rest))

        if row is None:
            return "404 Not Found", [("Content-Type", "text/plain; charset=utf-8")], b"missing"

        kind = "image/gif" if row["image_bytes"][:4] == b"GIF8" else "image/png"

        return "200 OK", [("Content-Type", kind)], row["image_bytes"]

    return _redirect("/editor")


def _like(
    conn: sqlite3.Connection,
    user: SessionUser | None,
    form: LikeForm,
    secret: str,
    picture_id: str,
) -> Response:
    """Like once, then return to the same gallery page."""
    author = None

    if user is not None and _member_ok(user, form["csrf"], secret) and picture_id.isdigit():
        author = picture_author(conn, int(picture_id))

    if author is not None and user is not None:
        like_once(conn, user["id"], int(picture_id))

    # The page script updates the count in place.
    if form["xhr"] == "1":
        count = like_count(conn, int(picture_id)) if picture_id.isdigit() else 0

        return _json({"likes": count})

    return _redirect(_gallery_address(form["page"], ""))


def _comment(
    conn: sqlite3.Connection,
    user: SessionUser | None,
    form: CommentForm,
    secret: str,
    picture_id: str,
) -> Response:
    """Store the comment and mail the author when they allow it. A refresh of the redirect posts nothing."""
    notice = ""
    stored = False

    if user is not None and _member_ok(user, form["csrf"], secret) and picture_id.isdigit():
        author = picture_author(conn, int(picture_id))
        body = form["body"]

        if author is not None and body:
            add_comment(conn, int(picture_id), user["id"], body)
            stored = True
            mail = comment_mail(
                author["username"],
                author["email"],
                _base() + "/pictures/" + picture_id,
                user["username"],
                bool(author["mail_ok"]),
            )

            # None means the author turned comment mail off. Only a failed send is reported.
            if mail is not None and not _send(author["email"], mail):
                notice = "nomail"

    # The page script appends the comment in place.
    if form["xhr"] == "1":
        return _json({
            "ok": stored,
            "body": form["body"],
            "username": user["username"] if user else "",
            "notice": _notice(notice),
        })

    return _redirect(_gallery_address(form["page"], notice))


def _gallery_address(page: str, notice: str, fragment: bool = False) -> str:
    parts: list[str] = []

    if page.isdigit() and int(page) > 1:
        parts.append("page=" + page)

    if notice:
        parts.append("notice=" + notice)

    if fragment:
        parts.append("fragment=1")

    return "/?" + "&".join(parts) if parts else "/"


def _member_ok(user: SessionUser | None, csrf: str, secret: str) -> bool:
    if user is None:
        return False

    return csrf_accepts(csrf, user["id"], user["session_version"], secret)


def _save_picture(
    conn: sqlite3.Connection,
    user: SessionUser,
    upload_b64: str,
    use_sample: str,
    frames: list[str],
) -> str:
    raw = _image_bytes(upload_b64, use_sample)

    if raw is None:
        return "nobase"

    try:
        open_base(raw)
    except ValueError:
        return "notimage"

    png = composite(raw, _frame_bytes(frames))
    insert_picture(conn, user["id"], png, time.time())

    return ""


def _frame_bytes(frames: list[str]) -> list[bytes]:
    chosen: list[bytes] = []
    folder = os.path.join(os.path.dirname(__file__), "..", "public", "frames")

    for name in frames:
        if name not in ("a", "b"):
            continue

        # "rb" reads bytes. "r" would decode text and break the PNG.
        # https://docs.python.org/3/library/functions.html#open
        with open(os.path.join(folder, name + ".png"), "rb") as handle:
            chosen.append(handle.read())

    return chosen


def _store_gif(
    conn: sqlite3.Connection,
    user: SessionUser,
    form: EditorForm,
    frames: list[str],
) -> str:
    if form["use_sample"] == "1" or form["upload_b64"]:
        return "gifcamera"

    snaps: list[bytes] = []
    overlay = _frame_bytes(frames)

    for key in ("snap0", "snap1", "snap2"):
        payload = form[key]

        try:
            raw = base64.b64decode(payload.split(",")[-1], validate=True)
            open_base(raw)
        except (binascii.Error, ValueError):
            return "gif"

        snaps.append(composite(raw, overlay))

    try:
        stored = save_gif(snaps)
    except ValueError:
        return "gif"

    insert_picture(conn, user["id"], stored, time.time())

    return ""


def _image_bytes(upload_b64: str, use_sample: str) -> bytes | None:
    payload = upload_b64

    # An upload or a capture wins over the sample photo.
    if payload:
        if "," in payload:
            payload = payload.split(",", 1)[1]

        try:
            # https://docs.python.org/3/library/base64.html#base64.b64decode
            return base64.b64decode(payload, validate=True)
        except binascii.Error:
            # Bad base64 still reaches open_base, which refuses it as not an image.
            # https://docs.python.org/3/library/binascii.html#binascii.Error
            return b"not-an-image"

    if use_sample == "1":
        path = os.path.join(os.path.dirname(__file__), "..", "public", "base.png")

        with open(path, "rb") as handle:
            return handle.read()

    return None


def _signup_codes(conn: sqlite3.Connection, username: str, email: str, password: str) -> list[str]:
    """Taken is reported even when the password also fails. The password lines are only the failures."""
    codes: list[str] = []

    if not _username_ok(username):
        codes.append("baduser")

    if not _email_ok(email):
        codes.append("bademail")

    names_ok = "baduser" not in codes and "bademail" not in codes

    # Only ask the database about names that are well formed.
    if names_ok and (username_taken(conn, username) or email_taken(conn, email)):
        codes.append("taken")

    return codes + password_codes(password)


def _signup_target(codes: list[str], username: str, email: str) -> str:
    return (
        "/signup?notice="
        + ",".join(codes)
        + "&username="
        + quote(username)
        + "&email="
        + quote(email)
    )


def _phrases(notice: str) -> list[str]:
    table = {
        "baduser": "username must be letters, digits, and underscore",
        "bademail": "email is not valid",
        "taken": "that username or email is taken",
        "short": "at least 8 characters",
        "long": "at most 128 characters",
        "letter": "one letter",
        "digit": "one digit",
    }

    return [table[code] for code in notice.split(",") if code in table]


def _login_error(notice: str) -> str:
    return {
        "unknown": "No account uses that username.",
        "badpw": "That password does not match.",
        "unconfirmed": "Open the confirmation link in the mail for this account before logging in.",
    }.get(notice, "")


def _editor_error(code: str) -> str:
    return {
        "nobase": "Capture a photo, upload a PNG, or use the sample photo before saving.",
        "notimage": "That file is not an image. Nothing was saved.",
        "notyours": "That picture is not yours. Nothing was deleted.",
        "refused": "the form was refused",
        "gif": "Three snaps are required.",
        "gifcamera": "Save GIF needs the live camera and a sticker.",
    }.get(code, "")


def _profile_error(
    conn: sqlite3.Connection,
    user: SessionUser,
    username: str,
    email: str,
    password: str,
) -> str | list[str]:
    if not _username_ok(username):
        return "username must be letters, digits, and underscore"

    if not _email_ok(email):
        return "email is not valid"

    if password and not accept_password(password):
        return _phrases(",".join(password_codes(password)))

    other = find_user(conn, username)

    if other is not None and other["id"] != user["id"]:
        return "that username or email is taken"

    row = one(
        conn.execute(
            "select id from users where lower(email) = lower(?) and id != ?",
            (email, user["id"]),
        )
    )

    if row is not None:
        return "that username or email is taken"

    return ""


def _user(conn: sqlite3.Connection, environ: WSGIEnvironment, secret: str) -> SessionUser | None:
    """The logged-in user, or None. The cookie signature and version must both match the row."""
    cookie = _cookie_value(env_str(environ, "HTTP_COOKIE", ""))

    if not cookie or not secret:
        return None

    parts = cookie.split(".")

    if not parts or not parts[0].isdigit():
        return None

    row = find_user_id(conn, int(parts[0]))

    if row is None:
        return None

    # Bad signature, expired, or logged out since: the version no longer matches the row.
    if read_session(cookie, secret, int(time.time()), row["session_version"]) is None:
        return None

    return session_user(row, csrf_token(row["id"], row["session_version"], secret))


def _cookie(user: User, secret: str) -> Header:
    """One Set-Cookie header. The attributes are parts of that header, not more headers.

    camagru is the name. The value is the user id, version, expiry, and signature.
    HttpOnly keeps page scripts from reading it.
    SameSite=Lax sends it on a normal click from another site, not on that site's form post.
    Path=/ makes the browser send it on every path of this host.
    Max-Age=43200 drops it after 12 hours. Max-Age=0, used on logout, deletes it.
    Secure is added only when CAMAGRU_BASE_URL starts with https.
    https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie
    """
    value = issue_cookie(user["id"], user["session_version"], secret, int(time.time()))
    base = os.environ.get("CAMAGRU_BASE_URL", "")
    secure = "; Secure" if base.startswith("https") else ""
    header = f"camagru={value}; HttpOnly; SameSite=Lax; Path=/; Max-Age=43200{secure}"

    return ("Set-Cookie", header)


def _cookie_value(header: str) -> str:
    for part in header.split(";"):
        name, sep, value = part.strip().partition("=")

        if sep and name == "camagru":
            return value

    return ""


def _notice(code: str) -> str:
    return {
        "sent": "Check your mail. The link in it is what lets you continue.",
        "confirmed": "Account confirmed. Log in with your username and password.",
        "reset": "Password updated. Log in with the new one.",
        "saved": "Profile saved.",
        "picture": "Picture saved.",
        "deleted": "Picture deleted.",
        "nomail": "the mail was not sent",
        "gif": "GIF saved.",
    }.get(code, "")


def _canonical(environ: WSGIEnvironment) -> Response | None:
    """Send the browser to CAMAGRU_BASE_URL when Host is a different name.

    localhost and 127.0.0.1 are different sites. A cookie and the stylesheet
    saved on one are invisible on the other. None means this request is already
    on that host, so the route runs.
    https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy
    """
    base = _base()
    host = env_str(environ, "HTTP_HOST", "")
    netloc = urlparse(base).netloc

    # Already on the base host, or nothing to compare: run the route.
    if not host or not netloc or host == netloc:
        return None

    path = env_str(environ, "PATH_INFO", "/") or "/"
    query = env_str(environ, "QUERY_STRING", "")
    target = base + path

    if query:
        target += "?" + query

    return _redirect(target)


def _send(recipient: str, body: str | Letter) -> bool:
    """Send one message over SMTP. A dead server returns False and prints nothing.

    A dict carries subject, plain text, and HTML. A string stays a plain message.
    https://docs.python.org/3/library/smtplib.html
    https://docs.python.org/3/library/email.message.html#email.message.EmailMessage.add_alternative
    """
    host = os.environ.get("CAMAGRU_SMTP_HOST", "127.0.0.1")
    port = int(os.environ.get("CAMAGRU_SMTP_PORT", "1025"))
    message = EmailMessage()
    message["To"] = recipient
    message["From"] = os.environ.get("CAMAGRU_MAIL_FROM", "camagru@localhost")

    # A letter dict has HTML and plain parts. A string is a plain message.
    if isinstance(body, dict):
        message["Subject"] = body["subject"]
        message.set_content(body["plain"])
        message.add_alternative(body["html"], subtype="html")
    else:
        message["Subject"] = "camagru"
        message.set_content(body)

    try:
        with smtplib.SMTP(host, port, timeout=5) as client:
            client.send_message(message)
    except OSError:
        return False

    return True


def _base() -> str:
    return os.environ.get("CAMAGRU_BASE_URL", "http://127.0.0.1:8765").rstrip("/")


def _username_ok(username: str) -> bool:
    if not username or len(username) > 32:
        return False

    for char in username:
        letter = "a" <= char.lower() <= "z"
        digit = char.isdigit()

        if not letter and not digit and char != "_":
            return False

    return True


def _email_ok(email: str) -> bool:
    if email.count("@") != 1:
        return False

    local, domain = email.split("@")

    return bool(local) and "." in domain and not domain.startswith(".") and not domain.endswith(".")


def _static(path: str) -> Response | None:
    name = STATIC.get(path)

    if name is None:
        return None

    folder = os.path.join(os.path.dirname(__file__), "..", "public")

    with open(os.path.join(folder, name), "rb") as handle:
        body = handle.read()

    kinds = {".css": "text/css", ".png": "image/png"}
    kind = kinds.get(os.path.splitext(name)[1], "text/html; charset=utf-8")

    return "200 OK", [("Content-Type", kind)], body


def _html(text: str, extra: Header | None = None) -> Response:
    headers = [("Content-Type", "text/html; charset=utf-8")]

    if extra is not None:
        headers.append(extra)

    return "200 OK", headers, text.encode()


def _json(data: dict[str, object]) -> Response:
    return "200 OK", [("Content-Type", "application/json")], json.dumps(data).encode()


def _redirect(location: str, extra: Header | None = None) -> Response:
    headers = [("Location", location)]

    if extra is not None:
        headers.append(extra)

    return "303 See Other", headers, b""
