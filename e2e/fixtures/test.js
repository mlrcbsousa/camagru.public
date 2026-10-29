const { test: base, expect } = require('@playwright/test');

const { AccountsPage } = require('../pages/accounts.page');
const { BonusPage } = require('../pages/bonus.page');
const { EditorPage } = require('../pages/editor.page');
const { GalleryPage } = require('../pages/gallery.page');
const { ShellPage } = require('../pages/shell.page');

const test = base.extend({
  accounts: async ({ page }, use) => {
    await use(new AccountsPage(page));
  },
  editor: async ({ page }, use) => {
    await use(new EditorPage(page));
  },
  gallery: async ({ page }, use) => {
    await use(new GalleryPage(page));
  },
  shell: async ({ page }, use) => {
    await use(new ShellPage(page));
  },
  bonus: async ({ page }, use) => {
    await use(new BonusPage(page));
  },
});

module.exports = { test, expect };
