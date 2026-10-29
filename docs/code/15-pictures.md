# 15 Pictures

The picture rows in [app/store.py](../../app/store.py). The account rows are walked in [05-store.md](05-store.md), the page that calls these functions is [11-editor-routes.md](11-editor-routes.md), and the editor walkthrough is [editor.md](../editor.md).

```sql
create table if not exists pictures (
    id integer primary key,
    user_id integer not null,
    image_bytes blob not null,
    created_at integer not null
);
```

The image is a blob in the database, not a file on disk. SQLite assigns `id`, and `created_at` is the unix time that `_save_picture` or `_store_gif` passes in, cut to whole seconds by `int(now)`.

The editor lists a member's pictures by `id`, newest first, which works because every save gets a higher id. The gallery is different: printed page 7 asks for creation-date order, and two pictures saved in the same second tie on that date, so the gallery sorts on `created_at` and breaks ties on `id`. That query is [19-gallery-query.md](19-gallery-query.md).

## Save, list, read, delete

`insert_picture(conn, user_id, image_bytes, now)` inserts one row and returns the new id. The values go in through `?` placeholders, so the bytes never become part of the SQL text. The column is named `image_bytes` because it holds either a PNG or a GIF.

`list_pictures(conn, user_id)` returns that member's rows newest first, with `order by id desc`, and the editor shows them in that order. Another member's rows are not in the result, which is why their thumbnails never appear.

`picture_bytes(conn, picture_id)` returns the row, or `None`. `GET /pictures/7` sends `row["image_bytes"]` as `image/gif` when the bytes start with `GIF8` and as `image/png` otherwise; that choice is walked in [24-reply.md](24-reply.md). The `id` is the argument rather than a field of the result, and `user_id` is selected but no caller reads it. Printed page 4 says captured images are public, which is why this GET does not check who is logged in.

`delete_picture(conn, picture_id, user_id)` deletes only when both match:

```python
cursor = conn.execute(
    "delete from pictures where id = ? and user_id = ?",
    (picture_id, user_id),
)
```

It returns true when one row went away. A delete of someone else's id matches nothing, so it returns false and the row stays; the page then redirects to `?error=notyours`, or answers `{"ok": false}` when the page script sent the delete ([24-reply.md](24-reply.md#json-instead-of-a-redirect)).
