# PRD: camagru

## Problem

A visitor cannot take or upload a photo, put a frame on it, and show that picture to other people. The school project is the occasion, but the product is the gallery.

## Solution

A small site where someone creates an account, confirms the email, takes or uploads a picture, has frames composited on it by the server, and publishes it. Anyone can look, logged-in people can like and comment, and a comment can email the author.

## Users

- Primary: a logged-in member who takes pictures and wants them public.
- Secondary: a visitor who only browses the gallery.
- Secondary: the author of a picture, who wants to know about comments and can turn that mail off.

## Goals

- A new person can register, confirm, log in, reset a password, edit the profile, and log out in one click.
- A member can publish a picture from the webcam or an upload, with 0, 1, or many frames composited on the server.
- Anyone can page through every picture, newest first, 5 per page.
- A logged-in member can like and comment, and a new comment emails the author unless that author turned the preference off.
- Once the mandatory part is perfect: likes, comments, and deletes update the current page, the webcam shows the edited result before save, the gallery loads the next 5 pictures on scroll and keeps a Next link, each picture has an X link and a Facebook link, and three webcam snaps can be saved as one GIF.

## Non-goals

- A CSS framework. The site uses one plain CSS file.
- A second database service, an ORM, a template package, or a web framework.
- Staging, and a production host for this deadline.

## Success metrics

| Metric | Baseline | Target | Measurement |
| --- | --- | --- | --- |
| Mandatory checks | Not built | Every mandatory step passes in a mock defense | Walk the steps in `docs/01-*.md` against a running `make up` |
| Ready date | 21 Oct 2026, no app | Runnable from a clean clone by 26 Oct 2026 | `make up` on a machine that has Docker |
| Defenses | 0 passed | 3 passed by 2 Nov 2026 | Intra |

## User stories

1. As a visitor, I want to register with a username, email, and a password that is not trivial, so that the account is mine.
2. As a new member, I want a unique link in my email, so that I cannot log in until I confirm.
3. As a member, I want to log in, log out from any page, reset a forgotten password by email, and change my username, email, or password.
4. As a member, I want a webcam preview, a list of frames, and a capture button, so that I can make a picture.
5. As a member without a camera, I want to upload an image instead.
6. As a member, I want the server to merge the photo and the frames, so that the saved file is the result.
7. As a member, I want to delete only my own pictures.
8. As a visitor, I want every picture, newest first, 5 per page.
9. As a member, I want to like and comment, and as an author I want an email unless I turned that off.
10. As a member, I want a like, a comment, or a delete to update the page I am on.
11. As a member, I want to see the frames on the webcam before I save.
12. As a visitor, I want the next 5 pictures when I reach the bottom, and a Next link that does the same.
13. As a member, I want an X link and a Facebook link for a picture.
14. As a member, I want three webcam snaps saved as one GIF.

## Scope

In: accounts, editor, gallery, mail, the one-command containers, the security cases on printed page 6, and the five bonuses after the mandatory part.

Out: a public portfolio rename.

## Constraints

- v4.1. Save accepts 0, 1, or many overlays once a base image is loaded, while Capture still waits for an overlay as printed page 8 asks.
- Every server function needs a PHP standard-library equivalent. Client pages are HTML, CSS, and JavaScript.
- Firefox >= 41 and Chrome >= 46, a header, a main, and a footer, and a layout usable on a small screen.
- No console or server log, except `getUserMedia` without HTTPS.
- Secrets live only in a gitignored `.env`, and a secret anywhere else fails the project.
- Build deadline 26 Oct 2026, and three defenses by 2 Nov 2026.

## Risks

- The Pillow-to-GD mapping is rejected at the defense. Mitigation: one image package, and one README row per call.
- The password rule is ours, because the PDF says "minimum level of complexity" and stops there. Mitigation: the rule is one sentence in the auth ADR, and the defense states it.
- Page script uses an API Chrome 46 lacks. Mitigation: the spec names the baseline.
- A bonus ships before the mandatory part is perfect. Mitigation: the bonus is built only on top of the four finished mandatory areas.

## Open questions

- None at product level. Delivery assumptions are in the spec.
