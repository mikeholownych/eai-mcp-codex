import { HttpClient } from './http-client';
import config from '../config';

export interface WorktreeData {
  repo: string;
  branch: string;
  path?: string;
  message?: string;
  files?: string[];
  author?: string;
}

export class GitWorktreeClient extends HttpClient {
  constructor() {
    super(config.services.gitWorktree);
  }

  async createWorktree(data: WorktreeData): Promise<any> {
    const payload = {
      repository_url: data.repo,
      branch: data.branch,
      path: data.path,
      metadata: { created_by: 'cli', created_at: new Date().toISOString() }
    };
    const response = await this.post('/worktrees', payload);
    return response.data;
  }

  async listWorktrees(filters: Record<string, string> = {}): Promise<any[]> {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([k, v]) => params.append(k, v));
    const response = await this.get(`/worktrees?${params.toString()}`);
    return response.data;
  }

  async getWorktree(worktreeId: string): Promise<any> {
    const response = await this.get(`/worktrees/${worktreeId}`);
    return response.data;
  }

  async removeWorktree(worktreeId: string): Promise<any> {
    const response = await this.delete(`/worktrees/${worktreeId}`);
    return response.data;
  }

  async syncWorktree(worktreeId: string): Promise<any> {
    const response = await this.post(`/worktrees/${worktreeId}/sync`);
    return response.data;
  }

  async getWorktreeStatus(worktreeId: string): Promise<any> {
    const response = await this.get(`/worktrees/${worktreeId}/status`);
    return response.data;
  }

  async commitChanges(worktreeId: string, commitData: WorktreeData): Promise<any> {
    const payload = {
      message: commitData.message,
      files: commitData.files ?? [],
      author: commitData.author
    };
    const response = await this.post(`/worktrees/${worktreeId}/commit`, payload);
    return response.data;
  }
}
