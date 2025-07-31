import { ModelRouterClient } from '../src/clients/model-router';

describe('ModelRouterClient', () => {
  it('uses configured base URL', () => {
    const client = new ModelRouterClient();
    expect((client as any).client.defaults.baseURL).toBe('http://localhost/api/model');
  });
});
