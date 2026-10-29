const { expect, test } = require('./fixtures/test');

test('signup stores an account and one confirmation mail', async ({ accounts, request }) => {
  await accounts.openSignup();
  await accounts.signup('ada', 'ada@example.com', 'Password1');
  await accounts.expectLoggedOut();
  await accounts.expectOneMail(request, 'ada@example.com', '/confirm/');
});

test('weak passwords and a duplicate username are refused', async ({ accounts }) => {
  await accounts.openSignup();
  await accounts.signup('ada', 'ada@example.com', 'password');
  await accounts.expectSignupRefused();
  await accounts.expectOnlyRule('one digit');
  await accounts.signup('ada', 'other@example.com', 'Password1');
  await accounts.expectSignupRefused();
  await accounts.signup('ada2', 'ada@example.com', 'Passwordzz');
  await accounts.expectSignupRefused();
  await accounts.expectOnlyRule('one digit');
});

test('login before confirmation sets no session', async ({ accounts }) => {
  await accounts.openLogin();
  await accounts.login('ada', 'Password1');
  await accounts.expectLoggedOut();
  await accounts.expectText('Open the confirmation link');
  await accounts.page.reload();
  await accounts.expectLoggedOut();
  await accounts.expectText('Open the confirmation link');
});

test('a login error sits apart from the form', async ({ accounts }) => {
  await accounts.openLogin();
  await accounts.login('nobody', 'Password1');
  const form = await accounts.page.locator('form[action="/login"]').boundingBox();
  const error = await accounts.page.locator('[data-testid="login-error"]').boundingBox();

  expect((error?.y || 0) - ((form?.y || 0) + (form?.height || 0))).toBeGreaterThanOrEqual(8);
});

test('the editor address while logged out opens login', async ({ accounts }) => {
  await accounts.page.goto('/editor');
  await accounts.page.waitForURL(/\/login/);
  await accounts.expectLoggedOut();
});

test('a quote in the password does not log in', async ({ accounts }) => {
  await accounts.openLogin();
  await accounts.login('ada', "blahblah' OR 1='1");
  await accounts.expectLoggedOut();
});

test('login after confirmation shows the member', async ({ accounts, request }) => {
  await accounts.openLinkFromMail(request, 'ada@example.com', '/confirm/');
  await accounts.expectLoggedOut();
  await accounts.page.reload();
  await accounts.expectLoggedOut();
  await accounts.openLogin();
  await accounts.login('ada', 'Password1');
  await accounts.expectLoggedIn('ada');
});

test('a profile post without the token does not save', async ({ accounts }) => {
  await accounts.openLogin();
  await accounts.login('ada', 'Password1');
  await accounts.openProfile();
  await accounts.page.evaluate(() => {
    var form = document.querySelector('form[action="/profile"]');
    var csrf = form.querySelector('input[name="csrf"]');

    csrf.value = 'nope';
    form.submit();
  });
  await accounts.expectText('the form was refused');
  await accounts.expectLoggedIn('ada');
});

test('a logout post without the token stays logged in', async ({ accounts }) => {
  await accounts.openLogin();
  await accounts.login('ada', 'Password1');
  await accounts.page.evaluate(() => {
    var form = document.createElement('form');

    form.method = 'post';
    form.action = '/logout';
    document.body.appendChild(form);
    form.submit();
  });
  await accounts.page.waitForLoadState('networkidle');
  await accounts.expectLoggedIn('ada');
});

test('logout on a page clears the session and the editor refuses them', async ({ accounts }) => {
  await accounts.openLogin();
  await accounts.login('ada', 'Password1');
  await accounts.logoutFromHere();
  await accounts.expectLoggedOut();
  await accounts.expectEditorRefused();
});

test('an empty reset does not claim a mail was sent', async ({ accounts }) => {
  await accounts.openReset();
  await accounts.resetRequest.click();
  await accounts.expectText('email is not valid');
  await expect(accounts.page.getByText('on its way')).toHaveCount(0);
});

test('reset mail sets a new password that meets the rule', async ({ accounts, request }) => {
  await accounts.openReset();
  await accounts.requestReset('ada@example.com');
  await accounts.expectOneMail(request, 'ada@example.com', '/reset/');
  await accounts.openLogin();
  await accounts.login('ada', 'Password1');
  await accounts.expectLoggedIn('ada');
  await accounts.logoutFromHere();
  await accounts.openLinkFromMail(request, 'ada@example.com', '/reset/');
  await accounts.chooseNewPassword('Password2');
  await accounts.openLogin();
  await accounts.login('ada', 'Password2');
  await accounts.expectLoggedIn('ada');
});

test('profile edits are the next login', async ({ accounts }) => {
  await accounts.openLogin();
  await accounts.login('ada', 'Password2');
  await accounts.openProfile();
  await accounts.editProfile('ada_new', 'ada2@example.com', 'Password3');
  await accounts.logoutFromHere();
  await accounts.openLogin();
  await accounts.login('ada_new', 'Password3');
  await accounts.expectLoggedIn('ada_new');
});
