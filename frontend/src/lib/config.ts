export const API_CONFIG = {
  baseUrl: process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000',
  timeoutMs: parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT_MS || '30000'),
}

export const STRIPE_CONFIG = {
  publishableKey: process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || '',
}

export const APP_CONFIG = {
  name: process.env.NEXT_PUBLIC_APP_NAME || 'EAI MCP Codex',
  version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
  enablePayments: process.env.NEXT_PUBLIC_ENABLE_PAYMENTS === 'true',
  enableAnalytics: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true',
}

export const FEATURE_FLAGS = {
  payments: APP_CONFIG.enablePayments,
  analytics: APP_CONFIG.enableAnalytics,
}
