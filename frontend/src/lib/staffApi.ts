/**
 * Staff API client for backend integration
 */

import { api } from './api'
import type { SystemHealth } from '@/types'

// Base staff API URL
const STAFF_API_BASE = '/api/staff'

// Types
export interface User {
  id: string
  name: string
  email: string
  role: 'customer' | 'admin' | 'manager' | 'support' | 'content'
  status: 'active' | 'inactive' | 'suspended'
  plan: string
  last_active?: Date
  created_at: Date
  updated_at: Date
  total_spent: number
  api_calls: number
}

export interface UserCreate {
  name: string
  email: string
  role: 'customer' | 'admin' | 'manager' | 'support' | 'content'
  status?: 'active' | 'inactive' | 'suspended'
  password: string
}

export interface UserUpdate {
  name?: string
  email?: string
  role?: 'customer' | 'admin' | 'manager' | 'support' | 'content'
  status?: 'active' | 'inactive' | 'suspended'
}

export interface Ticket {
  id: string
  title: string
  description: string
  status: 'open' | 'in-progress' | 'waiting-customer' | 'resolved' | 'closed'
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: string
  customer: {
    name: string
    email: string
    plan: string
  }
  assigned_to?: string
  created_at: Date
  updated_at: Date
  response_time?: number
  message_count: number
}

export interface TicketCreate {
  title: string
  description: string
  priority: 'low' | 'medium' | 'high' | 'urgent'
  category: string
  customer_id: string
}

export interface TicketUpdate {
  title?: string
  description?: string
  status?: 'open' | 'in-progress' | 'waiting-customer' | 'resolved' | 'closed'
  priority?: 'low' | 'medium' | 'high' | 'urgent'
  category?: string
  assigned_to?: string
}

export interface SystemStats {
  total_users: number
  active_users: number
  total_subscriptions: number
  active_subscriptions: number
  open_tickets: number
  closed_tickets: number
  system_uptime: string
  avg_response_time: number
}

export interface DashboardData {
  system_stats: SystemStats
  recent_tickets: Ticket[]
  system_alerts: Array<{
    id: number
    type: string
    message: string
    time: string
  }>
  quick_actions: Array<{
    name: string
    description: string
    href: string
    icon: string
    color: string
  }>
}

export interface ListResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
}

export interface StaffResponse<T = unknown> {
  success: boolean
  message: string
  data?: T
  timestamp: string
}

// Staff API Service
export class StaffApiService {
  // Dashboard & Stats
  static async getDashboard(): Promise<DashboardData> {
    const response = await api.get(`${STAFF_API_BASE}/dashboard`)
    return response.data
  }

  static async getSystemStats(): Promise<SystemStats> {
    const response = await api.get(`${STAFF_API_BASE}/stats`)
    return response.data
  }

  static async getSystemHealth(): Promise<SystemHealth> {
    const response = await api.get(`${STAFF_API_BASE}/health/system`)
    return response.data
  }

  // User Management
  static async getUsers(params?: {
    page?: number
    per_page?: number
    role?: string
    status?: string
    search?: string
  }): Promise<ListResponse<User>> {
    const response = await api.get(`${STAFF_API_BASE}/users`, { params })
    return {
      items: response.data.users,
      total: response.data.total,
      page: response.data.page,
      per_page: response.data.per_page,
    }
  }

  static async getUser(id: string): Promise<User> {
    const response = await api.get(`${STAFF_API_BASE}/users/${id}`)
    return response.data
  }

  static async createUser(userData: UserCreate): Promise<StaffResponse> {
    const response = await api.post(`${STAFF_API_BASE}/users`, userData)
    return response.data
  }

  static async updateUser(id: string, userData: UserUpdate): Promise<StaffResponse> {
    const response = await api.put(`${STAFF_API_BASE}/users/${id}`, userData)
    return response.data
  }

  static async deleteUser(id: string): Promise<StaffResponse> {
    const response = await api.delete(`${STAFF_API_BASE}/users/${id}`)
    return response.data
  }

  static async suspendUser(id: string): Promise<StaffResponse> {
    const response = await api.patch(`${STAFF_API_BASE}/users/${id}/suspend`)
    return response.data
  }

  static async activateUser(id: string): Promise<StaffResponse> {
    const response = await api.patch(`${STAFF_API_BASE}/users/${id}/activate`)
    return response.data
  }

  // Ticket Management
  static async getTickets(params?: {
    page?: number
    per_page?: number
    status?: string
    priority?: string
    category?: string
    search?: string
  }): Promise<ListResponse<Ticket>> {
    const response = await api.get(`${STAFF_API_BASE}/tickets`, { params })
    return {
      items: response.data.tickets,
      total: response.data.total,
      page: response.data.page,
      per_page: response.data.per_page,
    }
  }

  static async getTicket(id: string): Promise<Ticket> {
    const response = await api.get(`${STAFF_API_BASE}/tickets/${id}`)
    return response.data
  }

  static async createTicket(ticketData: TicketCreate): Promise<StaffResponse> {
    const response = await api.post(`${STAFF_API_BASE}/tickets`, ticketData)
    return response.data
  }

  static async updateTicket(id: string, ticketData: TicketUpdate): Promise<StaffResponse> {
    const response = await api.put(`${STAFF_API_BASE}/tickets/${id}`, ticketData)
    return response.data
  }

  static async assignTicket(id: string, assignTo: string): Promise<StaffResponse> {
    const response = await api.patch(`${STAFF_API_BASE}/tickets/${id}/assign?assign_to=${assignTo}`)
    return response.data
  }

  static async updateTicketStatus(id: string, status: string): Promise<StaffResponse> {
    const response = await api.patch(`${STAFF_API_BASE}/tickets/${id}/status?new_status=${status}`)
    return response.data
  }

  static async updateTicketPriority(id: string, priority: string): Promise<StaffResponse> {
    const response = await api.patch(
      `${STAFF_API_BASE}/tickets/${id}/priority?new_priority=${priority}`,
    )
    return response.data
  }

  static async getTicketStats(): Promise<{
    total_tickets: number
    by_status: Record<string, number>
    avg_response_time: number
  }> {
    const response = await api.get(`${STAFF_API_BASE}/tickets/stats`)
    return response.data
  }
}

// React hooks for staff API
export function useStaffApi() {
  return StaffApiService
}

// Error handling helper
export function handleStaffApiError(error: unknown): string {
  const apiError = error as { response?: { data?: { message?: string }, status?: number }, message?: string }
  if (apiError.response?.data?.message) {
    return apiError.response.data.message
  }
  if (apiError.response?.status === 401) {
    return 'Unauthorized access. Please check your permissions.'
  }
  if (apiError.response?.status === 403) {
    return 'Forbidden. You do not have permission to perform this action.'
  }
  if (apiError.response?.status === 404) {
    return 'Resource not found.'
  }
  if (apiError.response?.status && apiError.response.status >= 500) {
    return 'Server error. Please try again later.'
  }
  return apiError.message || 'An unexpected error occurred.'
}
