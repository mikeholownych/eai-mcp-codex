'use client'

import React from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useStaffDashboard } from '@/hooks/useStaff'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import {
  UserGroupIcon,
  LifebuoyIcon,
  CreditCardIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ShieldCheckIcon,
} from '@heroicons/react/24/outline'

const PRIORITY_COLORS: Record<string, string> = {
  high: 'bg-red-500/10 text-red-400',
  medium: 'bg-yellow-500/10 text-yellow-400',
  low: 'bg-green-500/10 text-green-400',
}

const STATUS_COLORS: Record<string, string> = {
  open: 'bg-blue-500/10 text-blue-400',
  'in-progress': 'bg-yellow-500/10 text-yellow-400',
  pending: 'bg-orange-500/10 text-orange-400',
  resolved: 'bg-green-500/10 text-green-400',
}

const ALERT_ICONS: Record<string, React.JSX.Element> = {
  warning: <ExclamationTriangleIcon className="h-4 w-4 text-yellow-400" />,
  error: <ExclamationTriangleIcon className="h-4 w-4 text-red-400" />,
  success: <CheckCircleIcon className="h-4 w-4 text-green-400" />,
  default: <CheckCircleIcon className="h-4 w-4 text-blue-400" />,
}

const getPriorityColor = (priority: string) =>
  PRIORITY_COLORS[priority] ?? 'bg-gray-500/10 text-gray-400'

const getStatusColor = (status: string) => STATUS_COLORS[status] ?? 'bg-gray-500/10 text-gray-400'

const getAlertIcon = (type: string) => ALERT_ICONS[type] ?? ALERT_ICONS.default

export default function StaffDashboard() {
  const { user } = useAuth()
  const { data: dashboardData, loading, error, refetch } = useStaffDashboard()

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
        <h3 className="mt-2 text-sm font-medium text-white">Error Loading Dashboard</h3>
        <p className="mt-1 text-sm text-gray-400">{error}</p>
        <Button variant="outline" className="mt-4" onClick={refetch}>
          Try Again
        </Button>
      </div>
    )
  }

  if (!dashboardData) {
    return null
  }

  const systemStats = [
    {
      name: 'Total Users',
      value: dashboardData.system_stats.total_users.toLocaleString(),
      change: '+12%',
      changeType: 'increase',
      icon: UserGroupIcon,
    },
    {
      name: 'Active Subscriptions',
      value: dashboardData.system_stats.active_subscriptions.toLocaleString(),
      change: '+8%',
      changeType: 'increase',
      icon: CreditCardIcon,
    },
    {
      name: 'Open Tickets',
      value: dashboardData.system_stats.open_tickets.toString(),
      change: '-15%',
      changeType: 'decrease',
      icon: LifebuoyIcon,
    },
    {
      name: 'System Uptime',
      value: dashboardData.system_stats.system_uptime,
      change: '+0.1%',
      changeType: 'increase',
      icon: CheckCircleIcon,
    },
  ]

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div>
        <h1 className="text-3xl font-bold text-white">Staff Dashboard</h1>
        <p className="mt-2 text-gray-400">
          Welcome back, {user?.name}. Here&apos;s your system overview for today.
        </p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {systemStats.map(item => {
          const Icon = item.icon
          return (
            <Card key={item.name} className="p-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <Icon className="h-8 w-8 text-gray-400" />
                </div>
                <div className="ml-5 w-0 flex-1">
                  <dl>
                    <dt className="text-sm font-medium text-gray-400 truncate">{item.name}</dt>
                    <dd className="flex items-baseline">
                      <div className="text-2xl font-semibold text-white">{item.value}</div>
                      <div
                        className={`ml-2 flex items-baseline text-sm font-semibold ${
                          item.changeType === 'increase' ? 'text-green-400' : 'text-red-400'
                        }`}
                      >
                        {item.changeType === 'increase' ? (
                          <ArrowUpIcon className="h-4 w-4 flex-shrink-0 self-center" />
                        ) : (
                          <ArrowDownIcon className="h-4 w-4 flex-shrink-0 self-center" />
                        )}
                        <span className="sr-only">
                          {item.changeType === 'increase' ? 'Increased' : 'Decreased'} by
                        </span>
                        {item.change}
                      </div>
                    </dd>
                  </dl>
                </div>
              </div>
            </Card>
          )
        })}
      </div>

      {/* Quick Actions */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {dashboardData.quick_actions.map(action => {
            const IconName =
              action.icon === 'UserGroupIcon'
                ? UserGroupIcon
                : action.icon === 'LifebuoyIcon'
                  ? LifebuoyIcon
                  : ExclamationTriangleIcon
            return (
              <Card
                key={action.name}
                className="p-6 hover:bg-slate-700/50 transition-colors cursor-pointer"
              >
                <div className="flex items-center">
                  <div
                    className={`flex-shrink-0 w-12 h-12 bg-gradient-to-r ${action.color} rounded-lg flex items-center justify-center`}
                  >
                    <IconName className="h-6 w-6 text-white" />
                  </div>
                  <div className="ml-4">
                    <h3 className="text-sm font-medium text-white">{action.name}</h3>
                    <p className="text-sm text-gray-400">{action.description}</p>
                  </div>
                </div>
              </Card>
            )
          })}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="lg:grid lg:grid-cols-2 lg:gap-8">
        {/* Recent Support Tickets */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">Recent Support Tickets</h2>
            <Button variant="outline" size="sm" href="/staff/tickets">
              View All
            </Button>
          </div>
          <Card className="p-6">
            <div className="space-y-4">
              {dashboardData.recent_tickets.map(ticket => (
                <div
                  key={ticket.id}
                  className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600"
                >
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <h3 className="text-sm font-medium text-white">{ticket.title}</h3>
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(ticket.priority)}`}
                      >
                        {ticket.priority}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(ticket.status)}`}
                      >
                        {ticket.status}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400 mb-1">{ticket.customer.name}</p>
                    <div className="flex items-center text-xs text-gray-500">
                      <ClockIcon className="h-3 w-3 mr-1" />
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </div>
                  </div>
                  <Button variant="outline" size="sm">
                    View
                  </Button>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* System Alerts */}
        <div>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold text-white">System Alerts</h2>
            <Button variant="outline" size="sm" href="/staff/system">
              View All
            </Button>
          </div>
          <Card className="p-6">
            <div className="space-y-4">
              {dashboardData.system_alerts.map(alert => (
                <div
                  key={alert.id}
                  className="flex items-start space-x-3 p-3 bg-slate-700/30 rounded-lg"
                >
                  <div className="flex-shrink-0 mt-0.5">{getAlertIcon(alert.type)}</div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white">{alert.message}</p>
                    <div className="flex items-center mt-1 text-xs text-gray-500">
                      <ClockIcon className="h-3 w-3 mr-1" />
                      {alert.time}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>

      {/* System Health Overview */}
      {user?.role === 'admin' && (
        <Card className="p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white flex items-center">
              <ShieldCheckIcon className="h-6 w-6 mr-2 text-green-400" />
              System Health Overview
            </h2>
            <Button variant="outline" size="sm" href="/staff/system">
              Detailed View
            </Button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-300">API Performance</h3>
                <span className="text-sm text-green-400">Healthy</span>
              </div>
              <div className="bg-slate-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full"
                  style={{ width: '94%' }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">94% success rate</p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-300">Database</h3>
                <span className="text-sm text-green-400">Optimal</span>
              </div>
              <div className="bg-slate-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full"
                  style={{ width: '89%' }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">89% utilization</p>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-300">Memory Usage</h3>
                <span className="text-sm text-yellow-400">Moderate</span>
              </div>
              <div className="bg-slate-700 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-yellow-500 to-yellow-600 h-2 rounded-full"
                  style={{ width: '67%' }}
                />
              </div>
              <p className="text-xs text-gray-500 mt-1">67% used</p>
            </div>
          </div>
        </Card>
      )}
    </div>
  )
}
