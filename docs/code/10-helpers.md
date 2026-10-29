# 10 helpers

The small functions at the bottom of [app/server.py](../../app/server.py), plus the form parsing in [app/boundary.py](../../app/boundary.py). The routes in [02-server.md](02-server.md) call them. Sending mail is covered in [06-mail.md](06-mail.md) and the cookie value in [03-session.md](03-session.md).

## Who is logged in

```python
def _user(conn: sqlite3.Connection, environ: WSGIEnvironment, secret: str) -> SessionUser | None:
    cookie = _cookie_value(env_str(environ, "HTTP_COOKIE", ""))

    if not cookie or not secret:
        return None

    parts = cookie.split(".")

    if not parts or not parts[0].isdigit():
        return None

    row = find_user_id(conn, int(parts[0]))

    if row is None:
        return None

    if read_session(cookie, secret, int(time.time()), row["session_version"]) is None:
        return None

    return session_user(row, csrf_token(row["id"], row["session_version"], secret))
```

A missing cookie or an empty secret means logged out. The cookie's first field is the user id, so it has to be digits, and a missing row is logged out too. `read_session` checks the signature and that the session version still matches the row, which is where a copied cookie dies after logout. `session_user` adds the Cross-Site Request Forgery (CSRF) token to the user so a form can print it; the token is never stored in the database.

`_cookie_value` walks the `Cookie` header, where several cookies are separated by `;`, and returns the value named `camagru`, or `""`.

## The posted fields

`parsed_body` in `boundary.py` reads `CONTENT_LENGTH` bytes from `wsgi.input`, and `parse_qs` turns `username=ada&password=` into a dict of lists. `keep_blank_values` keeps the empty password as `""`; without it a blank field would be missing and the page could not say which rule failed. `parsed_query` is the same parse on `QUERY_STRING`, the part after `?`. [parse_qs](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.parse_qs)

That parsed dict stays in `handle`. Each handler instead receives a typed form such as `signup_form(form)`, built by `allow`, which copies only the names in that handler's tuple and keeps the last value when a name is posted twice. A signup post of `username`, `email`, `password`, and `mail_ok` therefore gives `_signup` only the first three, and a gallery address `/?page=2&username=ada` gives `_gallery` `page`, `notice`, and `fragment`, but never `username`, which belongs to login.

## One host

```python
def _canonical(environ: WSGIEnvironment) -> Response | None:
    base = _base()
    host = env_str(environ, "HTTP_HOST", "")
    netloc = urlparse(base).netloc

    if not host or not netloc or host == netloc:
        return None

    path = env_str(environ, "PATH_INFO", "/") or "/"
    query = env_str(environ, "QUERY_STRING", "")
    target = base + path

    if query:
        target += "?" + query

    return _redirect(target)
```

Canonical means the one official address, which is `CAMAGRU_BASE_URL`. `HTTP_HOST` is the name the browser used for this request, and `netloc` is the host and port inside the base URL.

Open `http://127.0.0.1:8080/login` while the base URL is `http://localhost:8080`: host is `127.0.0.1:8080` and netloc is `localhost:8080`, so this returns a 303 to `http://localhost:8080/login`. The browser requests that URL, the host now matches, `_canonical` returns `None`, and login runs.

The redirect matters because a cookie set on `127.0.0.1` is not sent to `localhost`, and the stylesheet cache is separate too. Without it, a mail link and an already open tab can disagree about whether the member is logged in, and the page can show up unstyled. [Same-origin policy](https://developer.mozilla.org/en-US/docs/Web/Security/Same-origin_policy)

`_base` is `CAMAGRU_BASE_URL` with the trailing slash removed. The default in code is `http://127.0.0.1:8765`, the end-to-end port, while Compose uses `http://localhost:8080` when `.env` leaves it empty.

## Files

```python
STATIC = {
    "/app.css": "app.css",
    "/shell.html": "shell.html",
    "/base.png": "base.png",
    "/frames/a.png": "frames/a.png",
    "/frames/b.png": "frames/b.png",
}
```

`_static` looks the path up in that map; a path that is not a key returns `None` and routing continues. The file that gets opened is the value in the map, not the raw URL, so a request cannot ask for a file outside `public/`. The content type comes from the extension: `.css` is `text/css`, `.png` is `image/png`, and anything else is HTML.

`/app.css` is the stylesheet, `/base.png` is the sample photo, and the two frames are the stickers the editor overlays on the stage. `/shell.html` serves the raw file with `{{main}}` still unfilled. `render` in `pages.py` reads that same file and fills `{{main}}` with signup, login, and the other pages, which are not in this map, so opening `/shell.html` shows the empty chrome rather than a page with forms.

## The answer

```python
def _html(text: str, extra: Header | None = None) -> Response:
    headers = [("Content-Type", "text/html; charset=utf-8")]

    if extra is not None:
        headers.append(extra)

    return "200 OK", headers, text.encode()


def _redirect(location: str, extra: Header | None = None) -> Response:
    headers = [("Location", location)]

    if extra is not None:
        headers.append(extra)

    return "303 See Other", headers, b""
```

A response is a status, headers, and bytes, and `text.encode()` makes those bytes. `extra` is where a route attaches `Set-Cookie`. `303` tells the browser to GET the `Location`, so a later refresh reloads that page and does not send the form again. [303](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/303)

## The blue line

`_notice` maps a short code from the query string to a sentence. There are eight codes: `sent`, `confirmed`, `reset`, `saved`, `picture`, `deleted`, `nomail`, and `gif`. Any other code gives `""`, so a made-up `?notice=` cannot print attacker text. The page puts that sentence into `{{notice}}` or `{{message}}`.

## The name and the mail address

`_username_ok` allows 1 to 32 characters, each an ASCII letter, a digit, or `_`. `_email_ok` requires exactly one `@`, something before it, and a dot in the domain that is neither its first nor its last character. These are the signup checks for the name and address; the password rules are in [04-passwords.md](04-passwords.md).
