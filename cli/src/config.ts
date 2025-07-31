export default {
  api: {
    timeout: 5000
  },
  services: {
    modelRouter: { url: 'http://localhost/api/model' },
    planManagement: { url: 'http://localhost/api/plans' },
    gitWorktree: { url: 'http://localhost/api/git' },
    workflowOrchestrator: { url: 'http://localhost/api/workflows' },
    verificationFeedback: { url: 'http://localhost/api/feedback' }
  }
};
