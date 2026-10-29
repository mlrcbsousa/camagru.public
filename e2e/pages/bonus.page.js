const { expect } = require('@playwright/test');

const { testId } = require('../selectors');

class BonusPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    this.like = page.locator(testId('gallery-like'));
    this.deleteOwn = page.locator(testId('editor-delete'));
    this.preview = page.locator(testId('editor-preview'));
    this.items = page.locator(testId('gallery-item'));
    this.next = page.locator(testId('gallery-next'));
    this.shareX = page.locator(testId('share-x'));
    this.shareFacebook = page.locator(testId('share-facebook'));
    this.gifSave = page.locator(testId('gif-save'));
  }

  async openGallery() {
    await this.page.goto('/');
  }

  async openEditor() {
    await this.page.goto('/editor');
  }

  async likeHere() {
    await this.expectSameDocument(async () => {
      await this.like.first().click();
    });
  }

  async deleteHere() {
    await this.expectSameDocument(async () => {
      await this.deleteOwn.first().click();
    });
  }

  async expectSameDocument(action) {
    const before = this.page.url();

    await action();

    expect(this.page.url()).toBe(before);
  }

  async expectFrameOnPreview() {
    await expect(this.preview).toHaveAttribute('data-frame', '1');
  }

  async expectSixthAppended() {
    await this.page.evaluate(() => window.scrollTo(0, document.body.scrollHeight));
    await expect(this.items).toHaveCount(6);
  }

  async expectNextAppendsOnce() {
    await this.next.click();
    await expect(this.items).toHaveCount(6);
  }

  async expectShareLinks(pictureUrl) {
    await expect(this.shareX.first()).toHaveAttribute('href', new RegExp(pictureUrl));
    await expect(this.shareX.first()).toHaveAttribute('target', '_blank');
    await expect(this.shareFacebook.first()).toHaveAttribute('href', new RegExp(pictureUrl));
    await expect(this.shareFacebook.first()).toHaveAttribute('target', '_blank');
    await expect(this.page.locator('script[src*="x.com"], script[src*="facebook.com"]')).toHaveCount(0);
  }

  async expectGifStored() {
    await this.gifSave.click();
    await expect(this.page).toHaveURL(/notice=gif/, { timeout: 8000 });
    await expect(this.page.locator('[data-testid="editor-notice"]')).toHaveText('GIF saved.');
    await this.page.reload();
    await expect(this.page.locator('[data-testid="editor-notice"]')).toHaveText('GIF saved.');
  }
}

module.exports = { BonusPage };
