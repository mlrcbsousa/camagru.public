# Security

Which proof each route uses.

## Cookie 

`camagru` — who is logged in. The browser sends it on every path of this host. The server reads it on every request that is not a static file.

| Flow | Route | What happens |
| --- | --- | --- |
| Log in | `POST /login` | Password matches and the account is confirmed. The response sets the cookie. |
| Stay in after a profile save | `POST /profile` | A new cookie is set, so this browser stays logged in after `session_version` changes. |
| Log out | `POST /logout` | `session_version` is bumped and the cookie is cleared (`Max-Age=0`). |
| Open a page | any non-static `GET` | A missing, bad, expired, or old-version cookie means logged out. `/editor` goes to `/login`. `/profile` says to log in. `/` still shows the gallery. |

## CSRF

A hidden field on forms you can only submit while logged in. It is an HMAC of the user id and `session_version`. It is not stored, and it is not the mail link.

| Flow | Route | What happens |
| --- | --- | --- |
| The field is written into the page | `GET /`, `GET /editor`, `GET /profile` | Like, comment, save, delete, profile, and logout forms carry it. |
| Log out | `POST /logout` | A bad field does not log you out. |
| Save profile | `POST /profile` | A bad field redisplays the form as refused. |
| Save a still or a GIF | `POST /editor` | A bad field redirects to `/editor?error=refused`. |
| Like | `POST /pictures/<id>/like` | A bad field does not insert a like. |
| Comment | `POST /pictures/<id>/comment` | A bad field does not store a comment. |
| Delete | `POST /pictures/<id>/delete` | A bad field is the same reply as deleting someone else's picture. |

Signup, login, confirm, and reset do not use this field.

## Confirm token

The link in the signup mail. Only its hash is stored. One use.

| Flow | Route | What happens |
| --- | --- | --- |
| Sign up | `POST /signup` | An unconfirmed account is created and `/confirm/<token>` is mailed. No cookie. |
| Open the link | `GET /confirm/<token>` | The account is marked confirmed. Redirect to `/login?notice=confirmed`. Still no cookie. |
| Open it again, or a bad link | `GET /confirm/<token>` | The login page, and the account stays unconfirmed if it never succeeded. |
| Log in too early | `POST /login` | Redirect with `notice=unconfirmed`. |

## Reset token

The link in the reset mail. Same storage: hash only, one use, and a new one replaces the previous reset link.

| Flow | Route | What happens |
| --- | --- | --- |
| Ask for a reset | `POST /reset` | If that email has an account, `/reset/<token>` is mailed. The page says the same thing either way. |
| Open the link | `GET /reset/<token>` | The choose-password form. The token is not used up yet. |
| Choose a password | `POST /reset/<token>` | The token is consumed, the password is stored, `session_version` is bumped, and the account is marked confirmed. Redirect to `/login?notice=reset`. No cookie. |
| A weak password | `POST /reset/<token>` | The token is kept. |
| A second use, or a bad link | `POST /reset/<token>` | "that reset link is not valid." |