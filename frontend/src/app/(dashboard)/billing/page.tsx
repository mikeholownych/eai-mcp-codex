'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { paymentApi, billingApi } from '@/lib/api'
import { PaymentMethod, Customer, Subscription } from '@/types'
import PaymentMethodList from '@/components/payments/PaymentMethodList'
import PaymentMethodForm from '@/components/payments/PaymentMethodForm'
import {
  CreditCardIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  DocumentArrowDownIcon,
  PlusIcon,
} from '@heroicons/react/24/outline'

const plans = [
  {
    id: 'standard',
    name: 'Standard',
    price: 29,
    interval: 'month',
    features: [
      '5,000 API calls per month',
      'Basic code generation',
      'Standard AI models',
      'Community support',
      '10 GB storage',
      'Basic analytics',
    ],
    popular: false,
  },
  {
    id: 'pro',
    name: 'Pro',
    price: 79,
    interval: 'month',
    features: [
      '50,000 API calls per month',
      'Advanced code generation',
      'All AI models (including O3)',
      'Priority support',
      '100 GB storage',
      'Advanced analytics',
      'Custom integrations',
      'Team collaboration',
    ],
    popular: true,
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: null,
    interval: 'custom',
    features: [
      'Unlimited API calls',
      'Custom AI model training',
      'Dedicated support',
      'Unlimited storage',
      'Custom analytics',
      'White-label solution',
      'SLA guarantees',
      'On-premise deployment',
    ],
    popular: false,
  },
]

export default function BillingPage() {
  const { user } = useAuth()
  const queryClient = useQueryClient()
  const [currentPlan, setCurrentPlan] = useState('pro')
  const [isChangingPlan, setIsChangingPlan] = useState(false)
  const [showAddPaymentMethod, setShowAddPaymentMethod] = useState(false)
  const [customer, setCustomer] = useState<Customer | null>(null)

  // Fetch customer data
  const { data: customerData, isLoading: customerLoading } = useQuery({
    queryKey: ['customer', user?.id],
    queryFn: async () => {
      if (!user?.id) return null
      
      // Try to get existing customer, create if not exists
      try {
        const response = await paymentApi.getCustomer(user.id)
        if (response.success && response.data) {
          return response.data
        }
      } catch (error) {
        // Customer doesn't exist, create one
        const createResponse = await paymentApi.createCustomer({
          email: user.email,
          name: user.name,
          metadata: { userId: user.id, tenantId: user.tenantId },
        })
        if (createResponse.success && createResponse.data) {
          return createResponse.data
        }
      }
      return null
    },
    enabled: !!user?.id,
  })

  // Fetch payment methods
  const { data: paymentMethods = [], refetch: refetchPaymentMethods } = useQuery({
    queryKey: ['paymentMethods', customer?.id],
    queryFn: async () => {
      if (!customer?.id) return []
      const response = await paymentApi.getCustomerPaymentMethods(customer.id)
      return response.success ? response.data || [] : []
    },
    enabled: !!customer?.id,
  })

  // Fetch subscription data
  const { data: subscription } = useQuery({
    queryKey: ['subscription', user?.tenantId],
    queryFn: async () => {
      if (!user?.tenantId) return null
      const response = await billingApi.getSubscription()
      return response.success ? response.data : null
    },
    enabled: !!user?.tenantId,
  })

  // Fetch billing history
  const { data: billingHistory = [] } = useQuery({
    queryKey: ['billingHistory', user?.tenantId],
    queryFn: async () => {
      if (!user?.tenantId) return []
      const response = await billingApi.getInvoices()
      return response.success ? response.data || [] : []
    },
    enabled: !!user?.tenantId,
  })

  // Update customer state when data is fetched
  useEffect(() => {
    if (customerData) {
      setCustomer(customerData)
    }
  }, [customerData])

  const handlePlanChange = async (planId: string) => {
    setIsChangingPlan(true)

    try {
      // Here you would integrate with your subscription management system
      // For now, we'll just simulate the change
      setTimeout(() => {
        setCurrentPlan(planId)
        setIsChangingPlan(false)
      }, 2000)
    } catch (error) {
      console.error('Error changing plan:', error)
      setIsChangingPlan(false)
    }
  }

  const handlePaymentMethodSuccess = () => {
    setShowAddPaymentMethod(false)
    refetchPaymentMethods()
  }

  const currentPlanDetails = plans.find(plan => plan.id === currentPlan)

  if (customerLoading) {
    return (
      <div className="space-y-8">
        <div className="animate-pulse">
          <div className="h-8 bg-slate-700 rounded w-1/3 mb-2"></div>
          <div className="h-4 bg-slate-700 rounded w-1/2"></div>
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {[1, 2, 3].map(i => (
            <div key={i} className="animate-pulse">
              <div className="h-32 bg-slate-700 rounded"></div>
            </div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white">Billing & Subscription</h1>
        <p className="text-gray-400">
          Manage your subscription, payment methods, and billing history
        </p>
      </div>

      {/* Current Plan Overview */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Current Plan</h3>
            <span className="text-sm text-gray-400">
              {subscription?.status || 'Active'}
            </span>
          </div>
          <div className="mb-4">
            <h4 className="text-2xl font-bold text-white">
              {currentPlanDetails?.name}
            </h4>
            <p className="text-gray-400">
              {currentPlanDetails?.price ? `$${currentPlanDetails.price}/${currentPlanDetails.interval}` : 'Custom pricing'}
            </p>
          </div>
          <div className="space-y-2">
            {currentPlanDetails?.features.slice(0, 3).map((feature, index) => (
              <div key={index} className="flex items-center text-sm text-gray-300">
                <CheckCircleIcon className="h-4 w-4 text-green-400 mr-2" />
                {feature}
              </div>
            ))}
          </div>
          <Button
            variant="outline"
            className="w-full mt-4"
            disabled={isChangingPlan}
            loading={isChangingPlan}
          >
            Change Plan
          </Button>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Billing Cycle</h3>
            <CalendarDaysIcon className="h-5 w-5 text-gray-400" />
          </div>
          <div className="mb-4">
            <p className="text-sm text-gray-400">Next billing date</p>
            <p className="text-lg font-semibold text-white">
              {subscription?.currentPeriodEnd 
                ? new Date(subscription.currentPeriodEnd).toLocaleDateString()
                : 'N/A'
              }
            </p>
          </div>
          <div className="mb-4">
            <p className="text-sm text-gray-400">Amount</p>
            <p className="text-lg font-semibold text-white">
              {subscription?.amount 
                ? `$${subscription.amount} ${subscription.currency?.toUpperCase()}`
                : 'N/A'
              }
            </p>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-white">Usage</h3>
            <ChartBarIcon className="h-5 w-5 text-gray-400" />
          </div>
          <div className="space-y-3">
            <div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">API Calls</span>
                <span className="text-white">2,847 / 50,000</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2 mt-1">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '5.7%' }}></div>
              </div>
            </div>
            <div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-400">Storage</span>
                <span className="text-white">45 GB / 100 GB</span>
              </div>
              <div className="w-full bg-slate-700 rounded-full h-2 mt-1">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '45%' }}></div>
              </div>
            </div>
          </div>
        </Card>
      </div>

      {/* Payment Methods */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Payment Methods</h2>
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => setShowAddPaymentMethod(true)}
          >
            <PlusIcon className="h-4 w-4 mr-2" />
            Add Payment Method
          </Button>
        </div>

        {showAddPaymentMethod ? (
          <div className="border border-slate-600 rounded-lg p-6 bg-slate-800/50">
            <PaymentMethodForm
              customerId={customer?.id || ''}
              onSuccess={handlePaymentMethodSuccess}
              onCancel={() => setShowAddPaymentMethod(false)}
            />
          </div>
        ) : (
          <PaymentMethodList
            paymentMethods={paymentMethods}
            customerId={customer?.id || ''}
            onUpdate={refetchPaymentMethods}
          />
        )}
      </Card>

      {/* Billing History */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Billing History</h2>
          <Button variant="outline" size="sm">
            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            Export
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Date</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Description</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Amount</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Status</th>
                <th className="text-left py-3 px-4 text-sm font-medium text-gray-300">Invoice</th>
              </tr>
            </thead>
            <tbody>
              {billingHistory.length > 0 ? (
                billingHistory.map(item => (
                  <tr key={item.id} className="border-b border-slate-700">
                    <td className="py-3 px-4 text-gray-300">
                      {new Date(item.dueDate).toLocaleDateString()}
                    </td>
                    <td className="py-3 px-4 text-gray-300">
                      {item.items?.[0]?.description || 'Subscription'}
                    </td>
                    <td className="py-3 px-4 text-white font-medium">
                      ${item.amount} {item.currency?.toUpperCase()}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          item.status === 'paid'
                            ? 'bg-green-500/10 text-green-400'
                            : 'bg-red-500/10 text-red-400'
                        }`}
                      >
                        {item.status === 'paid' ? (
                          <CheckCircleIcon className="h-3 w-3 mr-1" />
                        ) : (
                          <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                        )}
                        {item.status}
                      </span>
                    </td>
                    <td className="py-3 px-4">
                      <Button variant="outline" size="sm">
                        <DocumentTextIcon className="h-4 w-4 mr-1" />
                        {item.id}
                      </Button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-gray-400">
                    No billing history available
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
