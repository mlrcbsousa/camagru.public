# 23 Preview

This walks through the bonus code in [public/editor.html](../../public/editor.html). Capture, the sample, and the upload are in [13-editor-page.md](13-editor-page.md), the server blend of one still is in [12-compose.md](12-compose.md), and the stored GIF is in [24-reply.md](24-reply.md).

## The sticker on the camera

```javascript
function markFrames() {
  var boxes = document.getElementsByName("frames");
  var count = 0;
  var index = 0;

  for (; index < boxes.length; index += 1) {
    byId("overlay-" + boxes[index].value).hidden = !boxes[index].checked;

    if (boxes[index].checked) {
      count += 1;
    }
  }

  byId("preview").setAttribute("data-frame", String(count));
}
```

Border is the `frames` checkbox with value `a`: ticking it shows `#overlay-a`, and unticking it sets `hidden` again. The camera video itself never changes, because the sticker is a second image laid over it rather than something drawn into the video.

`data-frame` is the number of ticked boxes, written onto `#preview`. No CSS reads it and the visitor never sees it; it is there for the browser test, which reads it to check that one sticker is selected. What the visitor sees is the overlay image.

The stage is `position: relative`, and the video, `#preview`, and both overlays are `position: absolute` with the same `top`, `left`, `width`, and `height`, so they share one box. Elements without a `z-index` paint in file order with the later one on top, and `.overlay` sets `z-index: 1` while the video and the preview do not, so both stickers paint above the camera and above the still. Between the two stickers the tie goes to file order again: `#overlay-b` comes after `#overlay-a`, so the star covers the border when both are ticked. `object-fit: fill` stretches each sticker to the stage. This stack is only the preview; the saved file is built by the server.

## When Save GIF is on

```javascript
  capture.disabled = still ? false : !(stream && hasSticker());
  byId("save").disabled = !hasBase();
  byId("gif-save").disabled = !(!still && stream && hasSticker());
```

Save turns on once a base is loaded, whether a snap, an upload, or the sample. Save GIF turns on only when the camera is live and a sticker is ticked. A sample, an upload, or a captured still leaves it off. A still cannot move between the one-second snaps, so it is not a GIF.

## Three snaps

```javascript
function snapSource() {
  if (stream && !byId("camera").hidden) {
    return byId("camera");
  }

  if (!byId("preview").hidden) {
    return byId("preview");
  }

  return null;
}
```

`saveGif` copies the live camera only. A hidden camera, a missing stream, or no sticker sets the stage line to `Open the camera and tick a sticker before saving a GIF.` and returns. The server also refuses `gif=1` when `use_sample` is `1` or `upload_b64` is set, and redirects to `/editor?error=gifcamera`.

```javascript
function saveGif() {
  var camera = byId("camera");
  var taken = 0;

  if (camera.hidden || !stream || !hasSticker()) {
    byId("stage-empty").textContent = "Open the camera and tick a sticker before saving a GIF.";
    return;
  }

  byId("gif-save").disabled = true;
  byId("gif-save").textContent = "Snapping...";

  function next() {
    byId("snap" + taken).value = snapOnce(camera);
    taken += 1;

    if (taken < 3) {
      setTimeout(next, 1000);
      return;
    }

    byId("gif").value = "1";
    byId("editor-form").submit();
  }

  next();
}
```

`snapOnce` calls `pngDataUrl`, the same helper Capture uses for one still. `next` stores the base64 in `snap0`, then `snap1`, then `snap2`. `setTimeout(next, 1000)` waits one second between copies. The source is the camera, so the person can move between snaps.

After the third copy `gif` becomes `1` and the form posts as a normal submit, not through the AJAX script. The server answers with a redirect to `/editor?notice=gif`, so a refresh loads that address again and does not post the snaps a second time. That page shows the usual `editor-notice` line, `GIF saved.`, and the new picture in the thumbnails.
