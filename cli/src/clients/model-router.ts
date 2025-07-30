import { HttpClient } from './http-client';
import config from '../config';

export interface RouteOptions {
  model?: string;
  temperature?: string;
  maxTokens?: number;
}

export interface ModelResponse {
  response: string;
  model: string;
  metadata?: Record<string, any>;
  usage?: { total_tokens: number; cost: number };
}

export class ModelRouterClient extends HttpClient {
  constructor() {
    super(config.services.modelRouter);
  }

  async routeRequest(prompt: string, options: RouteOptions = {}): Promise<ModelResponse> {
    const payload = {
      text: prompt,
      model: options.model,
      temperature: parseFloat(options.temperature ?? '0.7'),
      max_tokens: options.maxTokens ?? 1000,
      metadata: { source: 'cli', timestamp: new Date().toISOString() }
    };
    const response = await this.post<ModelResponse>('/model/route', payload);
    return response.data;
  }

  async listModels(): Promise<any[]> {
    const response = await this.get<any[]>('/model/models');
    return response.data;
  }

  async getRoutingRules(): Promise<any[]> {
    const response = await this.get<any[]>('/model/rules');
    return response.data;
  }

  async getMetrics(): Promise<any | null> {
    try {
      const response = await this.get('/metrics');
      return response.data;
    } catch {
      return null;
    }
  }
}
