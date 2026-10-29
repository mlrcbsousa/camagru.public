# Product Spec: camagru

## Summary

A member publishes webcam or uploaded photos with frames composited on the server, and visitors browse them. Likes, comments, and account changes require login. Decisions are in [adr/README.md](adr/README.md).

## User Journeys

- Visitor: open the gallery, page through pictures, follow signup.
- New member: signup, open the confirmation mail, follow the link, log in.
- Member: log in, edit a picture, see it on the gallery, like or comment, edit profile, log out from any page.
- Author: receive one mail per new comment, or turn that preference off and receive none.

## Triggers

- Signup form, confirmation link, login form, reset form, profile form, logout control.
- Capture control or upload, with a base image loaded.
- Like control, comment form, delete control, comment-mail preference.

## Core Workflow

1. `make up` starts the app container and Mailpit, and the app serves HTTP with `wsgiref`.
2. Signup stores a salted PBKDF2 hash and emails one confirmation link. Login is refused until that link is opened.
3. Login sets the signed cookie from [auth/0001](adr/auth/0001-signed-session-cookie.md), and logout increments `session_version` and clears the cookie. A password reset emails one link, and the new password is entered on that link's page and nowhere else.
4. The editor shows a webcam preview, the frame list, a capture control, an upload control, and thumbnails of that member's pictures.
5. Save is refused without a base image. With one, 0, 1, or many frames are allowed, and Pillow composites them on the server and stores a PNG.
6. The gallery lists every picture, newest first, 5 per page, with a Next link to the following page. Likes and comments require the cookie, and a new comment emails the author when their preference is on.

## Bonus

The bonuses sit on top of the finished mandatory part, and a bonus that is incomplete does not count.

- Like, comment, and delete use `XMLHttpRequest` and change the current page, while signup, login, and capture stay full form posts.
- The webcam preview draws the selected frames on the picture before save, but the stored file is still the server composite.
- Reaching the bottom of the gallery appends the next 5 pictures, the Next link does the same load, and the list stops on the last page.
- Each picture has a link to X and a link to Facebook whose address carries the picture URL. The page loads no script from those sites.
- A member can save three webcam snaps as one GIF, which Pillow writes. The PHP map is `imagegif`.

## Edge Cases

- Password outside 8 to 128 characters, or without a letter, or without a digit: signup and password change refuse it, so `password`, `12345678`, and `AAAAAAAA` fail and `Password1` passes.
- Duplicate username or email, compared case-insensitively: signup refuses it, so `Bob` and `bob` are the same username.
- Confirmation link reused or unknown: no login.
- Logged-out request to the editor, a like, a comment, a delete, or a profile change: refused, no change stored.
- Delete of someone else's picture: refused.
- Save with no base image: refused. Save with a base image and zero frames: stored.
- Upload that Pillow cannot open: refused, nothing stored, nothing logged. The page posts the file as base64, which the server decodes with `base64.b64decode`, so there is no multipart body to parse.
- Comment-mail preference off: comment stored, no mail.
- SMTP failure: comment stored, the page says the mail was not sent, the server prints nothing.
- State-changing form with a bad CSRF token: refused.
- `getUserMedia` without HTTPS: that console message is the only allowed log.
- Scroll or Next past the last gallery page: no further request, and the list does not return to page 1. An address past the last page redirects to the last page, and a fragment request (`fragment=1`) stays a fragment.

## Delivery Slices

| Slice | Description | Value | Acceptance Criteria | Test Evidence |
| --- | --- | --- | --- | --- |
| 1 Accounts | Signup, confirm, login, logout, reset, profile | Nobody else can use the account | AC-1 to AC-6 | Unit on hash, cookie, mail body. Playwright on the forms |
| 2 Editor | Webcam, upload, 0 to many frames, server PNG, own deletes | A picture exists | AC-7 to AC-11 | Unit on composite bytes. Playwright on save and delete |
| 3 Gallery | Public pages of 5, Next link, likes, comments, preference | People can see and respond | AC-12 to AC-16 | Unit on the page query. Playwright on paging and comment mail |
| 4 Shell | Layout, one CSS file, `.env`, no logs, injection refused, `make up` | The defense is not stopped early | AC-17 to AC-20 | Playwright on layout and XSS. Unit on SQL placeholders |
| 5 Bonus | In-place like, comment, and delete. Webcam preview of the edit. Scroll loads the next 5. X and Facebook links. One GIF | The five leads are real features | AC-21 to AC-25 | Unit on the GIF bytes. Playwright on the page updates, the scroll, and the share links |

The editor and the gallery need accounts, the shell constraints hold on every page, and the bonus builds on the four mandatory areas.

## Acceptance Criteria

- AC-1: Given a new email and username and `Password1`, when they submit signup, then a row exists, the stored secret is not `Password1`, and Mailpit has one confirmation link.
- AC-2: Given that account before the link is opened, when they submit login, then no session cookie is set.
- AC-3: Given the link was opened, when they log in with the username and password, then the next page shows they are logged in.
- AC-4: Given they are logged in, when they use logout on any page, then the cookie is gone and the editor refuses them.
- AC-5: Given a forgotten password, when they ask for a reset, then Mailpit has one reset link, and that link lets them set a new password that meets the rule.
- AC-6: Given they are logged in, when they change username, email, or password to valid new values, then the next login uses the new values.
- AC-7: Given they are logged out, when they open the editor, then the page refuses them and stores nothing.
- AC-8: Given a base image and zero frames, when they save, then a PNG is stored. Given no base image, when they save, then nothing is stored.
- AC-9: Given a base image and two frames, when they save, then the PNG bytes differ from the base image alone and from a one-frame composite.
- AC-10: Given no camera, when they choose a PNG, then the page posts it as base64 and that file is the base image. Given a non-image, when they post it, then nothing is stored.
- AC-11: Given a picture they own, when they delete it, then it is gone. Given someone else's picture, when they delete it, then it remains.
- AC-12: Given 6 pictures, when a visitor opens the gallery, then the first page shows 5, ordered by creation time descending and then id descending, and the next page shows the older one.
- AC-13: Given a visitor, when they try to like or comment, then nothing is stored.
- AC-14: Given a member, when they like a picture twice, then the picture has one like from them.
- AC-15: Given the author's preference is on, when a member comments, then the comment is visible and Mailpit has one mail to the author.
- AC-16: Given the author turned the preference off, when a member comments, then the comment is visible and no mail is sent.
- AC-17: Given any page, when it renders, then it has a header, a main, and a footer, and the layout is usable at 360px wide.
- AC-18: Given a comment containing `<script>`, when it is shown, then the browser does not run it. A username cannot contain that text. Signup refuses anything outside letters, digits, and underscore.
- AC-19: Given a login or a comment field with a quote, when it is submitted, then the SQL is unchanged and the text is stored as data.
- AC-20: Given a clean tree and `.env` filled just before the run, when `make up` runs, then the app and Mailpit answer, and the server log stays empty apart from a `getUserMedia` failure on plain HTTP.
- AC-21: Given a logged-in member, when they like, comment, or delete, then the current page updates and the browser does not load a new document.
- AC-22: Given a base image and one frame selected, when the webcam preview is showing, then the frame is visible on that preview before save. The stored file is still the server PNG.
- AC-23: Given 6 pictures, when a visitor reaches the bottom, then the sixth picture is appended. The Next link appends that same picture if it is not already shown. Nothing loads after the last picture.
- AC-24: Given a stored picture, when the page shows it, then it has one X link and one Facebook link, each address contains the picture URL, and the page has no script from those sites.
- AC-25: Given three webcam snaps, when the member saves a GIF, then Pillow reports one GIF and the file is stored.

## Non-Functional Requirements

- Security: salted PBKDF2, CSRF on every state-changing form, escaped HTML, parameterized SQL, upload rejected unless Pillow opens it, secrets only from the environment.
- Observability: no access log, no stack trace, no debug print. A mail failure is a sentence on the page.
- Performance: a gallery page reads its 5 pictures with one paged query, plus one comment query per card. There is no other budget.
- Reliability: a failed mail does not roll back the comment or the signup row. A reset mail can be requested again; a lost confirmation mail cannot be resent, but a completed password reset also confirms the account.

## Alert Controls

Comment mail only.

- Source of truth: a new comment row, which sends one mail. There is no digest and no second send.
- The preference defaults to on, off means no mail, and the author changes it on the profile while logged in.
- The recipient is the image author. The commenter sees the comment either way.
- SMTP failure: the comment stays, the page says the mail was not sent, and the process writes nothing.
- The link's origin and the sender address come from the environment, not from the code.

## Technical Constraints

- Python 3.15.0, which uv installs together with Pillow. Apart from Pillow, the app imports only the standard library: `sqlite3`, `hashlib`, `hmac`, `secrets`, `smtplib`, `email.message`, `wsgiref`, `socketserver`, `base64`, `binascii`, `io`, `json`, `re`, `html`, `time`, `urllib.parse`, and `os`, plus typing helpers. Each call needs a README row. There is no multipart parser and no `cgi`.
- The server mixes in `socketserver.ThreadingMixIn` and overrides `log_message` so stderr stays empty. Each request opens its own `sqlite3` connection and closes it, so `check_same_thread` stays at the default. A locked database is an error page, and the traceback never reaches stderr.
- `CAMAGRU_BASE_URL` is the public origin, and links in mail use it. The cookie is Secure only when it starts with `https`, and `make up` defaults to an `http` URL.
- Pages are HTML files plus escaping, with one plain CSS file. No template package and no CSS framework.
- Page JavaScript stays inside Firefox 41 and Chrome 46: no `const`, no `class`, no `async`, no `navigator.mediaDevices` as the only camera call. Use `navigator.getUserMedia` and the `webkit` prefix.
- Playwright and the unit tests stay out of the image `make up` builds.
- The module layout is `app/`, `public/`, `tests/`, `e2e/`, from the deploy ADR.

## Open Questions + Assumptions

- Gallery order is newest first, then higher id. The PDF says "ordered by date of creation" without saying which end comes first, and the id tie-break keeps two pictures from the same second in a stable order.
- A like is one row per member per picture, enforced by a unique constraint, so a second click does not add another. Removing a like is not required.
- A username is 1 to 32 characters of letters, digits, and underscore, unique case-insensitively. Login uses the same match, and the page shows the spelling stored at signup.
- There is no resend of the confirmation mail: signing up again with the same username or email is refused as taken. A new token of either kind replaces the previous one for that account.
- An email is unique case-insensitively and must contain exactly one `@` and a dot inside the domain.
- The page size is 5, the minimum the PDF allows, and the Next link and the scroll load use the same size.
