const { expect } = require('@playwright/test');

const { testId } = require('../selectors');

class GalleryPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    this.items = page.locator(testId('gallery-item'));
    this.next = page.locator(testId('gallery-next'));
    this.like = page.locator(testId('gallery-like'));
    this.likeCount = page.locator(testId('gallery-like-count'));
    this.commentBody = page.locator(testId('gallery-comment-body'));
    this.commentSubmit = page.locator(testId('gallery-comment-submit'));
    this.comments = page.locator(testId('gallery-comment'));
    this.mailNote = page.locator(testId('comment-mail-status'));
    this.preference = page.locator(testId('profile-mail-preference'));
  }

  async open() {
    await this.page.goto('/');
  }

  async openNext() {
    const href = await this.next.getAttribute('href');

    await this.page.goto(href);
  }

  async likeFirst() {
    await this.like.first().click();
  }

  /**
   * @param {string} text
   */
  async comment(text) {
    await this.commentBody.first().fill(text);
    await this.commentSubmit.first().click();
  }

  async turnMailOff() {
    await this.page.goto('/profile');
    await this.preference.uncheck();
    await this.page.locator(testId('profile-submit')).click();
  }

  async expectPageCount(count) {
    await expect(this.items).toHaveCount(count);
  }

  async expectLikeCount(count) {
    await expect(this.likeCount.first()).toHaveText(String(count));
  }

  async expectCommentText(text) {
    await expect(this.comments.filter({ hasText: text })).toHaveCount(1);
  }

  async expectNoComment() {
    await expect(this.comments).toHaveCount(0);
  }

  async expectNoMailSent() {
    await expect(this.mailNote).toHaveCount(0);
  }

  async expectMailFailed() {
    await expect(this.mailNote).toHaveText('the mail was not sent');
  }
}

module.exports = { GalleryPage };
