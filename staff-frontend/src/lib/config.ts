export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_URL || '/api',
  retryLimit: 3,
  timeoutMs: 5000,
}
