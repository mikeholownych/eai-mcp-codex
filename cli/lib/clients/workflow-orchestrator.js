const { HttpClient } = require('../http-client');
const config = require('../../config');

class WorkflowOrchestratorClient extends HttpClient {
  constructor() {
    super(config.services.workflowOrchestrator);
  }

  async createWorkflow(workflowData) {
    const payload = {
      name: workflowData.name,
      description: workflowData.description || '',
      steps: workflowData.steps || [],
      metadata: {
        created_by: 'cli',
        created_at: new Date().toISOString()
      }
    };

    const response = await this.post('/workflows', payload);
    return response.data;
  }

  async listWorkflows(filters = {}) {
    const params = new URLSearchParams();
    
    if (filters.status) params.append('status', filters.status);
    if (filters.limit) params.append('limit', filters.limit);

    const response = await this.get('/workflows?' + params.toString());
    return response.data;
  }

  async getWorkflow(workflowId) {
    const response = await this.get(`/workflows/${workflowId}`);
    return response.data;
  }

  async executeWorkflow(workflowId, inputs = {}) {
    const payload = {
      inputs,
      execution_mode: 'async',
      metadata: {
        triggered_by: 'cli',
        triggered_at: new Date().toISOString()
      }
    };

    const response = await this.post(`/workflows/${workflowId}/execute`, payload);
    return response.data;
  }

  async getWorkflowStatus(workflowId) {
    const response = await this.get(`/workflows/${workflowId}/status`);
    return response.data;
  }

  async getExecution(executionId) {
    const response = await this.get(`/executions/${executionId}`);
    return response.data;
  }

  async cancelExecution(executionId) {
    const response = await this.post(`/executions/${executionId}/cancel`);
    return response.data;
  }

  async getExecutionLogs(executionId) {
    const response = await this.get(`/executions/${executionId}/logs`);
    return response.data;
  }

  async listTemplates() {
    const response = await this.get('/templates');
    return response.data;
  }

  async createFromTemplate(templateId, parameters = {}) {
    const payload = {
      template_id: templateId,
      parameters
    };

    const response = await this.post('/workflows/from-template', payload);
    return response.data;
  }
}

module.exports = WorkflowOrchestratorClient;