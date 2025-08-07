/**
 * React hooks for staff functionality
 */

import { useState, useEffect, useCallback } from 'react'
import type { SystemHealth } from '@/types'
import {
  StaffApiService,
  User,
  Ticket,
  SystemStats,
  DashboardData,
  handleStaffApiError,
  UserCreate,
  UserUpdate,
  TicketCreate,
  TicketUpdate,
} from '../lib/staffApi'

// Dashboard Hook
export function useStaffDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const dashboardData = await StaffApiService.getDashboard()
      setData(dashboardData)
    } catch (err) {
      setError(handleStaffApiError(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchDashboard()
  }, [fetchDashboard])

  return { data, loading, error, refetch: fetchDashboard }
}

// System Stats Hook
export function useSystemStats() {
  const [stats, setStats] = useState<SystemStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const systemStats = await StaffApiService.getSystemStats()
      setStats(systemStats)
    } catch (err) {
      setError(handleStaffApiError(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return { stats, loading, error, refetch: fetchStats }
}

// System Health Hook
export function useSystemHealth() {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const systemHealth = await StaffApiService.getSystemHealth()
      setHealth(systemHealth)
    } catch (err) {
      setError(handleStaffApiError(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchHealth()
  }, [fetchHealth])

  return { health, loading, error, refetch: fetchHealth }
}

// Users Hook
export function useUsers(filters?: {
  page?: number
  per_page?: number
  role?: string
  status?: string
  search?: string
}) {
  const [users, setUsers] = useState<User[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.getUsers(filters)
      setUsers(response.items)
      setTotal(response.total)
    } catch (err) {
      setError(handleStaffApiError(err))
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchUsers()
  }, [fetchUsers])

  return { users, total, loading, error, refetch: fetchUsers }
}

// Single User Hook
export function useUser(id: string | null) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchUser = useCallback(async () => {
    if (!id) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const userData = await StaffApiService.getUser(id)
      setUser(userData)
    } catch (err) {
      setError(handleStaffApiError(err))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  return { user, loading, error, refetch: fetchUser }
}

// User Actions Hook
export function useUserActions() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createUser = async (userData: UserCreate) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.createUser(userData)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const updateUser = async (id: string, userData: UserUpdate) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.updateUser(id, userData)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const deleteUser = async (id: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.deleteUser(id)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const suspendUser = async (id: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.suspendUser(id)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const activateUser = async (id: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.activateUser(id)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return {
    createUser,
    updateUser,
    deleteUser,
    suspendUser,
    activateUser,
    loading,
    error,
    clearError: () => setError(null),
  }
}

// Tickets Hook
export function useTickets(filters?: {
  page?: number
  per_page?: number
  status?: string
  priority?: string
  category?: string
  search?: string
}) {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTickets = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.getTickets(filters)
      setTickets(response.items)
      setTotal(response.total)
    } catch (err) {
      setError(handleStaffApiError(err))
    } finally {
      setLoading(false)
    }
  }, [filters])

  useEffect(() => {
    fetchTickets()
  }, [fetchTickets])

  return { tickets, total, loading, error, refetch: fetchTickets }
}

// Single Ticket Hook
export function useTicket(id: string | null) {
  const [ticket, setTicket] = useState<Ticket | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTicket = useCallback(async () => {
    if (!id) {
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const ticketData = await StaffApiService.getTicket(id)
      setTicket(ticketData)
    } catch (err) {
      setError(handleStaffApiError(err))
    } finally {
      setLoading(false)
    }
  }, [id])

  useEffect(() => {
    fetchTicket()
  }, [fetchTicket])

  return { ticket, loading, error, refetch: fetchTicket }
}

// Ticket Actions Hook
export function useTicketActions() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const createTicket = async (ticketData: TicketCreate) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.createTicket(ticketData)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const updateTicket = async (id: string, ticketData: TicketUpdate) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.updateTicket(id, ticketData)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const assignTicket = async (id: string, assignTo: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.assignTicket(id, assignTo)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const updateTicketStatus = async (id: string, status: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.updateTicketStatus(id, status)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  const updateTicketPriority = async (id: string, priority: string) => {
    try {
      setLoading(true)
      setError(null)
      const response = await StaffApiService.updateTicketPriority(id, priority)
      return response
    } catch (err) {
      const errorMessage = handleStaffApiError(err)
      setError(errorMessage)
      throw new Error(errorMessage)
    } finally {
      setLoading(false)
    }
  }

  return {
    createTicket,
    updateTicket,
    assignTicket,
    updateTicketStatus,
    updateTicketPriority,
    loading,
    error,
    clearError: () => setError(null),
  }
}

// Ticket Stats Hook
export function useTicketStats() {
  const [stats, setStats] = useState<{
    total_tickets: number
    by_status: Record<string, number>
    avg_response_time: number
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const ticketStats = await StaffApiService.getTicketStats()
      setStats(ticketStats)
    } catch (err) {
      setError(handleStaffApiError(err))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    fetchStats()
  }, [fetchStats])

  return { stats, loading, error, refetch: fetchStats }
}
