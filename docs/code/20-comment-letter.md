# 20 Comment letter

`comment` and `_letter` in [app/mail.py](../../app/mail.py). The route that calls `comment` is [17-gallery-routes.md](17-gallery-routes.md), confirmation and reset share the same `_letter`, and sending is [06-mail.md](06-mail.md).

## One comment letter

The author is ada, the commenter is bob, the preference is on, and the link is `http://localhost:8080/pictures/9`.

```python
def comment(
    username: str,
    recipient: str,
    link: str,
    commenter: str,
    preference: bool,
) -> Letter | None:
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
```

With `preference` false the function returns `None`, so the route never calls `_send`, though the comment is still stored.

With `preference` true it returns a letter with the subject `New comment on your camagru picture` and this plain text:

```text
Hi ada,

bob commented on one of your pictures.

http://localhost:8080/pictures/9

You can turn these messages off on your camagru profile.

Sent to ada@example.com.
```

The HTML part has the same words without the `Sent to` line, and puts the link on the words `See the picture`. `html.escape` runs on the username, the sentence, the link, the link text, and the closing line, so a commenter name cannot become a tag.

Printed page 7 says the author is notified by email but does not say the mail must contain a link. This letter has one because every letter from `_letter` does, and since there is no address for a single comment, the link opens the picture. The walkthrough still checks this link, as [01-gallery.md](../01-gallery.md#notes) notes.

The author is mailed for their own comment too, because `comment` never compares the commenter with the author. The same note is in that walkthrough.

## The shared shape

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

Every mail has this shape: a subject, `Hi` and the username, one sentence, one link, a closing line, in plain text and HTML. Confirmation, reset, and the comment notice differ only in the seven arguments they pass, never in the shape.
