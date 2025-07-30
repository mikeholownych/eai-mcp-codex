const { HttpClient } = require('../http-client');
const config = require('../../config');

class VerificationFeedbackClient extends HttpClient {
  constructor() {
    super(config.services.verificationFeedback);
  }

  async submitFeedback(feedbackData) {
    const payload = {
      feedback_type: feedbackData.type,
      title: feedbackData.title,
      description: feedbackData.description || '',
      severity: feedbackData.severity || 'medium',
      metadata: {
        submitted_by: 'cli',
        submitted_at: new Date().toISOString(),
        ...feedbackData.metadata
      }
    };

    const response = await this.post('/feedback', payload);
    return response.data;
  }

  async listFeedback(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.type) params.append('type', filters.type);
    if (filters.severity) params.append('severity', filters.severity);
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await this.get('/feedback?' + params.toString());
    return response.data;
  }

  async getFeedback(feedbackId) {
    const response = await this.get(`/feedback/${feedbackId}`);
    return response.data;
  }

  async updateFeedback(feedbackId, updates) {
    const response = await this.put(`/feedback/${feedbackId}`, updates);
    return response.data;
  }

  async processFeedback(feedbackId) {
    const response = await this.post(`/feedback/${feedbackId}/process`);
    return response.data;
  }

  async getFeedbackSummary() {
    const response = await this.get('/feedback/summary');
    return response.data;
  }

  async verifyCode(codeData) {
    const payload = {
      code: codeData.code,
      language: codeData.language,
      verification_types: codeData.types || ['syntax', 'security', 'quality'],
      metadata: {
        source: 'cli',
        timestamp: new Date().toISOString()
      }
    };

    const response = await this.post('/verify/code', payload);
    return response.data;
  }

  async getVerificationResult(verificationId) {
    const response = await this.get(`/verify/${verificationId}`);
    return response.data;
  }
}

module.exports = VerificationFeedbackClient;