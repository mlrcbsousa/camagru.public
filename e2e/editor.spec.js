const fs = require('fs');
const path = require('path');

const { expect } = require('@playwright/test');

const { test } = require('./fixtures/test');

const SAMPLE = fs.readFileSync(path.join(__dirname, '..', 'public', 'base.png'));

async function member(accounts, request, name) {
  await accounts.openSignup();
  await accounts.signup(name, name + '@example.com', 'Password1');
  await accounts.openLinkFromMail(request, name + '@example.com', '/confirm/');
  await accounts.openLogin();
  await accounts.login(name, 'Password1');
}

test('a logged-out editor sends the visitor to log in', async ({ editor }) => {
  await editor.open();
  await expect(editor.page).toHaveURL(/\/login$/);
});

test('a base image and zero frames stores a picture', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'frame0');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  await editor.expectStoredThumb();
  await editor.deleteFirst();
});

test('save stays off until a base image is loaded', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'nobase');
  await editor.open();
  await expect(editor.save).toBeDisabled();
  await expect(editor.thumbs).toHaveCount(0);
});

test('capture stays off until a sticker is selected', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'capgate');
  await editor.open();
  await editor.waitForCamera();
  await expect(editor.capture).toBeDisabled();
  await editor.selectFrame('a');
  await expect(editor.capture).toBeEnabled();
  await editor.capture.click();
  await expect(editor.capture).toHaveText('Retake');
  await expect(editor.save).toBeEnabled();
  await editor.expectCameraOff();
});

test('the sample photo turns the camera off', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'camoff');
  await editor.open();
  await editor.waitForCamera();
  await editor.loadBase();
  await editor.expectCameraOff();
});

test('a refresh after save does not store it again', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'refresh');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  await expect(editor.page).toHaveURL(/\/editor\?notice=picture$/);
  await editor.page.reload();
  await editor.expectStoredThumb();
  await editor.deleteFirst();
  await editor.expectGone();
  await expect(editor.page).toHaveURL(/\/editor\?notice=picture$/);
});

test('two frames store a different picture', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'frame2');
  await editor.open();
  await editor.loadBase();
  await editor.selectFrame('a');
  await editor.selectFrame('b');
  await editor.saveCurrent();
  await editor.expectStoredThumb();
  await editor.deleteFirst();
});

test('a non-image upload stores nothing', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'notpng');
  await editor.open();
  await editor.uploadJunk();
  await editor.saveCurrent();
  await editor.expectNothingStored();
});

test('the owner delete removes the picture', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'owner');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  await editor.deleteFirst();
  await editor.expectGone();
});

test('deleting someone else picture leaves it', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'picowner');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  const id = await editor.firstPictureId();
  await accounts.logoutFromHere();
  await member(accounts, request, 'picother');
  await editor.open();
  await editor.deleteOther(id);
  await editor.expectStillThere(request, id);
});

test('a blocked camera keeps capture off and the sample still saves', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'nocam');
  await editor.blockCamera();
  await editor.open();
  await expect(editor.page.locator('#stage-empty')).toBeVisible();
  await editor.selectFrame('a');
  await expect(editor.capture).toBeDisabled();
  await editor.loadBase();
  await editor.saveCurrent();
  await editor.expectStoredThumb();
});

test('an uploaded png with no sticker stores a picture', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'realpng');
  await editor.open();
  await editor.uploadFile('base.png', SAMPLE);
  await editor.saveCurrent();
  await editor.expectStoredThumb();
});

test('a text file named fake.png is refused with a message', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'fakepng');
  await editor.open();
  await editor.uploadFile('fake.png', Buffer.from('hello\n'));
  await editor.saveCurrent();
  await expect(editor.page).toHaveURL(/\/editor\?error=notimage$/);
  await expect(editor.error).toHaveText('That file is not an image. Nothing was saved.');
  await expect(editor.thumbs).toHaveCount(0);
});

test('a thumbnail opens the stored png', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'openpng');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  const id = await editor.firstPictureId();
  const response = await request.get('/pictures/' + id);

  await expect(editor.page.locator('a[href="/pictures/' + id + '"]')).toHaveCount(1);
  expect(response.headers()['content-type']).toBe('image/png');
});

test('the camera comes back after a save and a refresh after delete removes nothing else', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'camback');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  await editor.waitForCamera();
  await editor.loadBase();
  await editor.saveCurrent();
  await editor.deleteOwn.last().click();
  await editor.page.reload();
  await expect(editor.thumbs).toHaveCount(1);
});

test('wide layout: spaced controls and a pictures column as tall as the workspace', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'wide');
  await editor.page.setViewportSize({ width: 1024, height: 800 });
  await editor.open();

  for (let index = 0; index < 4; index += 1) {
    await editor.loadBase();
    await editor.saveCurrent();
  }

  await editor.expectSpacedLayout();
  await editor.expectSideMatchesWorkspace();
});

test('narrow layout: spaced controls and two thumbnails per row', async ({ editor, accounts, request }) => {
  await member(accounts, request, 'narrow');
  await editor.page.setViewportSize({ width: 360, height: 800 });
  await editor.open();

  for (let index = 0; index < 2; index += 1) {
    await editor.loadBase();
    await editor.saveCurrent();
  }

  await editor.expectSpacedLayout();
  const first = await editor.thumbs.nth(0).boundingBox();
  const second = await editor.thumbs.nth(1).boundingBox();

  expect(Math.abs((first?.y || 0) - (second?.y || 1))).toBeLessThanOrEqual(1);
});
