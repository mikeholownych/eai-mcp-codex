'use client'

import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import {
  CurrencyDollarIcon,
  DocumentTextIcon,
  CalculatorIcon,
  ClipboardDocumentListIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  ChartBarIcon,
  DocumentArrowDownIcon,
  CreditCardIcon,
  BanknotesIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  PlusIcon,
  CalendarDaysIcon,
} from '@heroicons/react/24/outline'

const mockFinancialData = {
  revenue_metrics: {
    arr: 2450000,
    mrr: 204167,
    ltv: 8420,
    churn_rate: 3.2,
    growth_rate: 15.8
  },
  current_month: {
    revenue: 218500,
    expenses: 156200,
    profit: 62300,
    invoices_sent: 847,
    payments_received: 791
  },
  quarterly_summary: {
    q1_revenue: 612000,
    q2_revenue: 658000,
    q3_revenue: 704000,
    q4_projected: 756000
  },
  pending_items: {
    outstanding_invoices: 15,
    overdue_payments: 3,
    pending_refunds: 2,
    tax_filings_due: 1
  }
}

const mockRecentTransactions = [
  {
    id: 'INV-2024-001234',
    type: 'invoice',
    customer: 'TechCorp Industries',
    amount: 2400,
    status: 'paid',
    date: '2024-01-15',
    plan: 'Enterprise'
  },
  {
    id: 'REF-2024-000056',
    type: 'refund',
    customer: 'StartupXYZ',
    amount: -480,
    status: 'processed',
    date: '2024-01-14',
    plan: 'Professional'
  },
  {
    id: 'INV-2024-001235',
    type: 'invoice',
    customer: 'DevAgency LLC',
    amount: 960,
    status: 'pending',
    date: '2024-01-13',
    plan: 'Professional'
  }
]

const getStatusColor = (status: string) => {
  switch (status) {
    case 'paid': case 'processed': return 'bg-green-500/10 text-green-400'
    case 'pending': return 'bg-yellow-500/10 text-yellow-400'
    case 'overdue': return 'bg-red-500/10 text-red-400'
    default: return 'bg-gray-500/10 text-gray-400'
  }
}

const getTypeIcon = (type: string) => {
  switch (type) {
    case 'invoice': return <DocumentTextIcon className="h-4 w-4" />
    case 'refund': return <ArrowTrendingDownIcon className="h-4 w-4" />
    case 'payment': return <CreditCardIcon className="h-4 w-4" />
    default: return <CurrencyDollarIcon className="h-4 w-4" />
  }
}

export default function FinancialSuite() {
  const { user } = useAuth()
  const [selectedPeriod, setSelectedPeriod] = useState('current_month')
  const [showExportModal, setShowExportModal] = useState(false)

  // Check if user has permission to view financial data
  if (!user || !['admin', 'cfo', 'finance'].includes(user.role)) {
    return (
      <div className="text-center py-12">
        <ExclamationTriangleIcon className="mx-auto h-12 w-12 text-red-400" />
        <h3 className="mt-2 text-sm font-medium text-white">Access Denied</h3>
        <p className="mt-1 text-sm text-gray-400">
          You don't have permission to access financial data.
        </p>
      </div>
    )
  }

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency',
      currency: 'CAD'
    }).format(amount)
  }

  const formatPercentage = (value: number) => {
    return `${value > 0 ? '+' : ''}${value.toFixed(1)}%`
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Financial Suite</h1>
          <p className="mt-2 text-gray-400">
            Revenue analytics, invoicing, tax exports, and financial reporting
          </p>
        </div>
        
        <div className="flex items-center space-x-4">
          <select
            value={selectedPeriod}
            onChange={(e) => setSelectedPeriod(e.target.value)}
            className="bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600 focus:border-orange-500 focus:ring-1 focus:ring-orange-500"
          >
            <option value="current_month">Current Month</option>
            <option value="last_month">Last Month</option>
            <option value="quarterly">Quarterly</option>
            <option value="yearly">Yearly</option>
          </select>
          
          <Button
            variant="primary"
            onClick={() => setShowExportModal(true)}
          >
            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            Export Reports
          </Button>
        </div>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-5">
        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ArrowTrendingUpIcon className="h-8 w-8 text-green-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">ARR</p>
              <p className="text-2xl font-semibold text-white">
                {formatCurrency(mockFinancialData.revenue_metrics.arr)}
              </p>
              <p className="text-sm text-green-400">
                {formatPercentage(mockFinancialData.revenue_metrics.growth_rate)}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CurrencyDollarIcon className="h-8 w-8 text-blue-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">MRR</p>
              <p className="text-2xl font-semibold text-white">
                {formatCurrency(mockFinancialData.revenue_metrics.mrr)}
              </p>
              <p className="text-sm text-blue-400">Monthly Recurring</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-purple-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">LTV</p>
              <p className="text-2xl font-semibold text-white">
                {formatCurrency(mockFinancialData.revenue_metrics.ltv)}
              </p>
              <p className="text-sm text-purple-400">Customer Lifetime</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ArrowTrendingDownIcon className="h-8 w-8 text-red-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Churn Rate</p>
              <p className="text-2xl font-semibold text-white">
                {mockFinancialData.revenue_metrics.churn_rate}%
              </p>
              <p className="text-sm text-red-400">Monthly</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BanknotesIcon className="h-8 w-8 text-yellow-400" />
            </div>
            <div className="ml-5">
              <p className="text-sm font-medium text-gray-400">Net Profit</p>
              <p className="text-2xl font-semibold text-white">
                {formatCurrency(mockFinancialData.current_month.profit)}
              </p>
              <p className="text-sm text-yellow-400">This Month</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Quick Actions & Pending Items */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <Card className="p-6">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
            <ClipboardDocumentListIcon className="h-6 w-6 mr-2 text-orange-400" />
            Quick Actions
          </h2>
          
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Button
              variant="outline"
              className="p-4 h-auto flex-col items-start space-y-2"
            >
              <DocumentTextIcon className="h-6 w-6 text-blue-400" />
              <div className="text-left">
                <div className="font-medium text-white">Generate Invoice</div>
                <div className="text-sm text-gray-400">Create new customer invoice</div>
              </div>
            </Button>
            
            <Button
              variant="outline"
              className="p-4 h-auto flex-col items-start space-y-2"
            >
              <CalculatorIcon className="h-6 w-6 text-green-400" />
              <div className="text-left">
                <div className="font-medium text-white">CRA Tax Export</div>
                <div className="text-sm text-gray-400">Export for tax filing</div>
              </div>
            </Button>
            
            <Button
              variant="outline"
              className="p-4 h-auto flex-col items-start space-y-2"
            >
              <ChartBarIcon className="h-6 w-6 text-purple-400" />
              <div className="text-left">
                <div className="font-medium text-white">Financial Report</div>
                <div className="text-sm text-gray-400">Generate detailed report</div>
              </div>
            </Button>
            
            <Button
              variant="outline"
              className="p-4 h-auto flex-col items-start space-y-2"
            >
              <CreditCardIcon className="h-6 w-6 text-yellow-400" />
              <div className="text-left">
                <div className="font-medium text-white">Payroll Integration</div>
                <div className="text-sm text-gray-400">Sync with Gusto/QB</div>
              </div>
            </Button>
          </div>
        </Card>

        <Card className="p-6">
          <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
            <ExclamationTriangleIcon className="h-6 w-6 mr-2 text-yellow-400" />
            Pending Items
          </h2>
          
          <div className="space-y-4">
            <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
              <div className="flex items-center space-x-3">
                <DocumentTextIcon className="h-5 w-5 text-blue-400" />
                <div>
                  <div className="text-sm font-medium text-white">Outstanding Invoices</div>
                  <div className="text-xs text-gray-400">Awaiting payment</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-white">{mockFinancialData.pending_items.outstanding_invoices}</div>
                <div className="text-xs text-gray-400">invoices</div>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
              <div className="flex items-center space-x-3">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-400" />
                <div>
                  <div className="text-sm font-medium text-white">Overdue Payments</div>
                  <div className="text-xs text-gray-400">Require follow up</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-red-400">{mockFinancialData.pending_items.overdue_payments}</div>
                <div className="text-xs text-gray-400">overdue</div>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
              <div className="flex items-center space-x-3">
                <ArrowTrendingDownIcon className="h-5 w-5 text-yellow-400" />
                <div>
                  <div className="text-sm font-medium text-white">Pending Refunds</div>
                  <div className="text-xs text-gray-400">Processing</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-yellow-400">{mockFinancialData.pending_items.pending_refunds}</div>
                <div className="text-xs text-gray-400">refunds</div>
              </div>
            </div>
            
            <div className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
              <div className="flex items-center space-x-3">
                <CalendarDaysIcon className="h-5 w-5 text-orange-400" />
                <div>
                  <div className="text-sm font-medium text-white">Tax Filings Due</div>
                  <div className="text-xs text-gray-400">Upcoming deadlines</div>
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-semibold text-orange-400">{mockFinancialData.pending_items.tax_filings_due}</div>
                <div className="text-xs text-gray-400">due</div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Recent Transactions */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white flex items-center">
            <CurrencyDollarIcon className="h-6 w-6 mr-2 text-green-400" />
            Recent Transactions
          </h2>
          <Button variant="outline" size="sm">
            View All
          </Button>
        </div>
        
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-slate-700/50">
              <tr>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Transaction</th>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Customer</th>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Amount</th>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Status</th>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-700">
              {mockRecentTransactions.map((transaction) => (
                <tr key={transaction.id} className="hover:bg-slate-700/30">
                  <td className="py-4 px-4">
                    <div className="flex items-center space-x-3">
                      <div className="flex-shrink-0">
                        {getTypeIcon(transaction.type)}
                      </div>
                      <div>
                        <div className="text-sm font-medium text-white">{transaction.id}</div>
                        <div className="text-xs text-gray-400 capitalize">{transaction.type}</div>
                      </div>
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <div className="text-sm text-white">{transaction.customer}</div>
                    <div className="text-xs text-gray-400">{transaction.plan}</div>
                  </td>
                  <td className="py-4 px-4">
                    <div className={`text-sm font-medium ${
                      transaction.amount < 0 ? 'text-red-400' : 'text-green-400'
                    }`}>
                      {formatCurrency(Math.abs(transaction.amount))}
                    </div>
                  </td>
                  <td className="py-4 px-4">
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(transaction.status)}`}>
                      {transaction.status}
                    </span>
                  </td>
                  <td className="py-4 px-4">
                    <div className="text-sm text-gray-400">  
                      {new Date(transaction.date).toLocaleDateString()}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Quarterly Performance Chart */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-white mb-6 flex items-center">
          <ChartBarIcon className="h-6 w-6 mr-2 text-blue-400" />
          Quarterly Revenue Performance
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {Object.entries(mockFinancialData.quarterly_summary).map(([quarter, revenue]) => {
            const isProjected = quarter.includes('projected')
            return (
              <div key={quarter} className="text-center">
                <div className={`text-2xl font-bold mb-2 ${
                  isProjected ? 'text-gray-400' : 'text-white'
                }`}>
                  {formatCurrency(revenue)}
                </div>
                <div className="text-sm text-gray-400 uppercase tracking-wide">
                  {quarter.replace('_', ' ')}
                </div>
                {isProjected && (
                  <div className="text-xs text-yellow-400 mt-1">
                    Projected
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </Card>

      {/* Export Modal would go here */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 p-6 rounded-lg max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-white mb-4">
              Export Financial Reports
            </h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Report Type
                </label>
                <select className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600">
                  <option>Revenue Summary</option>
                  <option>Tax Export (CRA)</option>
                  <option>Invoice Report</option>
                  <option>Customer LTV Analysis</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Format
                </label>
                <select className="w-full bg-slate-700 text-white rounded-lg px-3 py-2 border border-slate-600">
                  <option>PDF</option>
                  <option>CSV</option>
                  <option>JSON</option>
                  <option>Excel</option>
                </select>
              </div>
              <div className="flex space-x-3 mt-6">
                <Button 
                  variant="outline" 
                  className="flex-1"
                  onClick={() => setShowExportModal(false)}
                >
                  Cancel
                </Button>
                <Button 
                  variant="primary" 
                  className="flex-1"
                  onClick={() => {
                    // Handle export
                    setShowExportModal(false)
                  }}
                >
                  Export
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}