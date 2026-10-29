const { expect } = require('@playwright/test');

const { testId } = require('../selectors');

class AccountsPage {
  /**
   * @param {import('@playwright/test').Page} page
   */
  constructor(page) {
    this.page = page;
    this.username = page.locator(testId('signup-username'));
    this.email = page.locator(testId('signup-email'));
    this.password = page.locator(testId('signup-password'));
    this.signupSubmit = page.locator(testId('signup-submit'));
    this.signupError = page.locator(testId('signup-error'));
    this.loginUsername = page.locator(testId('login-username'));
    this.loginPassword = page.locator(testId('login-password'));
    this.loginSubmit = page.locator(testId('login-submit'));
    this.session = page.locator(testId('session-status'));
    this.logout = page.locator(testId('logout-submit'));
    this.resetEmail = page.locator(testId('reset-email'));
    this.resetRequest = page.locator(testId('reset-request-submit'));
    this.resetPassword = page.locator(testId('reset-password'));
    this.resetSubmit = page.locator(testId('reset-submit'));
    this.profileUsername = page.locator(testId('profile-username'));
    this.profileEmail = page.locator(testId('profile-email'));
    this.profilePassword = page.locator(testId('profile-password'));
    this.profileSubmit = page.locator(testId('profile-submit'));
    this.editor = page.locator(testId('editor-root'));
  }

  async openSignup() {
    await this.page.goto('/signup');
  }

  /**
   * @param {string} username
   * @param {string} email
   * @param {string} password
   */
  async signup(username, email, password) {
    await this.username.fill(username);
    await this.email.fill(email);
    await this.password.fill(password);
    await this.signupSubmit.click();
  }

  async openLogin() {
    await this.page.goto('/login');
  }

  /**
   * @param {string} username
   * @param {string} password
   */
  async login(username, password) {
    await this.loginUsername.fill(username);
    await this.loginPassword.fill(password);
    await this.loginSubmit.click();
  }

  async logoutFromHere() {
    await this.logout.click();
  }

  async openReset() {
    await this.page.goto('/reset');
  }

  /**
   * @param {string} email
   */
  async requestReset(email) {
    await this.resetEmail.fill(email);
    await this.resetRequest.click();
  }

  /**
   * @param {string} password
   */
  async chooseNewPassword(password) {
    await this.resetPassword.fill(password);
    await this.resetSubmit.click();
  }

  async openProfile() {
    await this.page.goto('/profile');
  }

  /**
   * @param {string} username
   * @param {string} email
   * @param {string} password
   */
  async editProfile(username, email, password) {
    await this.profileUsername.fill(username);
    await this.profileEmail.fill(email);
    await this.profilePassword.fill(password);
    await this.profileSubmit.click();
  }

  async expectLoggedOut() {
    await expect(this.session).toHaveText('');
    await expect(this.logout).toHaveCount(0);
  }

  async expectLoggedIn(username) {
    await expect(this.session).toHaveText(username);
  }

  async expectSignupRefused() {
    await expect(this.signupError).toBeVisible();
  }

  /**
   * @param {string} rule
   */
  async expectOnlyRule(rule) {
    await expect(this.page.locator('li')).toHaveText([rule]);
  }

  /**
   * @param {string} text
   */
  async expectText(text) {
    await expect(this.page.getByText(text)).toBeVisible();
  }

  async expectEditorRefused() {
    await this.page.goto('/editor');
    await expect(this.editor).toHaveCount(0);
  }

  /**
   * @param {import('@playwright/test').APIRequestContext} request
   * @param {string} recipient
   * @param {string} pathPart
   */
  async openLinkFromMail(request, recipient, pathPart) {
    const raw = JSON.stringify(await this.mailFor(request, recipient, pathPart));
    const match = raw.match(/https?:\/\/[^"\\]+/);

    await this.page.goto(match[0]);
  }

  async expectOneMail(request, recipient, pathPart) {
    await this.mailFor(request, recipient, pathPart);
  }

  async mailFor(request, recipient, pathPart) {
    const response = await request.get('http://127.0.0.1:8026/api/v1/messages');

    expect(response.ok()).toBeTruthy();

    const body = await response.json();
    const messages = body.messages || [];
    const mine = messages.filter((message) => {
      const to = (message.To || []).map((item) => item.Address);

      return to.indexOf(recipient) !== -1 && JSON.stringify(message).indexOf(pathPart) !== -1;
    });

    expect(mine).toHaveLength(1);

    return mine[0];
  }
}

module.exports = { AccountsPage };
