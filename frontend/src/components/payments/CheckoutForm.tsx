'use client'

import React, { useState } from 'react'
import { useStripe, useElements, CardElement } from '@stripe/react-stripe-js'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import Button from '@/components/ui/Button'
import { paymentApi } from '@/lib/api'
import { toast } from '@/lib/toast'

const checkoutSchema = z.object({
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

type CheckoutFormData = z.infer<typeof checkoutSchema>

interface CheckoutFormProps {
  customerId: string
  amount: number
  currency: string
  description: string
  onSuccess?: (paymentIntent: any) => void
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

export default function CheckoutForm({ 
  customerId, 
  amount, 
  currency, 
  description, 
  onSuccess, 
  onCancel 
}: CheckoutFormProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [isLoading, setIsLoading] = useState(false)

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<CheckoutFormData>({
    resolver: zodResolver(checkoutSchema),
  })

  const formatAmount = (amount: number, currency: string) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(amount / 100) // Assuming amount is in cents
  }

  const onSubmit = async (data: CheckoutFormData) => {
    if (!stripe || !elements) {
      toast.error('Stripe is not loaded')
      return
    }

    setIsLoading(true)

    try {
      // Create a payment intent
      const paymentIntentResponse = await paymentApi.createPaymentIntent({
        customerId,
        amount,
        currency,
        captureMethod: 'automatic',
        confirmationMethod: 'automatic',
        metadata: {
          description,
          source: 'frontend',
        },
      })

      if (!paymentIntentResponse.success || !paymentIntentResponse.data) {
        throw new Error(paymentIntentResponse.error || 'Failed to create payment intent')
      }

      const cardElement = elements.getElement(CardElement)
      if (!cardElement) {
        throw new Error('Card element not found')
      }

      // Confirm the payment intent with the card element
      const { error, paymentIntent } = await stripe.confirmCardPayment(
        paymentIntentResponse.data.providerId,
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

      if (paymentIntent?.status === 'succeeded') {
        toast.success('Payment completed successfully!')
        onSuccess?.(paymentIntent)
      } else if (paymentIntent?.status === 'requires_action') {
        // Handle 3D Secure authentication
        const { error: confirmError } = await stripe.confirmCardPayment(
          paymentIntentResponse.data.providerId
        )
        
        if (confirmError) {
          throw new Error(confirmError.message)
        }
        
        toast.success('Payment completed successfully!')
        onSuccess?.(paymentIntent)
      } else {
        throw new Error('Payment was not successful')
      }
    } catch (error) {
      console.error('Error processing payment:', error)
      toast.error(error instanceof Error ? error.message : 'Failed to process payment')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-white mb-2">Complete Payment</h3>
        <p className="text-gray-400 mb-4">{description}</p>
        <div className="bg-slate-800 p-4 rounded-lg">
          <p className="text-white font-medium">
            Total: {formatAmount(amount, currency)}
          </p>
        </div>
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

      {/* Security Notice */}
      <div className="bg-blue-500/10 border border-blue-500/20 rounded-lg p-4">
        <p className="text-sm text-blue-400">
          🔒 Your payment information is secure and encrypted. We never store your card details.
        </p>
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
          Pay {formatAmount(amount, currency)}
        </Button>
      </div>
    </form>
  )
}
