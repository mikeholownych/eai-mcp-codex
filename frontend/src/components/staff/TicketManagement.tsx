'use client'

import React, { useState, useMemo } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import { useTickets, useTicketActions, useTicketStats } from '@/hooks/useStaff'
import { Ticket, TicketCreate, TicketUpdate } from '@/lib/staffApi'

const TicketManagement: React.FC = () => {
  const { tickets, loading, error, refetch } = useTickets()
  const {
    createTicket,
    updateTicket,
    updateTicketStatus,
    loading: actionLoading,
  } = useTicketActions()
  const { stats } = useTicketStats()

  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [priorityFilter, setPriorityFilter] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('')
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)

  const [formData, setFormData] = useState({
    title: '',
    description: '',
    priority: 'medium' as 'low' | 'medium' | 'high' | 'urgent',
    category: '',
    customer_id: '',
    assigned_to: '',
    status: 'open' as 'open' | 'in-progress' | 'waiting-customer' | 'resolved' | 'closed',
  })

  const filteredTickets = useMemo(() => {
    return tickets.filter(ticket => {
      const matchesSearch =
        ticket.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        ticket.description.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus = !statusFilter || ticket.status === statusFilter
      const matchesPriority = !priorityFilter || ticket.priority === priorityFilter
      const matchesCategory = !categoryFilter || ticket.category === categoryFilter

      return matchesSearch && matchesStatus && matchesPriority && matchesCategory
    })
  }, [tickets, searchTerm, statusFilter, priorityFilter, categoryFilter])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'open':
        return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'in-progress':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'waiting-customer':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'resolved':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'closed':
        return 'bg-slate-600 text-slate-300'
      default:
        return 'bg-slate-600 text-slate-300'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent':
        return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'high':
        return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'medium':
        return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'low':
        return 'bg-green-500/20 text-green-400 border-green-500/30'
      default:
        return 'bg-slate-600 text-slate-300'
    }
  }

  const handleCreateTicket = async () => {
    try {
      await createTicket(formData as TicketCreate)
      setIsCreateModalOpen(false)
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        category: '',
        customer_id: '',
        assigned_to: '',
        status: 'open',
      })
      refetch()
    } catch (error) {
      console.error('Failed to create ticket:', error)
    }
  }

  const handleUpdateTicket = async () => {
    if (!selectedTicket) return

    try {
      await updateTicket(selectedTicket.id, formData as TicketUpdate)
      setIsEditModalOpen(false)
      setSelectedTicket(null)
      setFormData({
        title: '',
        description: '',
        priority: 'medium',
        category: '',
        customer_id: '',
        assigned_to: '',
        status: 'open',
      })
      refetch()
    } catch (error) {
      console.error('Failed to update ticket:', error)
    }
  }

  const openEditModal = (ticket: Ticket) => {
    setSelectedTicket(ticket)
    setFormData({
      title: ticket.title,
      description: ticket.description,
      priority: ticket.priority as 'low' | 'medium' | 'high' | 'urgent',
      category: ticket.category,
      customer_id: '',
      assigned_to: ticket.assigned_to || '',
      status: ticket.status as 'open' | 'in-progress' | 'waiting-customer' | 'resolved' | 'closed',
    })
    setIsEditModalOpen(true)
  }

  const formatResponseTime = (responseTime?: number) => {
    if (!responseTime) return 'N/A'
    if (responseTime < 60) return `${Math.round(responseTime)}s`
    if (responseTime < 3600) return `${Math.round(responseTime / 60)}m`
    return `${Math.round(responseTime / 3600)}h`
  }

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Ticket Management</h1>
          <p className="text-slate-400">Manage customer support tickets and issues</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Create Ticket
        </Button>
      </div>

      {/* Stats Overview */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <div className="text-center">
              <p className="text-2xl font-bold text-white">{stats.total_tickets}</p>
              <p className="text-sm text-slate-400">Total Tickets</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-2xl font-bold text-orange-400">{stats.by_status?.open || 0}</p>
              <p className="text-sm text-slate-400">Open</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-2xl font-bold text-blue-400">
                {stats.by_status?.['in-progress'] || 0}
              </p>
              <p className="text-sm text-slate-400">In Progress</p>
            </div>
          </Card>
          <Card>
            <div className="text-center">
              <p className="text-2xl font-bold text-green-400">{stats.avg_response_time || 0}m</p>
              <p className="text-sm text-slate-400">Avg Response</p>
            </div>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Input
              placeholder="Search tickets..."
              value={searchTerm}
              onChange={value => setSearchTerm(value)}
            />
            <Select
              placeholder="Filter by status"
              value={statusFilter}
              onValueChange={value => setStatusFilter(value)}
              options={[
                { value: '', label: 'All Status' },
                { value: 'open', label: 'Open' },
                { value: 'in-progress', label: 'In Progress' },
                { value: 'waiting-customer', label: 'Waiting Customer' },
                { value: 'resolved', label: 'Resolved' },
                { value: 'closed', label: 'Closed' },
              ]}
            />
            <Select
              placeholder="Filter by priority"
              value={priorityFilter}
              onValueChange={value => setPriorityFilter(value)}
              options={[
                { value: '', label: 'All Priority' },
                { value: 'urgent', label: 'Urgent' },
                { value: 'high', label: 'High' },
                { value: 'medium', label: 'Medium' },
                { value: 'low', label: 'Low' },
              ]}
            />
            <Select
              placeholder="Filter by category"
              value={categoryFilter}
              onValueChange={value => setCategoryFilter(value)}
              options={[
                { value: '', label: 'All Categories' },
                { value: 'technical', label: 'Technical' },
                { value: 'billing', label: 'Billing' },
                { value: 'account', label: 'Account' },
                { value: 'feature', label: 'Feature Request' },
                { value: 'bug', label: 'Bug Report' },
              ]}
            />
          </div>
        </div>
      </Card>

      {/* Tickets Table */}
      <Card>
        <div className="p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold text-red-400 mb-2">Error Loading Tickets</h2>
              <p className="text-slate-400">{error}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Ticket
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Customer
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Priority
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Category
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Assigned
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Response Time
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Created
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {filteredTickets.map(ticket => (
                    <tr key={ticket.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                      <td className="py-3 px-4">
                        <div>
                          <div className="font-medium text-white">{ticket.title}</div>
                          <div className="text-sm text-slate-400">#{ticket.id}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <div>
                          <div className="font-medium text-white">{ticket.customer.name}</div>
                          <div className="text-sm text-slate-400">{ticket.customer.email}</div>
                          <div className="text-xs text-slate-500">{ticket.customer.plan}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant="secondary"
                          size="sm"
                          className={getPriorityColor(ticket.priority)}
                        >
                          {ticket.priority}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <Badge
                          variant="secondary"
                          size="sm"
                          className={getStatusColor(ticket.status)}
                        >
                          {ticket.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{ticket.category}</td>
                      <td className="py-3 px-4 text-slate-300">
                        {ticket.assigned_to || 'Unassigned'}
                      </td>
                      <td className="py-3 px-4 text-slate-300">
                        {formatResponseTime(ticket.response_time)}
                      </td>
                      <td className="py-3 px-4 text-slate-300">{formatDate(ticket.created_at)}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditModal(ticket)}
                            className="p-1"
                          >
                            <svg
                              className="w-4 h-4"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                              />
                            </svg>
                          </Button>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => updateTicketStatus(ticket.id, 'resolved')}
                            className="p-1 text-green-400 hover:text-green-300"
                            title="Mark as resolved"
                          >
                            <svg
                              className="w-4 h-4"
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                              />
                            </svg>
                          </Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </Card>

      {/* Create Ticket Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New Ticket"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Ticket Title"
            placeholder="Enter ticket title"
            value={formData.title}
            onChange={value => setFormData(prev => ({ ...prev, title: value }))}
            required
          />
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">Description</label>
            <textarea
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
              placeholder="Describe the issue or request..."
              value={formData.description}
              onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
            />
          </div>
          <Select
            label="Priority"
            value={formData.priority}
            onValueChange={value =>
              setFormData(prev => ({
                ...prev,
                priority: value as 'low' | 'medium' | 'high' | 'urgent',
              }))
            }
            options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'urgent', label: 'Urgent' },
            ]}
            required
          />
          <Input
            label="Category"
            placeholder="e.g., technical, billing, account"
            value={formData.category}
            onChange={value => setFormData(prev => ({ ...prev, category: value }))}
            required
          />
          <Input
            label="Customer ID"
            placeholder="Enter customer ID"
            value={formData.customer_id}
            onChange={value => setFormData(prev => ({ ...prev, customer_id: value }))}
            required
          />
          <div className="flex justify-end space-x-3 pt-4">
            <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateTicket} loading={actionLoading}>
              Create Ticket
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit Ticket Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit Ticket"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Ticket Title"
            placeholder="Enter ticket title"
            value={formData.title}
            onChange={value => setFormData(prev => ({ ...prev, title: value }))}
            required
          />
          <div className="space-y-2">
            <label className="block text-sm font-medium text-slate-300">Description</label>
            <textarea
              className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded-md text-slate-100 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={4}
              placeholder="Describe the issue or request..."
              value={formData.description}
              onChange={e => setFormData(prev => ({ ...prev, description: e.target.value }))}
            />
          </div>
          <Select
            label="Priority"
            value={formData.priority}
            onValueChange={value =>
              setFormData(prev => ({
                ...prev,
                priority: value as 'low' | 'medium' | 'high' | 'urgent',
              }))
            }
            options={[
              { value: 'low', label: 'Low' },
              { value: 'medium', label: 'Medium' },
              { value: 'high', label: 'High' },
              { value: 'urgent', label: 'Urgent' },
            ]}
            required
          />
          <Select
            label="Status"
            value={formData.status}
            onValueChange={value =>
              setFormData(prev => ({
                ...prev,
                status: value as
                  | 'open'
                  | 'in-progress'
                  | 'waiting-customer'
                  | 'resolved'
                  | 'closed',
              }))
            }
            options={[
              { value: 'open', label: 'Open' },
              { value: 'in-progress', label: 'In Progress' },
              { value: 'waiting-customer', label: 'Waiting Customer' },
              { value: 'resolved', label: 'Resolved' },
              { value: 'closed', label: 'Closed' },
            ]}
            required
          />
          <Input
            label="Category"
            placeholder="e.g., technical, billing, account"
            value={formData.category}
            onChange={value => setFormData(prev => ({ ...prev, category: value }))}
            required
          />
          <div className="flex justify-end space-x-3 pt-4">
            <Button variant="outline" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateTicket} loading={actionLoading}>
              Update Ticket
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default TicketManagement
