# Frontend Payment Integration

This document describes the payment processing integration in the frontend application.

## Overview

The frontend integrates with the backend payment service to provide a complete payment processing experience using Stripe Elements for secure card input and PCI compliance.

## Components

### Core Components

1. **StripeProvider** (`src/components/providers/StripeProvider.tsx`)
   - Wraps the app with Stripe Elements context
   - Provides Stripe instance to child components

2. **PaymentMethodForm** (`src/components/payments/PaymentMethodForm.tsx`)
   - Secure form for adding new payment methods
   - Uses Stripe Elements for card input
   - Handles setup intents for tokenization

3. **PaymentMethodList** (`src/components/payments/PaymentMethodList.tsx`)
   - Displays saved payment methods
   - Allows deletion of payment methods
   - Shows payment method status and details

4. **CheckoutForm** (`src/components/payments/CheckoutForm.tsx`)
   - Complete checkout experience
   - Processes payments using payment intents
   - Handles 3D Secure authentication

### API Integration

The payment API is integrated through `src/lib/api.ts` with the following endpoints:

- **Customer Management**: Create, get, update customers
- **Payment Intents**: Create, confirm, capture, cancel payments
- **Payment Methods**: Create, list, delete payment methods
- **Setup Intents**: Create payment method setup flows
- **Refunds**: Process refunds for charges

## Setup

### 1. Environment Variables

Create a `.env.local` file with the following variables:

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT_MS=30000

# Stripe Configuration
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here

# Feature Flags
NEXT_PUBLIC_ENABLE_PAYMENTS=true
```

### 2. Dependencies

Install required dependencies:

```bash
npm install @stripe/react-stripe-js @stripe/stripe-js @tanstack/react-query
```

### 3. App Configuration

Wrap your app with the necessary providers:

```tsx
// app/layout.tsx
import StripeProvider from '@/components/providers/StripeProvider'
import QueryProvider from '@/components/providers/QueryProvider'

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <QueryProvider>
          <StripeProvider>
            {children}
          </StripeProvider>
        </QueryProvider>
      </body>
    </html>
  )
}
```

## Usage

### Adding Payment Methods

```tsx
import PaymentMethodForm from '@/components/payments/PaymentMethodForm'

function AddPaymentMethod() {
  const handleSuccess = (paymentMethod) => {
    console.log('Payment method added:', paymentMethod)
  }

  return (
    <PaymentMethodForm
      customerId="cus_123"
      onSuccess={handleSuccess}
      onCancel={() => setShowForm(false)}
    />
  )
}
```

### Displaying Payment Methods

```tsx
import PaymentMethodList from '@/components/payments/PaymentMethodList'

function PaymentMethods() {
  const [paymentMethods, setPaymentMethods] = useState([])

  return (
    <PaymentMethodList
      paymentMethods={paymentMethods}
      customerId="cus_123"
      onUpdate={() => refetchPaymentMethods()}
    />
  )
}
```

### Processing Payments

```tsx
import CheckoutForm from '@/components/payments/CheckoutForm'

function Checkout() {
  const handlePaymentSuccess = (paymentIntent) => {
    console.log('Payment successful:', paymentIntent)
  }

  return (
    <CheckoutForm
      customerId="cus_123"
      amount={7900} // $79.00 in cents
      currency="usd"
      description="Pro Plan - Monthly Subscription"
      onSuccess={handlePaymentSuccess}
      onCancel={() => setShowCheckout(false)}
    />
  )
}
```

## Security Features

1. **PCI Compliance**: Card data never touches your servers
2. **Tokenization**: Payment methods are stored as tokens
3. **3D Secure**: Automatic handling of Strong Customer Authentication
4. **Idempotency**: Prevents duplicate payments
5. **Webhook Verification**: Secure webhook processing

## Error Handling

The components include comprehensive error handling:

- Network errors
- Stripe API errors
- Validation errors
- User cancellation

Errors are displayed using the toast notification system.

## Testing

### Test Cards

Use these test card numbers for development:

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`

### Test Environment

The integration supports both test and live environments:

- **Test**: Uses Stripe test keys
- **Live**: Uses Stripe live keys

## Monitoring

Payment events are logged and can be monitored through:

- Stripe Dashboard
- Application logs
- Webhook events
- Audit trails

## Best Practices

1. **Always use HTTPS** in production
2. **Validate amounts** on both client and server
3. **Handle webhooks** for payment status updates
4. **Implement proper error handling**
5. **Use idempotency keys** for all operations
6. **Test thoroughly** with Stripe test cards
7. **Monitor payment failures** and implement retry logic

## Troubleshooting

### Common Issues

1. **Stripe not loaded**: Check publishable key configuration
2. **Payment declined**: Verify test card numbers
3. **3D Secure errors**: Ensure proper redirect handling
4. **Network errors**: Check API endpoint configuration

### Debug Mode

Enable debug logging by setting:

```env
NEXT_PUBLIC_DEBUG=true
```

This will log detailed information about payment operations to the console.
