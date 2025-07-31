import { HttpClient } from '../src/clients/http-client';

describe('HttpClient', () => {
  it('constructs with base URL', () => {
    const client = new HttpClient({ url: 'http://localhost', timeout: 1000 });
    expect((client as any).client.defaults.baseURL).toBe('http://localhost');
  });
});
