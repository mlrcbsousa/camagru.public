# 24 Reply

This walks through the bonus replies in [app/server.py](../../app/server.py). The page script that reads them is in [22-ajax.md](22-ajax.md), the three snaps are in [23-preview.md](23-preview.md), one still is in [12-compose.md](12-compose.md), and the GIF bytes come from `save_gif` in [app/compose.py](../../app/compose.py).

## JSON instead of a redirect

```python
def _json(data: dict[str, object]) -> Response:
    return "200 OK", [("Content-Type", "application/json")], json.dumps(data).encode()
```

`_json` builds the reply the script reads: `json.dumps` turns the dictionary into text, and the status is `200` rather than the `303` a redirect uses.

A like, a comment, or a delete with `xhr=1` returns that JSON, and without `xhr=1` the same action still redirects, so each action keeps one address instead of a second path. Only the script adds `xhr=1`. A browser with the script turned off posts the form as written, the field is absent, and the handler takes the redirect, which is why the switch is a form field and not a different URL.

```python
if form["xhr"] == "1":
    count = like_count(conn, int(picture_id)) if picture_id.isdigit() else 0

    return _json({"likes": count})

return _redirect(_gallery_address(form["page"], ""))
```

A like on picture 9 with `xhr=1` returns `{"likes": 1}`. The count is read after `like_once`, whose insert ignores a repeat, so a second like from the same member still returns `1`. The same like without `xhr=1` redirects back to the gallery page.

```python
if form["xhr"] == "1":
    return _json({
        "ok": stored,
        "body": form["body"],
        "username": user["username"] if user else "",
        "notice": _notice(notice),
    })

return _redirect(_gallery_address(form["page"], notice))
```

A stored comment `hello` from `ada` returns `{"ok": true, "body": "hello", "username": "ada", "notice": ""}`. When nothing was written `stored` is false, and so is `ok`. When the mail fails, `notice` is `the mail was not sent`, because that is the sentence `_notice("nomail")` returns. `body` is the posted text, which the page script inserts as text, as [22-ajax.md](22-ajax.md) shows.

```python
if posted["xhr"] == "1":
    picture_id = rest[: -len("/delete")]
    deleted = (
        user is not None
        and picture_id.isdigit()
        and csrf_accepts(posted["csrf"], user["id"], user["session_version"], secret)
        and delete_picture(conn, int(picture_id), user["id"])
    )

    return _json({"ok": deleted})
```

`delete_picture` is true only when the row belongs to this member, so ada deleting her picture 9 gets `{"ok": true}`, while Bob trying the same gets `{"ok": false}` and the row stays. Without `xhr=1`, a logged-in member's failed delete redirects to `/editor?error=notyours` (a logged-out post goes to `/login`).

## The next page

```python
def gallery_query(parsed: Parsed) -> GalleryQuery:
    fields = allow(parsed, ("page", "notice", "fragment"))

    return {"page": fields["page"], "notice": fields["notice"], "fragment": fields["fragment"]}
```

`fragment` is one of the three query fields kept; anything other than `page`, `notice`, or `fragment` is dropped.

```python
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
```

`GET /?page=2&fragment=1` sets that last argument true.

```python
if fragment:
    return "".join(blocks) + pager
```

That return is just the cards for page 2 followed by the pager line, which holds Previous and, when `has_next` is true, Next. It carries no gallery title and no header, and the script in [22-ajax.md](22-ajax.md) appends the cards and keeps only the Next link.

A page number past the last page never reaches that return, because `_gallery` redirects first:

```python
if page_number > last:
    code = query["notice"] if notice else ""

    return _redirect(_gallery_address(str(last), code, query["fragment"] == "1"))
```

```python
def _gallery_address(page: str, notice: str, fragment: bool = False) -> str:
    parts: list[str] = []

    if page.isdigit() and int(page) > 1:
        parts.append("page=" + page)

    if notice:
        parts.append("notice=" + notice)

    if fragment:
        parts.append("fragment=1")

    return "/?" + "&".join(parts) if parts else "/"
```

The redirect keeps `fragment=1`, so with two pages `GET /?page=3&fragment=1` is sent to `/?page=2&fragment=1`. `XMLHttpRequest` follows that redirect on its own, and the script gets the cards of the last page as a fragment rather than a full page. Those cards are already on screen, so the `img[src=...]` test in `appendNextCards` skips them, and since that fragment has no Next link the control turns into `No more pictures`. A like or a comment calls `_gallery_address` with two arguments, so `fragment` stays false and their redirect is a normal gallery address.

## The sticker names

```python
def _last(parsed: dict[str, list[str]], key: str) -> str:
    values = parsed.get(key, [])

    if not values:
        return ""

    return values[-1]


def allow(parsed: Parsed, keys: tuple[str, ...]) -> dict[str, str]:
    return {key: _last(parsed, key) for key in keys}


def allow_many(parsed: Parsed, key: str) -> list[str]:
    return list(parsed.get(key, []))
```

`allow` keeps one string per key, and since `_last` returns `values[-1]`, a repeated field keeps its last copy. `allow_many` keeps the whole list.

```python
def editor_form(parsed: Parsed) -> EditorForm:
    fields = allow(parsed, ("csrf", "upload_b64", "use_sample", "gif", "snap0", "snap1", "snap2"))
```

A field that is not in that tuple is dropped, and `frames` is deliberately not in it, because it can repeat.

```python
return _editor(
    conn,
    secret,
    method,
    editor_form(form),
    user,
    editor_query(query),
    allow_many(form, "frames"),
)
```

Instead it is read with `allow_many`, so Border plus star arrives as `["a", "b"]`, in the order the form sent them.

```python
def _frame_bytes(frames: list[str]) -> list[bytes]:
    chosen: list[bytes] = []
    folder = os.path.join(os.path.dirname(__file__), "..", "public", "frames")

    for name in frames:
        if name not in ("a", "b"):
            continue

        with open(os.path.join(folder, name + ".png"), "rb") as handle:
            chosen.append(handle.read())

    return chosen
```

`a` reads `public/frames/a.png` and `b` reads `public/frames/b.png`; any other name is skipped. The list order is the order the stickers are drawn, and a still save calls this same function:

```python
png = composite(raw, _frame_bytes(frames))
insert_picture(conn, user["id"], png, time.time())
```

## One GIF

```python
if form["gif"] == "1":
    error = _store_gif(conn, user, form, frames)

    return _redirect("/editor?error=gif" if error else "/editor?notice=gif")
```

With `gif` set to `1` no still is saved: the handler stores the animation, or redirects with `error=gif` when it cannot. After `notice=gif` the editor shows the same `editor-notice` line as any other save, with the text `GIF saved.` from `_notice`.

```python
def _store_gif(
    conn: sqlite3.Connection,
    user: SessionUser,
    form: EditorForm,
    frames: list[str],
) -> str:
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
```

Each snap is decoded and opened as an image before it is composited, so a bad snap returns `"gif"` right there and nothing is inserted. Three good snaps are composited with the same sticker files and handed to `save_gif`, which opens them again; if that fails, the same `"gif"` return sends the browser to `/editor?error=gif`. An empty return means success and gets the `notice=gif` redirect.

```python
def save_gif(snaps: Sequence[bytes]) -> bytes:
    images = [open_base(snap).convert("RGBA") for snap in snaps]
    out = io.BytesIO()
    images[0].save(
        out,
        format="GIF",
        save_all=True,
        append_images=images[1:],
        loop=0,
    )

    return out.getvalue()
```

A snap Pillow cannot open raises `ValueError` here, which `_store_gif` catches and turns into `"gif"`, so the browser lands on `/editor?error=gif` and nothing is inserted. There is no fallback file: anything other than a real GIF would not play in a browser, so the save refuses instead.

The first image is the first frame, `append_images` adds the other two, and `loop=0` makes it repeat forever. `getvalue` returns the bytes stored as the picture. Pillow's `format="GIF"` plays the role of PHP GD's `imagegif`, and printed page 5 allows the library because that PHP function exists; the row is in the README's function mapping table. [imagegif](https://www.php.net/manual/en/function.imagegif.php). [Pillow GIF](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif).

```python
def insert_picture(conn: sqlite3.Connection, user_id: int, image_bytes: bytes, now: float) -> int | None:
    cursor = conn.execute(
        "insert into pictures (user_id, image_bytes, created_at) values (?, ?, ?)",
        (user_id, image_bytes, int(now)),
    )
    conn.commit()

    return cursor.lastrowid
```

A GIF and a still go through this same insert, which stores the file bytes in `image_bytes` with no second column and no type flag.

```python
kind = "image/gif" if row["image_bytes"][:4] == b"GIF8" else "image/png"

return "200 OK", [("Content-Type", kind)], row["image_bytes"]
```

So `GET /pictures/9` looks at the first four bytes instead: `GIF8` matches both `GIF87a` and `GIF89a` and gets `image/gif`, and anything else is `image/png`. The gallery card is just `<img src="/pictures/9">`, which names no file type, so the browser relies on the `Content-Type` header, and a GIF is never labeled as a PNG.
