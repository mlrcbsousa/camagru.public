# 22 AJAX

This walks through the script at the bottom of [public/shell.html](../../public/shell.html); the header, main, and footer around it are in [08-html.md](08-html.md) and the card markup is in [18-gallery-page.md](18-gallery-page.md). Like, comment, and delete post to the same addresses as without the script, and the script only stops the browser from leaving the page.

AJAX stands for Asynchronous JavaScript and XML ([AJAX](https://developer.mozilla.org/en-US/docs/Glossary/AJAX)). Here it means the page updates itself from the reply instead of loading a new document. The reply is JSON, not XML; the name is just the old one for this kind of request.

## Which forms

```javascript
function ajaxAction(action) {
  return action.indexOf("/like") !== -1 || action.indexOf("/comment") !== -1 || action.indexOf("/delete") !== -1;
}
```

`/pictures/9/like` matches and `/signup` does not. `bindAjax` runs on load, and again after a later page of cards is added, and sets `onsubmit` only on forms posting to those three actions.

## The post

```javascript
function encodeForm(form) {
  var parts = [];
  var index = 0;

  for (; index < form.elements.length; index += 1) {
    var field = form.elements[index];

    if (!field.name) {
      continue;
    }

    if ((field.type === "checkbox" || field.type === "radio") && !field.checked) {
      continue;
    }

    parts.push(encodeURIComponent(field.name) + "=" + encodeURIComponent(field.value));
  }

  return parts.join("&");
}
```

A normal form post includes a checkbox only when it is ticked, and `field.checked` is that test. A ticked box sends its `value` (Border sends `frames=a`, the star sends `frames=b`, both send both fields), while an unticked box sends nothing at all, not `0`, `false`, or `""`. A hidden `csrf` or `page` field has a name and is not a checkbox, so it is always sent. Like, comment, and delete have no checkbox, but the check lives in the shared encoder so that an unticked box can never be posted as if it were on.

```javascript
function ajaxSubmit(event) {
  event.preventDefault();
  var form = event.target;
  var action = form.getAttribute("action");
  var xhr = new XMLHttpRequest();

  xhr.open("POST", action);
  xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
  xhr.onload = function () {
    applyAjaxResult(form, action, JSON.parse(xhr.responseText));
  };
  xhr.send(encodeForm(form) + "&xhr=1");
}
```

`preventDefault` cancels the normal submit, so the address does not change. `XMLHttpRequest` is the built-in that sends the request and hands the reply to this script. Firefox 41 and Chrome 46 both have `fetch` too, so that is not why it was passed over: `XMLHttpRequest` puts the reply string on `xhr.responseText` inside `onload` in one step, while `fetch` returns a promise and reading the body is a second step. Either gives the same result, and this file uses `XMLHttpRequest`.

`xhr.responseText` is the reply as one string. `JSON.parse` reads JSON syntax only (braces, quotes, commas, numbers) and builds a JavaScript object, a bag of named values rather than a page or HTML. A comment body containing the characters `<script>` stays a plain string inside that object, because the parse neither looks for tags nor runs anything.

For example, a like on picture 9 posts `csrf`, `page`, and `xhr=1` to `/pictures/9/like` and gets back the string `{"likes": 1}`. After `JSON.parse`, `data.likes` is the number `1`, and the address stays `/`.

## Like

```javascript
function applyAjaxResult(form, action, data) {
  var card = closestParent(form, "card");
```

`form` is the submitted form, passed through from `event.target` in `ajaxSubmit`. The function needs no picture id: the form already sits inside one card and its `action` names that picture, so the reply belongs to that card and `applyAjaxResult` changes only that card.

`closestParent` walks up from the form through `parentNode` until it finds the class, `card` for a like or a comment and `thumb` for a delete, so it returns an ancestor, never a child.

```javascript
  if (action.indexOf("/like") !== -1 && card) {
    var total = card.querySelector(".like-total");
    var count = Number(data.likes);

    total.querySelector("[data-testid='gallery-like-count']").textContent = String(count);
    total.lastChild.textContent = count === 1 ? " like" : " likes";
  }
```

The count span on that card becomes `1` and the text node after it becomes a space plus `like`. A second like from the same member still returns `1`, so the card stays at `1 like`.

## Comment

```javascript
  if (action.indexOf("/comment") !== -1 && card && data.ok) {
    item = document.createElement("li");
    item.setAttribute("data-testid", "gallery-comment");
    item.appendChild(document.createTextNode(": " + data.body));
    var name = document.createElement("b");

    name.textContent = data.username;
    item.insertBefore(name, item.firstChild);
    var empty = card.querySelector(".no-comments");

    if (empty) {
      empty.parentNode.removeChild(empty);
    }

    card.querySelector(".comments").appendChild(item);
    form.querySelector("[name='body']").value = "";
    showNotice(data.notice);
  }
```

The comment form sits inside the card, so the new line goes into that card's list, and this path never uses `innerHTML`.

A comment `hello` from `ada` on picture 9 comes back as the string `{"ok": true, "body": "hello", "username": "ada", "notice": ""}`, and `JSON.parse` makes `data.body` the string `hello`. `createTextNode` and `textContent` copy that string into a text node, which holds characters the way a paragraph holds words. The HTML parser is never called, so `<script>alert('THE GAME')</script>` shows up as those letters; it does not become a `<script>` element and the browser does not run it.

The one place this script does parse HTML is the next page of the gallery. That reply is an HTML string the server already built, such as `<article>...</article>`, and `appendNextCards` assigns it to `holder.innerHTML`, which creates element nodes. A comment typed in the box never takes that path, and when a full page is drawn the server escapes every comment first, as [18-gallery-page.md](18-gallery-page.md) shows.

After a stored comment the `No comments yet.` line is removed and the input is cleared. An empty `notice` adds nothing, while `the mail was not sent` is written above the gallery when the reply carries that sentence.

## Delete

```javascript
  if (action.indexOf("/delete") !== -1 && data.ok) {
    item = closestParent(form, "thumb");

    if (item) {
      item.parentNode.removeChild(item);
    }
  }
```

Delete lives on the editor page, which uses the same shell and script. The delete form sits inside its thumbnail, so `closestParent(form, "thumb")` is that figure. A delete posts to `/pictures/9/delete`; a reply of `{"ok": true}` removes the figure while the address stays `/editor`, and `{"ok": false}` leaves it in place.

## The next page

```javascript
function loadNext() {
  var link = document.querySelector("[data-testid='gallery-next']");

  if (!link || link.getAttribute("data-loading") === "1" || link.getAttribute("data-done") === "1") {
    return;
  }

  link.setAttribute("data-loading", "1");
  var xhr = new XMLHttpRequest();

  xhr.open("GET", link.getAttribute("href") + "&fragment=1");
  xhr.onload = function () {
    appendNextCards(xhr.responseText);
    link.removeAttribute("data-loading");
  };
  xhr.send();
}
```

When the Next address is `/?page=2`, the request is `GET /?page=2&fragment=1`. `bindNext` makes a click on Next call this function instead of following the link.

```javascript
function bindScroll() {
  window.onscroll = function () {
    var atBottom = window.innerHeight + window.scrollY >= document.body.scrollHeight - 4;

    if (atBottom) {
      loadNext();
    }
  };
}
```

`scrollHeight` is the full height of the page, `innerHeight` the height of the window, and `scrollY` how far the window has scrolled down. Window height plus scroll reaches the full height once the bottom is on screen, and the `- 4` adds four pixels of slack so the next page loads when the scroll is that close instead of waiting for an exact match.

`data-loading` blocks a second request while the first is still open, and `data-done` blocks any request after the last page.

```javascript
function appendNextCards(html) {
  var holder = document.createElement("div");
  var gallery = document.querySelector(".gallery");
  var link = document.querySelector("[data-testid='gallery-next']");
  var more = null;

  holder.innerHTML = html;

  while (holder.children.length) {
    var node = holder.children[0];

    holder.removeChild(node);

    var image = node.querySelector("img");
    var next = node.getAttribute("data-testid") === "gallery-next" ? node : node.querySelector("[data-testid='gallery-next']");

    if (next && !image) {
      more = next;
    } else if (image && !document.querySelector("img[src='" + image.getAttribute("src") + "']")) {
      gallery.appendChild(node);
    }
  }
```

`html` is the reply string from `xhr.responseText`, and assigning it to `innerHTML` is the step that parses it into element nodes inside `holder`. Because `holder` is not in the page, that line shows nothing by itself. The loop then takes each element off `holder`, starting with `holder.children[0]`, and decides whether it joins the gallery.

The `img[src=...]` test skips a card whose picture is already on the page. A card with a new `src` is added, and `bindAjax` runs afterwards so its Like and Comment use this script. When the fragment has no Next link, the control loses its address and its text becomes `No more pictures`, so a later click returns at the `data-done` check.
