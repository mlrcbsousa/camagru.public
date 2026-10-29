# 14 Editor fill

`editor_page` in [app/pages.py](../../app/pages.py). The other pages are walked in [07-pages.md](07-pages.md), the file it fills is [13-editor-page.md](13-editor-page.md), and the editor walkthrough is [editor.md](../editor.md).

`editor.html` has three markers: `{{csrf}}`, `{{message}}`, and `{{thumbs}}`. `_fill` replaces those double braces and does not scan the result again, and a single brace is not a marker.

## The thumbnails are Python, not markers

```python
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
```

The `f` in front of a quote makes it a Python f-string, so `{picture["id"]}` is filled by Python while the string is built, before `_fill` ever runs. That is why those braces are single. The finished HTML is one string, and it becomes the value of `{{thumbs}}`.

With no pictures yet, the value is `<p class="empty">No pictures yet.</p>`; otherwise it is a `div` of those figures. Each image links to `/pictures/<id>`, which serves the stored PNG or GIF from [11-editor-routes.md](11-editor-routes.md), and the Delete button is the POST form for that same id, which the page script sends in place as described in [22-ajax.md](22-ajax.md).

`escape` runs on the CSRF token. The id is an integer from the database, so it needs no escaping, and no username is printed in this block.

## The message

A notice such as "Picture saved." is a blue paragraph, and an error replaces it; either one becomes the value of `{{message}}`. `_editor` decides which from the address, so the sentence is not in the file. A GIF save uses the same line, so `?notice=gif` gives "GIF saved." in `{{message}}`.

`render` then drops the whole editor into `{{main}}` of the shell, with the username and the logout form; that shell fill is covered in [07-pages.md](07-pages.md). The picture rows are [15-pictures.md](15-pictures.md).
