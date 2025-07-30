import axios, { AxiosInstance, AxiosResponse } from 'axios'
import { ApiResponse, User, CodeRequest, ChatSession, SupportTicket, Subscription } from '@/types'

class ApiClient {
  private client: AxiosInstance
  private baseURL: string

  constructor() {
    this.baseURL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost'
    
    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    })

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.getAuthToken()
        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.handleUnauthorized()
        }
        return Promise.reject(error)
      }
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
  async login(email: string, password: string): Promise<ApiResponse<{ user: User; token: string }>> {
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

  // Model Router endpoints
  async routeRequest(prompt: string, options?: {
    model?: string
    temperature?: number
    maxTokens?: number
  }): Promise<ApiResponse<CodeRequest>> {
    const response = await this.client.post('/api/model/route', {
      text: prompt,
      ...options,
    })
    return response.data
  }

  async getModels(): Promise<ApiResponse<string[]>> {
    const response = await this.client.get('/api/model/models')
    return response.data
  }

  // Plan Management endpoints
  async createPlan(data: {
    title: string
    description: string
    requirements: string[]
  }): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/plans/create', data)
    return response.data
  }

  async getPlans(): Promise<ApiResponse<any[]>> {
    const response = await this.client.get('/api/plans')
    return response.data
  }

  async getPlan(id: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/plans/${id}`)
    return response.data
  }

  // Git Worktree endpoints
  async createWorktree(data: {
    repository: string
    branch: string
    name: string
  }): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/git/create', data)
    return response.data
  }

  async getWorktrees(): Promise<ApiResponse<any[]>> {
    const response = await this.client.get('/api/git/list')
    return response.data
  }

  // Workflow Orchestrator endpoints
  async createWorkflow(data: {
    name: string
    description: string
    steps: any[]
  }): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/workflows/create', data)
    return response.data
  }

  async executeWorkflow(id: string): Promise<ApiResponse<any>> {
    const response = await this.client.post(`/api/workflows/${id}/execute`)
    return response.data
  }

  async getWorkflows(): Promise<ApiResponse<any[]>> {
    const response = await this.client.get('/api/workflows')
    return response.data
  }

  // Verification Feedback endpoints
  async submitFeedback(data: {
    type: string
    title: string
    description: string
    metadata?: any
  }): Promise<ApiResponse<any>> {
    const response = await this.client.post('/api/feedback/submit', data)
    return response.data
  }

  async getFeedback(): Promise<ApiResponse<any[]>> {
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

  async sendChatMessage(sessionId: string, message: string): Promise<ApiResponse<any>> {
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

  async updateTicket(id: string, data: Partial<SupportTicket>): Promise<ApiResponse<SupportTicket>> {
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

  async getInvoices(): Promise<ApiResponse<any[]>> {
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
  async getVideos(): Promise<ApiResponse<any[]>> {
    const response = await this.client.get('/api/videos')
    return response.data
  }

  async getVideo(id: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/videos/${id}`)
    return response.data
  }

  // Analytics endpoints
  async getAnalytics(timeRange: string): Promise<ApiResponse<any>> {
    const response = await this.client.get(`/api/analytics?range=${timeRange}`)
    return response.data
  }

  async getDashboardStats(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/api/analytics/dashboard')
    return response.data
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<any>> {
    const response = await this.client.get('/health')
    return response.data
  }

  // System status
  async getSystemStatus(): Promise<ApiResponse<any>> {
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
  getModels: apiClient.getModels.bind(apiClient),
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