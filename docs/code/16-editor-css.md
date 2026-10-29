# 16 Editor CSS

The editor rules in [public/app.css](../../public/app.css). The shared header, forms, and messages are [09-css.md](09-css.md), the browser floor is [accounts.md](../accounts.md#7-old-browsers), and the editor walkthrough is [editor.md](../editor.md).

## The stage

```css
.stage {
  position: relative;
  height: 0;
  margin-bottom: 12px;
  padding-top: 75%;
  overflow: hidden;
  border-radius: 8px;
  background: #24292f;
}

.stage video, .stage img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}
```

`padding-top: 75%` makes the 4:3 box. A percentage padding is a fraction of the element's width, so the padding is three quarters of the width tall and the box comes out 4 wide by 3 tall. `height: 0` empties the content box, which means the visible height is all padding. `aspect-ratio` would say this in one line, but Firefox 41 does not have it.

The video and the preview image are `position: absolute`, so they add nothing to that content height. Their `height: 100%` resolves against the stage's padding box, the area the padding opened, not the `0` content box, and `top: 0` with `left: 0` lays them over it. `object-fit: cover` then crops them to fill the box, which both browsers at the floor support.

## Stickers and buttons

`.frames` and `.actions` space their children with `margin` because the floor has no flex `gap`. The file input sits on top of its label at `opacity: 0`, so the label is the visible Upload button while the input still receives the click.

`button:disabled` is half transparent, which is how Capture looks before a sticker is picked and Save looks before there is a photo.

## Your pictures

Below 760px the thumbnails are `width: 48%`, two per row, and the right one drops its margin with `:nth-child(2n)`.

At 760px and up, `.editor` becomes a row where the workspace takes twice the width of the side column. `.editor-side .thumbs` is `position: absolute` with `top`, `right`, `bottom`, and `left` set and `overflow-y: auto`, so the list is exactly as tall as the workspace below its heading and scrolls inside itself. `position: sticky` would also pin it, but the floor has no reliable sticky, so the absolute box stands in for it.
