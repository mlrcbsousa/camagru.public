const { expect, test } = require('./fixtures/test');

async function member(accounts, request, name, email) {
  await accounts.openSignup();
  await accounts.signup(name, email, 'Password1');
  await accounts.openLinkFromMail(request, email, '/confirm/');
  await accounts.openLogin();
  await accounts.login(name, 'Password1');
}

async function savePictures(editor, count) {
  let index = 0;

  while (index < count) {
    await editor.open();
    await editor.loadBase();
    await editor.saveCurrent();
    index += 1;
  }
}

test('six pictures show five then the older one', async ({ gallery, accounts, editor, request }) => {
  await request.post('/e2e/reset');
  await member(accounts, request, 'author', 'author@example.com');
  await savePictures(editor, 6);
  await accounts.logoutFromHere();
  await gallery.open();
  await gallery.expectPageCount(5);
  await gallery.openNext();
  await gallery.expectPageCount(1);
});

test('a page past the end lands on the last page', async ({ page, gallery, accounts, editor, request }) => {
  await request.post('/e2e/reset');
  await member(accounts, request, 'pager', 'pager@example.com');
  await savePictures(editor, 6);
  await page.goto('/?page=23');
  await expect(page).toHaveURL(/page=2$/);
  await gallery.expectPageCount(1);
  await expect(page.locator('[data-testid="gallery-previous"]')).toBeVisible();
});

test('a visitor is not offered like or comment', async ({ gallery }) => {
  await gallery.open();
  await expect(gallery.like).toHaveCount(0);
  await expect(gallery.commentBody).toHaveCount(0);
  await expect(gallery.page.locator('main').getByRole('link', { name: 'Log in' })).toBeVisible();
});

test('a second like does not add another', async ({ gallery, accounts, request }) => {
  await member(accounts, request, 'fan', 'fan@example.com');
  await gallery.open();
  await gallery.likeFirst();
  await gallery.likeFirst();
  await gallery.expectLikeCount(1);
});

test('a comment mails the author when the preference is on', async ({ gallery, accounts, editor, request }) => {
  await request.post('/e2e/reset');
  await member(accounts, request, 'author', 'author@example.com');
  await savePictures(editor, 1);
  await accounts.logoutFromHere();
  await member(accounts, request, 'fan', 'fan@example.com');
  await request.post('http://127.0.0.1:8026/api/v1/clear');
  await gallery.open();
  await gallery.comment('nice');
  await gallery.expectCommentText('nice');
  await accounts.expectOneMail(request, 'author@example.com', '/pictures/');
});

test('smtp down keeps the comment and prints nothing', async ({ gallery, accounts, request }) => {
  await accounts.openLogin();
  await accounts.login('fan', 'Password1');
  await request.post('http://127.0.0.1:8026/api/v1/refuse');
  await gallery.open();
  await gallery.comment('still here');
  await gallery.expectCommentText('still here');
  await gallery.expectMailFailed();
});

test('preference off stores the comment and sends no mail', async ({ gallery, accounts, request }) => {
  await accounts.openLogin();
  await accounts.login('author', 'Password1');
  await gallery.turnMailOff();
  await request.post('http://127.0.0.1:8026/api/v1/clear');
  await gallery.open();
  await gallery.comment('quiet');
  await gallery.expectCommentText('quiet');
  await gallery.expectNoMailSent();
});
