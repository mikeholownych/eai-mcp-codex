'use client'

import React from 'react'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import Badge from '@/components/ui/Badge'
import { useStaffDashboard, useSystemHealth } from '@/hooks/useStaff'

const StaffDashboard: React.FC = () => {
  const { data: dashboardData, loading, error } = useStaffDashboard()
  const { data: healthData } = useSystemHealth()

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="text-center py-12">
        <h2 className="text-xl font-semibold text-red-400 mb-2">Error Loading Dashboard</h2>
        <p className="text-slate-400">{error}</p>
      </div>
    )
  }

  const stats = dashboardData?.system_stats || {}
  const alerts = dashboardData?.system_alerts || []
  const quickActions = dashboardData?.quick_actions || []
  const recentTickets = dashboardData?.recent_tickets || []

  const getHealthColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'text-green-400'
      case 'warning': return 'text-yellow-400'
      case 'critical': return 'text-red-400'
      default: return 'text-slate-400'
    }
  }

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'bg-red-500/20 text-red-400 border-red-500/30'
      case 'high': return 'bg-orange-500/20 text-orange-400 border-orange-500/30'
      case 'medium': return 'bg-yellow-500/20 text-yellow-400 border-yellow-500/30'
      case 'low': return 'bg-green-500/20 text-green-400 border-green-500/30'
      default: return 'bg-slate-600 text-slate-300'
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Dashboard</h1>
          <p className="text-slate-400">System overview and quick actions</p>
        </div>
        <div className="flex items-center space-x-2">
          <Badge variant="success" className="flex items-center">
            <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
            All Systems Operational
          </Badge>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">Total Users</p>
              <p className="text-2xl font-bold text-white">{stats.total_users || 0}</p>
              <p className="text-xs text-slate-500">
                {stats.active_users || 0} active
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">Active Subscriptions</p>
              <p className="text-2xl font-bold text-white">{stats.active_subscriptions || 0}</p>
              <p className="text-xs text-slate-500">
                {stats.total_subscriptions || 0} total
              </p>
            </div>
            <div className="w-12 h-12 bg-green-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-18C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2z" />
              </svg>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">Open Tickets</p>
              <p className="text-2xl font-bold text-white">{stats.open_tickets || 0}</p>
              <p className="text-xs text-slate-500">
                {stats.closed_tickets || 0} resolved
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 5v2m0 4v2m0 4v2M5 5a2 2 0 00-2 2v3a2 2 0 110 4v3a2 2 0 002 2h14a2 2 0 002-2v-3a2 2 0 110-4V7a2 2 0 00-2-2H5z" />
              </svg>
            </div>
          </div>
        </Card>

        <Card>
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-slate-400">System Uptime</p>
              <p className="text-2xl font-bold text-white">{stats.system_uptime || 'N/A'}</p>
              <p className="text-xs text-slate-500">
                Avg response: {stats.avg_response_time || 0}ms
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-500/20 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
          </div>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Tickets */}
        <Card>
          <Card.Header>
            <h3 className="text-lg font-semibold text-white">Recent Support Tickets</h3>
          </Card.Header>
          <CardContent>
            <div className="space-y-4">
              {recentTickets.length > 0 ? recentTickets.map((ticket) => (
                <div key={ticket.id} className="flex items-center justify-between p-3 bg-slate-700/50 rounded-lg">
                  <div className="flex-1">
                    <h4 className="text-sm font-medium text-white">{ticket.title}</h4>
                    <p className="text-xs text-slate-400">{ticket.customer.name} • {ticket.category}</p>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Badge 
                      variant="secondary" 
                      size="sm" 
                      className={getPriorityColor(ticket.priority)}
                    >
                      {ticket.priority}
                    </Badge>
                    <Badge variant="outline" size="sm">
                      {ticket.status}
                    </Badge>
                  </div>
                </div>
              )) : (
                <p className="text-center text-slate-400 py-8">No recent tickets</p>
              )}
            </div>
          </CardContent>
          <Card.Footer>
            <Button variant="outline" size="sm" className="w-full">
              View All Tickets
            </Button>
          </Card.Footer>
        </Card>

        {/* System Alerts */}
        <Card>
          <Card.Header>
            <h3 className="text-lg font-semibold text-white">System Alerts</h3>
          </Card.Header>
          <CardContent>
            <div className="space-y-4">
              {alerts.length > 0 ? alerts.map((alert) => (
                <div key={alert.id} className="flex items-start space-x-3 p-3 bg-slate-700/50 rounded-lg">
                  <div className={`w-2 h-2 rounded-full mt-2 ${
                    alert.type === 'error' ? 'bg-red-400' : 
                    alert.type === 'warning' ? 'bg-yellow-400' : 'bg-blue-400'
                  }`}></div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-white">{alert.message}</p>
                    <p className="text-xs text-slate-400">{alert.time}</p>
                  </div>
                </div>
              )) : (
                <p className="text-center text-slate-400 py-8">No system alerts</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card>
        <Card.Header>
          <h3 className="text-lg font-semibold text-white">Quick Actions</h3>
        </Card.Header>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {quickActions.map((action, index) => (
              <Button
                key={index}
                variant="outline"
                className="h-auto p-4 flex flex-col items-center space-y-2 hover:bg-slate-700"
              >
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${action.color}`}>
                  <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={action.icon} />
                  </svg>
                </div>
                <span className="text-sm font-medium text-white text-center">{action.name}</span>
                <span className="text-xs text-slate-400 text-center">{action.description}</span>
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default StaffDashboard