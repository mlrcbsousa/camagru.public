# 21 Gallery CSS

This walks through the gallery rules in [public/app.css](../../public/app.css). The shared header, forms, and messages are in [09-css.md](09-css.md), the card markup is in [18-gallery-page.md](18-gallery-page.md), and the browser floor is in [accounts.md](../accounts.md#7-old-browsers).

## The cards

```css
.gallery {
  display: flex;
  flex-wrap: wrap;
}

.card {
  width: 100%;
  margin: 0 0 16px;
  overflow: hidden;
  border: 1px solid #e3e5e8;
  border-radius: 8px;
  background: #fff;
}
```

The cards sit in a wrapping row. Below 760px each card takes the full width, so they stack. From 760px up a card is `width: 48%` with `margin-right: 4%`, and `.card:nth-child(2n)` drops that right margin, so two cards fill each row. The space between them is plain margin rather than `gap` or a grid, because Firefox 41 has neither for this layout.

## The photo

```css
.card-photo {
  position: relative;
  height: 0;
  padding-top: 75%;
  overflow: hidden;
}

.card-photo img {
  position: absolute;
  top: 0;
  left: 0;
  display: block;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

`padding-top: 75%` makes the 4:3 box. A percentage padding is measured against the width, so 75% makes the box three quarters as tall as it is wide. With `height: 0` the content box is empty and all the visible height comes from the padding. `aspect-ratio` would say this in one line, but Firefox 41 does not have it.

The image is `position: absolute`, so it adds nothing to the content height, and its `height: 100%` resolves against the padding box (the area the padding opened) rather than the `0` content box. `object-fit: cover` then crops the picture to fill that box, which both browsers at the floor support.

## The byline and the like

```css
.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card .like-form {
  margin-right: 8px;
}
```

The byline sits on the left and the like row on the right, and `align-items: center` keeps the count on the same line as the name. `.card form` sets `margin: 0` on every form in the card, and `.like-form` alone would lose to that rule on specificity, so the gap is written as `.card .like-form`.

`.card form` also clears the page form's border, padding, and white background, so a form inside a card is flat.

## The comments

```css
.comments {
  height: 96px;
  margin: 0;
  padding: 0;
  overflow-y: auto;
  border-top: 1px solid #eaeef2;
  list-style: none;
  font-size: 14px;
}

.comments li {
  padding: 4px 0;
  border-bottom: 1px solid #eaeef2;
  word-wrap: break-word;
}
```

The list is a fixed 96px tall and a longer thread scrolls inside it, so a comment never makes one card taller than the one beside it. `word-wrap: break-word` breaks a long word; `overflow-wrap: anywhere` would too, but it is newer than Firefox 41.

The comment field is a row where the input is `flex: 1 1 auto` and the button keeps its width. The input also gets `min-width: 0`, which lets it shrink instead of pushing the button off the card.
