"""Mail bodies. smtplib sends them. PHP's mail() is the behavior to defend.

Every message goes through _letter, so each one has the same greeting, link, and closing line.
https://docs.python.org/3/library/smtplib.html
https://docs.python.org/3/library/html.html#html.escape
"""

from html import escape

from app.boundary import Letter


def confirmation(username: str, recipient: str, link: str) -> Letter:
    """A confirmation letter. The link is the only way to log in."""
    return _letter(
        "Confirm your camagru account",
        username,
        recipient,
        "Thanks for creating a camagru account. Open this link to confirm it. Until you do, login is refused.",
        "Confirm the account",
        link,
        "If you did not sign up, ignore this message.",
    )


def reset(username: str, recipient: str, link: str) -> Letter:
    """A reset letter. The new password is chosen on the link, not in this message."""
    return _letter(
        "Reset your camagru password",
        username,
        recipient,
        "A password reset was requested. Open this link to choose a new password. "
        "The link works once. Your current password keeps working until you do.",
        "Choose a new password",
        link,
        "If you did not ask for this, ignore this message.",
    )


def comment(
    username: str,
    recipient: str,
    link: str,
    commenter: str,
    preference: bool,
) -> Letter | None:
    """The comment notice, or None when the author turned notification off."""
    if not preference:
        return None

    return _letter(
        "New comment on your camagru picture",
        username,
        recipient,
        f"{commenter} commented on one of your pictures.",
        "See the picture",
        link,
        "You can turn these messages off on your camagru profile.",
    )


def _letter(
    subject: str,
    username: str,
    recipient: str,
    intro: str,
    link_text: str,
    link: str,
    closing: str,
) -> Letter:
    plain = f"Hi {username},\n\n{intro}\n\n{link}\n\n{closing}\n\nSent to {recipient}.\n"
    html = (
        "<p>Hi " + escape(username) + ",</p>"
        "<p>" + escape(intro) + "</p>"
        '<p><a href="' + escape(link) + '">' + escape(link_text) + "</a></p>"
        "<p>" + escape(closing) + "</p>"
    )

    return {"subject": subject, "plain": plain, "html": html}
