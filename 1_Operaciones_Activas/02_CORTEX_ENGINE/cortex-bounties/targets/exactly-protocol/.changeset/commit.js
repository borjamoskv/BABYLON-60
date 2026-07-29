// C5-REAL EXERGY CERTIFIED
/** @type {import('@changesets/types').CommitFunctions} */
module.exports = {
  getVersionMessage: ({ releases: [{ newVersion }] }) => Promise.resolve(`🔖 v${newVersion}`),
};
