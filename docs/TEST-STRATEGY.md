# Test Strategy: camagru

The suite lives in `tests/` (unit) and `e2e/` (Playwright). `make up` is the command that starts the app, and it does not install Playwright.

## Risk Summary

| Area | Risk | Impact | Test Response |
| --- | --- | --- | --- |
| Password storage, session, CSRF | High | Account takeover, or a plain password fails the defense | Unit, then Playwright on login |
| SQL and HTML injection | High | The defense stops on printed page 6 | Unit for SQL, Playwright for escaped HTML |
| Upload and composite | High | The project fails if the composite is not server-side, or a bad file is stored | Unit on PNG bytes |
| Comment mail | High | Mandatory mail, and a log line stops the defense | Unit on the message, Playwright against the test mailbox |
| Gallery page | Medium | Public list, page size 5, Next link, and scroll load | Unit on the query, Playwright on Next and scroll |
| Bonus | Medium | A superficial bonus does not count | Playwright on in-place updates, preview, share links. Unit on GIF bytes |
| Layout and logs | Medium | Missing header or any log stops the defense | Playwright on the layout and the empty `server-log` paragraph. Process output read in `make logs` during the walkthrough |

## Test Matrix

| Slice / AC | PRD Guard | Behaviour | Level | Scenario | Expected Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| AC-1, AC-5 | Goal 1 | Hash and mail body | Unit | `Password1` stored, `password` and `12345678` refused, reset body has one link | Stored value differs from the password. Verification uses `compare_digest`. Link is single-use | `make test` |
| AC-2, AC-3, AC-4 | Goal 1 | Cookie | Unit | Login after confirm sets a signed cookie. Logout bumps `session_version`. Expired and old-version cookies are rejected. Empty secret never listens. Bad CSRF does nothing | Cookie absent or present as specified | `make test` |
| AC-8, AC-9, AC-10 | Goal 2 | Composite | Unit | Zero, one, and two frames with visible pixels. Non-image base64 | PNG differs per frame count. Non-image raises and stores nothing | `make test` |
| AC-12, AC-14 | Goals 3, 4 | Page query and one like | Unit | 6 rows, like posted twice | Page 1 has the 5 newest. One like row | `make test` |
| AC-19 | Printed page 6 | Placeholder SQL | Unit | Password `blahblah' OR 1='1` | Login sets no cookie. The quote is not spliced into the statement | `make test` |
| AC-1 to AC-7, AC-11, AC-13, AC-15 to AC-18, AC-20 | All goals | Browser paths | E2E | Signup through the test mailbox, editor, gallery, XSS text, empty `server-log` paragraph | Observable result in the AC | `make e2e` |
| AC-21 to AC-24 | Bonus | Page updates | E2E | Like, comment, delete stay on the page. Frame visible on the webcam before save. Scroll appends the next 5 and stops. X and Facebook links carry the picture URL | No new document load. No third-party script. No load after the last page | `make e2e` |
| AC-25 | Bonus | GIF | Unit, E2E | Three snaps | Stored file is one GIF | `make test`, `make e2e` |

## Negative Tests

- The passwords `password`, `12345678`, and a 7-character mixed password are refused.
- A second use of a confirmation link does not log anyone in.
- A logged-out editor, like, comment, delete, or profile change stores nothing.
- Deleting another member's picture leaves the picture stored.
- Save with no base image stores nothing.
- A non-image upload stores nothing.
- A bad CSRF token stores nothing.
- With the preference off, no comment mail is sent.
- With SMTP down, the comment is kept.

## Regression Checks

- Save with zero frames succeeds once a base image is loaded, so a test that requires a frame before Save is wrong.
- A gallery fragment request past the last page redirects to the last page and stays a fragment.
- `sqlite3` errors propagate to the request handler, which answers with a short 500. A swallowed database error would be a PDO error-mode miss.
- Playwright is not installed in the image `make up` builds.

## Observability Checks

- An e2e test asserts that the empty `server-log` paragraph in `public/shell.html` stays empty. `QuietHandler.log_message` in `app/__main__.py` drops the request lines, and the 500 page catches exceptions so no traceback is printed.
- The process output itself is not captured by a test. It is checked by reading `make logs` during the walkthrough, after a signup, a save, and a comment.
- A `getUserMedia` console line on plain HTTP is the only allowed client message.
- There is no metric stack; the defense is the alert.

## CI Expectations

- `.github/workflows/ci.yml` runs the checks on every pull request and on `main`.
- `make test` runs `python -m unittest discover -s tests` on Python 3.15.0 through uv.
- `make e2e` runs Playwright from `e2e/`, with JSDoc types. It does not boot the app image: Playwright starts `e2e/serve.py`, which runs the app on port 8765 with a stand-in SMTP server on 2525 and a Mailpit-shaped inbox on 8026. `make up` uses 8080, 1025, and 8025, so `make e2e` can run while the containers are up.
- A failing test blocks the merge. A test for behaviour a branch does not implement is skipped, with the issue id as the skip text.

## Coverage Gaps

- Real webcam hardware. The e2e grants a fake camera, and the upload AC covers a machine with no camera.
- Firefox 41 and Chrome 46 binaries. Playwright's current browsers are newer, so the page script constraint is checked by review, not by a browser install in CI.

## Files

Unit tests, run with `unittest`:

- `tests/test_passwords.py`: rejects `password`, `12345678`, `AAAAAAAA`, a 7-character password, and a 129-character password, and accepts `Password1`. The stored hash is not the password, the iteration count is 600000, and a wrong password does not verify.
- `tests/test_session.py`: signed cookie round-trip, tampered cookie rejected, expired cookie rejected, cookie from before logout rejected, empty secret does not listen, bad CSRF rejected.
- `tests/test_mail.py`: the confirmation, reset, and comment messages each contain one link and the right recipient, and preference off builds no message.
- `tests/test_compose.py`: a real photo with a sticker becomes a new PNG, and 0, 1, and 2 frames give different bytes. A non-image raises, three snaps save one GIF, and a bad snap is refused.
- `tests/test_gallery.py`: 6 pictures, page size 5, `created_at` descending then id descending. A second like does not insert a second row. A query past the last page returns no rows, the request redirects that address to the last page, and a fragment request past the end is redirected to a fragment.
- `tests/test_accounts.py`: signup, confirm, login, logout, reset, and profile through the request handler, including the password `blahblah' OR 1='1`, which does not log in, and profile and logout posts without the CSRF token, which change nothing.
- `tests/test_editor.py`: save and delete redirect, save without a base image and a non-image upload store nothing, another member's picture survives a delete, and the editor opens with Save and Capture off.
- `tests/test_fields.py`: a parsed form or query keeps only the fields that route reads.

E2E, JSDoc, with its own `package.json` under `e2e/`:

- `e2e/accounts.spec.js`: AC-1 through AC-6, reading the inbox that `e2e/serve.py` serves on port 8026.
- `e2e/editor.spec.js`: AC-7 through AC-11.
- `e2e/gallery.spec.js`: AC-12 through AC-16.
- `e2e/shell.spec.js`: AC-17 through AC-20, including the empty `server-log` paragraph.
- `e2e/bonus.spec.js`: AC-21 through AC-25.
- `e2e/walkthrough.spec.js`: the numbered steps in `docs/01-*.md`, in order, with each test named after its step. `cd e2e && npm run walkthrough` runs it alone.

Omitted: a visual pixel diff, a load test.
