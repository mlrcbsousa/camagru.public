# 18 Gallery page

`gallery_page` in [app/pages.py](../../app/pages.py) turns the rows into HTML. It neither queries nor decides the page number; the handler that does is [17-gallery-routes.md](17-gallery-routes.md). The photo box, the like row, and the fixed-height comment list are styled in [21-gallery-css.md](21-gallery-css.md).

## One card

A logged-in member viewing page 2, picture 9 by ada, one like, and one comment from bob whose text is `hello`:

```html
<article data-testid="gallery-item" class="card">
  <div class="card-photo"><img alt="" src="/pictures/9"></div>
  <div class="card-body">
    <div class="card-head">
      <p class="byline">by ada</p>
      <div class="like-row">
        <form class="like-form" method="post" action="/pictures/9/like">
          <input type="hidden" name="csrf" value="...">
          <input type="hidden" name="page" value="2">
          <button data-testid="gallery-like" class="secondary" type="submit">Like</button>
        </form>
        <span class="like-total"><span data-testid="gallery-like-count">1</span> like</span>
      </div>
    </div>
    <ul class="comments">
      <li data-testid="gallery-comment"><b>bob</b>: hello</li>
    </ul>
    <form class="comment-form" method="post" action="/pictures/9/comment">
      <input type="hidden" name="csrf" value="...">
      <input type="hidden" name="page" value="2">
      <input data-testid="gallery-comment-body" name="body" placeholder="Add a comment">
      <button data-testid="gallery-comment-submit" type="submit">Comment</button>
    </form>
    <p class="share">
      <a data-testid="share-x" target="_blank" rel="noopener noreferrer" href="https://x.com/intent/tweet?url=http://localhost:8080/pictures/9">Share on X</a>
      <a data-testid="share-facebook" target="_blank" rel="noopener noreferrer" href="https://www.facebook.com/sharer/sharer.php?u=http://localhost:8080/pictures/9">Share on Facebook</a>
    </p>
  </div>
</article>
```

The hidden `page` is the number this view was given, so a like or a comment on page 2 posts `page=2`, which is what the redirect in [17-gallery-routes.md](17-gallery-routes.md#the-address-the-redirect-uses) reads. The share links are walked in [25-share.md](25-share.md).

A count of `1` uses the word `like`; any other count, including `0`, uses `likes`.

`escape` runs on the username and the comment text, so a body of `<script>` is stored as text and drawn as text. It is the same `html.escape` as the account pages ([07-pages.md](07-pages.md)). The bold tag comes from the template and the username is only the text inside it, so a name cannot close the tag.

An empty comment list is a single `<li class="no-comments">No comments yet.</li>`, not a `gallery-comment` row.

## Logged out

When `user` is `None`, both forms are skipped but the count stays, and above the cards the page adds `Log in` to like and comment. Printed page 7 allows those actions only for a connected user; this function hides the controls, and the route still refuses a forged post.

The CSRF value is `user["csrf"]` when someone is logged in, so the logged-out HTML carries no token at all.

## The pager

```python
if int(page_number) > 1:
    previous = int(page_number) - 1
    href = "/" if previous == 1 else f"/?page={previous}"
    links.append(f'<a data-testid="gallery-previous" href="{href}">Previous</a>')

if has_next:
    links.append(f'<a data-testid="gallery-next" href="/?page={int(page_number) + 1}">Next</a>')
```

Page 2 links Previous to `/` and page 3 links it to `/?page=2`. Next is `/?page=` plus one, drawn only when the handler set `has_next`. The handler redirects a number past the last page before this function runs, so Previous never appears on an empty page 23.

The empty gallery, no rows on page 1, is the sentence `No pictures yet.`, and the pager is omitted because `links` is empty.

A notice such as `the mail was not sent` is an escaped paragraph above the cards; [17-gallery-routes.md](17-gallery-routes.md#opening-the-gallery) is where the code `nomail` becomes that sentence.

`render` fills the shell with this main, the username and logout form when someone is logged in, and the path `/`, so the header marks Gallery. When `fragment` is true the function skips the heading and the shell and returns only the cards and the pager, which is what infinite scroll appends ([24-reply.md](24-reply.md#the-next-page)).
