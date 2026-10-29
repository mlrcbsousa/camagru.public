# 25 Share

This walks through the two share links on a gallery card, drawn in [app/pages.py](../../app/pages.py). The picture address they carry is built in [app/server.py](../../app/server.py), and the card around them is in [18-gallery-page.md](18-gallery-page.md).

## The picture address

```python
gallery_card(
    row,
    comments_for(conn, row["id"]),
    _base() + "/pictures/" + str(row["id"]),
)
```

`_base` is `CAMAGRU_BASE_URL` without a trailing slash, so picture 9 on `http://127.0.0.1:8765` gets `http://127.0.0.1:8765/pictures/9`, and that string becomes the card's `url`.

## The two links

```python
'<p class="share">'
+ f'<a data-testid="share-x" target="_blank" rel="noopener noreferrer" href="https://x.com/intent/tweet?url={escape(row["url"])}">Share on X</a>'
+ f'<a data-testid="share-facebook" target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/sharer/sharer.php?u={escape(row["url"])}">Share on Facebook</a>'
+ "</p></div></article>"
```

`escape` makes the address safe inside the `href`. The X link is `https://x.com/intent/tweet?url=` plus that address and the Facebook link is `https://www.facebook.com/sharer/sharer.php?u=` plus the same address; both are the sites' own share pages.

`target="_blank"` opens each one in a new window so Camagru stays open. A new window normally receives `window.opener`, a handle back to the page that opened it, which would let the share site move Camagru to another address. `noopener` sets that handle to null ([noopener](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel/noopener)), and `noreferrer` does the same while also omitting the `Referer` header, so the share site is not told which Camagru address opened it ([noreferrer](https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/rel/noreferrer)).

The card loads no script from x.com or facebook.com. The gallery image is `<img src="/pictures/9">` and the share link carries the full address of that same picture. What the browser gets back when it fetches `/pictures/9`, the file bytes and the `Content-Type` header, is covered in [24-reply.md](24-reply.md); this page only builds the link.
