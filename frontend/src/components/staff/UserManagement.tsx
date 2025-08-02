'use client'

import React, { useState, useMemo } from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import Select from '@/components/ui/Select'
import Badge from '@/components/ui/Badge'
import Modal from '@/components/ui/Modal'
import { useUsers, useUserActions } from '@/hooks/useStaff'
import { User, UserCreate, UserUpdate } from '@/lib/staffApi'

const UserManagement: React.FC = () => {
  const { users, total, loading, error, refetch } = useUsers()
  const { createUser, updateUser, deleteUser, suspendUser, activateUser, loading: actionLoading } = useUserActions()
  
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [roleFilter, setRoleFilter] = useState('')
  const [selectedUser, setSelectedUser] = useState<User | null>(null)
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  const [isEditModalOpen, setIsEditModalOpen] = useState(false)
  
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: 'customer' as const,
    status: 'active' as const,
    password: ''
  })

  const filteredUsers = useMemo(() => {
    return users.filter(user => {
      const matchesSearch = user.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                           user.email.toLowerCase().includes(searchTerm.toLowerCase())
      const matchesStatus = !statusFilter || user.status === statusFilter
      const matchesRole = !roleFilter || user.role === roleFilter
      
      return matchesSearch && matchesStatus && matchesRole
    })
  }, [users, searchTerm, statusFilter, roleFilter])

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-500/20 text-green-400 border-green-500/30'
      case 'inactive': return 'bg-slate-600 text-slate-300'
      case 'suspended': return 'bg-red-500/20 text-red-400 border-red-500/30'
      default: return 'bg-slate-600 text-slate-300'
    }
  }

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin': return 'bg-blue-500/20 text-blue-400 border-blue-500/30'
      case 'manager': return 'bg-purple-500/20 text-purple-400 border-purple-500/30'
      case 'support': return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'content': return 'bg-green-500/20 text-green-400 border-green-500/30'
      default: return 'bg-slate-600 text-slate-300'
    }
  }

  const handleCreateUser = async () => {
    try {
      await createUser(formData as UserCreate)
      setIsCreateModalOpen(false)
      setFormData({ name: '', email: '', role: 'customer', status: 'active', password: '' })
      refetch()
    } catch (error) {
      console.error('Failed to create user:', error)
    }
  }

  const handleUpdateUser = async () => {
    if (!selectedUser) return
    
    try {
      await updateUser(selectedUser.id, formData as UserUpdate)
      setIsEditModalOpen(false)
      setSelectedUser(null)
      setFormData({ name: '', email: '', role: 'customer', status: 'active', password: '' })
      refetch()
    } catch (error) {
      console.error('Failed to update user:', error)
    }
  }

  const openEditModal = (user: User) => {
    setSelectedUser(user)
    setFormData({
      name: user.name,
      email: user.email,
      role: user.role,
      status: user.status,
      password: ''
    })
    setIsEditModalOpen(true)
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount)
  }

  const formatDate = (date: Date) => {
    return new Date(date).toLocaleDateString()
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">User Management</h1>
          <p className="text-slate-400">Manage customer accounts and access permissions</p>
        </div>
        <Button onClick={() => setIsCreateModalOpen(true)}>
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Add User
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Input
              placeholder="Search users..."
              value={searchTerm}
              onChange={(value) => setSearchTerm(value)}
            />
            <Select
              placeholder="Filter by status"
              value={statusFilter}
              onValueChange={(value) => setStatusFilter(value)}
              options={[
                { value: '', label: 'All Status' },
                { value: 'active', label: 'Active' },
                { value: 'inactive', label: 'Inactive' },
                { value: 'suspended', label: 'Suspended' }
              ]}
            />
            <Select
              placeholder="Filter by role"
              value={roleFilter}
              onValueChange={(value) => setRoleFilter(value)}
              options={[
                { value: '', label: 'All Roles' },
                { value: 'customer', label: 'Customer' },
                { value: 'admin', label: 'Admin' },
                { value: 'manager', label: 'Manager' },
                { value: 'support', label: 'Support' },
                { value: 'content', label: 'Content' }
              ]}
            />
          </div>
        </CardContent>
      </Card>

      {/* Users Table */}
      <Card>
        <CardContent>
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            </div>
          ) : error ? (
            <div className="text-center py-12">
              <h2 className="text-xl font-semibold text-red-400 mb-2">Error Loading Users</h2>
              <p className="text-slate-400">{error}</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-700">
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">User</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Role</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Status</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Plan</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Spent</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">API Calls</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Joined</th>
                    <th className="text-left py-3 px-4 text-sm font-medium text-slate-300">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredUsers.map((user) => (
                    <tr key={user.id} className="border-b border-slate-700 hover:bg-slate-700/50">
                      <td className="py-3 px-4">
                        <div>
                          <div className="font-medium text-white">{user.name}</div>
                          <div className="text-sm text-slate-400">{user.email}</div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="secondary" size="sm" className={getRoleColor(user.role)}>
                          {user.role}
                        </Badge>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="secondary" size="sm" className={getStatusColor(user.status)}>
                          {user.status}
                        </Badge>
                      </td>
                      <td className="py-3 px-4 text-slate-300">{user.plan}</td>
                      <td className="py-3 px-4 text-slate-300">{formatCurrency(user.total_spent)}</td>
                      <td className="py-3 px-4 text-slate-300">{user.api_calls.toLocaleString()}</td>
                      <td className="py-3 px-4 text-slate-300">{formatDate(user.created_at)}</td>
                      <td className="py-3 px-4">
                        <div className="flex items-center space-x-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => openEditModal(user)}
                            className="p-1"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </Button>
                          {user.status === 'active' ? (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => suspendUser(user.id)}
                              className="p-1 text-red-400 hover:text-red-300"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                              </svg>
                            </Button>
                          ) : (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => activateUser(user.id)}
                              className="p-1 text-green-400 hover:text-green-300"
                            >
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                              </svg>
                            </Button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create User Modal */}
      <Modal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        title="Create New User"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Full Name"
            placeholder="Enter user's full name"
            value={formData.name}
            onChange={(value) => setFormData(prev => ({ ...prev, name: value }))}
            required
          />
          <Input
            label="Email Address"
            placeholder="Enter email address"
            type="email"
            value={formData.email}
            onChange={(value) => setFormData(prev => ({ ...prev, email: value }))}
            required
          />
          <Select
            label="Role"
            value={formData.role}
            onValueChange={(value) => setFormData(prev => ({ ...prev, role: value as any }))}
            options={[
              { value: 'customer', label: 'Customer' },
              { value: 'admin', label: 'Admin' },
              { value: 'manager', label: 'Manager' },
              { value: 'support', label: 'Support' },
              { value: 'content', label: 'Content' }
            ]}
            required
          />
          <Select
            label="Status"
            value={formData.status}
            onValueChange={(value) => setFormData(prev => ({ ...prev, status: value as any }))}
            options={[
              { value: 'active', label: 'Active' },
              { value: 'inactive', label: 'Inactive' },
              { value: 'suspended', label: 'Suspended' }
            ]}
            required
          />
          <Input
            label="Password"
            placeholder="Enter password"
            type="password"
            value={formData.password}
            onChange={(value) => setFormData(prev => ({ ...prev, password: value }))}
            required
          />
          <div className="flex justify-end space-x-3 pt-4">
            <Button variant="outline" onClick={() => setIsCreateModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateUser} loading={actionLoading}>
              Create User
            </Button>
          </div>
        </div>
      </Modal>

      {/* Edit User Modal */}
      <Modal
        isOpen={isEditModalOpen}
        onClose={() => setIsEditModalOpen(false)}
        title="Edit User"
        size="md"
      >
        <div className="space-y-4">
          <Input
            label="Full Name"
            placeholder="Enter user's full name"
            value={formData.name}
            onChange={(value) => setFormData(prev => ({ ...prev, name: value }))}
            required
          />
          <Input
            label="Email Address"
            placeholder="Enter email address"
            type="email"
            value={formData.email}
            onChange={(value) => setFormData(prev => ({ ...prev, email: value }))}
            required
          />
          <Select
            label="Role"
            value={formData.role}
            onValueChange={(value) => setFormData(prev => ({ ...prev, role: value as any }))}
            options={[
              { value: 'customer', label: 'Customer' },
              { value: 'admin', label: 'Admin' },
              { value: 'manager', label: 'Manager' },
              { value: 'support', label: 'Support' },
              { value: 'content', label: 'Content' }
            ]}
            required
          />
          <Select
            label="Status"
            value={formData.status}
            onValueChange={(value) => setFormData(prev => ({ ...prev, status: value as any }))}
            options={[
              { value: 'active', label: 'Active' },
              { value: 'inactive', label: 'Inactive' },
              { value: 'suspended', label: 'Suspended' }
            ]}
            required
          />
          <div className="flex justify-end space-x-3 pt-4">
            <Button variant="outline" onClick={() => setIsEditModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleUpdateUser} loading={actionLoading}>
              Update User
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}

export default UserManagement