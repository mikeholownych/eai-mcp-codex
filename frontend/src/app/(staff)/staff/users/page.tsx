'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useUsers, useUserActions } from '@/hooks/useStaff'
import { User } from '@/lib/staffApi'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Input from '@/components/ui/Input'
import { useRouter } from 'next/navigation'
import { debug } from '@/lib/utils'
import { getUserStatusColor, getUserStatusIcon } from '@/lib/statusHelpers'
import {
  UserGroupIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  PencilIcon,
  TrashIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  EyeIcon,
  UserCircleIcon,
} from '@heroicons/react/24/outline'


const roleColors: Record<string, string> = {
  admin: 'bg-red-500/10 text-red-400',
  manager: 'bg-blue-500/10 text-blue-400',
  support: 'bg-green-500/10 text-green-400',
  content: 'bg-purple-500/10 text-purple-400',
  customer: 'bg-gray-500/10 text-gray-400',
}

const getRoleColor = (role: string) => roleColors[role] ?? 'bg-gray-500/10 text-gray-400'


export default function UserManagement() {
  const { user: currentUser } = useAuth()
  const router = useRouter()
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedRole, setSelectedRole] = useState<string>('all')
  const [selectedStatus, setSelectedStatus] = useState<string>('all')
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [userStats, setUserStats] = useState({
    total: 0,
    active: 0,
    staff: 0,
    suspended: 0
  })

  // Build filters for API call
  const filters = {
    page: currentPage,
    per_page: 20,
    role: selectedRole === 'all' ? undefined : selectedRole,
    status: selectedStatus === 'all' ? undefined : selectedStatus,
    search: searchTerm || undefined
  }

  const { users, total, loading, error, refetch } = useUsers(filters)
  const { suspendUser, activateUser, deleteUser, loading: actionLoading } = useUserActions()

  // Update stats when users change
  useEffect(() => {
    if (users) {
      setUserStats({
        total: total,
        active: users.filter(u => u.status === 'active').length,
        staff: users.filter(u => ['admin', 'manager', 'support', 'content'].includes(u.role)).length,
        suspended: users.filter(u => u.status === 'suspended').length
      })
    }
  }, [users, total])

  // Check if user has permission to manage users
  if (!currentUser || !['admin', 'manager'].includes(currentUser.role)) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
        <p className="mt-1 text-sm text-gray-400">
          You don&apos;t have permission to access user management.
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
        <h3 className="mt-2 text-sm font-medium text-white">Error Loading Users</h3>
        <p className="mt-1 text-sm text-gray-400">{error}</p>
        <Button variant="outline" className="mt-4" onClick={refetch}>
          Try Again
        </Button>
      </div>
    )
  }

  const handleCreateUser = () => {
    setShowCreateModal(true)
  }

  const handleEditUser = (userId: string) => {
    debug('Edit user', { userId })
    router.push(`/staff/users?edit=${userId}`)
  }

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user? This action cannot be undone.')) {
      return
    }
    
    try {
      await deleteUser(userId)
      refetch() // Refresh the users list
    } catch (error) {
      debug('Failed to delete user', error)
      alert('Failed to delete user')
    }
  }

  const handleSuspendUser = async (userId: string) => {
    const user = users.find(u => u.id === userId)
    if (!user) return

    try {
      if (user.status === 'suspended') {
        await activateUser(userId)
      } else {
        await suspendUser(userId)
      }
      refetch() // Refresh the users list
    } catch (error) {
      debug('Failed to update user status', error)
      alert('Failed to update user status')
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">User Management</h1>
          <p className="text-gray-400">Manage users, roles, and permissions</p>
        </div>
        
        <Button variant="primary" onClick={handleCreateUser}>
          <PlusIcon className="h-4 w-4 mr-2" />
          Create User
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <UserGroupIcon className="h-8 w-8 text-blue-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Total Users</p>
              <p className="text-2xl font-semibold text-white">{userStats.total.toLocaleString()}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="h-8 w-8 text-green-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Active Users</p>
              <p className="text-2xl font-semibold text-white">{userStats.active.toLocaleString()}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ShieldCheckIcon className="h-8 w-8 text-purple-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Staff Members</p>
              <p className="text-2xl font-semibold text-white">{userStats.staff.toLocaleString()}</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ExclamationTriangleIcon className="h-8 w-8 text-red-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Suspended</p>
              <p className="text-2xl font-semibold text-white">{userStats.suspended.toLocaleString()}</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Filters */}
      <Card className="p-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search users..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
            />
          </div>

          <select
            value={selectedRole}
            onChange={(e) => setSelectedRole(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="all">All Roles</option>
            <option value="customer">Customer</option>
            <option value="admin">Admin</option>
            <option value="manager">Manager</option>
            <option value="support">Support</option>
            <option value="content">Content</option>
          </select>

          <select
            value={selectedStatus}
            onChange={(e) => setSelectedStatus(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="all">All Status</option>
            <option value="active">Active</option>
            <option value="inactive">Inactive</option>
            <option value="suspended">Suspended</option>
          </select>

          <div className="text-sm text-gray-400 flex items-center">
            Showing {users.length} of {total} users
          </div>
        </div>
      </Card>

      {/* Users Table */}
      <Card className="p-0 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700/50">
              <tr>
                <th className="text-left py-3 px-6 font-medium text-gray-300">User</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Role</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Status</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Plan</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Last Active</th>
                <th className="text-left py-3 px-6 font-medium text-gray-300">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {users.map((user) => (
                <tr key={user.id} className="hover:bg-slate-700/30">
                  <td className="py-4 px-6">
                    <div className="flex items-center">
                      <UserCircleIcon className="h-8 w-8 text-gray-400 mr-3" />
                      <div>
                        <div className="text-sm font-medium text-white">{user.name}</div>
                        <div className="text-sm text-gray-400">{user.email}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getRoleColor(user.role)}`}>
                      {user.role.toUpperCase()}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getUserStatusColor(user.status)}`}>
                      {getUserStatusIcon(user.status)}
                      <span className="ml-1">{user.status}</span>
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <span className="text-sm text-white">{user.plan}</span>
                  </td>
                  <td className="py-4 px-6">
                    <span className="text-sm text-gray-400">
                      {user.last_active ? new Date(user.last_active).toLocaleDateString() : 'Never'}
                    </span>
                  </td>
                  <td className="py-4 px-6">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleEditUser(user.id)}
                        className="p-1 text-gray-400 hover:text-blue-400 transition-colors"
                        title="View Details"
                        disabled={actionLoading}
                      >
                        <EyeIcon className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleEditUser(user.id)}
                        className="p-1 text-gray-400 hover:text-yellow-400 transition-colors"
                        title="Edit User"
                        disabled={actionLoading}
                      >
                        <PencilIcon className="h-4 w-4" />
                      </button>
                      {currentUser.role === 'admin' && (
                        <>
                          <button
                            onClick={() => handleSuspendUser(user.id)}
                            className="p-1 text-gray-400 hover:text-orange-400 transition-colors"
                            title={user.status === 'suspended' ? 'Activate User' : 'Suspend User'}
                            disabled={actionLoading}
                          >
                            <ExclamationTriangleIcon className="h-4 w-4" />
                          </button>
                          <button
                            onClick={() => handleDeleteUser(user.id)}
                            className="p-1 text-gray-400 hover:text-red-400 transition-colors"
                            title="Delete User"
                            disabled={actionLoading}
                          >
                            <TrashIcon className="h-4 w-4" />
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {users.length === 0 && !loading && (
        <Card className="p-12 text-center">
          <UserGroupIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No users found</h3>
          <p className="text-gray-400 mb-6">
            Try adjusting your search criteria or create a new user.
          </p>
          <Button variant="primary" onClick={handleCreateUser}>
            <PlusIcon className="h-4 w-4 mr-2" />
            Create User
          </Button>
        </Card>
      )}

      {/* Pagination could be added here */}
    </div>
  )
}