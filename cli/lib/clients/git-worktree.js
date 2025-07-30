const { HttpClient } = require('../http-client');
const config = require('../../config');

class GitWorktreeClient extends HttpClient {
  constructor() {
    super(config.services.gitWorktree);
  }

  async createWorktree(worktreeData) {
    const payload = {
      repository_url: worktreeData.repo,
      branch: worktreeData.branch,
      path: worktreeData.path,
      metadata: {
        created_by: 'cli',
        created_at: new Date().toISOString()
      }
    };

    const response = await this.post('/worktrees', payload);
    return response.data;
  }

  async listWorktrees(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.status) params.append('status', filters.status);
    if (filters.repository) params.append('repository', filters.repository);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await this.get('/worktrees?' + params.toString());
    return response.data;
  }

  async getWorktree(worktreeId) {
    const response = await this.get(`/worktrees/${worktreeId}`);
    return response.data;
  }

  async removeWorktree(worktreeId) {
    await this.delete(`/worktrees/${worktreeId}`);
    return { success: true };
  }

  async syncWorktree(worktreeId) {
    const response = await this.post(`/worktrees/${worktreeId}/sync`);
    return response.data;
  }

  async getWorktreeStatus(worktreeId) {
    const response = await this.get(`/worktrees/${worktreeId}/status`);
    return response.data;
  }

  async commitChanges(worktreeId, commitData) {
    const payload = {
      message: commitData.message,
      files: commitData.files || [],
      author: commitData.author
    };

    const response = await this.post(`/worktrees/${worktreeId}/commit`, payload);
    return response.data;
  }
}

module.exports = GitWorktreeClient;