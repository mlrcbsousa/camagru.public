const { expect } = require('@playwright/test');

const { testId } = require('../selectors');

class EditorPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    this.root = page.locator(testId('editor-root'));
    this.preview = page.locator(testId('editor-preview'));
    this.frame = page.locator(testId('editor-frame'));
    this.capture = page.locator(testId('editor-capture'));
    this.upload = page.locator(testId('editor-upload'));
    this.save = page.locator(testId('editor-save'));
    this.error = page.locator(testId('editor-error'));
    this.thumbs = page.locator(testId('editor-thumb'));
    this.deleteOwn = page.locator(testId('editor-delete'));
  }

  async open() {
    await this.page.goto('/editor');
  }

  async loadBase() {
    await this.page.locator(testId('editor-use-sample')).click();
  }

  async uploadJunk() {
    await this.upload.setInputFiles({
      name: 'note.txt',
      mimeType: 'text/plain',
      buffer: Buffer.from('not-an-image'),
    });
    await this.page.waitForFunction(() => {
      var field = document.getElementById('upload-b64');

      return field && field.value.length > 0;
    });
  }

  async saveCurrent() {
    await this.save.click();
  }

  /**
   * @param {string} name
   */
  async selectFrame(name) {
    await this.page.locator(testId('editor-frame-' + name)).click();
  }

  async expectStoredThumb() {
    await expect(this.thumbs).toHaveCount(1);
  }

  async expectNothingStored() {
    await expect(this.thumbs).toHaveCount(0);
    await expect(this.error).toBeVisible();
  }

  async firstPictureId() {
    const src = await this.thumbs.first().getAttribute('src');

    return src.split('/').pop();
  }

  /**
   * @param {string} id
   */
  async deleteOther(id) {
    await this.page.evaluate((pictureId) => {
      var form = document.createElement('form');
      var csrf = document.querySelector('input[name="csrf"]');

      form.method = 'post';
      form.action = '/pictures/' + pictureId + '/delete';
      form.appendChild(csrf.cloneNode());
      document.body.appendChild(form);
      form.submit();
    }, id);
    await this.page.waitForURL('**/editor?error=notyours');
  }

  async waitForCamera() {
    await this.page.waitForFunction(() => !document.getElementById('camera').hidden);
  }

  async blockCamera() {
    await this.page.addInitScript(() => {
      navigator.mediaDevices.getUserMedia = () => Promise.reject(new Error('blocked'));
    });
  }

  /**
   * @param {string} name
   * @param {Buffer} buffer
   */
  async uploadFile(name, buffer) {
    await this.upload.setInputFiles({ name, mimeType: 'image/png', buffer });
    await expect(this.save).toBeEnabled();
  }

  /**
   * @param {string} selector
   */
  async box(selector) {
    const found = await this.page.locator(selector).first().boundingBox();

    expect(found).not.toBeNull();

    return /** @type {{ x: number, y: number, width: number, height: number }} */ (found);
  }

  async expectSpacedLayout() {
    const stage = await this.box('#stage');
    const form = await this.box('#editor-form');
    const stickers = await this.box('.frames');
    const actions = await this.box('.actions');
    const nav = await this.box('header nav a:last-child');
    const name = await this.box('[data-testid="session-status"]');
    const logout = await this.box('[data-testid="logout-submit"]');
    const wide = await this.page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth);

    expect(form.y).toBeGreaterThanOrEqual(stage.y + stage.height + 8);
    expect(actions.y).toBeGreaterThanOrEqual(stickers.y + stickers.height + 8);
    expect(name.x).toBeGreaterThanOrEqual(nav.x + nav.width + 8);
    expect(logout.x).toBeGreaterThanOrEqual(name.x + name.width + 8);
    expect(logout.x - (name.x + name.width)).toBeLessThanOrEqual(24);
    expect(wide).toBe(true);
  }

  async expectSideMatchesWorkspace() {
    const main = await this.box('.editor-main');
    const side = await this.box('.editor-side');

    expect(Math.abs(side.y + side.height - (main.y + main.height))).toBeLessThanOrEqual(2);
  }

  async expectCameraOff() {
    await expect(this.page.locator('#camera')).toBeHidden();
    expect(await this.page.evaluate(() => window.stream === null)).toBe(true);
  }

  async deleteFirst() {
    await this.deleteOwn.first().click();
  }

  async expectGone() {
    await expect(this.thumbs).toHaveCount(0);
  }

  /**
   * @param {import('@playwright/test').APIRequestContext} request
   * @param {string} id
   */
  async expectStillThere(request, id) {
    const response = await request.get('/pictures/' + id);

    expect(response.status()).toBe(200);
  }
}

module.exports = { EditorPage };
