import { GitWorktreeClient } from '../src/clients/git-worktree';

describe('GitWorktreeClient', () => {
  it('uses configured base URL', () => {
    const client = new GitWorktreeClient();
    expect((client as any).client.defaults.baseURL).toBe('http://localhost/api/git');
  });
});
