/**
 * React hooks for staff functionality
 */

<<<<<<< HEAD
import { useState, useEffect, useCallback } from "react";
import type { SystemHealth } from "@/types";
import {
  StaffApiService,
  User,
  Ticket,
  SystemStats,
  DashboardData,
=======
import { useState, useEffect, useCallback } from 'react'
import type { SystemHealth } from '@/types'
import { 
  StaffApiService, 
  User, 
  Ticket, 
  SystemStats, 
  DashboardData, 
>>>>>>> main
  handleStaffApiError,
  UserCreate,
  UserUpdate,
  TicketCreate,
<<<<<<< HEAD
  TicketUpdate,
} from "../lib/staffApi";

// Dashboard Hook
export function useStaffDashboard() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const dashboardData = await StaffApiService.getDashboard();
      setData(dashboardData);
    } catch (err) {
      setError(handleStaffApiError(err as unknown));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  return { data, loading, error, refetch: fetchDashboard };
=======
  TicketUpdate
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
>>>>>>> main
}

// System Stats Hook
export function useSystemStats() {
<<<<<<< HEAD
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const systemStats = await StaffApiService.getSystemStats();
      setStats(systemStats);
    } catch (err) {
      setError(handleStaffApiError(err as unknown));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
=======
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
>>>>>>> main
}

// System Health Hook
export function useSystemHealth() {
<<<<<<< HEAD
  const [health, setHealth] = useState<SystemHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchHealth = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const systemHealth = await StaffApiService.getSystemHealth();
      setHealth(systemHealth);
    } catch (err) {
      setError(handleStaffApiError(err as unknown));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHealth();
  }, [fetchHealth]);

  return { health, loading, error, refetch: fetchHealth };
=======
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
>>>>>>> main
}

// Users Hook
export function useUsers(filters?: {
<<<<<<< HEAD
  page?: number;
  per_page?: number;
  role?: string;
  status?: string;
  search?: string;
}) {
  const [users, setUsers] = useState<User[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUsers = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.getUsers(filters);
      setUsers(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(handleStaffApiError(err as unknown));
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  return { users, total, loading, error, refetch: fetchUsers };
=======
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
>>>>>>> main
}

// Single User Hook
export function useUser(id: string | null) {
<<<<<<< HEAD
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchUser = useCallback(async () => {
    if (!id) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const userData = await StaffApiService.getUser(id);
      setUser(userData);
    } catch (err) {
      setError(handleStaffApiError(err as unknown));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  return { user, loading, error, refetch: fetchUser };
=======
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
>>>>>>> main
}

// User Actions Hook
export function useUserActions() {
<<<<<<< HEAD
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createUser = async (userData: UserCreate) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.createUser(userData);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateUser = async (id: string, userData: UserUpdate) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.updateUser(id, userData);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const deleteUser = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.deleteUser(id);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const suspendUser = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.suspendUser(id);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const activateUser = async (id: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.activateUser(id);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
=======
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
>>>>>>> main

  return {
    createUser,
    updateUser,
    deleteUser,
    suspendUser,
    activateUser,
    loading,
    error,
<<<<<<< HEAD
    clearError: () => setError(null),
  };
=======
    clearError: () => setError(null)
  }
>>>>>>> main
}

// Tickets Hook
export function useTickets(filters?: {
<<<<<<< HEAD
  page?: number;
  per_page?: number;
  status?: string;
  priority?: string;
  category?: string;
  search?: string;
}) {
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTickets = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.getTickets(filters);
      setTickets(response.items);
      setTotal(response.total);
    } catch (err) {
      setError(handleStaffApiError(err as unknown));
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchTickets();
  }, [fetchTickets]);

  return { tickets, total, loading, error, refetch: fetchTickets };
=======
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
>>>>>>> main
}

// Single Ticket Hook
export function useTicket(id: string | null) {
<<<<<<< HEAD
  const [ticket, setTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTicket = useCallback(async () => {
    if (!id) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const ticketData = await StaffApiService.getTicket(id);
      setTicket(ticketData);
    } catch (err) {
      setError(handleStaffApiError(err as unknown));
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchTicket();
  }, [fetchTicket]);

  return { ticket, loading, error, refetch: fetchTicket };
=======
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
>>>>>>> main
}

// Ticket Actions Hook
export function useTicketActions() {
<<<<<<< HEAD
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createTicket = async (ticketData: TicketCreate) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.createTicket(ticketData);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateTicket = async (id: string, ticketData: TicketUpdate) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.updateTicket(id, ticketData);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const assignTicket = async (id: string, assignTo: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.assignTicket(id, assignTo);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateTicketStatus = async (id: string, status: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.updateTicketStatus(id, status);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const updateTicketPriority = async (id: string, priority: string) => {
    try {
      setLoading(true);
      setError(null);
      const response = await StaffApiService.updateTicketPriority(id, priority);
      return response;
    } catch (err) {
      const errorMessage = handleStaffApiError(err);
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  };
=======
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
>>>>>>> main

  return {
    createTicket,
    updateTicket,
    assignTicket,
    updateTicketStatus,
    updateTicketPriority,
    loading,
    error,
<<<<<<< HEAD
    clearError: () => setError(null),
  };
=======
    clearError: () => setError(null)
  }
>>>>>>> main
}

// Ticket Stats Hook
export function useTicketStats() {
<<<<<<< HEAD
  const [stats, setStats] = useState<{
    total_tickets: number;
    by_status: Record<string, number>;
    avg_response_time: number;
  } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const ticketStats = await StaffApiService.getTicketStats();
      setStats(ticketStats);
    } catch (err) {
      setError(handleStaffApiError(err as unknown));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
}
=======
  const [stats, setStats] = useState<{ total_tickets: number; by_status: Record<string, number>; avg_response_time: number } | null>(null)
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
>>>>>>> main
