const { expect } = require('@playwright/test');

const { testId } = require('../selectors');

class ShellPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    this.header = page.locator(testId('shell-header'));
    this.main = page.locator(testId('shell-main'));
    this.footer = page.locator(testId('shell-footer'));
    this.log = page.locator(testId('server-log'));
  }

  /**
   * @param {string} path
   */
  async open(path) {
    await this.page.setViewportSize({ width: 360, height: 640 });
    await this.page.goto(path);
  }

  async expectRegions() {
    await expect(this.header).toBeVisible();
    await expect(this.main).toBeVisible();
    await expect(this.footer).toBeVisible();
  }

  async expectScriptDidNotRun() {
    await expect(this.page.locator(testId('xss-ran'))).toHaveCount(0);
  }

  async expectLogEmpty() {
    await expect(this.log).toHaveText('');
  }
}

module.exports = { ShellPage };
