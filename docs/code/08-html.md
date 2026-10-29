# 08 html

The files in [public/](../../public/). `pages.py` fills their markers and wraps every page in `shell.html`. The tags are indented only so a person can see which element sits inside which; whitespace between tags is not a parsing rule, so the browser does not care.

## Shell

```html
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>camagru</title>
  <link rel="stylesheet" href="/app.css">
</head>
<body>
  <header data-testid="shell-header">
    <nav>{{nav}}</nav>
    <p data-testid="session-status" title="{{session}}">{{session}}</p>
    {{logout}}
  </header>
  <main data-testid="shell-main">
    {{main}}
  </main>
  <footer data-testid="shell-footer">camagru</footer>
  <p data-testid="server-log"></p>
```

`viewport` makes the phone's width the layout width. Without it, a phone pretends to be a wide desktop and shrinks the page, so the layout never reaches its narrow phone form.

`{{nav}}`, `{{logout}}`, and `{{main}}` are HTML built in `pages.py`, and `{{session}}` is the escaped username. `title="{{session}}"` shows the full name on hover when the header cuts it with an ellipsis. `data-testid` exists for the end-to-end tests and is invisible to a visitor.

The empty `<p data-testid="server-log">` lets a test check that the page did not print a server error into the document. CSS hides it while it is empty.

## Sign up

```html
<div class="account">
  <h1>Sign up</h1>
  <p class="lead">A username, an email, and a password with a letter and a digit. The confirmation link arrives by email.</p>
  <form method="post" action="/signup" autocomplete="off">
    <label>Username <input data-testid="signup-username" name="username" value="{{username}}" autocomplete="username"></label>
    <label>Email <input data-testid="signup-email" name="email" value="{{email}}" autocomplete="email"></label>
    <label>Password <input data-testid="signup-password" name="password" type="password" autocomplete="new-password"></label>
    <button data-testid="signup-submit" type="submit">Sign up</button>
  </form>
  {{message}}
</div>
```

`class="account"` is what centers this form; the gallery has no such wrapper, so it stays wide. `autocomplete` tells the browser what each field is, and `new-password` asks it not to fill a saved password into a signup.

`{{message}}` sits outside the form. It is called message rather than error because the same hole holds either the red failure or the blue line: "Check your mail" on signup, "Profile saved." on profile. Login keeps the two apart, with `{{notice}}` for the blue line above the form and `{{message}}` for the red one below it.

Login is otherwise the same shape, with `autocomplete="current-password"` and a link to `/reset`.

## Reset

`reset-request.html` posts only the email; there is no password field. Its button is `<button name="action" value="request">`, so the body contains `action=request`.

`reset-choose.html` posts the new password, and its button's value is `choose`. `{{token}}` becomes a hidden input carrying the token, and `{{action}}` fills the form action with the token URL. Both reset pages fill `{{action}}`; on the request page it is `/reset`.

## Profile

```html
    <input type="hidden" name="csrf" value="{{csrf}}">
    <label>Password <input data-testid="profile-password" name="password" type="password" autocomplete="new-password"></label>
```

The CSRF field proves the post came from this form and not from another site. The password box starts empty, and leaving it empty keeps the current hash. `{{message}}` under the form holds either the red block or the blue "Profile saved." line.
