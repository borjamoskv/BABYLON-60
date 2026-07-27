// C5-REAL EXERGY CERTIFIED
module.exports = ({ github, context }) =>
  github.rest.actions.createWorkflowDispatch({
    owner: context.repo.owner,
    repo: context.repo.repo,
    workflow_id: 'release-cycle.yml',
    ref: process.env.REF || process.env.GITHUB_REF_NAME,
  });
