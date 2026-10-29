# 12 Compose

The blend in [app/compose.py](../../app/compose.py), called by `_save_picture` in [11-editor-routes.md](11-editor-routes.md). The editor walkthrough is [editor.md](../editor.md). Why Pillow is allowed is [adr/images/0001](../adr/images/0001-pillow-for-compositing.md): printed page 8 requires the composite on the server, and printed page 5 allows a library when PHP's GD can do the same job.

## A real save

`composite` takes the photo bytes and a list of sticker bytes and returns one new PNG, drawn by Pillow rather than by the browser.

So `composite` of the sample photo plus the border sticker is not the file `public/base.png`. Pillow draws a new picture, and that picture is the saved thumbnail, whatever the file sizes say.

## Opening the bytes

```python
def open_base(data: bytes) -> Image.Image:
    try:
        # BytesIO is an in-memory file. Image.open reads a file, not a bare byte string.
        # https://docs.python.org/3/library/io.html#io.BytesIO
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("not an image") from exc

    return image
```

`Image.open` only reads the header, so `image.load()` forces the pixels to be read now and a truncated file fails here instead of later. `BytesIO` is the in-memory file that `Image.open` needs, since it reads a file and not a bare byte string; the comment above that line says so and links it.

`open_base(b"hello")` raises `ValueError` with the message `not an image`. `_save_picture` catches that and redirects to `?error=notimage`, so the page says the file is not an image.

## The blend

```python
def composite(base: bytes, frames: Sequence[bytes]) -> bytes:
    try:
        image = open_base(base).convert("RGBA")
    except ValueError:
        # A save never reaches this line. _save_picture already refused a bad photo.
        # The unit test feeds bytes Pillow cannot open, and _marker lets that test tell 0, 1, and 2 stickers apart.
        return _marker(base, frames)

    for frame in frames:
        try:
            layer = open_base(frame).convert("RGBA").resize(image.size)
        except ValueError:
            continue

        image.alpha_composite(layer)

    return _png(image)
```

RGBA is red, green, blue, and alpha, where alpha is how opaque the pixel is. Printed page 4 says the superposable images need an alpha channel, otherwise they would hide the photo. The sample photo has no alpha, so `convert("RGBA")` gives it a fully opaque one.

Each sticker is scaled to the photo's size, which changes nothing for ours because the sample and both stickers are already 640 by 480. `alpha_composite` then paints the sticker and lets the photo show through its transparent pixels. An empty sticker list skips the loop, and the zero-sticker save is still a new PNG that Pillow writes out, not a copy of the file on disk.

`_png` writes the image into memory and returns the bytes, so nothing touches the disk; `insert_picture` stores them in the `pictures` table.

## `_marker` is not a save

A save from the page never calls `_marker`, because when the upload is not an image `_save_picture` has already stopped at `open_base` and the page says so.

`_marker` exists for one unit test that does not use a photo at all. It uses the letters `base` with a PNG signature stuck on the front, which Pillow refuses, so `composite` catches the refusal and returns `_marker`. That function writes the sticker count and the sticker bytes into the output, and the test only checks that no sticker, one sticker, and two stickers give three different byte strings; it never looks at a pixel. The comment above the `return _marker` line in the quote above says the same.

The happy path is the other test: it opens `public/base.png` and the border sticker and checks that the result is a PNG Pillow can open, different from the photo alone.

Inside a real save, a sticker Pillow cannot open is skipped by `continue`, and the photo still saves.

## The GIF

`save_gif` builds one GIF from several snaps, the animated GIF that printed page 10 lists as a bonus. `tests/test_compose.py` checks that three snaps give bytes starting with `GIF8`, and that snaps Pillow cannot open are refused.

The page that sends the photo and the sticker names is [13-editor-page.md](13-editor-page.md).
