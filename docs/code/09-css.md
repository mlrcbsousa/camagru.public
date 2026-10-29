# 09 css

A walk through [public/app.css](../../public/app.css), which uses no framework. The subject names Firefox 41 and Chrome 46, and neither supports flexbox `gap` ([caniuse](https://caniuse.com/flexbox-gap)), so all spacing here is `margin`.

## The page

```css
* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font: 16px/1.5 system-ui, -apple-system, "Segoe UI", sans-serif;
  color: #1f2328;
  background: #f6f7f9;
}
```

`border-box` makes a width include the padding and the border, so a 420px form stays 420px after padding is added. Without it the padding is extra and the form grows past its measure.

`margin: 0` removes the browser's default gap around the page, and `16px/1.5` is the font size and line height. `system-ui` is the operating system's font; Firefox 41 does not know that name and falls through to `sans-serif`.

## The header

```css
header {
  display: flex;
  flex-wrap: nowrap;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e3e5e8;
}

header p {
  flex: 0 1 8rem;
  min-width: 0;
  max-width: 8rem;
  margin: 0 12px;
  overflow: hidden;
  color: #57606a;
  text-align: right;
  text-overflow: ellipsis;
  white-space: nowrap;
}

header p:empty {
  display: none;
}
```

`flex` lays the nav, the username, and the logout button in one row, and `nowrap` stops a long name from pushing Log out onto a second line. The username starts at 8rem, never grows past it, and may shrink (the `1` in `flex: 0 1 8rem`). `min-width: 0` is required because a flex item otherwise refuses to shrink below its text. The ellipsis needs all three of `overflow: hidden`, `white-space: nowrap`, and a bounded width. `:empty` hides the username element when nobody is logged in, so it leaves no gap.

`header form` clears the white card, the padding, and the border, because the logout control is a form and the `form` rule below would otherwise draw a card in the header. `header nav a` spaces the links with `margin-right: 16px` instead of `gap`.

## The column

```css
main {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px 16px;
}

.account {
  max-width: 420px;
  margin: 0 auto;
}
```

`margin: 0 auto` centers a block that has a width. The gallery lives directly in `main` and can use the full 960px, while sign up, login, reset, and profile sit in `.account`, so their forms are a narrow column in the middle. `.lead` is the grey sentence under the title.

## The form

```css
form {
  display: flex;
  flex-direction: column;
  max-width: 420px;
  padding: 16px;
  background: #fff;
  border: 1px solid #e3e5e8;
  border-radius: 8px;
}

form > * {
  margin-bottom: 12px;
}
```

The white card is the form itself. `flex-direction: column` stacks the fields, and `form > *` gives each direct child the bottom margin that `gap` would have provided. `:last-child` removes that margin after the button so the card does not end with an empty strip.

`label` is also a column, so the caption sits above the input, and `label input` adds `margin-top: 4px` between the caption and the box. `label.check` is a row for a checkbox, which profile uses for comment mail.

`button` is blue and only as wide as its label (`align-self: flex-start`). `button.secondary` and `header button` are white, which is the rule the logout button picks up.

## Messages

```css
.notice {
  padding: 8px 12px;
  border-radius: 6px;
  background: #ddf4ff;
}

[data-testid$="-error"] {
  margin-top: 12px;
  padding: 8px 12px;
  border-radius: 6px;
  background: #ffebe9;
  color: #cf222e;
}
```

`.notice` is the blue line: mail sent, profile saved, account confirmed. `[data-testid$="-error"]` matches any test id that ends in `-error` (`$=` means "ends with"), which is the red block from `problem`. The visitor sees the color, and Playwright finds the block by its test id.

`img, input, button { max-width: 100% }` keeps a picture or a control inside the column. The editor rules are in [16-editor-css.md](16-editor-css.md).
