'use client'

import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useSystemStats, useSystemHealth } from '@/hooks/useStaff'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import {
  ShieldCheckIcon,
  ServerIcon,
  CpuChipIcon,
  CloudIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  ClockIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  ChartBarIcon,
  BoltIcon,
  CommandLineIcon,
  Cog6ToothIcon,
} from '@heroicons/react/24/outline'

const HEALTH_COLORS: Record<string, string> = {
  healthy: 'text-green-400',
  optimal: 'text-green-400',
  good: 'text-green-400',
  moderate: 'text-yellow-400',
  warning: 'text-yellow-400',
  critical: 'text-red-400',
  error: 'text-red-400',
}

const HEALTH_ICONS: Record<string, React.JSX.Element> = {
  healthy: <CheckCircleIcon className="h-5 w-5 text-green-400" />,
  optimal: <CheckCircleIcon className="h-5 w-5 text-green-400" />,
  good: <CheckCircleIcon className="h-5 w-5 text-green-400" />,
  moderate: <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />,
  warning: <ExclamationTriangleIcon className="h-5 w-5 text-yellow-400" />,
  critical: <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />,
  error: <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />,
  loading: <ClockIcon className="h-5 w-5 text-gray-400" />,
}

const getHealthColor = (status: string) => HEALTH_COLORS[status.toLowerCase()] ?? 'text-gray-400'

<<<<<<< HEAD
const getHealthIcon = (status: string) => HEALTH_ICONS[status.toLowerCase()] ?? HEALTH_ICONS.loading
=======
const getHealthIcon = (status: string) =>
  HEALTH_ICONS[status.toLowerCase()] ?? HEALTH_ICONS.loading

>>>>>>> main

const mockMetrics = {
  cpu_usage: { current: 45.2, trend: 'up', change: '+5.2%' },
  memory_usage: { current: 67.0, trend: 'stable', change: '+0.1%' },
  disk_usage: { current: 23.8, trend: 'up', change: '+2.3%' },
  network_io: { current: 156.7, trend: 'down', change: '-12.4%' },
  active_connections: { current: 847, trend: 'up', change: '+15.2%' },
  requests_per_minute: { current: 2340, trend: 'up', change: '+8.7%' },
}

const mockAlerts = [
  {
    id: 1,
    type: 'warning',
    message: 'API Gateway response time increased by 15%',
    service: 'nginx',
    time: '5 minutes ago',
    severity: 'medium',
  },
  {
    id: 2,
    type: 'info',
    message: 'Database backup completed successfully',
    service: 'postgresql',
    time: '1 hour ago',
    severity: 'low',
  },
  {
    id: 3,
    type: 'warning',
    message: 'High memory usage detected on workflow-orchestrator',
    service: 'workflow-orchestrator',
    time: '2 hours ago',
    severity: 'medium',
  },
]

export default function SystemMonitoring() {
  const { user } = useAuth()
  const { loading: statsLoading, error: statsError } = useSystemStats()
<<<<<<< HEAD
  const {
    health: systemHealth,
    loading: healthLoading,
    error: healthError,
    refetch,
  } = useSystemHealth()
=======
  const { health: systemHealth, loading: healthLoading, error: healthError, refetch } = useSystemHealth()
>>>>>>> main
  const [selectedTimeRange, setSelectedTimeRange] = useState('1h')
  const [autoRefresh, setAutoRefresh] = useState(true)

  const loading = statsLoading || healthLoading
  const error = statsError || healthError

  // Check if user has permission to view system monitoring
  if (!user || !['admin', 'manager'].includes(user.role)) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
        <p className="mt-1 text-sm text-gray-400">
          You don&apos;t have permission to access system monitoring.
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
        <h3 className="mt-2 text-sm font-medium text-white">Error Loading System Data</h3>
        <p className="mt-1 text-sm text-gray-400">{error}</p>
        <Button variant="outline" className="mt-4" onClick={refetch}>
          Try Again
        </Button>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">System Analytics & Monitoring</h1>
          <p className="mt-2 text-gray-400">
            Real-time system health, performance metrics, and service monitoring
          </p>
        </div>

        <div className="flex items-center space-x-4">
          <select
            value={selectedTimeRange}
            onChange={e => setSelectedTimeRange(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="1h">Last Hour</option>
            <option value="6h">Last 6 Hours</option>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
          </select>

          <Button
            variant={autoRefresh ? 'primary' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
          >
            {autoRefresh ? 'Auto-Refresh ON' : 'Auto-Refresh OFF'}
          </Button>

          <Button variant="outline" size="sm" onClick={refetch}>
            Refresh
          </Button>
        </div>
      </div>

      {/* System Health Overview */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white flex items-center">
            <ShieldCheckIcon className="h-6 w-6 mr-2 text-green-400" />
            System Health Overview
          </h2>
          <div className="flex items-center space-x-2">
            <div className="flex items-center">
              <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
              <span className="text-sm text-gray-400">All Systems Operational</span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-300">API Performance</h3>
              {systemHealth?.api_performance
                ? getHealthIcon(systemHealth.api_performance.status)
                : getHealthIcon('loading')}
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Success Rate</span>
                <span className="text-white">
                  {systemHealth?.api_performance?.success_rate || 0}%
                </span>
              </div>
              <div className="bg-slate-600 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full"
                  style={{ width: `${systemHealth?.api_performance?.success_rate || 0}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">
                Avg response time: {systemHealth?.api_performance?.avg_response_time || 0}ms
              </p>
            </div>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-300">Database</h3>
              {systemHealth?.database_status
                ? getHealthIcon(systemHealth.database_status.status)
                : getHealthIcon('loading')}
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Utilization</span>
                <span className="text-white">
                  {systemHealth?.database_status?.utilization || 0}%
                </span>
              </div>
              <div className="bg-slate-600 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full"
                  style={{ width: `${systemHealth?.database_status?.utilization || 0}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">
                Connection pool: {systemHealth?.database_status?.connection_pool || 'unknown'}
              </p>
            </div>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-300">Memory Usage</h3>
              {systemHealth?.memory_usage
                ? getHealthIcon(systemHealth.memory_usage.status)
                : getHealthIcon('loading')}
            </div>
            <div className="space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Used</span>
                <span className="text-white">
                  {systemHealth?.memory_usage?.usage_percent || 0}%
                </span>
              </div>
              <div className="bg-slate-600 rounded-full h-2">
                <div
                  className="bg-gradient-to-r from-yellow-500 to-yellow-600 h-2 rounded-full"
                  style={{ width: `${systemHealth?.memory_usage?.usage_percent || 0}%` }}
                />
              </div>
              <p className="text-xs text-gray-500">
                Available: {systemHealth?.memory_usage?.available_gb || 0}GB
              </p>
            </div>
          </div>

          <div className="bg-slate-700/50 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-300">Services</h3>
              <CheckCircleIcon className="h-5 w-5 text-green-400" />
            </div>
            <div className="space-y-1">
              {systemHealth?.service_status ? (
                Object.entries(systemHealth.service_status).map(([service, status]) => (
                  <div key={service} className="flex justify-between text-xs">
                    <span className="text-gray-400 capitalize">{service.replace('_', ' ')}</span>
                    <span className={getHealthColor(status)}>{status}</span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-gray-500">Loading services...</div>
              )}
            </div>
          </div>
        </div>
      </Card>

      {/* Performance Metrics */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
          <ChartBarIcon className="h-6 w-6 mr-2 text-blue-400" />
          Performance Metrics
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.entries(mockMetrics).map(([metric, data]) => (
            <div key={metric} className="bg-slate-700/30 rounded-lg p-4">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-gray-300 capitalize">
                  {metric.replace('_', ' ')}
                </h3>
                <div
                  className={`flex items-center text-xs font-medium ${
                    data.trend === 'up'
                      ? 'text-green-400'
                      : data.trend === 'down'
                        ? 'text-red-400'
                        : 'text-gray-400'
                  }`}
                >
                  {data.trend === 'up' ? (
                    <ArrowUpIcon className="h-3 w-3 mr-1" />
                  ) : data.trend === 'down' ? (
                    <ArrowDownIcon className="h-3 w-3 mr-1" />
                  ) : null}
                  {data.change}
                </div>
              </div>
              <div className="text-2xl font-bold text-white mb-1">
                {typeof data.current === 'number'
                  ? data.current > 100
                    ? data.current.toLocaleString()
                    : `${data.current}%`
                  : data.current}
              </div>
              <div className="text-xs text-gray-500">vs previous {selectedTimeRange}</div>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Service Status */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
            <ServerIcon className="h-6 w-6 mr-2 text-purple-400" />
            Service Status
          </h2>

          <div className="space-y-4">
            {[
              {
                name: 'Model Router',
                status: 'running',
                uptime: '99.9%',
                port: '8001',
                icon: CpuChipIcon,
              },
              {
                name: 'Plan Management',
                status: 'running',
                uptime: '99.8%',
                port: '8002',
                icon: Cog6ToothIcon,
              },
              {
                name: 'Git Worktree Manager',
                status: 'running',
                uptime: '99.7%',
                port: '8003',
                icon: CommandLineIcon,
              },
              {
                name: 'Workflow Orchestrator',
                status: 'running',
                uptime: '99.9%',
                port: '8004',
                icon: BoltIcon,
              },
              {
                name: 'Verification Feedback',
                status: 'running',
                uptime: '99.6%',
                port: '8005',
                icon: CheckCircleIcon,
              },
              {
                name: 'Staff Service',
                status: 'running',
                uptime: '100%',
                port: '8006',
                icon: ShieldCheckIcon,
              },
            ].map(service => {
              const Icon = service.icon
              return (
                <div
                  key={service.name}
                  className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <Icon className="h-5 w-5 text-gray-400" />
                    <div>
                      <h3 className="text-sm font-medium text-white">{service.name}</h3>
                      <p className="text-xs text-gray-400">Port {service.port}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className="text-xs text-gray-400">Uptime: {service.uptime}</span>
                    <div className="flex items-center">
                      <div className="w-2 h-2 bg-green-400 rounded-full mr-2"></div>
                      <span className="text-sm text-green-400 capitalize">{service.status}</span>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        </Card>

        {/* System Alerts */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
            <ExclamationTriangleIcon className="h-6 w-6 mr-2 text-yellow-400" />
            Recent Alerts
          </h2>

          <div className="space-y-4">
            {mockAlerts.map(alert => (
              <div
                key={alert.id}
                className="flex items-start space-x-3 p-3 bg-slate-700/30 rounded-lg"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {alert.type === 'warning' ? (
                    <ExclamationTriangleIcon className="h-4 w-4 text-yellow-400" />
                  ) : alert.type === 'error' ? (
                    <ExclamationTriangleIcon className="h-4 w-4 text-red-400" />
                  ) : (
                    <CheckCircleIcon className="h-4 w-4 text-blue-400" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white">{alert.message}</p>
                  <div className="flex items-center mt-1 text-xs text-gray-500 space-x-4">
                    <span className="capitalize">{alert.service}</span>
                    <span>{alert.time}</span>
                    <span
                      className={`px-2 py-1 rounded text-xs ${
                        alert.severity === 'high'
                          ? 'bg-red-500/10 text-red-400'
                          : alert.severity === 'medium'
                            ? 'bg-yellow-500/10 text-yellow-400'
                            : 'bg-blue-500/10 text-blue-400'
                      }`}
                    >
                      {alert.severity}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 text-center">
            <Button variant="outline" size="sm">
              View All Alerts
            </Button>
          </div>
        </Card>
      </div>

      {/* Infrastructure Overview */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
          <CloudIcon className="h-6 w-6 mr-2 text-indigo-400" />
          Infrastructure Overview
        </h2>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Containers</h3>
            <div className="space-y-2">
              {[
                { name: 'PostgreSQL', status: 'running', memory: '512MB' },
                { name: 'Redis', status: 'running', memory: '128MB' },
                { name: 'Nginx', status: 'running', memory: '64MB' },
                { name: 'Consul', status: 'running', memory: '256MB' },
              ].map(container => (
                <div
                  key={container.name}
                  className="flex justify-between items-center p-2 bg-slate-700/30 rounded"
                >
                  <span className="text-sm text-white">{container.name}</span>
                  <div className="flex items-center space-x-2">
                    <span className="text-xs text-gray-400">{container.memory}</span>
                    <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Network</h3>
            <div className="space-y-2">
              <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                <span className="text-sm text-gray-400">Ingress Traffic</span>
                <span className="text-sm text-white">2.4 GB/hr</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                <span className="text-sm text-gray-400">Egress Traffic</span>
                <span className="text-sm text-white">1.8 GB/hr</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                <span className="text-sm text-gray-400">Active Connections</span>
                <span className="text-sm text-white">847</span>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-medium text-white">Storage</h3>
            <div className="space-y-2">
              <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                <span className="text-sm text-gray-400">Database Size</span>
                <span className="text-sm text-white">12.4 GB</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                <span className="text-sm text-gray-400">Log Files</span>
                <span className="text-sm text-white">3.2 GB</span>
              </div>
              <div className="flex justify-between p-2 bg-slate-700/30 rounded">
                <span className="text-sm text-gray-400">Available Space</span>
                <span className="text-sm text-white">124 GB</span>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  )
}
