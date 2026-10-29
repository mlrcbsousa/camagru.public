# 01 Editor

Walkthrough for the editor, where a member captures or uploads a photo, adds stickers, and saves the server-side composite. The accounts clicks are in [accounts.md](accounts.md#9-steps), the screen contract is [DESIGN.md](DESIGN.md), and the Pillow decision is [adr/images/0001](adr/images/0001-pillow-for-compositing.md).

A printed page is the footer number in the subject.

## 1. Requirements

| Requirement | Subject | Acceptance |
| --- | --- | --- |
| Pillow blends the PNG. PHP GD is the equivalent. No other new library. | Printed page 5 | The image builds. |
| Webcam preview, a list of superposable images, capture, thumbnails of earlier pictures, upload, and a server-side PNG. | Printed page 8, V.4 | The editor page. |
| Capture stays inactive until a sticker is selected. | Printed page 8 | Section 3 |
| A save needs a base image. Zero, one, or several stickers all save. | Printed page 8 does not forbid a zero-sticker upload. | AC-8, AC-9, AC-10 |
| Logged-out `/editor` redirects to login. A member deletes only their own picture. | Printed page 8 | AC-7, AC-11 |
| Header, main, and footer. Usable at phone width. No console or server log except `getUserMedia` on plain HTTP. | Printed page 5 | AC-17 |

## 2. Stickers

The subject calls them superposable images and asks for a selectable list of images with an alpha channel (printed pages 4 and 8), and this app calls them stickers. The subject names no count or picture, so two are enough for "a list".

The stickers are PNG files in the repo, [public/frames/a.png](../public/frames/a.png) and [public/frames/b.png](../public/frames/b.png). The browser shows them as checkboxes and posts only their names. The server reads those files, blends them onto the base with Pillow in [app/compose.py](../app/compose.py), and stores the result as PNG bytes in the `pictures` table, so no picture is written to disk. `/pictures/<id>` serves those bytes.

## 3. Capture and a zero-sticker save

Printed page 8 says the button that takes the picture stays inactive until a superposable image is selected. Separately, a save needs a loaded base, from the webcam or an upload, and an upload with no sticker, one, or several must all work.

The two rules are about different controls: the subject's line is the webcam Capture button, and the zero-sticker rule is the upload. Read that way they do not conflict, so the editor follows both. Capture needs a ticked sticker, while an upload or the sample photo saves with none. Capture with no sticker ticked stays inactive, which is printed page 8, and step 4 shows the zero-sticker case.

## 4. Refresh

Save answers with a redirect to `/editor`, so a refresh reloads that address instead of posting the picture again. Delete runs in place from the page script, and without the script it redirects the same way. The redirect also protects against a replayed delete: SQLite may reuse the highest id after a delete, so a second post could hit the next picture with that id. Even then it could only remove a picture the same member owns, because the delete checks the owner.

## 5. Steps

Leave the browser console and `make logs` open, and open the site as <http://localhost:8080>. A `getUserMedia` line on plain HTTP is the only one that passes.

`cd e2e && npm run walkthrough` runs these steps with Playwright, in this order, and fails on any console line. Its test names carry the step numbers below, so run it before the manual pass.

1. While logged out, open `/editor`. Pass: the address becomes `/login`.
2. Log in and open Editor. Pass: header, main, and footer are present, and the username sits next to Log out. The stage shows the camera after it is allowed, Save and Capture are inactive, and Your pictures says there are none. No console line other than the camera warning, and `make logs` shows no request line.
3. With the camera live, look at Capture with no sticker ticked, then tick Border. Pass: Capture is inactive, then active. Click it. Pass: the stage freezes, the button reads Retake, Save turns on, and the camera indicator on the tab goes off.
4. Click Use sample photo with no sticker ticked. Pass: the camera indicator goes off. Save. Pass: the address is `/editor?notice=picture`, the page says Picture saved, and Your pictures shows one thumbnail. The camera comes back on, because the saved page loads fresh and every editor load starts the webcam preview, the main section on printed page 8.
5. Refresh the page. Pass: still one thumbnail. Open `/editor` fresh. Pass: Save is inactive until a photo is loaded again.
6. Use the sample photo, tick only Border, and Save. Pass: a second thumbnail with the border. Click it. Pass: the browser opens the stored PNG at `/pictures/<id>`, and the border is part of the image. Use the browser Back button to return. The live camera does not show the sticker before Save in the mandatory part; that is the bonus preview.
7. Use the sample photo, tick Border and Star sticker, and Save. Pass: a third thumbnail with both. On a wide window, Your pictures ends level with the bottom of the workspace and scrolls on its own.
8. Upload a PNG with no sticker and Save. Pass: a new thumbnail. Then repeat with camera access blocked from the address bar. Pass: the stage keeps the empty sentence, Capture stays inactive, and an upload or the sample still saves.
9. Create a text file named `fake.png`, for example `echo hello > fake.png`. Upload it and Save. Pass: the page says the file is not an image, and the thumbnail count does not change. A real non-PNG file is hidden by the picker.
10. Delete the newest thumbnail. Pass: that picture is gone, the others stay, and the address stays on `/editor`. Refresh. Pass: nothing else is deleted.
11. This one goes past the required checks. Log out, sign up a second user, confirm, and log in. Open Editor. Pass: the first user's thumbnails are absent, so there is no Delete for them.
12. Narrow the window to about 360px. Pass: the username has space on both sides, the stage, stickers, buttons, and thumbnails do not touch or overlap, and thumbnails sit two per row.
