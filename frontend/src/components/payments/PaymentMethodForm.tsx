'use client'

import React, { useState } from 'react'
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Button from '@/components/ui/Button'
import { paymentApi } from '@/lib/api'
import { toast } from '@/lib/toast'

const paymentMethodSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  email: z.string().email('Valid email is required'),
  address: z.object({
    line1: z.string().min(1, 'Address is required'),
    city: z.string().min(1, 'City is required'),
    state: z.string().min(1, 'State is required'),
    postalCode: z.string().min(1, 'Postal code is required'),
    country: z.string().min(1, 'Country is required'),
  }),
})

type PaymentMethodFormData = z.infer<typeof paymentMethodSchema>

interface PaymentMethodFormProps {
  customerId: string
  onSuccess?: (paymentMethod: any) => void
  onCancel?: () => void
}

const cardElementOptions = {
  style: {
    base: {
      fontSize: '16px',
      color: '#ffffff',
      '::placeholder': {
        color: '#9ca3af',
      },
      backgroundColor: 'transparent',
    },
    invalid: {
      color: '#ef4444',
    },
  },
}

export default function PaymentMethodForm({ customerId, onSuccess, onCancel }: PaymentMethodFormProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<PaymentMethodFormData>({
    resolver: zodResolver(paymentMethodSchema),
  })

  const onSubmit = async (data: PaymentMethodFormData) => {
    if (!stripe || !elements) {
      toast.error('Stripe is not loaded')
      return
    }

    setIsLoading(true)

    try {
      // Create a setup intent
      const setupIntentResponse = await paymentApi.createSetupIntent({
        customerId,
        paymentMethodTypes: ['card'],
        metadata: { source: 'frontend' },
      })

      if (!setupIntentResponse.success || !setupIntentResponse.data) {
        throw new Error(setupIntentResponse.error || 'Failed to create setup intent')
      }

      const cardElement = elements.getElement(CardElement)
      if (!cardElement) {
        throw new Error('Card element not found')
      }

      // Confirm the setup intent with the card element
      const { error, setupIntent } = await stripe.confirmCardSetup(
        setupIntentResponse.data.id,
        {
          payment_method: {
            card: cardElement,
            billing_details: {
              name: data.name,
              email: data.email,
              address: data.address,
            },
          },
        }
      )

      if (error) {
        throw new Error(error.message)
      }

      if (setupIntent?.status === 'succeeded') {
        // Create payment method in our backend
        const paymentMethodResponse = await paymentApi.createPaymentMethod({
          customerId,
          paymentMethodType: 'card',
          paymentMethodData: {
            providerPaymentMethodId: setupIntent.payment_method,
            billingDetails: {
              name: data.name,
              email: data.email,
              address: data.address,
            },
          },
        })

        if (paymentMethodResponse.success && paymentMethodResponse.data) {
          toast.success('Payment method added successfully')
          onSuccess?.(paymentMethodResponse.data)
        } else {
          throw new Error(paymentMethodResponse.error || 'Failed to save payment method')
        }
      } else {
        throw new Error('Setup intent was not successful')
      }
    } catch (error) {
      console.error('Error adding payment method:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to add payment method')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-white mb-4">Add Payment Method</h3>
        <p className="text-gray-400 mb-6">
          Add a new credit or debit card to your account for future payments.
        </p>
      </div>

      {/* Card Element */}
      <div className="space-y-2">
        <label className="block text-sm font-medium text-gray-300">Card Information</label>
        <div className="p-3 border border-slate-600 rounded-lg bg-slate-800">
          <CardElement options={cardElementOptions} />
        </div>
      </div>

      {/* Billing Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Full Name</label>
          <input
            {...register('name')}
            type="text"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="John Doe"
          />
          {errors.name && <p className="mt-1 text-sm text-red-400">{errors.name.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
          <input
            {...register('email')}
            type="email"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="john@example.com"
          />
          {errors.email && <p className="mt-1 text-sm text-red-400">{errors.email.message}</p>}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Address</label>
        <input
          {...register('address.line1')}
          type="text"
          className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 mb-3"
          placeholder="123 Main St"
        />
        {errors.address?.line1 && <p className="mt-1 text-sm text-red-400">{errors.address.line1.message}</p>}
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">City</label>
          <input
            {...register('address.city')}
            type="text"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="New York"
          />
          {errors.address?.city && <p className="mt-1 text-sm text-red-400">{errors.address.city.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">State</label>
          <input
            {...register('address.state')}
            type="text"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="NY"
          />
          {errors.address?.state && <p className="mt-1 text-sm text-red-400">{errors.address.state.message}</p>}
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-300 mb-2">Postal Code</label>
          <input
            {...register('address.postalCode')}
            type="text"
            className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="10001"
          />
          {errors.address?.postalCode && <p className="mt-1 text-sm text-red-400">{errors.address.postalCode.message}</p>}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-300 mb-2">Country</label>
        <input
          {...register('address.country')}
          type="text"
          className="w-full px-3 py-2 bg-slate-800 border border-slate-600 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="United States"
        />
        {errors.address?.country && <p className="mt-1 text-sm text-red-400">{errors.address.country.message}</p>}
      </div>

      {/* Action Buttons */}
      <div className="flex justify-end space-x-3 pt-4">
        <Button
          type="button"
          variant="outline"
          onClick={onCancel}
          disabled={isLoading}
        >
          Cancel
        </Button>
        <Button
          type="submit"
          disabled={isLoading}
          loading={isLoading}
        >
          Add Payment Method
        </Button>
      </div>
    </form>
  )
}
