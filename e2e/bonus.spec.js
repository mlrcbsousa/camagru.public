const { request } = require('@playwright/test');
const { test } = require('./fixtures/test');

test.afterAll(async () => {
  const api = await request.newContext({ baseURL: 'http://127.0.0.1:8765' });

  await api.post('/e2e/reset');
  await api.dispose();
});

async function member(accounts, request, name) {
  await accounts.openSignup();
  await accounts.signup(name, name + '@example.com', 'Password1');
  await accounts.openLinkFromMail(request, name + '@example.com', '/confirm/');
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

test('like, comment, and delete stay on this document', async ({ bonus, gallery, accounts, editor, request }) => {
  await member(accounts, request, 'stay');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  await bonus.openGallery();
  await bonus.likeHere();
  await bonus.expectSameDocument(async () => {
    await gallery.comment('stay');
  });
  await bonus.openEditor();
  await bonus.deleteHere();
});

test('the selected frame is on the webcam before save', async ({ bonus, editor, accounts, request }) => {
  await member(accounts, request, 'frame');
  await bonus.openEditor();
  await editor.selectFrame('a');
  await bonus.expectFrameOnPreview();
});

test('scroll and next append the sixth picture once', async ({ bonus, accounts, editor, request }) => {
  await request.post('/e2e/reset');
  await member(accounts, request, 'scroll');
  await savePictures(editor, 6);
  await bonus.openGallery();
  await bonus.expectSixthAppended();
  await bonus.expectNextAppendsOnce();
});

test('share links carry the picture url and load no third-party script', async ({ bonus, accounts, editor, request }) => {
  await request.post('/e2e/reset');
  await member(accounts, request, 'share');
  await editor.open();
  await editor.loadBase();
  await editor.saveCurrent();
  await bonus.openGallery();
  await bonus.expectShareLinks('pictures/1');
});

test('three snaps save one gif', async ({ bonus, accounts, editor, request }) => {
  await member(accounts, request, 'gif');
  await bonus.openEditor();
  await editor.waitForCamera();
  await editor.selectFrame('a');
  await bonus.expectGifStored();
});
