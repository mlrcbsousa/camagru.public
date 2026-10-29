const { expect, test } = require('./fixtures/test');

const pages = ['/', '/login', '/editor'];

for (const path of pages) {
  test('layout at 360px on ' + path, async ({ shell }) => {
    await shell.open(path);
    await shell.expectRegions();
  });
}

test('a script comment is text', async ({ gallery, accounts, editor, request }) => {
  await accounts.openSignup();
  await accounts.signup('xss', 'xss@example.com', 'Password1');
  await accounts.openLinkFromMail(request, 'xss@example.com', '/confirm/');
  await accounts.login('xss', 'Password1');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  await gallery.open();
  await gallery.comment('<script>window.__xss = 1</script>');
  await expect(gallery.comments.filter({ hasText: 'script' }).first()).toBeVisible();
  expect(await gallery.page.evaluate(() => window.__xss)).toBeUndefined();
});

test('a quote in login is stored as data', async ({ accounts }) => {
  await accounts.openLogin();
  await accounts.login("bob'", 'Password1');
  await accounts.expectLoggedOut();
});

test('the server log stays empty', async ({ shell }) => {
  await shell.open('/');
  await shell.expectLogEmpty();
});
