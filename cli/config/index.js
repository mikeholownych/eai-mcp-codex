const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '../../.env') });

const config = {
  // Service endpoints (routed through nginx API gateway)
  services: {
    modelRouter: {
      url: process.env.MODEL_ROUTER_URL || 'http://localhost/api/model',
      timeout: 30000
    },
    planManagement: {
      url: process.env.PLAN_MANAGEMENT_URL || 'http://localhost/api/plans', 
      timeout: 10000
    },
    gitWorktree: {
      url: process.env.GIT_WORKTREE_URL || 'http://localhost/api/git',
      timeout: 15000
    },
    workflowOrchestrator: {
      url: process.env.WORKFLOW_ORCHESTRATOR_URL || 'http://localhost/api/workflows',
      timeout: 60000
    },
    verificationFeedback: {
      url: process.env.VERIFICATION_FEEDBACK_URL || 'http://localhost/api/feedback',
      timeout: 10000
    }
  },
  
  // CLI settings
  cli: {
    defaultPageSize: 20,
    maxRetries: 3,
    retryDelay: 1000
  },

  // API settings
  api: {
    timeout: 30000,
    retries: 3
  }
};

module.exports = config;