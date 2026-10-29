# Security

Which proof each route uses.
The decision is [ADR 0001](adr/auth/0001-signed-session-cookie.md).
The handlers are in [app/server.py](../app/server.py).

## Cookie

`camagru` is who is logged in.
The browser sends it on every path of this host.
The server reads it on every request that is not a static file.

### Log in

`POST /login`.
The password matches and the account is confirmed.
The response sets the cookie.

### Stay in after a profile save

`POST /profile`.
A new cookie is set after `session_version` changes.
This browser stays logged in.

### Clear the cookie

`POST /logout`.
`session_version` is bumped.
The cookie is cleared with `Max-Age=0`.

### Open a page

Any non-static `GET`.
A missing, bad, expired, or old-version cookie means logged out.
`/editor` goes to `/login`.
`/profile` says to log in.
`/` still shows the gallery.

## CSRF

A hidden field on forms a logged-in member can submit.
It is an HMAC of the user id and `session_version`.
It is not stored, and it is not a mail link.

### Written into the page

`GET /`, `GET /editor`, and `GET /profile`.
Like, comment, save, delete, profile, and logout forms carry it.

### Refuse a bad logout

`POST /logout`.
A bad field does not log the member out.

### Save profile

`POST /profile`.
A bad field redisplays the form as refused.

### Save a still or a GIF

`POST /editor`.
A bad field redirects to `/editor?error=refused`.

### Like

`POST /pictures/<id>/like`.
A bad field does not insert a like.

### Comment

`POST /pictures/<id>/comment`.
A bad field does not store a comment.

### Delete

`POST /pictures/<id>/delete`.
A bad field gets the same reply as a picture owned by someone else.
The page script gets `{"ok": false}`.
Without the script the browser goes to `/editor?error=notyours`.
The delete requires that picture id and this member's user id.
The statement is `delete from pictures where id = ? and user_id = ?`.

Signup, login, confirm, and reset do not carry this field.

## Confirm token

The link in the signup mail.
Only its hash is stored.
One use.

### Sign up

`POST /signup`.
An unconfirmed account is created.
`/confirm/<token>` is mailed.
No cookie is set.

### Open the confirm link

`GET /confirm/<token>`.
The account is marked confirmed.
Redirect to `/login?notice=confirmed`.
Still no cookie.

### Open it again, or a bad link

`GET /confirm/<token>`.
The login page is shown.
An account that never succeeded stays unconfirmed.

### Log in too early

`POST /login`.
Redirect with `notice=unconfirmed`.

## Reset token

The link in the reset mail.
Same storage: hash only, and one use.
A new one replaces the previous reset link.

### Ask for a reset

`POST /reset`.
If that email has an account, `/reset/<token>` is mailed.
The page says the same thing either way.

### Open the reset link

`GET /reset/<token>`.
The choose-password form is shown.
The token is not used up yet.

### Choose a password

`POST /reset/<token>`.
The token is consumed and the password is stored.
`session_version` is bumped.
The account is marked confirmed.
Redirect to `/login?notice=reset`.
No cookie is set.

### A weak password

`POST /reset/<token>`.
The token is kept.

### A second use, or a bad link

`POST /reset/<token>`.
The page says "that reset link is not valid."
