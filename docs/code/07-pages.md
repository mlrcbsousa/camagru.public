# 07 pages

Line by line for [app/pages.py](../../app/pages.py). This is the view: it turns values into HTML, and it neither decides who is logged in nor touches the database.

## Fill

The HTML files in `public/` contain markers like `{{username}}`, and `_fill` replaces each marker with the string it was given. `_read` loads the file from `ROOT`, the `public/` directory next to `app/`.

```python
def _fill(template: str, fields: dict[str, str]) -> str:
    def replacer(match: re.Match[str]) -> str:
        return fields.get(match.group(1), match.group(0))

    return re.sub(r"\{\{([a-z0-9_]+)\}\}", replacer, template)
```

`re.sub` calls `replacer` once per marker. `match.group(0)` is the whole marker, such as `{{username}}`, and `match.group(1)` is the name inside the parentheses, `username`. `fields.get(name, whole marker)` returns the value when that name was provided and the original `{{username}}` text when it was not, so an unknown marker stays visible instead of becoming the word `None`.

Printed page 5 forbids a library I did not write unless a PHP standard-library equivalent exists. Jinja is that kind of library, and PHP has no template engine: it fills a string with `str_replace`, which is what `_fill` does ([manual](https://www.php.net/manual/en/function.str-replace.php)). Whatever is passed in for `{{username}}` must therefore already be escaped, or a name could become HTML.

```python
def escape(value: object) -> str:
    if value is None:
        return ""

    return html_escape(str(value), quote=True)
```

There is no hand-written escaping: `html_escape` is the standard-library `html.escape` imported under another name. `quote=True` also turns a single quote into `&#x27;`, and `None` becomes `""` because `html.escape` does not accept `None`. When someone pastes a `<script>` into a comment, this function is why it shows up as text.

https://docs.python.org/3/library/html.html#html.escape

## The shell

```python
def render(main: str, session_label: str, logout: str = "", path: str = "/") -> str:
    shell = _read("shell.html")

    return _fill(
        shell,
        {
            "session": escape(session_label),
            "logout": logout,
            "main": main,
            "nav": _nav(not session_label, path),
        },
    )
```

`shell.html` is the header, the `<main>`, and the footer. `main` is the page body, already HTML, so it is not escaped again. `session_label` is the username, or `""` when logged out, so the header stays blank rather than saying "logged out". `_nav` leaves out the link for `path`, so Sign up is missing on `/signup` and Gallery is missing on `/`.

`_logout` builds the header form: empty when `user` is `None`, otherwise a post to `/logout` with the hidden CSRF field. Its button is what the end-to-end test clicks.

## One page

`signup_page`, `login_page`, `reset_page`, and `profile_page` follow the same three steps: read the HTML file, fill the markers, and wrap the result in the shell.

`reset_page` picks the file: with a token it is `reset-choose.html`, the new-password form, and without one it is `reset-request.html`, the email form.

`problem` builds the red block, and one call can carry two kinds of line. `rules` are the four password phrases (`at least 8 characters` and the rest), which go under the heading `Invalid password.`, while `others` is everything else, such as "that username or email is taken", and stays as paragraphs above the list. That way a signup can fail both ways at once. A notice is a blue paragraph and does not go through `problem`.

`session_label` is the text in the header: the username when someone is logged in and `""` when not. The shell puts it in `{{session}}`, and an empty label is how the header stays blank instead of saying "logged out". `_nav` receives `not session_label`, which is true when that string is empty and selects the logged-out set of links.

The braces are not a sandbox. A marker is safe only because the value was escaped before it was inserted and because a value is never scanned for more markers. Replacing one key at a time would break that, since a username of `{{email}}` could be rewritten into the email if `{{email}}` were replaced afterwards, so `_fill` replaces every marker of the original file in one pass and writes each value as plain text. `{{main}}`, `{{nav}}`, `{{logout}}`, `{{message}}`, and similar slots hold HTML this program built, so they are not escaped a second time; any visitor text inside them was escaped when that HTML was built.

`plain_page` wraps a short body in the shell, such as the "Log in to edit your profile." sentence. That body is trusted HTML written by `server.py`, not by a visitor.
