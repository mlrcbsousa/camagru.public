/**
 * @param {string} id
 * @returns {string}
 */
function testId(id) {
  return `[data-testid="${id}"]`;
}

module.exports = { testId };
