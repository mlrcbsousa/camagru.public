import os  # https://docs.python.org/3/library/os.path.html#os.path.join
import re  # https://docs.python.org/3/library/re.html
from collections.abc import (
    Sequence,  # https://docs.python.org/3/library/collections.abc.html
)
from html import (
    escape as html_escape,  # https://docs.python.org/3/library/html.html#html.escape
)

from app.boundary import GalleryCard, SessionUser, Thumb, User, session_user

ROOT = os.path.join(os.path.dirname(__file__), "..", "public")


def render(main: str, session_label: str, logout: str = "", path: str = "/") -> str:
    """Fill the shell: navigation, the username when logged in, logout, and the page body.

    An empty session label means logged out. The header does not say "logged out".
    """
    shell = _read("shell.html")

    return _fill(
        shell,
        {
            "session": escape(session_label),
            "logout": logout,
            "main": main,
            "nav": _nav(not session_label, path),
        },
    )


def signup_page(
    username: str = "",
    email: str = "",
    error: str | list[str] = "",
    notice: str = "",
) -> str:
    """The signup form. A notice replaces the error, and the visitor stays logged out."""
    error_html = ""

    if error:
        error_html = problem(error, "signup-error")

    if notice:
        error_html = f'<p class="notice">{escape(notice)}</p>' + error_html

    main = _fill(
        _read("signup.html"),
        {
            "username": escape(username),
            "email": escape(email),
            "message": error_html,
        },
    )

    return render(main, "", path="/signup")


def login_page(
    user: SessionUser | None = None,
    username: str = "",
    error: str = "",
    notice: str = "",
) -> str:
    """The login form. A logged-in user keeps their name and the logout control."""
    error_html = problem(error, "login-error") if error else ""
    notice_html = f'<p class="notice">{escape(notice)}</p>' if notice else ""
    main = _fill(
        _read("login.html"),
        {
            "username": escape(username),
            "message": error_html,
            "notice": notice_html,
        },
    )
    label = "" if user is None else user["username"]

    return render(main, label, _logout(user), "/login")


def reset_page(
    email: str = "",
    error: str | list[str] = "",
    token: str = "",
    action: str = "/reset",
    notice: str = "",
) -> str:
    """The email form, or the new-password form when the mail link was opened."""
    error_html = ""
    token_html = ""
    template = "reset-request.html"

    if error:
        error_html = problem(error, "reset-error")

    if notice:
        error_html = f'<p class="notice">{escape(notice)}</p>'

    # Opened from the mail: show the new-password form instead of the email form.
    if token:
        template = "reset-choose.html"
        token_html = f'<input type="hidden" name="token" value="{escape(token)}">'

    main = _fill(
        _read(template),
        {
            "email": escape(email),
            "message": error_html,
            "token": token_html,
            "action": escape(action),
        },
    )

    return render(main, "", path="/reset")


def profile_page(
    user: User,
    csrf: str,
    error: str | list[str] = "",
    notice: str = "",
) -> str:
    """The profile form, with the current username and email filled in."""
    current = session_user(user, csrf)
    error_html = problem(error, "profile-error") if error else ""

    if notice:
        error_html = f'<p class="notice">{escape(notice)}</p>' + error_html

    main = _fill(
        _read("profile.html"),
        {
            "csrf": escape(csrf),
            "username": escape(current["username"]),
            "email": escape(current["email"]),
            "message": error_html,
            "mail_checked": "checked" if current["mail_ok"] else "",
        },
    )

    return render(main, current["username"], _logout(current), "/profile")


def editor_page(
    user: SessionUser,
    error: str,
    own: Sequence[Thumb],
    notice: str = "",
) -> str:
    message_html = ""

    if notice:
        message_html = f'<p class="notice" data-testid="editor-notice">{escape(notice)}</p>'

    if error:
        message_html = f'<p data-testid="editor-error">{escape(error)}</p>'

    thumbs: list[str] = []

    for picture in own:
        thumbs.append(
            '<figure class="thumb">'
            f'<a href="/pictures/{picture["id"]}">'
            f'<img data-testid="editor-thumb" alt="Saved picture {picture["id"]}" src="/pictures/{picture["id"]}">'
            "</a>"
            f'<form method="post" action="/pictures/{picture["id"]}/delete">'
            f'<input type="hidden" name="csrf" value="{escape(user["csrf"])}">'
            '<button data-testid="editor-delete" class="secondary" type="submit">Delete</button>'
            "</form></figure>"
        )

    thumbs_html = '<p class="empty">No pictures yet.</p>'

    if thumbs:
        thumbs_html = '<div class="thumbs">' + "".join(thumbs) + "</div>"

    main = _fill(
        _read("editor.html"),
        {
            "csrf": escape(user["csrf"]),
            "message": message_html,
            "thumbs": thumbs_html,
        },
    )

    return render(main, user["username"], _logout(user), "/editor")


def gallery_page(
    user: SessionUser | None,
    rows: Sequence[GalleryCard],
    page_number: int,
    has_next: bool,
    notice: str,
    fragment: bool = False,
) -> str:
    """Public cards. Like and Comment are drawn only for a logged-in member (printed page 7)."""
    csrf = escape(user["csrf"]) if user else ""
    page_field = f'<input type="hidden" name="page" value="{int(page_number)}">'
    blocks: list[str] = []

    for row in rows:
        comments = "".join(
            '<li data-testid="gallery-comment">'
            f'<b>{escape(item["username"])}</b>: {escape(item["body"])}'
            "</li>"
            for item in row["comments"]
        )

        if not comments:
            comments = '<li class="no-comments">No comments yet.</li>'

        like_form = ""
        comment_form = ""

        # Like and Comment are drawn only for a logged-in member.
        if user:
            like_form = (
                f'<form class="like-form" method="post" action="/pictures/{row["id"]}/like">'
                f'<input type="hidden" name="csrf" value="{csrf}">'
                + page_field
                + '<button data-testid="gallery-like" class="secondary" type="submit">Like</button>'
                "</form>"
            )
            comment_form = (
                f'<form class="comment-form" method="post" action="/pictures/{row["id"]}/comment">'
                f'<input type="hidden" name="csrf" value="{csrf}">'
                + page_field
                + '<input data-testid="gallery-comment-body" name="body" placeholder="Add a comment">'
                '<button data-testid="gallery-comment-submit" type="submit">Comment</button>'
                "</form>"
            )

        likes = int(row["likes"])
        word = "like" if likes == 1 else "likes"

        blocks.append(
            '<article data-testid="gallery-item" class="card">'
            f'<div class="card-photo"><img alt="" src="/pictures/{row["id"]}"></div>'
            '<div class="card-body">'
            '<div class="card-head">'
            f'<p class="byline">by {escape(row["username"])}</p>'
            '<div class="like-row">'
            + like_form
            + f'<span class="like-total"><span data-testid="gallery-like-count">{likes}</span> {word}</span>'
            "</div>"
            "</div>"
            f'<ul class="comments">{comments}</ul>'
            + comment_form
            + '<p class="share">'
            + f'<a data-testid="share-x" target="_blank" rel="noopener noreferrer" href="https://x.com/intent/tweet?url={escape(row["url"])}">Share on X</a>'
            + f'<a data-testid="share-facebook" target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/sharer/sharer.php?u={escape(row["url"])}">Share on Facebook</a>'
            + "</p></div></article>"
        )

    notice_html = ""

    if notice:
        notice_html = f'<p data-testid="comment-mail-status">{escape(notice)}</p>'

    hint = ""

    if user is None:
        hint = '<p class="empty"><a href="/login">Log in</a> to like and comment.</p>'

    items = '<p class="empty">No pictures yet.</p>'

    if blocks:
        items = '<div class="gallery">' + "".join(blocks) + "</div>"

    links: list[str] = []

    if int(page_number) > 1:
        previous = int(page_number) - 1
        href = "/" if previous == 1 else f"/?page={previous}"
        links.append(f'<a data-testid="gallery-previous" href="{href}">Previous</a>')

    if has_next:
        links.append(f'<a data-testid="gallery-next" href="/?page={int(page_number) + 1}">Next</a>')

    pager = '<p class="pager">' + "".join(links) + "</p>" if links else ""

    # Infinite scroll asks for the next cards only, without the shell.
    if fragment:
        return "".join(blocks) + pager

    main = (
        "<h1>Gallery</h1>"
        '<p class="lead">Newest first. Five pictures on a page.</p>'
        + hint
        + notice_html
        + items
        + pager
    )
    label = "" if user is None else user["username"]

    return render(main, label, _logout(user), "/")


def plain_page(user: SessionUser | None, body: str, path: str = "") -> str:
    label = "" if user is None else user["username"]

    return render(body, label, _logout(user), path)


RULE_LINES = (
    "at least 8 characters",
    "at most 128 characters",
    "one letter",
    "one digit",
)


def problem(error: str | list[str], testid: str = "") -> str:
    """Red text. Password lines are only the rules this value failed."""
    if not error:
        return ""

    items = error if isinstance(error, list) else [error]
    rules = [item for item in items if item in RULE_LINES]
    others = [item for item in items if item not in RULE_LINES]
    attr = f' data-testid="{testid}"' if testid else ""
    body = "".join(f"<p>{escape(item)}</p>" for item in others)

    if rules:
        body += "<p>Invalid password.</p><ul>"
        body += "".join(f"<li>{escape(item)}</li>" for item in rules) + "</ul>"

    return f"<div{attr}>{body}</div>"


def _nav(logged_out: bool, path: str) -> str:
    """Links for this session. The page the visitor is on is left out."""
    items = [("/", "Gallery")]

    if logged_out:
        items.extend([("/signup", "Sign up"), ("/login", "Log in")])
    else:
        items.extend([("/editor", "Editor"), ("/profile", "Profile")])

    links: list[str] = []

    for href, label in items:
        if href == path:
            continue

        links.append(f'<a href="{href}">{label}</a>')

    return " ".join(links)


def escape(value: object) -> str:
    """html.escape. None becomes an empty string.

    https://docs.python.org/3/library/html.html#html.escape
    """
    if value is None:
        return ""

    return html_escape(str(value), quote=True)


def _logout(user: SessionUser | None) -> str:
    if user is None:
        return ""

    return (
        '<form method="post" action="/logout">'
        f'<input type="hidden" name="csrf" value="{escape(user["csrf"])}">'
        '<button data-testid="logout-submit" type="submit">Log out</button>'
        "</form>"
    )


def _read(name: str) -> str:
    path = os.path.join(ROOT, name)

    with open(path, encoding="utf-8") as handle:
        return handle.read()


def _fill(template: str, fields: dict[str, str]) -> str:
    """Replace {{markers}} in the original file only. A value is not scanned again.

    https://docs.python.org/3/library/re.html#re.sub
    """

    def replacer(match: re.Match[str]) -> str:
        return fields.get(match.group(1), match.group(0))

    return re.sub(r"\{\{([a-z0-9_]+)\}\}", replacer, template)
