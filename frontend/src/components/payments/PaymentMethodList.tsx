'use client'

import React, { useState } from 'react'
import { PaymentMethod } from '@/types'
import { paymentApi } from '@/lib/api'
import { toast } from '@/lib/toast'
import Button from '@/components/ui/Button'
import {
  CreditCardIcon,
  TrashIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline'

interface PaymentMethodListProps {
  paymentMethods: PaymentMethod[]
  customerId: string
  onUpdate: () => void
}

const getCardBrandIcon = (brand?: string) => {
  const brandLower = brand?.toLowerCase()
  
  switch (brandLower) {
    case 'visa':
      return '💳'
    case 'mastercard':
      return '💳'
    case 'amex':
    case 'american express':
      return '💳'
    case 'discover':
      return '💳'
    default:
      return '💳'
  }
}

const getCardBrandName = (brand?: string) => {
  const brandLower = brand?.toLowerCase()
  
  switch (brandLower) {
    case 'visa':
      return 'Visa'
    case 'mastercard':
      return 'Mastercard'
    case 'amex':
    case 'american express':
      return 'American Express'
    case 'discover':
      return 'Discover'
    default:
      return 'Card'
  }
}

export default function PaymentMethodList({ paymentMethods, customerId, onUpdate }: PaymentMethodListProps) {
  const [deletingId, setDeletingId] = useState<string | null>(null)

  const handleDeletePaymentMethod = async (paymentMethodId: string) => {
    if (!confirm('Are you sure you want to remove this payment method?')) {
      return
    }

    setDeletingId(paymentMethodId)

    try {
      const response = await paymentApi.deletePaymentMethod(paymentMethodId)
      
      if (response.success) {
        toast.success('Payment method removed successfully')
        onUpdate()
      } else {
        throw new Error(response.error || 'Failed to remove payment method')
      }
    } catch (error) {
      console.error('Error deleting payment method:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to remove payment method')
    } finally {
      setDeletingId(null)
    }
  }

  const formatExpiry = (month?: number, year?: number) => {
    if (!month || !year) return 'N/A'
    return `${month.toString().padStart(2, '0')}/${year.toString().slice(-2)}`
  }

  if (paymentMethods.length === 0) {
    return (
      <div className="text-center py-8">
        <CreditCardIcon className="mx-auto h-12 w-12 text-gray-400" />
        <h3 className="mt-2 text-sm font-medium text-gray-300">No payment methods</h3>
        <p className="mt-1 text-sm text-gray-500">
          Get started by adding a payment method to your account.
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {paymentMethods.map((method) => (
        <div
          key={method.id}
          className={`flex items-center justify-between p-4 bg-slate-700/50 rounded-lg border border-slate-600 ${
            !method.isEnabled ? 'opacity-50' : ''
          }`}
        >
          <div className="flex items-center">
            <div className="w-10 h-6 bg-slate-600 rounded mr-3 flex items-center justify-center">
              <span className="text-xs font-bold text-white">
                {getCardBrandIcon(method.brand)}
              </span>
            </div>
            <div>
              <div className="flex items-center">
                <p className="text-white font-medium">
                  {getCardBrandName(method.brand)} •••• {method.last4}
                </p>
                {method.isDefault && (
                  <span className="ml-3 bg-green-500/10 text-green-400 px-2 py-1 rounded text-xs">
                    Default
                  </span>
                )}
                {!method.isEnabled && (
                  <span className="ml-3 bg-red-500/10 text-red-400 px-2 py-1 rounded text-xs flex items-center">
                    <ExclamationTriangleIcon className="h-3 w-3 mr-1" />
                    Disabled
                  </span>
                )}
              </div>
              <p className="text-sm text-gray-400">
                Expires {formatExpiry(method.expiryMonth, method.expiryYear)}
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleDeletePaymentMethod(method.id)}
              disabled={deletingId === method.id}
              loading={deletingId === method.id}
            >
              <TrashIcon className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  )
}
