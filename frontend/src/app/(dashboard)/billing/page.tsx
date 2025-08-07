'use client'

import React, { useState } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Card from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import {
  CreditCardIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  CalendarDaysIcon,
  ChartBarIcon,
  DocumentArrowDownIcon,
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

const billingHistory = [
  {
    id: '1',
    date: '2024-01-15',
    description: 'Pro Plan - Monthly Subscription',
    amount: 79,
    status: 'paid',
    invoice: 'INV-2024-001',
  },
  {
    id: '2',
    date: '2023-12-15',
    description: 'Pro Plan - Monthly Subscription',
    amount: 79,
    status: 'paid',
    invoice: 'INV-2023-012',
  },
  {
    id: '3',
    date: '2023-11-15',
    description: 'Standard Plan - Monthly Subscription',
    amount: 29,
    status: 'paid',
    invoice: 'INV-2023-011',
  },
]

const paymentMethods = [
  {
    id: '1',
    type: 'card',
    brand: 'visa',
    last4: '4242',
    expiry: '12/26',
    isDefault: true,
  },
  {
    id: '2',
    type: 'card',
    brand: 'mastercard',
    last4: '8888',
    expiry: '08/25',
    isDefault: false,
  },
]

export default function BillingPage() {
  const [currentPlan, setCurrentPlan] = useState('pro')
  const [isChangingPlan, setIsChangingPlan] = useState(false)
  useAuth()

  const handlePlanChange = async (planId: string) => {
    setIsChangingPlan(true)

    // Simulate plan change
    setTimeout(() => {
      setCurrentPlan(planId)
      setIsChangingPlan(false)
    }, 2000)
  }

  const currentPlanDetails = plans.find(plan => plan.id === currentPlan)

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
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-green-600 rounded-lg flex items-center justify-center">
              <CheckCircleIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-white">Current Plan</h3>
              <p className="text-2xl font-bold text-green-400">{currentPlanDetails?.name}</p>
              <p className="text-sm text-gray-400">
                {currentPlanDetails?.price
                  ? `$${currentPlanDetails.price}/${currentPlanDetails.interval}`
                  : 'Custom pricing'}
              </p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center">
              <CalendarDaysIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-white">Next Billing</h3>
              <p className="text-xl font-bold text-white">Feb 15, 2024</p>
              <p className="text-sm text-gray-400">Auto-renewal enabled</p>
            </div>
          </div>
        </Card>

        <Card className="p-6">
          <div className="flex items-center">
            <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg flex items-center justify-center">
              <ChartBarIcon className="h-6 w-6 text-white" />
            </div>
            <div className="ml-4">
              <h3 className="text-lg font-semibold text-white">Usage This Month</h3>
              <p className="text-xl font-bold text-white">28,456 / 50,000</p>
              <p className="text-sm text-gray-400">API calls</p>
            </div>
          </div>
        </Card>
      </div>

      {/* Usage Details */}
      <Card className="p-6">
        <h2 className="text-xl font-semibold text-white mb-4">Current Usage</h2>
        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-300">API Calls</span>
              <span className="text-sm text-gray-400">28,456 / 50,000</span>
            </div>
            <div className="bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-orange-500 to-orange-600 h-2 rounded-full"
                style={{ width: '57%' }}
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-300">Storage</span>
              <span className="text-sm text-gray-400">45 GB / 100 GB</span>
            </div>
            <div className="bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-blue-500 to-blue-600 h-2 rounded-full"
                style={{ width: '45%' }}
              />
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-300">Bandwidth</span>
              <span className="text-sm text-gray-400">12 GB / 50 GB</span>
            </div>
            <div className="bg-slate-700 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-green-500 to-green-600 h-2 rounded-full"
                style={{ width: '24%' }}
              />
            </div>
          </div>
        </div>
      </Card>

      {/* Available Plans */}
      <div>
        <h2 className="text-xl font-semibold text-white mb-6">Available Plans</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {plans.map(plan => (
            <Card
              key={plan.id}
              className={`p-6 relative ${
                plan.id === currentPlan
                  ? 'ring-2 ring-orange-500 bg-orange-500/5'
                  : plan.popular
                    ? 'ring-2 ring-blue-500'
                    : ''
              }`}
            >
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <span className="bg-blue-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                    Most Popular
                  </span>
                </div>
              )}

              {plan.id === currentPlan && (
                <div className="absolute -top-3 right-4">
                  <span className="bg-green-500 text-white px-3 py-1 rounded-full text-xs font-medium">
                    Current Plan
                  </span>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-xl font-semibold text-white mb-2">{plan.name}</h3>
                <div className="mb-4">
                  {plan.price ? (
                    <>
                      <span className="text-3xl font-bold text-white">${plan.price}</span>
                      <span className="text-gray-400">/{plan.interval}</span>
                    </>
                  ) : (
                    <span className="text-2xl font-bold text-white">Custom</span>
                  )}
                </div>
              </div>

              <ul className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center text-sm">
                    <CheckCircleIcon className="h-4 w-4 text-green-400 mr-3 flex-shrink-0" />
                    <span className="text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                variant={plan.id === currentPlan ? 'outline' : 'primary'}
                className="w-full"
                disabled={plan.id === currentPlan || isChangingPlan}
                loading={isChangingPlan}
                onClick={() => plan.id !== currentPlan && handlePlanChange(plan.id)}
              >
                {plan.id === currentPlan
                  ? 'Current Plan'
                  : plan.price
                    ? 'Upgrade'
                    : 'Contact Sales'}
              </Button>
            </Card>
          ))}
        </div>
      </div>

      {/* Payment Methods */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Payment Methods</h2>
          <Button variant="outline" size="sm">
            <CreditCardIcon className="h-4 w-4 mr-2" />
            Add Payment Method
          </Button>
        </div>

        <div className="space-y-4">
          {paymentMethods.map(method => (
            <div
              key={method.id}
              className="flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600"
            >
              <div className="flex items-center">
                <div className="w-10 h-6 bg-slate-600 rounded mr-3 flex items-center justify-center">
                  <span className="text-xs font-bold text-white uppercase">{method.brand}</span>
                </div>
                <div>
                  <p className="text-white font-medium">•••• •••• •••• {method.last4}</p>
                  <p className="text-sm text-gray-400">Expires {method.expiry}</p>
                </div>
                {method.isDefault && (
                  <span className="ml-3 bg-green-500/10 text-green-400 px-2 py-1 rounded text-xs">
                    Default
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-2">
                <Button variant="outline" size="sm">
                  Edit
                </Button>
                <Button variant="outline" size="sm">
                  Remove
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      {/* Billing History */}
      <Card className="p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Billing History</h2>
          <Button variant="outline" size="sm">
            <DocumentArrowDownIcon className="h-4 w-4 mr-2" />
            Download All
          </Button>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-600">
                <th className="text-left py-3 px-4 font-medium text-gray-300">Date</th>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Description</th>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Amount</th>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Status</th>
                <th className="text-left py-3 px-4 font-medium text-gray-300">Invoice</th>
              </tr>
            </thead>
            <tbody>
              {billingHistory.map(item => (
                <tr key={item.id} className="border-b border-slate-700">
                  <td className="py-3 px-4 text-gray-300">
                    {new Date(item.date).toLocaleDateString()}
                  </td>
                  <td className="py-3 px-4 text-gray-300">{item.description}</td>
                  <td className="py-3 px-4 text-white font-medium">${item.amount}</td>
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
                      {item.invoice}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  )
}
