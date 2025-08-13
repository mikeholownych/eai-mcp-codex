'use client'

import React from 'react'
import { Elements } from '@stripe/react-stripe-js'
import { loadStripe } from '@stripe/stripe-js'

import { STRIPE_CONFIG } from '@/lib/config'

// Initialize Stripe with your publishable key
const stripePromise = loadStripe(STRIPE_CONFIG.publishableKey)

interface StripeProviderProps {
  children: React.ReactNode
}

export default function StripeProvider({ children }: StripeProviderProps) {
  return (
    <Elements stripe={stripePromise}>
      {children}
    </Elements>
  )
}
