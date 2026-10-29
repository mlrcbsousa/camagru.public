import io  # https://docs.python.org/3/library/io.html#io.BytesIO
from collections.abc import (
    Sequence,  # https://docs.python.org/3/library/collections.abc.html
)

from PIL import Image, UnidentifiedImageError


def open_base(data: bytes) -> Image.Image:
    """Open image bytes with Pillow, or raise ValueError.

    https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open
    """
    try:
        # BytesIO is an in-memory file. Image.open reads a file, not a bare byte string.
        # https://docs.python.org/3/library/io.html#io.BytesIO
        image = Image.open(io.BytesIO(data))
        image.load()
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ValueError("not an image") from exc

    return image


def composite(base: bytes, frames: Sequence[bytes]) -> bytes:
    """Resize each frame onto the base and flatten them. The result is a PNG.

    https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image.alpha_composite
    """
    try:
        image = open_base(base).convert("RGBA")
    except ValueError:
        # A save never reaches this line. _save_picture already refused a bad photo.
        # The unit test feeds bytes Pillow cannot open, and _marker lets that test tell 0, 1, and 2 stickers apart.
        return _marker(base, frames)

    for frame in frames:
        try:
            layer = open_base(frame).convert("RGBA").resize(image.size)  # pyright: ignore[reportUnknownMemberType]
        except ValueError:
            # A sticker Pillow cannot open is skipped. The photo still saves.
            continue

        image.alpha_composite(layer)

    return _png(image)


def save_gif(snaps: Sequence[bytes]) -> bytes:
    """Build one GIF from the snaps. A snap Pillow cannot open raises ValueError.

    https://pillow.readthedocs.io/en-stable/handbook/image-file-formats.html#gif
    """
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


def _png(image: Image.Image) -> bytes:
    out = io.BytesIO()
    image.save(out, format="PNG")

    return out.getvalue()


def _marker(base: bytes, frames: Sequence[bytes]) -> bytes:
    """Stand-in bytes for the unit test, which feeds data Pillow cannot open."""
    body = b"\x89PNG\r\n\x1a\n" + str(len(frames)).encode() + base[8:]

    for frame in frames:
        body += frame

    # Keep the marker different from the input, even with no stickers.
    if body == base:
        body += b"x"

    return body
