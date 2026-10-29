# 01 Shell

Walkthrough for the shared page shell and the injection checks that run through it. The accounts, editor, and gallery clicks are in their own files, and the screen contract is [DESIGN.md](DESIGN.md).

A printed page is the footer number in the subject.

## Requirements

| Requirement | Subject | Acceptance |
| --- | --- | --- |
| Header, main, and footer on every page. Usable at phone width. | Printed page 5 | AC-17 |
| A comment containing a script is shown as text. A username cannot contain it. | Printed page 6 | AC-18 |
| A quote in a field is stored as data. The SQL text does not change. | Printed page 6 | AC-19 |
| `make up` serves the app. The server log stays empty apart from a `getUserMedia` warning on plain HTTP. | Printed page 5 | AC-20 |

## Steps

Leave the browser console and `make logs` open, and open the site as <http://localhost:8080>. `cd e2e && npm run walkthrough` runs these after the accounts, editor, and gallery steps, and its test names carry the numbers below.

1. At about 360px, open `/`, `/login`, `/signup`, and `/profile`. Pass: each page has a header, a main, and a footer, and nothing runs past the window.
2. Log in, save one picture, and comment `<script>window.__xss = 1</script>`. Pass: the comment is visible as text, script words included, and `window.__xss` stays unset, so the browser did not run it.
3. Comment again with `it's a picture`. Pass: the comment is visible with the quote, and a refresh does not add a second copy.
4. Sign up with username `<script>`. Pass: the page refuses it, because usernames are letters, digits, and underscore.
5. Open `/` and read the empty element `server-log`. Pass: it has no text, and `make logs` shows no request line.
