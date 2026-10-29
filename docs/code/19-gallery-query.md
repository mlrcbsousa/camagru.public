# 19 Gallery query

The gallery reads and writes in [app/store.py](../../app/store.py): `gallery_rows`, `picture_count`, `picture_author`, `like_once`, `add_comment`, and `comments_for`. The route that calls them is [17-gallery-routes.md](17-gallery-routes.md), and the HTML is [18-gallery-page.md](18-gallery-page.md).

Every value in these statements goes in through a `?` placeholder, so not even the page number is pasted into the SQL text.

## `many` and `one`

```python
def many(cursor: sqlite3.Cursor) -> list[sqlite3.Row]:
    raw = cast(list[object], cursor.fetchall())  # pyright: ignore[reportAny]
    rows: list[sqlite3.Row] = []

    for item in raw:
        if not isinstance(item, sqlite3.Row):
            raise TypeError("row")

        rows.append(item)

    return rows
```

`many` and `one` live in [app/boundary.py](../../app/boundary.py). `fetchall` returns every row the statement produced, and the sqlite3 stubs type that list as `Any`. `Any` is allowed only in this boundary module, and only if the next line narrows it: the `cast` makes the list `list[object]`, the `pyright: ignore` comment marks the one read of `Any`, and the loop does the narrowing, since each item must be a `sqlite3.Row`, so the return type is `list[sqlite3.Row]` and `gallery_rows` and `comments_for` work with rows, not `Any`. `one` is the same check for `fetchone`, returning `None` when the statement matched nothing, which is why `picture_count` and `picture_author`, each one row or none, use it.

Nothing inside `many` catches the `TypeError`. A real sqlite3 cursor yields rows, so the check passes, but if an item were not a row, the raise would leave `many`, then `gallery_rows`, then `handle`. `application` has `except Exception`, which catches a `TypeError`, and answers `500` with the body `something went wrong` without printing anything; `CAMAGRU_DEBUG` adds the exception type to that sentence. The point of the check is the type that comes back out: a bad value stops here instead of being used later as a row.

## The page of pictures

```python
def gallery_rows(conn: sqlite3.Connection, page_number: int, size: int) -> list[GalleryRow]:
    offset = (int(page_number) - 1) * int(size)
    rows = many(
        conn.execute(
            """
            select pictures.id, pictures.user_id, pictures.created_at,
                   users.username, users.email, users.mail_ok,
                   (select count(*) from likes where likes.picture_id = pictures.id) as likes
            from pictures
            join users on users.id = pictures.user_id
            order by pictures.created_at desc, pictures.id desc
            limit ? offset ?
            """,
            (int(size), offset),
        )
    )

    return [gallery_row(row) for row in rows]
```

Take six pictures inserted with times `10, 10, 9, 8, 7, 6`, so their ids are 1 through 6. `gallery_rows(conn, 1, 5)` returns ids `2, 1, 3, 4, 5`: the two rows at time 10 are ordered by id descending, so 2 comes before 1, and the older times follow. `gallery_rows(conn, 2, 5)` returns id `6`. Printed page 7 asks for creation-date order; the id is only the tie break, not a second sort the subject names.

`limit 5 offset 0` is page 1 and `limit 5 offset 5` is page 2. `gallery_rows(conn, 3, 5)` with one picture uses offset 10 and returns `[]`, but the route never renders that empty page because it redirects first.

The like count is a subquery on each selected picture, not a second round trip. The comments are the extra query, one `comments_for` per row, which [17-gallery-routes.md](17-gallery-routes.md#opening-the-gallery) already counts.

`users.email` and `users.mail_ok` are on the row, but the card does not print them.

```python
def picture_author(conn: sqlite3.Connection, picture_id: int) -> PictureAuthor | None:
    row = one(
        conn.execute(
            """
            select pictures.id, users.username, users.email, users.mail_ok
            from pictures
            join users on users.id = pictures.user_id
            where pictures.id = ?
            """,
            (picture_id,),
        )
    )

    if row is None:
        return None

    return author_from_row(row)
```

`picture_author(conn, 9)` returns ada's username, email, and `mail_ok` for the letter. A missing id returns `None`, and the route then stores no comment and no like.

`picture_count` runs `select count(*) as n from pictures` and only returns the number; it is the route that turns six pictures into a last page of 2.

## One like

```python
def like_once(conn: sqlite3.Connection, user_id: int, picture_id: int) -> None:
    conn.execute(
        "insert or ignore into likes (user_id, picture_id) values (?, ?)",
        (user_id, picture_id),
    )
    conn.commit()
```

The `likes` table has `unique (user_id, picture_id)`. `like_once(conn, 4, 9)` inserts that pair, and a second call hits the unique constraint, where `or ignore` tells SQLite to keep the old row and not raise ([ON CONFLICT](https://www.sqlite.org/lang_conflict.html)). The count stays 1. A different member is a different pair, so their like is a second row.

## Comments

```python
def add_comment(conn: sqlite3.Connection, picture_id: int, user_id: int, body: str) -> None:
    conn.execute(
        "insert into comments (picture_id, user_id, body) values (?, ?, ?)",
        (picture_id, user_id, body),
    )
    conn.commit()
```

```python
def comments_for(conn: sqlite3.Connection, picture_id: int) -> list[Comment]:
    rows = many(
        conn.execute(
            """
            select comments.body, users.username
            from comments
            join users on users.id = comments.user_id
            where comments.picture_id = ?
            order by comments.id
            """,
            (picture_id,),
        )
    )

    return [comment_from_row(row) for row in rows]
```

Picture 9 gets `hello` from bob, then `again` from ada, and `comments_for(conn, 9)` returns bob's line first, then ada's, because `order by comments.id` is insertion order. The subject does not say how to order the lines under one picture.

The body is stored exactly as posted. This function does not escape it; the page does, when drawing.
