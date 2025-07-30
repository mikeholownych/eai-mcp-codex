const { HttpClient } = require('../http-client');
const config = require('../../config');

class ModelRouterClient extends HttpClient {
  constructor() {
    super(config.services.modelRouter);
  }

  async routeRequest(prompt, options = {}) {
    const payload = {
      text: prompt,
      model: options.model,
      temperature: parseFloat(options.temperature) || 0.7,
      max_tokens: options.maxTokens || 1000,
      metadata: {
        source: 'cli',
        timestamp: new Date().toISOString()
      }
    };

    const response = await this.post('/model/route', payload);
    return response.data;
  }

  async listModels() {
    const response = await this.get('/model/models');
    return response.data;
  }

  async getRoutingRules() {
    const response = await this.get('/model/rules');
    return response.data;
  }

  async getMetrics() {
    try {
      const response = await this.get('/metrics');
      return response.data;
    } catch (error) {
      // Metrics endpoint might not be available
      return null;
    }
  }
}

module.exports = ModelRouterClient;