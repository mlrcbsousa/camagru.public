const fs = require('fs');
const path = require('path');

const { expect, test } = require('@playwright/test');

const { AccountsPage } = require('./pages/accounts.page');
const { EditorPage } = require('./pages/editor.page');

const SAMPLE = fs.readFileSync(path.join(__dirname, '..', 'public', 'base.png'));

test.describe.configure({ mode: 'serial' });

/** @type {import('@playwright/test').BrowserContext} */
let context;
/** @type {import('@playwright/test').Page} */
let page;
/** @type {AccountsPage} */
let accounts;
/** @type {EditorPage} */
let editor;
/** @type {string[]} */
const consoleLines = [];

test.beforeAll(async ({ browser }) => {
  context = await browser.newContext({
    baseURL: 'http://127.0.0.1:8765',
    permissions: ['camera'],
    viewport: { width: 1024, height: 800 },
  });
  page = await context.newPage();
  page.on('console', (message) => {
    if (message.text().indexOf('getUserMedia') === -1) {
      consoleLines.push(message.type() + ': ' + message.text());
    }
  });
  page.on('pageerror', (error) => consoleLines.push('pageerror: ' + error.message));
  accounts = new AccountsPage(page);
  editor = new EditorPage(page);
});

test.afterAll(async () => {
  await context.close();
});

test.afterEach(() => {
  expect(consoleLines).toEqual([]);
});

test.describe('docs/accounts.md section 9', () => {
  test('4. a lowercase password is refused with its rule', async () => {
    await accounts.openSignup();
    await accounts.signup('evalada', 'evalada@example.com', 'password');
    await accounts.expectText('Invalid password.');
    await accounts.expectOnlyRule('one digit');
    await expect(page.locator('header nav a[href="/signup"]')).toHaveCount(0);
    await accounts.expectLoggedOut();
  });

  test('5. signup sends one confirmation mail and a refresh does not resend', async ({ request }) => {
    await accounts.signup('evalada', 'evalada@example.com', 'Password1');
    await accounts.expectText('Check your mail.');
    await page.reload();
    await accounts.expectOneMail(request, 'evalada@example.com', '/confirm/');
    await accounts.expectLoggedOut();
  });

  test('6. login before the link says to confirm and a refresh does not replay it', async () => {
    await accounts.openLogin();
    await accounts.login('evalada', 'Password1');
    await accounts.expectText('Open the confirmation link');
    await page.reload();
    await accounts.expectLoggedOut();
  });

  test('7. the link confirms without logging in, then login works', async ({ request }) => {
    await accounts.openLinkFromMail(request, 'evalada@example.com', '/confirm/');
    await accounts.expectLoggedOut();
    await accounts.login('evalada', 'Password1');
    await accounts.expectLoggedIn('evalada');
  });

  test('8. after logout the editor sends the visitor to login', async () => {
    await accounts.logoutFromHere();
    await page.goto('/editor');
    await expect(page).toHaveURL(/\/login$/);
  });

  test('9. the reset request page has no password field', async () => {
    await accounts.openReset();
    await expect(page.locator('input[type="password"]')).toHaveCount(0);
  });

  test('10. the mailed link sets a new password and the old one stops working', async ({ request }) => {
    await accounts.requestReset('evalada@example.com');
    await accounts.openLinkFromMail(request, 'evalada@example.com', '/reset/');
    await accounts.chooseNewPassword('Password2');
    await accounts.login('evalada', 'Password2');
    await accounts.expectLoggedIn('evalada');
    await accounts.logoutFromHere();
    await accounts.openLogin();
    await accounts.login('evalada', 'Password1');
    await accounts.expectText('That password does not match.');
  });

  test('11. asking for a reset leaves the current password', async () => {
    await accounts.openReset();
    await accounts.requestReset('evalada@example.com');
    await accounts.openLogin();
    await accounts.login('evalada', 'Password2');
    await accounts.expectLoggedIn('evalada');
  });

  test('12. profile changes are the next login and a blank password keeps it', async () => {
    await accounts.openProfile();
    await accounts.editProfile('evalada2', 'evalada2@example.com', 'Password3');
    await accounts.expectText('Profile saved.');
    await accounts.logoutFromHere();
    await accounts.openLogin();
    await accounts.login('evalada2', 'Password3');
    await accounts.expectLoggedIn('evalada2');
    await accounts.openProfile();
    await accounts.editProfile('evalada2', 'evalada2@example.com', '');
    await accounts.logoutFromHere();
    await accounts.openLogin();
    await accounts.login('evalada2', 'Password3');
    await accounts.expectLoggedIn('evalada2');
  });

  test('14. a quoted password does not log in', async () => {
    await accounts.logoutFromHere();
    await accounts.openLogin();
    await accounts.login('evalada2', "blahblah' OR 1='1");
    await accounts.expectLoggedOut();
    await accounts.expectText('That password does not match.');
  });

  test('15. the account pages fit 360px', async () => {
    await page.setViewportSize({ width: 360, height: 800 });

    for (const address of ['/signup', '/login', '/reset']) {
      await page.goto(address);
      await expect(page.locator('header')).toBeVisible();
      await expect(page.locator('main')).toBeVisible();
      await expect(page.locator('footer')).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    }

    await page.setViewportSize({ width: 1024, height: 800 });
  });
});

test.describe('docs/editor.md section 5', () => {
  test('1. a logged-out editor sends the visitor to login', async () => {
    await page.goto('/editor');
    await expect(page).toHaveURL(/\/login$/);
  });

  test('2. the editor opens with Save and Capture off', async () => {
    await accounts.login('evalada2', 'Password3');
    await editor.open();
    await editor.waitForCamera();
    await expect(editor.save).toBeDisabled();
    await expect(editor.capture).toBeDisabled();
    await expect(page.getByText('No pictures yet.')).toBeVisible();
    await editor.expectSpacedLayout();
  });

  test('3. capture needs a sticker and stops the camera', async () => {
    await editor.selectFrame('a');
    await expect(editor.capture).toBeEnabled();
    await editor.capture.click();
    await expect(editor.capture).toHaveText('Retake');
    await expect(editor.save).toBeEnabled();
    await editor.expectCameraOff();
    await editor.selectFrame('a');
  });

  test('4. the sample photo saves with no sticker and the camera stops until the reload', async () => {
    await editor.loadBase();
    await editor.expectCameraOff();
    await editor.saveCurrent();
    await expect(page).toHaveURL(/\/editor\?notice=picture$/);
    await expect(page.getByText('Picture saved.')).toBeVisible();
    await expect(editor.thumbs).toHaveCount(1);
    await editor.waitForCamera();
  });

  test('5. a refresh does not save again', async () => {
    await page.reload();
    await expect(editor.thumbs).toHaveCount(1);
    await expect(editor.save).toBeDisabled();
  });

  test('6. one sticker saves and the thumbnail opens the stored png', async () => {
    await editor.loadBase();
    await editor.selectFrame('a');
    await editor.saveCurrent();
    await expect(editor.thumbs).toHaveCount(2);
    await editor.thumbs.first().click();
    await expect(page).toHaveURL(/\/pictures\/\d+$/);
    await page.goBack();
  });

  test('7. two stickers save and the pictures column matches the workspace', async () => {
    await editor.loadBase();
    await editor.selectFrame('a');
    await editor.selectFrame('b');
    await editor.saveCurrent();
    await expect(editor.thumbs).toHaveCount(3);
    await editor.expectSideMatchesWorkspace();
  });

  test('8. an uploaded png saves, and a blocked camera still allows the sample', async () => {
    await editor.uploadFile('base.png', SAMPLE);
    await editor.saveCurrent();
    await expect(editor.thumbs).toHaveCount(4);

    const blocked = await context.newPage();
    const other = new EditorPage(blocked);

    await other.blockCamera();
    await other.open();
    await expect(blocked.locator('#stage-empty')).toBeVisible();
    await other.selectFrame('a');
    await expect(other.capture).toBeDisabled();
    await other.loadBase();
    await other.saveCurrent();
    await expect(other.thumbs).toHaveCount(5);
    await blocked.close();
    await page.reload();
  });

  test('9. a text file named fake.png is refused with a message', async () => {
    await editor.uploadFile('fake.png', Buffer.from('hello\n'));
    await editor.saveCurrent();
    await expect(editor.error).toHaveText('That file is not an image. Nothing was saved.');
    await expect(editor.thumbs).toHaveCount(5);
  });

  test('10. delete removes only the newest and a refresh deletes nothing else', async () => {
    await editor.deleteOwn.first().click();
    await expect(page).toHaveURL(/\/editor/);
    await expect(editor.thumbs).toHaveCount(4);
    await page.reload();
    await expect(editor.thumbs).toHaveCount(4);
  });

  test('11. a second member sees none of the first member pictures', async ({ request }) => {
    await accounts.logoutFromHere();
    await accounts.openSignup();
    await accounts.signup('evalbob', 'evalbob@example.com', 'Password1');
    await accounts.openLinkFromMail(request, 'evalbob@example.com', '/confirm/');
    await accounts.login('evalbob', 'Password1');
    await editor.open();
    await expect(editor.thumbs).toHaveCount(0);
    await expect(editor.deleteOwn).toHaveCount(0);
  });

  test('12. the editor fits 360px', async () => {
    await page.setViewportSize({ width: 360, height: 800 });
    await editor.open();
    await editor.expectSpacedLayout();
  });
});

test.describe('docs/gallery.md', () => {
  test('1. a logged-out gallery has no like or comment control', async () => {
    await page.setViewportSize({ width: 1024, height: 800 });
    await accounts.logoutFromHere();
    await page.goto('/');
    await expect(page.locator('[data-testid="gallery-like"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="gallery-comment-body"]')).toHaveCount(0);
    await expect(page.locator('main').getByRole('link', { name: 'Log in' })).toBeVisible();
  });

  test('2. six pictures show five and a next link', async ({ request }) => {
    await request.post('/e2e/reset');
    await accounts.openLogin();
    await accounts.login('evalada2', 'Password3');

    for (let index = 0; index < 6; index += 1) {
      await editor.open();
      await editor.loadBase();
      await editor.saveCurrent();
    }

    await page.goto('/');
    await expect(page.getByText('Newest first')).toBeVisible();
    await expect(page.locator('[data-testid="gallery-item"]')).toHaveCount(5);
    await expect(page.locator('[data-testid="gallery-next"]')).toBeVisible();
  });

  test('3. next appends the older picture and stays on this page', async () => {
    await page.locator('[data-testid="gallery-next"]').click();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.locator('[data-testid="gallery-item"]')).toHaveCount(6);
  });

  test('4. a second like on page 2 stays at one and stays on page 2', async () => {
    await page.goto('/?page=2');
    await page.locator('[data-testid="gallery-like"]').first().click();
    await expect(page).toHaveURL(/page=2$/);
    await page.locator('[data-testid="gallery-like"]').first().click();
    await expect(page).toHaveURL(/page=2$/);
    await expect(page.locator('.like-total').first()).toHaveText('1 like');
    await page.reload();
    await expect(page.locator('.like-total').first()).toHaveText('1 like');
  });

  test('5. logging out removes the controls and keeps the count as text', async () => {
    await accounts.logoutFromHere();
    await page.goto('/?page=2');
    await expect(page.locator('[data-testid="gallery-like"]')).toHaveCount(0);
    await expect(page.locator('[data-testid="gallery-comment-body"]')).toHaveCount(0);
    await expect(page.locator('.like-total').first()).toHaveText('1 like');
  });

  test('6. comment mail starts on', async () => {
    await accounts.openLogin();
    await accounts.login('evalada2', 'Password3');
    await page.goto('/profile');
    await expect(page.locator('[data-testid="profile-mail-preference"]')).toBeChecked();
  });

  test('7. a comment is visible and mails the author', async ({ request }) => {
    await accounts.logoutFromHere();
    await accounts.openLogin();
    await accounts.login('evalbob', 'Password1');
    await page.goto('/');
    await page.locator('[data-testid="gallery-comment-body"]').first().fill('hello gallery');
    await page.locator('[data-testid="gallery-comment-submit"]').first().click();
    const line = page.locator('[data-testid="gallery-comment"]').filter({ hasText: 'hello gallery' });

    await expect(line).toHaveCount(1);
    await expect(line.locator('b')).toHaveText('evalbob');

    const mail = await accounts.mailFor(request, 'evalada2@example.com', '/pictures/');

    expect(mail.Text).toContain('Hi evalada2,');
    expect(mail.Text).toContain('evalbob commented');
  });

  test('8. a refresh does not repeat the comment', async () => {
    let prompted = false;

    page.once('dialog', async (dialog) => {
      prompted = true;
      await dialog.dismiss();
    });
    await page.reload();
    await expect(page).toHaveURL(/\/$/);
    await expect(page.locator('[data-testid="gallery-comment"]').filter({ hasText: 'hello gallery' })).toHaveCount(1);
    expect(prompted).toBe(false);
  });

  test('9. comment mail off stores the comment and sends no mail', async ({ request }) => {
    await accounts.logoutFromHere();
    await accounts.openLogin();
    await accounts.login('evalada2', 'Password3');
    await page.goto('/profile');
    await page.locator('[data-testid="profile-mail-preference"]').uncheck();
    await page.locator('[data-testid="profile-submit"]').click();
    const before = await mailCount(request, 'evalada2@example.com');

    await accounts.logoutFromHere();
    await accounts.openLogin();
    await accounts.login('evalbob', 'Password1');
    await page.goto('/');
    await page.locator('[data-testid="gallery-comment-body"]').first().fill('quiet gallery');
    await page.locator('[data-testid="gallery-comment-submit"]').first().click();
    await expect(page.locator('[data-testid="gallery-comment"]').filter({ hasText: 'quiet gallery' })).toHaveCount(1);
    expect(await mailCount(request, 'evalada2@example.com')).toBe(before);
  });

  test('10. the gallery fits 360px with the like count on the byline row', async () => {
    await page.setViewportSize({ width: 360, height: 800 });
    await page.goto('/');
    await expect(page.locator('[data-testid="gallery-item"]').first()).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

    const byline = await page.locator('.byline').first().boundingBox();
    const likes = await page.locator('.like-total').first().boundingBox();

    expect(Math.abs((byline?.y || 0) + (byline?.height || 0) / 2 - ((likes?.y || 0) + (likes?.height || 0) / 2))).toBeLessThan(12);
  });

  test('10. the like button and its count have space between them', async () => {
    await accounts.openLogin();
    await accounts.login('evalbob', 'Password1');
    await page.setViewportSize({ width: 360, height: 800 });
    await page.goto('/');
    const button = await page.locator('[data-testid="gallery-like"]').first().boundingBox();
    const count = await page.locator('.like-total').first().boundingBox();

    expect((count?.x || 0) - ((button?.x || 0) + (button?.width || 0))).toBeGreaterThanOrEqual(6);
  });

  test('10. wide cards in a row are the same height', async () => {
    await page.setViewportSize({ width: 1024, height: 800 });
    await page.goto('/');
    const first = await page.locator('[data-testid="gallery-item"]').nth(0).boundingBox();
    const second = await page.locator('[data-testid="gallery-item"]').nth(1).boundingBox();

    expect(Math.abs((first?.height || 0) - (second?.height || 1))).toBeLessThanOrEqual(1);
  });
});

/**
 * @param {import('@playwright/test').APIRequestContext} request
 * @param {string} recipient
 */
async function mailCount(request, recipient) {
  const response = await request.get('http://127.0.0.1:8026/api/v1/messages');
  const body = await response.json();

  return (body.messages || []).filter((message) => {
    const to = (message.To || []).map((item) => item.Address);

    return to.indexOf(recipient) !== -1;
  }).length;
}

test.describe('docs/shell.md', () => {
  test('1. the pages have a header, a main, and a footer at 360px', async () => {
    await page.setViewportSize({ width: 360, height: 800 });

    for (const address of ['/', '/login', '/signup', '/profile']) {
      await page.goto(address);
      await expect(page.locator('[data-testid="shell-header"]')).toBeVisible();
      await expect(page.locator('[data-testid="shell-main"]')).toBeVisible();
      await expect(page.locator('[data-testid="shell-footer"]')).toBeVisible();
      expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
    }
  });

  test('2. a script comment is text and does not run', async ({ request }) => {
    await request.post('/e2e/reset');
    await accounts.openSignup();
    await accounts.signup('shell', 'shell@example.com', 'Password1');
    await accounts.openLinkFromMail(request, 'shell@example.com', '/confirm/');
    await accounts.login('shell', 'Password1');
    await editor.open();
    await editor.loadBase();
    await editor.saveCurrent();
    await page.goto('/');
    await page.locator('[data-testid="gallery-comment-body"]').first().fill('<script>window.__xss = 1</script>');
    await page.locator('[data-testid="gallery-comment-submit"]').first().click();
    await expect(page.locator('[data-testid="gallery-comment"]').first()).toContainText('script');
    expect(await page.evaluate(() => window.__xss)).toBeUndefined();
  });

  test('3. a quote in a comment is stored as text', async () => {
    await page.goto('/');
    await page.locator('[data-testid="gallery-comment-body"]').first().fill("it's a picture");
    await page.locator('[data-testid="gallery-comment-submit"]').first().click();
    await page.reload();
    await expect(page.locator('[data-testid="gallery-comment"]').filter({ hasText: "it's a picture" })).toHaveCount(1);
  });

  test('4. a username cannot contain a script', async () => {
    await accounts.logoutFromHere();
    await accounts.openSignup();
    await accounts.signup('<script>', 'script@example.com', 'Password1');
    await expect(page.getByText('letters, digits, and underscore')).toBeVisible();
  });

  test('5. the server log element stays empty', async () => {
    await page.goto('/');
    await expect(page.locator('[data-testid="server-log"]')).toHaveText('');
  });
});

test.describe('docs/bonus.md', () => {
  test('1. like and comment stay on this document', async ({ request }) => {
    await request.post('/e2e/reset');
    await accounts.openSignup();
    await accounts.signup('bonus', 'bonus@example.com', 'Password1');
    await accounts.openLinkFromMail(request, 'bonus@example.com', '/confirm/');
    await accounts.login('bonus', 'Password1');
    await editor.open();
    await editor.loadBase();
    await editor.saveCurrent();
    await page.goto('/');
    const before = page.url();

    await page.locator('[data-testid="gallery-like"]').first().click();
    await expect(page).toHaveURL(before);
    await page.locator('[data-testid="gallery-comment-body"]').first().fill('stay');
    await page.locator('[data-testid="gallery-comment-submit"]').first().click();
    await expect(page).toHaveURL(before);
    await expect(page.locator('[data-testid="gallery-comment"]').filter({ hasText: 'stay' })).toHaveCount(1);
    await expect(page.locator('.no-comments')).toHaveCount(0);
  });

  test('2. delete stays on the editor', async () => {
    await editor.open();
    await page.locator('[data-testid="editor-delete"]').first().click();
    await expect(page).toHaveURL(/\/editor/);
    await expect(page.locator('[data-testid="editor-thumb"]')).toHaveCount(0);
  });

  test('3. the selected sticker is on the stage before save', async () => {
    await editor.open();
    await editor.waitForCamera();
    await editor.selectFrame('a');
    await expect(page.locator('#overlay-a')).toBeVisible();
  });

  test('4. scrolling appends the sixth picture once', async () => {
    for (let index = 0; index < 6; index += 1) {
      await editor.open();
      await editor.loadBase();
      await editor.saveCurrent();
    }

    await page.setViewportSize({ width: 1024, height: 400 });
    await page.goto('/');
    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await expect(page.locator('[data-testid="gallery-item"]')).toHaveCount(6);
    await expect(page.locator('[data-testid="gallery-next"]')).toHaveText('No more pictures');
    await expect(page.locator('[data-testid="gallery-next"]')).not.toHaveAttribute('href');
    await page.locator('[data-testid="gallery-next"]').click();
    await expect(page.locator('[data-testid="gallery-item"]')).toHaveCount(6);
  });

  test('5. share links carry the picture url and load no outside script', async () => {
    const href = await page.locator('[data-testid="share-x"]').first().getAttribute('href');

    expect(href).toContain('/pictures/');
    await expect(page.locator('[data-testid="share-x"]').first()).toHaveAttribute('target', '_blank');
    expect(await page.locator('[data-testid="share-facebook"]').first().getAttribute('href')).toContain('/pictures/');
    await expect(page.locator('[data-testid="share-facebook"]').first()).toHaveAttribute('target', '_blank');
    await expect(page.locator('script[src*="x.com"], script[src*="facebook.com"]')).toHaveCount(0);
  });

  test('6. three snaps from the live camera save one gif', async () => {
    await editor.open();
    await editor.waitForCamera();
    await expect(page.locator('[data-testid="gif-save"]')).toBeDisabled();
    await editor.loadBase();
    await expect(page.locator('[data-testid="gif-save"]')).toBeDisabled();
    await editor.open();
    await editor.waitForCamera();
    await editor.selectFrame('a');
    await expect(page.locator('[data-testid="gif-save"]')).toBeEnabled();
    await page.locator('[data-testid="gif-save"]').click();
    await expect(page).toHaveURL(/notice=gif/, { timeout: 8000 });
    await expect(page.locator('[data-testid="editor-notice"]')).toHaveText('GIF saved.');
    await page.reload();
    await expect(page.locator('[data-testid="editor-notice"]')).toHaveText('GIF saved.');
  });
});
