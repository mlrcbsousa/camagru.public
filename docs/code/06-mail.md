# 06 mail

Line by line for [app/mail.py](../../app/mail.py). This file only builds the letters; sending is `_send` in [app/server.py](../../app/server.py).

`confirmation`, `reset`, and `comment` each return a letter dict, except that `comment` returns `None` when the author turned notification off. The gallery route calls `comment`, see [17-gallery-routes.md](17-gallery-routes.md).

```python
def confirmation(username: str, recipient: str, link: str) -> Letter:
    return _letter(
        "Confirm your camagru account",
        username,
        recipient,
        "Thanks for creating a camagru account. Open this link to confirm it. Until you do, login is refused.",
        "Confirm the account",
        link,
        "If you did not sign up, ignore this message.",
    )
```

All three go through `_letter`, so every message has the same greeting, link, and closing line:

```python
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
```

`escape` is `html.escape`, so a username cannot become a tag in the HTML part, while the plain part is text and is not escaped. The confirmation link is the only way to confirm the account, and the message says to ignore it if you did not sign up.

`reset` passes the subject "Reset your camagru password" and a body saying the link works once and that the current password keeps working until a new one is chosen.

https://docs.python.org/3/library/html.html#html.escape

## Sending

This is `_send` in [app/server.py](../../app/server.py).

`EmailMessage`, from `email.message` in the standard library, is the letter itself, headers and body, and opens no network connection; `smtplib` is what sends it.

```python
message = EmailMessage()
message["To"] = recipient
message["From"] = os.environ.get("CAMAGRU_MAIL_FROM", "camagru@localhost")

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
```

`set_content` is the plain part and `add_alternative` adds the HTML part, so a mail program shows the HTML and keeps the plain text for clients that cannot. A string body would stay a single plain message with the subject `camagru`, but every caller passes a letter dict, so all three letters take the HTML path.

The host defaults to `127.0.0.1` and the port to `1025`. Compose sets the host to `mailpit`, and the end-to-end runner sets the port to `2525`, where its fake SMTP server listens.

`with smtplib.SMTP(host, port, timeout=5) as client` opens the connection and closes it when the block ends, even when sending raises. Writing `client = smtplib.SMTP(...)` would open it too, but then the code would have to call `quit` on every path, including the failure path, and `with` is that guarantee. https://docs.python.org/3/reference/compound_stmts.html#the-with-statement

A dead server raises `OSError` (operating system error), the base class for a refused connection, a timeout, and a reset. `_send` catches it and returns `False` without printing anything. https://docs.python.org/3/library/exceptions.html#OSError

At signup, `insert_user` has already called `commit()` before `_send` runs, so the account row is durable and a failed mail does not roll the signup back. The person has an account, and a finished password reset also confirms it.

https://docs.python.org/3/library/email.message.html#email.message.EmailMessage.set_content
https://docs.python.org/3/library/email.message.html#email.message.EmailMessage.add_alternative
https://docs.python.org/3/library/smtplib.html
