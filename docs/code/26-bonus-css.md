# 26 Bonus CSS

This walks through the bonus rules at the end of [public/app.css](../../public/app.css). The card grid is in [21-gallery-css.md](21-gallery-css.md), the stage box is in [16-editor-css.md](16-editor-css.md), and why the stickers sit in that box is in [23-preview.md](23-preview.md).

## The stickers

```css
.stage .overlay {
  z-index: 1;
  object-fit: fill;
}
```

`.stage video` and `.stage img` are already `position: absolute` and fill the stage, and with no `z-index` they paint in file order. This rule gives both sticker images `z-index: 1`, which lifts them above the camera and the still. `object-fit: fill` stretches each sticker to the stage, because the photo rule's `cover` would crop it.

## The share row

```css
.share {
  display: flex;
  font-size: 14px;
}

.share a {
  margin-right: 12px;
}
```

Share on X and Share on Facebook sit in one row, spaced by `margin-right` on each link rather than `gap`, because Firefox 41 does not have flexbox `gap`. The links themselves are in [25-share.md](25-share.md).
