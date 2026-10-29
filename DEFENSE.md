# Defense

Notes drawn from [docs/adr/README.md](docs/adr/README.md). Do not publish this file.

- The subject is v4.1. Save accepts 0, 1, or many overlays once a base image is loaded. [subject/0001](docs/adr/subject/0001-build-to-v4-1.md).
- A Slack message is not a ruling. [sources/0001](docs/adr/sources/0001-slack-is-not-a-ruling.md).
- The server is Python 3.15.0, which the image installs, with uv as the installer only. It uses `sqlite3` with placeholders, Pillow mapped to GD, and `smtplib` mapped to `mail`. [stack/0001](docs/adr/stack/0001-python-and-sqlite3.md), [images/0001](docs/adr/images/0001-pillow-for-compositing.md), [mail/0001](docs/adr/mail/0001-mail-through-smtplib.md).
- Login is an HMAC-signed cookie, checked against a `session_version` on the user row. The database stores a salted PBKDF2-SHA256 hash with 600000 iterations, and a password needs 8 to 128 characters, a letter, and a digit. [auth/0001](docs/adr/auth/0001-signed-session-cookie.md).
- `make up` starts the app container and Mailpit. The sqlite file lives on the `camagru-data` volume mounted in the app container, and Playwright is not in that image. [deploy/0001](docs/adr/deploy/0001-one-app-container-and-mailpit.md).
- A secret anywhere but the `.env` written before `make up` fails the project, and so does any log other than `getUserMedia` without HTTPS.
