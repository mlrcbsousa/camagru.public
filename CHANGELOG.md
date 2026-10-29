# Changelog

## [0.0.14] - 2026-10-29

- Update the README regarding module notes, the PHP mapping, and the end-to-end tests - 42S-30

## [0.0.13] - 2026-10-29

- Save GIF snaps the live camera only, and a sample or an upload is refused - 42S-10

## [0.0.12] - 2026-10-29

- A GIF save shows one notice, a scrolled gallery past its last page still gets cards, and `make e2e` runs next to `make up` - 42S-35

## [0.0.11] - 2026-10-28

- Each non-obvious branch in the server and page scripts has a one-line comment - 42S-30

## [0.0.10] - 2026-10-24

- Likes, comments, and deletes stay on the page, the gallery scrolls, pictures can be shared, and three snaps save one GIF - 42S-21
- A comment removes the empty line, share links open a new window, and GIF snaps are 1s apart - 42S-21

## [0.0.9] - 2026-10-24

- Every page has a header, a main, and a footer, comments stay text, and `make up` starts the app and Mailpit - 42S-9

## [0.0.8] - 2026-10-24

- The gallery shows five pictures a page, and a member can like once and comment, with mail when the author wants it - 42S-8
- A gallery page past the last one redirects to the last page - 42S-8

## [0.0.7] - 2026-10-24

- A member can save a server PNG with zero or more frames, upload a base image, and delete their own picture - 42S-7

## [0.0.6] - 2026-10-24

- A member can sign up, confirm, log in, reset a password, edit the profile, and log out - 42S-6
- A reset password is accepted only on the mailed link, and logout ends the session - 42S-6
- Signup and reset redirect after success, and login says why it failed - 42S-6
- A failed login redirects, so refresh does not send the password again - 42S-6
- An empty reset does not claim a mail was sent - 42S-6
- `make up` starts the app and Mailpit - 42S-6
- Build type-checks with basedpyright - 42S-6

## [0.0.5] - 2026-10-23

- Added the failing unit suite and the Playwright page objects - 42S-22
- Pinned the named runtime to Python 3.15.0 - 42S-22

## [0.0.4] - 2026-10-23

- Added the product spec, the design index, and the test strategy - 42S-5
- Changed the e2e job to Node 24 and linked each tool's documentation - 42S-5

## [0.0.3] - 2026-10-23

- Wired lint, unit test, build, and e2e to ruff, unittest, compileall, and Playwright - 42S-5

## [0.0.2] - 2026-10-23

- Added the check, build, and deploy pipeline - 42S-5
- Added the accepted architecture decisions - 42S-5

## [0.0.1] - 2026-10-23

- Added the repo skeleton and the check commands - 42S-5
