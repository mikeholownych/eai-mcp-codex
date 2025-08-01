'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useTickets, useTicketActions, useTicketStats } from '@/hooks/useStaff'
import { Ticket } from '@/lib/staffApi'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { debug } from '@/lib/utils'
import {
  LifebuoyIcon,
  MagnifyingGlassIcon,
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  UserCircleIcon,
  TagIcon,
  ChatBubbleBottomCenterTextIcon,
  ArrowRightIcon,
  FunnelIcon,
} from '@heroicons/react/24/outline'


const priorityColors: Record<string, string> = {
  urgent: 'bg-red-500/10 text-red-400 border-red-500/20',
  high: 'bg-orange-500/10 text-orange-400 border-orange-500/20',
  medium: 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20',
  low: 'bg-green-500/10 text-green-400 border-green-500/20',
}

const getPriorityColor = (priority: string) =>
  priorityColors[priority] ?? 'bg-gray-500/10 text-gray-400 border-gray-500/20'

const statusColors: Record<string, string> = {
  open: 'bg-blue-500/10 text-blue-400',
  'in-progress': 'bg-yellow-500/10 text-yellow-400',
  'waiting-customer': 'bg-purple-500/10 text-purple-400',
  resolved: 'bg-green-500/10 text-green-400',
  closed: 'bg-gray-500/10 text-gray-400',
}

const getStatusColor = (status: string) => statusColors[status] ?? 'bg-gray-500/10 text-gray-400'

const statusIcons: Record<string, JSX.Element> = {
  open: <ClockIcon className="h-4 w-4" />,
  'in-progress': <ExclamationTriangleIcon className="h-4 w-4" />,
  'waiting-customer': <ClockIcon className="h-4 w-4" />,
  resolved: <CheckCircleIcon className="h-4 w-4" />,
  closed: <CheckCircleIcon className="h-4 w-4" />,
}

const getStatusIcon = (status: string) => statusIcons[status] ?? <ClockIcon className="h-4 w-4" />

const categories = [
  'All Categories',
  'API',
  'Billing',
  'Performance',
  'Bug Report',
  'Feature Request',
  'Account',
  'Security',
  'General'
]

export default function StaffTicketManagement() {
  const { user } = useAuth()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [selectedPriority, setSelectedPriority] = useState<string>('all')
  const [selectedCategory, setSelectedCategory] = useState<string>('All Categories')
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [currentPage, setCurrentPage] = useState(1)

  // Build filters for API call
  const filters = {
    page: currentPage,
    per_page: 20,
    status: selectedStatus === 'all' ? undefined : selectedStatus,
    priority: selectedPriority === 'all' ? undefined : selectedPriority,
    category: selectedCategory === 'All Categories' ? undefined : selectedCategory,
    search: searchTerm || undefined
  }

  const { tickets, total, loading, error, refetch } = useTickets(filters)
  const { stats: ticketStats, loading: statsLoading } = useTicketStats()
  const { assignTicket, updateTicketStatus, updateTicketPriority, loading: actionLoading } = useTicketActions()

  // Check if user has permission to view tickets
  if (!user || !['admin', 'manager', 'support'].includes(user.role)) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
        <p className="mt-1 text-sm text-gray-400">
          You don't have permission to access support tickets.
        </p>
      </div>
    )
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-white"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-white">Error Loading Tickets</h3>
        <p className="mt-1 text-sm text-gray-400">{error}</p>
        <Button variant="outline" className="mt-4" onClick={refetch}>
          Try Again
        </Button>
      </div>
    )
  }

  const handleAssignTicket = async (ticketId: string, assignTo: string) => {
    try {
      await assignTicket(ticketId, assignTo)
      refetch() // Refresh the tickets list
    } catch (error) {
      debug('Failed to assign ticket', error)
      alert('Failed to assign ticket')
    }
  }

  const handleUpdateStatus = async (ticketId: string, newStatus: string) => {
    try {
      await updateTicketStatus(ticketId, newStatus)
      refetch() // Refresh the tickets list
      if (selectedTicket && selectedTicket.id === ticketId) {
        // Update the selected ticket status for immediate UI feedback
        setSelectedTicket({ ...selectedTicket, status: newStatus as any })
      }
    } catch (error) {
      debug('Failed to update ticket status', error)
      alert('Failed to update ticket status')
    }
  }

  const handleUpdatePriority = async (ticketId: string, newPriority: string) => {
    try {
      await updateTicketPriority(ticketId, newPriority)
      refetch() // Refresh the tickets list
      if (selectedTicket && selectedTicket.id === ticketId) {
        // Update the selected ticket priority for immediate UI feedback
        setSelectedTicket({ ...selectedTicket, priority: newPriority as any })
      }
    } catch (error) {
      debug('Failed to update ticket priority', error)
      alert('Failed to update ticket priority')
    }
  }

  const handleViewTicket = (ticket: Ticket) => {
    setSelectedTicket(ticket)
  }

  if (selectedTicket) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <Button
            variant="outline"
            onClick={() => setSelectedTicket(null)}
          >
            ← Back to Tickets
          </Button>
          <div className="flex items-center space-x-3">
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(selectedTicket.status)}`}>
              {getStatusIcon(selectedTicket.status)}
              <span className="ml-1">{selectedTicket.status.replace('-', ' ').toUpperCase()}</span>
            </span>
            <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium border ${getPriorityColor(selectedTicket.priority)}`}>
              {selectedTicket.priority.toUpperCase()}
            </span>
          </div>
        </div>

        <Card className="p-6">
          <div className="space-y-6">
            <div>
              <h1 className="text-2xl font-bold text-white mb-2">{selectedTicket.title}</h1>
              <p className="text-gray-400">{selectedTicket.id}</p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
                  <h3 className="text-sm font-medium text-gray-300 mb-2">Description</h3>
                  <p className="text-white">{selectedTicket.description}</p>
                </div>

                <div className="bg-slate-700/50 rounded-lg p-4">
                  <h3 className="text-sm font-medium text-gray-300 mb-4">Conversation</h3>
                  <div className="space-y-4">
                    <div className="flex items-start space-x-3">
                      <UserCircleIcon className="h-8 w-8 text-gray-400 mt-1" />
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-1">
                          <span className="text-sm font-medium text-white">{selectedTicket.customer.name}</span>
                          <span className="text-xs text-gray-500">Customer</span>
                          <span className="text-xs text-gray-500">{new Date(selectedTicket.created_at).toLocaleString()}</span>
                        </div>
                        <div className="bg-slate-600 rounded-lg p-3">
                          <p className="text-sm text-white">{selectedTicket.description}</p>
                        </div>
                      </div>
                    </div>
                    
                    <div className="text-center text-sm text-gray-500">
                      {selectedTicket.message_count - 1} more messages...
                    </div>
                  </div>
                </div>
              </div>

              <div className="lg:col-span-1">
                <Card className="p-4">
                  <h3 className="text-sm font-medium text-gray-300 mb-4">Ticket Details</h3>
                  <div className="space-y-4">
                    <div>
                      <label className="text-xs text-gray-400">Customer</label>
                      <div className="mt-1">
                        <p className="text-sm text-white">{selectedTicket.customer.name}</p>
                        <p className="text-xs text-gray-400">{selectedTicket.customer.email}</p>
                        <span className="inline-flex items-center px-2 py-1 rounded text-xs bg-blue-500/10 text-blue-400 mt-1">
                          {selectedTicket.customer.plan}
                        </span>
                      </div>
                    </div>

                    <div>
                      <label className="text-xs text-gray-400">Category</label>
                      <div className="flex items-center mt-1">
                        <TagIcon className="h-4 w-4 text-gray-400 mr-2" />
                        <span className="text-sm text-white">{selectedTicket.category}</span>
                      </div>
                    </div>

                    <div>
                      <label className="text-xs text-gray-400">Assigned To</label>
                      <p className="text-sm text-white mt-1">{selectedTicket.assigned_to || 'Unassigned'}</p>
                    </div>

                    <div>
                      <label className="text-xs text-gray-400">Created</label>
                      <p className="text-sm text-white mt-1">{new Date(selectedTicket.created_at).toLocaleDateString()}</p>
                    </div>

                    <div>
                      <label className="text-xs text-gray-400">Last Updated</label>
                      <p className="text-sm text-white mt-1">{new Date(selectedTicket.updated_at).toLocaleDateString()}</p>
                    </div>

                    {selectedTicket.response_time && (
                      <div>
                        <label className="text-xs text-gray-400">Response Time</label>
                        <p className="text-sm text-white mt-1">{selectedTicket.response_time}h</p>
                      </div>
                    )}
                  </div>

                  <div className="mt-6 space-y-2">
                    <Button variant="primary" size="sm" className="w-full">
                      Reply to Customer
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      disabled={actionLoading}
                      onClick={() => {
                        const nextStatus = selectedTicket.status === 'open' ? 'in-progress' : 
                                          selectedTicket.status === 'in-progress' ? 'resolved' :
                                          selectedTicket.status === 'resolved' ? 'closed' : 'open'
                        handleUpdateStatus(selectedTicket.id, nextStatus)
                      }}
                    >
                      {actionLoading ? 'Updating...' : 'Update Status'}
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                      disabled={actionLoading}
                      onClick={() => handleAssignTicket(selectedTicket.id, user?.name || 'Current User')}
                    >
                      {actionLoading ? 'Assigning...' : 'Assign to Me'}
                    </Button>
                  </div>
                </Card>
              </div>
            </div>
          </div>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Support Tickets</h1>
        <p className="text-gray-400">Manage and respond to customer support requests</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <LifebuoyIcon className="h-8 w-8 text-blue-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Total Tickets</p>
              <p className="text-2xl font-semibold text-white">
                {statsLoading ? '-' : (ticketStats?.total_tickets || 0)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="h-8 w-8 text-yellow-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Open Tickets</p>
              <p className="text-2xl font-semibold text-white">
                {statsLoading ? '-' : (ticketStats?.by_status?.open || 0)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-8 w-8 text-orange-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">In Progress</p>
              <p className="text-2xl font-semibold text-white">
                {statsLoading ? '-' : (ticketStats?.by_status?.['in-progress'] || 0)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-8 w-8 text-green-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Avg Response</p>
              <p className="text-2xl font-semibold text-white">
                {statsLoading ? '-' : `${(ticketStats?.avg_response_time || 0).toFixed(1)}h`}
              </p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search tickets..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            />
          </div>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="all">All Status</option>
            <option value="open">Open</option>
            <option value="in-progress">In Progress</option>
            <option value="waiting-customer">Waiting Customer</option>
            <option value="resolved">Resolved</option>
            <option value="closed">Closed</option>
          </select>

          <select
            value={selectedPriority}
            onChange={(e) => setSelectedPriority(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="all">All Priority</option>
            <option value="urgent">Urgent</option>
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>

          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            {categories.map((category) => (
              <option key={category} value={category}>{category}</option>
            ))}
          </select>

          <div className="text-sm text-gray-400 flex items-center">
            {tickets.length} of {total} tickets
          </div>
        </div>
      </Card>

      {/* Tickets List */}
      <div className="space-y-4">
        {tickets.map((ticket) => (
          <Card key={ticket.id} className="p-6 hover:bg-slate-700/30 transition-colors cursor-pointer" onClick={() => handleViewTicket(ticket)}>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h3 className="text-lg font-semibold text-white">{ticket.title}</h3>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(ticket.status)}`}>
                    {getStatusIcon(ticket.status)}
                    <span className="ml-1">{ticket.status.replace('-', ' ')}</span>
                  </span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium border ${getPriorityColor(ticket.priority)}`}>
                    {ticket.priority.toUpperCase()}
                  </span>
                </div>
                
                <p className="text-gray-400 mb-3 line-clamp-2">{ticket.description}</p>
                
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-500">
                  <div className="flex items-center">
                    <UserCircleIcon className="h-4 w-4 mr-1" />
                    <span>{ticket.customer.name}</span>
                  </div>
                  <div className="flex items-center">
                    <TagIcon className="h-4 w-4 mr-1" />
                    <span>{ticket.category}</span>
                  </div>
                  <div className="flex items-center">
                    <ClockIcon className="h-4 w-4 mr-1" />
                    <span>{new Date(ticket.created_at).toLocaleDateString()}</span>
                  </div>
                  <div className="flex items-center">
                    <ChatBubbleBottomCenterTextIcon className="h-4 w-4 mr-1" />
                    <span>{ticket.message_count} messages</span>
                  </div>
                </div>
              </div>
              
              <ArrowRightIcon className="h-5 w-5 text-gray-400 ml-4" />
            </div>
          </Card>
        ))}
      </div>

      {tickets.length === 0 && !loading && (
        <Card className="p-12 text-center">
          <LifebuoyIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No tickets found</h3>
          <p className="text-gray-400">
            No support tickets match your current filters.
          </p>
        </Card>
      )}
    </div>
  )
}