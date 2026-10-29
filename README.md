# camagru

Web app for webcam or uploaded photos with a server-side overlay. Subject v4.1. This tree is the private v1.

## Status

The server is Python 3.15.0 with `sqlite3`, Pillow, and `smtplib`, installed by uv. It runs as one app container next to Mailpit, and `make up` starts both. Decisions are in [docs/adr/README.md](docs/adr/README.md), documentation and others - e.g. security notes are in [docs/security.md](docs/security.md).

## AI usage

An assistant helped document the modules in `docs/`, explain concepts that were new in this stack, research the PHP standard-library equivalents in the table below, and write the end-to-end tests.

## Function mapping

Every function the server uses has a row here, and the PHP column names the standard-library equivalent the subject asks for. Manuals:

- [Python sqlite3](https://docs.python.org/3/library/sqlite3.html)
- [PDO](https://www.php.net/manual/en/book.pdo.php)
- [PDO_SQLITE](https://www.php.net/manual/en/ref.pdo-sqlite.php)
- [Python hashlib](https://docs.python.org/3/library/hashlib.html)
- [PHP hash](https://www.php.net/manual/en/book.hash.php)
- [Python smtplib](https://docs.python.org/3/library/smtplib.html)
- [PHP mail](https://www.php.net/manual/en/function.mail.php)
- [PHP GD](https://www.php.net/manual/en/book.image.php)
- [Pillow](https://pillow.readthedocs.io/en/stable/handbook/tutorial.html)
- [PHP hash_pbkdf2](https://www.php.net/manual/en/function.hash-pbkdf2.php)
- [Python hmac](https://docs.python.org/3/library/hmac.html)
- [PHP hash_equals](https://www.php.net/manual/en/function.hash-equals.php)
- [Python wsgiref](https://docs.python.org/3/library/wsgiref.html)
- [PHP built-in server](https://www.php.net/manual/en/features.commandline.webserver.php)
- [Python base64](https://docs.python.org/3/library/base64.html)
- [PHP base64_decode](https://www.php.net/manual/en/function.base64-decode.php)

| Python | PHP equivalent | Notes |
| --- | --- | --- |
| `sqlite3.connect` | `new PDO('sqlite:...')` | One connection per route request, closed when it ends. Static files skip the database. [sqlite3.connect](https://docs.python.org/3/library/sqlite3.html#sqlite3.connect), [PDO_SQLITE](https://www.php.net/manual/en/ref.pdo-sqlite.php) |
| `Connection.executescript` | `PDO::exec` | Creates the tables when they are missing. [executescript](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.executescript), [PDO::exec](https://www.php.net/manual/en/pdo.exec.php) |
| `Connection.execute` with `?` placeholders | `PDO::prepare` then `PDOStatement::execute` | Printed page 6: a user must not be able to alter the SQL. [execute](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.execute), [PDO::prepare](https://www.php.net/manual/en/pdo.prepare.php) |
| `sqlite3.Row` with `Cursor.fetchone` and `fetchall` | `PDOStatement::fetch` and `fetchAll` with `PDO::FETCH_ASSOC` | Columns are read by name. [Row](https://docs.python.org/3/library/sqlite3.html#sqlite3.Row), [fetch](https://www.php.net/manual/en/pdostatement.fetch.php) |
| `Cursor.lastrowid` | `PDO::lastInsertId` | The id of a new user or picture. [lastrowid](https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.lastrowid), [lastInsertId](https://www.php.net/manual/en/pdo.lastinsertid.php) |
| `Cursor.rowcount` | `PDOStatement::rowCount` | A delete reports whether the picture was the member's own. [rowcount](https://docs.python.org/3/library/sqlite3.html#sqlite3.Cursor.rowcount), [rowCount](https://www.php.net/manual/en/pdostatement.rowcount.php) |
| `Connection.commit` and `rollback` | `PDO::commit` and `PDO::rollBack` | Each write is committed, and a refused profile change is rolled back. [commit](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.commit), [PDO::commit](https://www.php.net/manual/en/pdo.commit.php) |
| exceptions from `sqlite3` | `PDO::ERRMODE_EXCEPTION` | Python raises by default. A taken username or email is `IntegrityError`, and a locked database is `OperationalError`. [Exceptions](https://docs.python.org/3/library/sqlite3.html#exceptions), [PDO errors](https://www.php.net/manual/en/pdo.error-handling.php) |
| `smtplib.SMTP` and `send_message` | `mail` | Behavior the subject requires. The SMTP bytes map to socket writes. [smtplib](https://docs.python.org/3/library/smtplib.html), [mail](https://www.php.net/manual/en/function.mail.php) |
| `email.message.EmailMessage` | `mail` headers | Builds the message `smtplib` sends, with a plain and an HTML part. [EmailMessage](https://docs.python.org/3/library/email.message.html), [mail](https://www.php.net/manual/en/function.mail.php) |
| Pillow open, resize, alpha composite, PNG save | `imagecreatefromstring`, `imagecopyresampled`, alpha blend, `imagepng` | A still. A file Pillow cannot open raises `UnidentifiedImageError`, where GD returns `false`. [Image.open](https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.open), [imagepng](https://www.php.net/manual/en/function.imagepng.php) |
| Pillow `Image.save` format GIF | `imagegif` | Bonus. Three snaps, one file. A snap Pillow cannot open is not stored. [GIF](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#gif), [imagegif](https://www.php.net/manual/en/function.imagegif.php) |
| `io.BytesIO` | `imagecreatefromstring` argument | Pillow reads a file. The bytes sit in memory. PHP GD takes the string directly. [BytesIO](https://docs.python.org/3/library/io.html#io.BytesIO), [imagecreatefromstring](https://www.php.net/manual/en/function.imagecreatefromstring.php) |
| `html.escape` | `htmlspecialchars` | Comment text, names, and mail HTML. [html.escape](https://docs.python.org/3/library/html.html#html.escape), [htmlspecialchars](https://www.php.net/manual/en/function.htmlspecialchars.php) |
| `json.dumps` | `json_encode` | Like, comment, and delete replies when the page script posts. [json.dumps](https://docs.python.org/3/library/json.html#json.dumps), [json_encode](https://www.php.net/manual/en/function.json-encode.php) |
| `hashlib.sha256` | `hash('sha256', ...)` | The mail token is stored as this digest, not as the link. [sha256](https://docs.python.org/3/library/hashlib.html#hashlib.sha256), [hash](https://www.php.net/manual/en/function.hash.php) |
| `hashlib.pbkdf2_hmac` | `hash_pbkdf2` | Salted password hash. [pbkdf2_hmac](https://docs.python.org/3/library/hashlib.html#hashlib.pbkdf2_hmac), [hash_pbkdf2](https://www.php.net/manual/en/function.hash-pbkdf2.php) |
| `hmac.new` | `hash_hmac` | The login cookie and the CSRF token. [hmac.new](https://docs.python.org/3/library/hmac.html#hmac.new), [hash_hmac](https://www.php.net/manual/en/function.hash-hmac.php) |
| `hmac.compare_digest` | `hash_equals` | Password, cookie signature, and CSRF compare. [compare_digest](https://docs.python.org/3/library/hmac.html#hmac.compare_digest), [hash_equals](https://www.php.net/manual/en/function.hash-equals.php) |
| `secrets.token_bytes` / `token_urlsafe` | `random_bytes` | Password salt and one-time mail tokens. [secrets](https://docs.python.org/3/library/secrets.html), [random_bytes](https://www.php.net/manual/en/function.random-bytes.php) |
| `time.time` | `time` | Picture `created_at`, token expiry, and cookie expiry. [time.time](https://docs.python.org/3/library/time.html#time.time), [time](https://www.php.net/manual/en/function.time.php) |
| `re.sub` with a function | `preg_replace_callback` | Fills `{{name}}` in the HTML files. A filled value is not scanned again. [re.sub](https://docs.python.org/3/library/re.html#re.sub), [preg_replace_callback](https://www.php.net/manual/en/function.preg-replace-callback.php) |
| `urllib.parse.quote` | `rawurlencode` | Username and email in a redirect query. [quote](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.quote), [rawurlencode](https://www.php.net/manual/en/function.rawurlencode.php) |
| `urllib.parse.urlparse` | `parse_url` | Host check that forces one site name. [urlparse](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.urlparse), [parse_url](https://www.php.net/manual/en/function.parse-url.php) |
| `urllib.parse.parse_qs` | `parse_str` | Form bodies and the query string. No multipart parser. [parse_qs](https://docs.python.org/3/library/urllib.parse.html#urllib.parse.parse_qs), [parse_str](https://www.php.net/manual/en/function.parse-str.php) |
| `base64.b64decode` with `validate=True` | `base64_decode` with `strict` | The page posts an upload as base64. No multipart parser. [b64decode](https://docs.python.org/3/library/base64.html#base64.b64decode), [base64_decode](https://www.php.net/manual/en/function.base64-decode.php) |
| `binascii.Error` | `base64_decode` returning `false` | What `b64decode` raises on text that is not base64, so the upload is refused. [binascii.Error](https://docs.python.org/3/library/binascii.html#binascii.Error), [base64_decode](https://www.php.net/manual/en/function.base64-decode.php) |
| `open` | `file_get_contents` | HTML pages, the stylesheet, sticker PNGs, and the sample photo. [open](https://docs.python.org/3/library/functions.html#open), [file_get_contents](https://www.php.net/manual/en/function.file-get-contents.php) |
| `os.path.join`, `dirname`, and `splitext` | `__DIR__`, `dirname`, and `pathinfo` | Paths into `public/` and to the database folder. The extension picks a static file's `Content-Type`. [os.path](https://docs.python.org/3/library/os.path.html), [pathinfo](https://www.php.net/manual/en/function.pathinfo.php) |
| `os.makedirs` | `mkdir` with `recursive` | Creates the database folder when it is missing. [makedirs](https://docs.python.org/3/library/os.html#os.makedirs), [mkdir](https://www.php.net/manual/en/function.mkdir.php) |
| `os.environ` | `getenv` | `CAMAGRU_SECRET`, `CAMAGRU_BASE_URL`, `CAMAGRU_BIND`, `CAMAGRU_PORT`, `CAMAGRU_SMTP_HOST`, `CAMAGRU_SMTP_PORT`, `CAMAGRU_MAIL_FROM`, `DATABASE_PATH`, and, outside `make up`, `CAMAGRU_DEBUG` and `CAMAGRU_E2E`. [os.environ](https://docs.python.org/3/library/os.html#os.environ), [getenv](https://www.php.net/manual/en/function.getenv.php) |
| `wsgiref.simple_server.WSGIServer` | PHP built-in server | The process entry. Not `make_server`. [WSGIServer](https://docs.python.org/3/library/wsgiref.html#wsgiref.simple_server.WSGIServer), [built-in server](https://www.php.net/manual/en/features.commandline.webserver.php) |
| `wsgiref.simple_server.WSGIRequestHandler` | PHP built-in server | `QuietHandler` overrides `log_message`, so no request line reaches stderr. [WSGIRequestHandler](https://docs.python.org/3/library/wsgiref.html#wsgiref.simple_server.WSGIRequestHandler), [built-in server](https://www.php.net/manual/en/features.commandline.webserver.php) |
| `socketserver.ThreadingMixIn` | PHP built-in server | One idle connection does not stall the site. [ThreadingMixIn](https://docs.python.org/3/library/socketserver.html#socketserver.ThreadingMixIn), [built-in server](https://www.php.net/manual/en/features.commandline.webserver.php) |

This table is the only Python-to-PHP map, so no second copy is kept.

The subject forbids a library I did not write unless PHP's standard library can do the same job. The rule does not run the other way: a function in the language I chose does not have to be rewritten just because PHP spells it differently, so `open` stays `open` because PHP has `file_get_contents`, and `hashlib` stays because PHP has `hash`. A package such as Pillow is allowed only because GD has `imagepng` and `imagegif`; without a PHP equivalent the package would be out and the work would be written in the app. Typing helpers from `typing`, `collections.abc`, and `wsgiref.types` are not a runtime library, so they are not in this table.

## Run

`make up` builds the app image and starts it with Mailpit. The app is at <http://localhost:8080> and the mailbox at <http://localhost:8025>. Fill `CAMAGRU_SECRET` in `.env` before `make up`, because compose refuses to start without it. `CAMAGRU_BASE_URL` defaults to `http://localhost:8080`. See [CICD.md](CICD.md).

