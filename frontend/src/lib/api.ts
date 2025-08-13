import axios, { AxiosInstance } from 'axios'
<<<<<<< HEAD
import {
  ApiResponse,
  User,
  ChatSession,
  SupportTicket,
  Subscription,
  ModelRouteResponse,
  AvailableModel,
  ModelStats,
  Invoice,
} from '@/types'
=======
import { ApiResponse, User, ChatSession, SupportTicket, Subscription, ModelRouteResponse, AvailableModel, ModelStats } from '@/types'
>>>>>>> main
import { API_CONFIG } from './config'

class ApiClient {
  private client: AxiosInstance
  private baseURL: string

  constructor() {
    this.baseURL = API_CONFIG.baseUrl

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: API_CONFIG.timeoutMs,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      config => {
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      error => Promise.reject(error),
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      response => response,
      error => {
        if (error.response?.status === 401) {
          this.handleUnauthorized()
        }
        return Promise.reject(error)
      },
    )
  }

  private getAuthToken(): string | null {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('auth_token')
    }
    return null
  }

  private handleUnauthorized(): void {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
  }

  // Auth endpoints
  async login(
    email: string,
    password: string,
  ): Promise<ApiResponse<{ user: User; token: string }>> {
    const response = await this.client.post('/api/auth/login', { email, password })
    return response.data
  }

  async register(data: {
    name: string
    email: string
    password: string
    tenantName?: string
  }): Promise<ApiResponse<{ user: User; token: string }>> {
    const response = await this.client.post('/api/auth/register', data)
    return response.data
  }

  async logout(): Promise<ApiResponse> {
    const response = await this.client.post('/api/auth/logout')
    return response.data
  }

  async getCurrentUser(): Promise<ApiResponse<User>> {
    const response = await this.client.get('/api/auth/me')
    return response.data
  }

  // Model Router endpoints - Updated to match backend API
<<<<<<< HEAD
  async routeRequest(
    prompt: string,
    options?: {
      model?: string
      temperature?: number
      maxTokens?: number
      taskType?: string
      priority?: string
      systemPrompt?: string
      context?: Record<string, unknown>
    },
  ): Promise<ApiResponse<ModelRouteResponse>> {
=======
  async routeRequest(prompt: string, options?: {
    model?: string
    temperature?: number
    maxTokens?: number
    taskType?: string
    priority?: string
    systemPrompt?: string
    context?: Record<string, unknown>
  }): Promise<ApiResponse<ModelRouteResponse>> {
>>>>>>> main
    const requestId = Date.now().toString()
    const response = await this.client.post('/model/route', {
      text: prompt,
      request_id: requestId,
      temperature: options?.temperature || 0.7,
      max_tokens: options?.maxTokens || 4096,
      task_type: options?.taskType,
      priority: options?.priority || 'medium',
      system_prompt: options?.systemPrompt,
      context: options?.context,
    })
    return response.data
  }

  async getAvailableModels(): Promise<ApiResponse<AvailableModel[]>> {
    const response = await this.client.get('/model/models')
    return response.data
  }

  async getModelStats(): Promise<ApiResponse<ModelStats>> {
    const response = await this.client.get('/model/stats')
    return response.data
  }

  async testClaudeConnection(): Promise<ApiResponse<{ status: string; message: string }>> {
    const response = await this.client.post('/model/health/claude')
    return response.data
  }

  // Plan Management endpoints
  async createPlan(data: {
    title: string
    description: string
    requirements: string[]
  }): Promise<ApiResponse<{ id: string; title: string; status: string }>> {
    const response = await this.client.post('/api/plans/create', data)
    return response.data
  }

<<<<<<< HEAD
  async getPlans(): Promise<
    ApiResponse<Array<{ id: string; title: string; description: string; status: string }>>
  > {
=======
  async getPlans(): Promise<ApiResponse<Array<{ id: string; title: string; description: string; status: string }>>> {
>>>>>>> main
    const response = await this.client.get('/api/plans')
    return response.data
  }

<<<<<<< HEAD
  async getPlan(
    id: string,
  ): Promise<
    ApiResponse<{ id: string; title: string; description: string; requirements: string[] }>
  > {
=======
  async getPlan(id: string): Promise<ApiResponse<{ id: string; title: string; description: string; requirements: string[] }>> {
>>>>>>> main
    const response = await this.client.get(`/api/plans/${id}`)
    return response.data
  }

  // Git Worktree endpoints
  async createWorktree(data: {
    repository: string
    branch: string
    name: string
  }): Promise<ApiResponse<{ id: string; path: string; status: string }>> {
    const response = await this.client.post('/api/git/create', data)
    return response.data
  }

<<<<<<< HEAD
  async getWorktrees(): Promise<
    ApiResponse<Array<{ id: string; repository: string; branch: string; name: string }>>
  > {
=======
  async getWorktrees(): Promise<ApiResponse<Array<{ id: string; repository: string; branch: string; name: string }>>> {
>>>>>>> main
    const response = await this.client.get('/api/git/list')
    return response.data
  }

  // Workflow Orchestrator endpoints
  async createWorkflow(data: {
    name: string
    description: string
    steps: Array<{ id: string; name: string; type: string }>
  }): Promise<ApiResponse<{ id: string; name: string; status: string }>> {
    const response = await this.client.post('/api/workflows/create', data)
    return response.data
  }

<<<<<<< HEAD
  async executeWorkflow(
    id: string,
  ): Promise<ApiResponse<{ id: string; status: string; result: unknown }>> {
=======
  async executeWorkflow(id: string): Promise<ApiResponse<{ id: string; status: string; result: unknown }>> {
>>>>>>> main
    const response = await this.client.post(`/api/workflows/${id}/execute`)
    return response.data
  }

<<<<<<< HEAD
  async getWorkflows(): Promise<
    ApiResponse<Array<{ id: string; name: string; description: string; status: string }>>
  > {
=======
  async getWorkflows(): Promise<ApiResponse<Array<{ id: string; name: string; description: string; status: string }>>> {
>>>>>>> main
    const response = await this.client.get('/api/workflows')
    return response.data
  }

  // Verification Feedback endpoints
  async submitFeedback(data: {
    type: string
    title: string
    description: string
    metadata?: Record<string, unknown>
  }): Promise<ApiResponse<{ id: string; status: string }>> {
    const response = await this.client.post('/api/feedback/submit', data)
    return response.data
  }

<<<<<<< HEAD
  async getFeedback(): Promise<
    ApiResponse<Array<{ id: string; type: string; title: string; status: string }>>
  > {
=======
  async getFeedback(): Promise<ApiResponse<Array<{ id: string; type: string; title: string; status: string }>>> {
>>>>>>> main
    const response = await this.client.get('/api/feedback/list')
    return response.data
  }

  // Chat endpoints
  async createChatSession(title?: string): Promise<ApiResponse<ChatSession>> {
    const response = await this.client.post('/api/chat/sessions', { title })
    return response.data
  }

  async getChatSessions(): Promise<ApiResponse<ChatSession[]>> {
    const response = await this.client.get('/api/chat/sessions')
    return response.data
  }

<<<<<<< HEAD
  async sendChatMessage(
    sessionId: string,
    message: string,
  ): Promise<ApiResponse<{ id: string; content: string; role: string; timestamp: Date }>> {
=======
  async sendChatMessage(sessionId: string, message: string): Promise<ApiResponse<{ id: string; content: string; role: string; timestamp: Date }>> {
>>>>>>> main
    const response = await this.client.post(`/api/chat/sessions/${sessionId}/messages`, {
      content: message,
    })
    return response.data
  }

  // Support endpoints
  async createTicket(data: {
    title: string
    description: string
    priority: 'low' | 'medium' | 'high' | 'urgent'
  }): Promise<ApiResponse<SupportTicket>> {
    const response = await this.client.post('/api/support/tickets', data)
    return response.data
  }

  async getTickets(): Promise<ApiResponse<SupportTicket[]>> {
    const response = await this.client.get('/api/support/tickets')
    return response.data
  }

  async updateTicket(
    id: string,
    data: Partial<SupportTicket>,
  ): Promise<ApiResponse<SupportTicket>> {
    const response = await this.client.patch(`/api/support/tickets/${id}`, data)
    return response.data
  }

  // Billing endpoints
  async getSubscription(): Promise<ApiResponse<Subscription>> {
    const response = await this.client.get('/api/billing/subscription')
    return response.data
  }

  async updateSubscription(planId: string): Promise<ApiResponse<Subscription>> {
    const response = await this.client.post('/api/billing/subscription/update', { planId })
    return response.data
  }

  async getInvoices(): Promise<ApiResponse<Invoice[]>> {
    const response = await this.client.get('/api/billing/invoices')
    return response.data
  }

  async downloadInvoice(invoiceId: string): Promise<Blob> {
    const response = await this.client.get(`/api/billing/invoices/${invoiceId}/pdf`, {
      responseType: 'blob',
    })
    return response.data
  }

  // Video Library endpoints
<<<<<<< HEAD
  async getVideos(): Promise<
    ApiResponse<Array<{ id: string; title: string; description: string; duration: number }>>
  > {
=======
  async getVideos(): Promise<ApiResponse<Array<{ id: string; title: string; description: string; duration: number }>>> {
>>>>>>> main
    const response = await this.client.get('/api/videos')
    return response.data
  }

<<<<<<< HEAD
  async getVideo(
    id: string,
  ): Promise<ApiResponse<{ id: string; title: string; description: string; url: string }>> {
=======
  async getVideo(id: string): Promise<ApiResponse<{ id: string; title: string; description: string; url: string }>> {
>>>>>>> main
    const response = await this.client.get(`/api/videos/${id}`)
    return response.data
  }

  // Analytics endpoints
<<<<<<< HEAD
  async getAnalytics(
    timeRange: string,
  ): Promise<ApiResponse<{ metrics: Array<{ metric: string; value: number; change: number }> }>> {
=======
  async getAnalytics(timeRange: string): Promise<ApiResponse<{ metrics: Array<{ metric: string; value: number; change: number }> }>> {
>>>>>>> main
    const response = await this.client.get(`/api/analytics?range=${timeRange}`)
    return response.data
  }

<<<<<<< HEAD
  async getDashboardStats(): Promise<
    ApiResponse<{ users: number; subscriptions: number; revenue: number }>
  > {
=======
  async getDashboardStats(): Promise<ApiResponse<{ users: number; subscriptions: number; revenue: number }>> {
>>>>>>> main
    const response = await this.client.get('/api/analytics/dashboard')
    return response.data
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<{ status: string; timestamp: Date }>> {
    const response = await this.client.get('/health')
    return response.data
  }

  // System status
<<<<<<< HEAD
  async getSystemStatus(): Promise<
    ApiResponse<{ status: string; services: Record<string, string> }>
  > {
=======
  async getSystemStatus(): Promise<ApiResponse<{ status: string; services: Record<string, string> }>> {
>>>>>>> main
    const response = await this.client.get('/status')
    return response.data
  }
}

// Create singleton instance
export const apiClient = new ApiClient()

// Export individual service objects for better organization
export const authApi = {
  login: apiClient.login.bind(apiClient),
  register: apiClient.register.bind(apiClient),
  logout: apiClient.logout.bind(apiClient),
  getCurrentUser: apiClient.getCurrentUser.bind(apiClient),
}

export const modelApi = {
  routeRequest: apiClient.routeRequest.bind(apiClient),
  getAvailableModels: apiClient.getAvailableModels.bind(apiClient),
  getModelStats: apiClient.getModelStats.bind(apiClient),
  testClaudeConnection: apiClient.testClaudeConnection.bind(apiClient),
}

export const planApi = {
  createPlan: apiClient.createPlan.bind(apiClient),
  getPlans: apiClient.getPlans.bind(apiClient),
  getPlan: apiClient.getPlan.bind(apiClient),
}

export const gitApi = {
  createWorktree: apiClient.createWorktree.bind(apiClient),
  getWorktrees: apiClient.getWorktrees.bind(apiClient),
}

export const workflowApi = {
  createWorkflow: apiClient.createWorkflow.bind(apiClient),
  executeWorkflow: apiClient.executeWorkflow.bind(apiClient),
  getWorkflows: apiClient.getWorkflows.bind(apiClient),
}

export const feedbackApi = {
  submitFeedback: apiClient.submitFeedback.bind(apiClient),
  getFeedback: apiClient.getFeedback.bind(apiClient),
}

export const chatApi = {
  createChatSession: apiClient.createChatSession.bind(apiClient),
  getChatSessions: apiClient.getChatSessions.bind(apiClient),
  sendChatMessage: apiClient.sendChatMessage.bind(apiClient),
}

export const supportApi = {
  createTicket: apiClient.createTicket.bind(apiClient),
  getTickets: apiClient.getTickets.bind(apiClient),
  updateTicket: apiClient.updateTicket.bind(apiClient),
}

export const billingApi = {
  getSubscription: apiClient.getSubscription.bind(apiClient),
  updateSubscription: apiClient.updateSubscription.bind(apiClient),
  getInvoices: apiClient.getInvoices.bind(apiClient),
  downloadInvoice: apiClient.downloadInvoice.bind(apiClient),
}

// Export the axios instance for direct use
export const api = apiClient['client']

export default apiClient
