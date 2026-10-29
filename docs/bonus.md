# 01 Bonus

Walkthrough for the bonus features: in-place updates, the live sticker preview, infinite pagination, share links, and the GIF. The mandatory features are in their own files, and the screen contract is [DESIGN.md](DESIGN.md).

A printed page is the footer number in the subject. Printed page 10 says these are scored only when the mandatory part is perfect.

## Requirements

| Requirement | Subject | Acceptance |
| --- | --- | --- |
| Like, comment, and delete update the current page. The browser does not load a new document. | Printed page 10, AJAX | AC-21 |
| The selected sticker is visible on the webcam preview before save. The stored file is still the server PNG. | Printed page 10, live preview | AC-22 |
| Reaching the bottom appends the next five. The Next link does the same, skipping any picture already shown. Nothing loads after the last. | Printed page 10, infinite pagination | AC-23 |
| Each picture has one X link and one Facebook link. Each address contains the picture URL. The page loads no script from those sites. | Printed page 10, social share | AC-24 |
| Three snaps save one GIF. | Printed page 10 | AC-25 |

## Steps

Leave the browser console and `make logs` open, and open the site as <http://localhost:8080>. `cd e2e && npm run walkthrough` runs these after the mandatory steps, and its test names carry the numbers below.

1. Log in, save one picture, and open the gallery. Like it, then comment. Pass: the address stays `/`, the count and the comment change without a new document, and the line "No comments yet." is gone.
2. Open the editor and delete that picture. Pass: the thumbnail disappears and the address stays `/editor`.
3. Tick Border while the camera is live. Pass: the border image is visible on the stage before Save.
4. Save six pictures, open the gallery, and scroll to the bottom. Pass: the sixth picture is appended, and the control reads "No more pictures" with no address. Click it. Pass: it does not add a seventh copy, and the page stays on `/`.
5. On a picture, read the X link and the Facebook link. Pass: each address contains `/pictures/` and that picture's id, each opens a new window, and the page source has no script from x.com or facebook.com.
6. Open the editor. Pass: Save GIF is off. Load the sample photo. Pass: Save GIF stays off. Open the editor again, wait for the camera, and tick Border. Pass: Save GIF turns on. Click it. Pass: the address is `/editor?notice=gif` and the page says GIF saved. Refresh. Pass: no resubmit prompt, and the notice is still there. The snaps are 1s apart. A sample or an upload cannot save a GIF.
