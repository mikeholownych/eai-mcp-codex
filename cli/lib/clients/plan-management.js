const { HttpClient } = require('../http-client');
const config = require('../../config');

class PlanManagementClient extends HttpClient {
  constructor() {
    super(config.services.planManagement);
  }

  async createPlan(planData) {
    const payload = {
      title: planData.title,
      description: planData.description || '',
      tags: planData.tags || [],
      status: 'draft',
      created_at: new Date().toISOString()
    };

    const response = await this.post('/plans', payload);
    return response.data;
  }

  async listPlans(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit);
    if (filters.offset) params.append('offset', filters.offset);

    const response = await this.get('/plans?' + params.toString());
    return response.data;
  }

  async getPlan(planId) {
    const response = await this.get(`/plans/${planId}`);
    return response.data;
  }

  async updatePlan(planId, updates) {
    const response = await this.put(`/plans/${planId}`, updates);
    return response.data;
  }

  async deletePlan(planId) {
    await this.delete(`/plans/${planId}`);
    return { success: true };
  }

  async addTask(planId, taskData) {
    const response = await this.post(`/plans/${planId}/tasks`, taskData);
    return response.data;
  }

  async updateTask(planId, taskId, updates) {
    const response = await this.put(`/plans/${planId}/tasks/${taskId}`, updates);
    return response.data;
  }

  async generateTasks(planId, options = {}) {
    const response = await this.post(`/plans/${planId}/generate-tasks`, options);
    return response.data;
  }
}

module.exports = PlanManagementClient;