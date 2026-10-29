# Screens

Each screen is described in its own section here, and a screen without a section does not exist.

The bar for the account screens is that a person who has not read the code can sign up, open the confirmation link in Mailpit, log in, log out, reset the password, and edit the profile without asking what a control does.

Every page shares the shell: a header with the navigation and the session, a main column, and a footer that says camagru. Logged out, the navigation is Gallery, Sign up, Log in. Logged in, it is Gallery, Editor, Profile, and a Log out button.

## Sign up `/signup`

Logged out. The header does not say "logged out", and Sign up is left out of the navigation on its own page. The page shows a title, one sentence, then username, email, password, and Sign up, centered. Success redirects, so a refresh does not send the form again, and tells the person to check their mail. A password error lists only the rules that failed, and any error keeps the typed username and email. This page never creates a session.

## Log in `/login`

A title, one sentence, username, password, Log in, and a link to reset; Log in is left out of the navigation here. Success lands on the gallery with the username in the header. An unknown username, a wrong password, and an unconfirmed account each get their own message, and the header stays empty.

## Reset request `/reset`

A title and one sentence saying the new password is chosen on the mailed link, not here, then Email and Send link and nothing else. Success says a link is on its way if the account exists, whether or not it does. This page has no password field.

## Choose a password `/reset/<token>`

Reached only from the mail. A title, one sentence saying the link works once, the new password field, and Set password, with no email field. Success goes to log in. A weak password keeps the person on this page and the link keeps working. An unknown or used link says it is not valid and changes no password.

## Profile `/profile`

Logged in. A title, then the sentence "Change your username, email, password, or comment mail. Leave the password blank to keep the current one." The fields show the current username and email, a checkbox turns comment mail on or off, and Save applies them. The password field starts empty. An error stays on the page and keeps the session. Logged out, the page says to log in.

## Editor `/editor`

Logged in, inside the same shell as the other pages. The workspace has a stage and the sticker list, with the member's thumbnails beside it. Logged out, the editor redirects to log in.

| Control | State |
| --- | --- |
| Stage | Shows a sentence until the camera is allowed, a PNG is uploaded, or the sample photo is used. A still replaces the live camera. |
| Camera | Starts on every editor load and runs only while the stage is live. A capture, an upload, or the sample stops it, so the browser camera indicator goes off. Retake, or the page load after Save, starts it again. |
| Capture | Inactive until the camera is live and a sticker is ticked (printed page 8). After a capture it reads Retake. |
| Save | Inactive until a base image is loaded: a capture, an upload, or the sample. Zero, one, or both stickers are allowed, and the server still refuses a post with no base image. |
| After Save or Delete | Save redirects to `/editor` with a notice. Delete in the browser removes that thumbnail and stays on this document. A refresh does not post again. The saved file is the server composite. |
| Your pictures | Newest first. On a wide screen they form a column beside the workspace that ends level with it and scrolls on its own; on a narrow screen they sit two per row under the workspace. A thumbnail links to the full picture. |
| Sticker preview on the live camera | The selected frames draw on the live camera before save. Save GIF is in the bonus section. |

## Gallery `/`

Public, logged in or not. A title, then "Newest first. Five pictures on a page." Each card shows the picture, who made it, a like count, and the comments, and the page has Previous and Next links when those pages exist. Logged out, a line says to log in to like and comment, and those controls are absent; logged in, Like and the comment field are on the card. A comment emails the author when their preference is on, and the page says the mail was not sent when SMTP fails. An empty gallery says "No pictures yet."

## Bonus

The editor draws the selected frames on the live camera before save. Save GIF builds one animation from three snaps of that live camera, 1s apart, and only while a sticker is ticked. A sample or an upload cannot save a GIF. The stored still is the server composite either way. Like and comment update the gallery card in place, and a first comment removes "No comments yet."; Delete removes the editor thumbnail in place. Scrolling to the bottom of the gallery loads the next five pictures, and after the last page the control reads "No more pictures" and has no address. Each card has Share on X and Share on Facebook links that open a new window, and the page loads no third-party script.
