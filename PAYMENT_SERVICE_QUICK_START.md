# Payment Service Quick Start Guide

This guide will help you set up and run the payment processing service quickly.

## 🚀 Quick Setup (Automated)

### Option 1: Using the Setup Script (Recommended)

```bash
# Run the automated setup script
./scripts/setup-payment-service.sh
```

This script will:
- Check system requirements
- Create virtual environment
- Install dependencies
- Create configuration files
- Provide next steps

### Option 2: Manual Setup

If you prefer manual setup, follow these steps:

## 📋 Prerequisites

- Python 3.11+
- pip3
- PostgreSQL (or Docker)
- Redis (or Docker)
- Stripe account

## 🔧 Manual Installation

### 1. Install Python Dependencies

```bash
# Navigate to payment service directory
cd src/payments

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in `src/payments/`:

```env
# Payment Service Environment Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/payments

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Stripe Configuration (Get from https://dashboard.stripe.com/apikeys)
STRIPE_SECRET_KEY=sk_test_your_stripe_secret_key_here
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# Security Configuration
SECRET_KEY=your-secret-key-here-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Feature Flags
ENABLE_WEBHOOKS=true
ENABLE_AUDIT_LOGGING=true
ENABLE_RATE_LIMITING=true

# Monitoring Configuration
ENABLE_METRICS=true
METRICS_PORT=9090
```

### 3. Database Setup

#### Option A: Using Docker (Recommended for Development)

```bash
# Start PostgreSQL and Redis
docker-compose up postgres redis -d

# Initialize database
python -c "from database import init_db; init_db()"
```

#### Option B: Local Installation

1. Install PostgreSQL and Redis locally
2. Create a database named `payments`
3. Run the initialization script:

```bash
python -c "from database import init_db; init_db()"
```

### 4. Start the Service

```bash
# Start the payment service
python start.py
```

The service will be available at `http://localhost:8000`

## 🧪 Testing the Service

### Health Check

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "services": {
    "database": "healthy",
    "redis": "healthy",
    "stripe": "healthy"
  }
}
```

### API Documentation

Visit `http://localhost:8000/docs` for interactive API documentation.

## 🔗 Frontend Integration

### 1. Install Frontend Dependencies

```bash
cd frontend
npm install @stripe/react-stripe-js @stripe/stripe-js @tanstack/react-query
```

### 2. Configure Frontend Environment

Create `.env.local` in the frontend directory:

```env
# API Configuration
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
NEXT_PUBLIC_API_TIMEOUT_MS=30000

# Stripe Configuration
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_publishable_key_here

# Feature Flags
NEXT_PUBLIC_ENABLE_PAYMENTS=true
```

### 3. Start Frontend

```bash
npm run dev
```

## 🧪 Testing with Stripe

### Test Card Numbers

Use these test card numbers for development:

- **Success**: `4242 4242 4242 4242`
- **Decline**: `4000 0000 0000 0002`
- **3D Secure**: `4000 0025 0000 3155`
- **Requires Authentication**: `4000 0025 0000 3155`

### Test Scenarios

1. **Add Payment Method**: Use the billing page to add a test card
2. **Process Payment**: Create a payment intent and confirm it
3. **Test Webhooks**: Use Stripe CLI to forward webhooks locally

## 🔧 Stripe CLI Setup (Optional)

For webhook testing:

```bash
# Install Stripe CLI
# macOS: brew install stripe/stripe-cli/stripe
# Windows: Download from https://github.com/stripe/stripe-cli/releases

# Login to Stripe
stripe login

# Forward webhooks to local service
stripe listen --forward-to localhost:8000/webhooks/stripe
```

## 🐳 Docker Deployment

### Development

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f payment-service
```

### Production

```bash
# Build and run production container
docker build -t payment-service .
docker run -d -p 8000:8000 --env-file .env payment-service
```

## 📊 Monitoring

### Health Endpoints

- `GET /health` - Service health check
- `GET /metrics` - Prometheus metrics (if enabled)

### Logs

Logs are written to:
- Console output
- `logs/payment_service.log`

## 🔒 Security Considerations

1. **Never commit API keys** to version control
2. **Use environment variables** for all sensitive data
3. **Enable HTTPS** in production
4. **Validate webhook signatures** (enabled by default)
5. **Use idempotency keys** for all operations

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check PostgreSQL is running
   - Verify DATABASE_URL in .env
   - Ensure database exists

2. **Stripe API Errors**
   - Verify STRIPE_SECRET_KEY is correct
   - Check Stripe account status
   - Ensure you're using test keys for development

3. **Webhook Issues**
   - Verify STRIPE_WEBHOOK_SECRET
   - Check webhook endpoint URL
   - Use Stripe CLI for local testing

4. **Frontend Integration Issues**
   - Check NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY
   - Verify API_BASE_URL points to correct service
   - Check browser console for errors

### Getting Help

1. Check the logs: `tail -f logs/payment_service.log`
2. Verify environment variables: `python -c "from config import PaymentSettings; print(PaymentSettings())"`
3. Test database connection: `python -c "from database import check_db_health; print(check_db_health())"`

## 📚 Next Steps

1. **Customize the service** for your specific needs
2. **Add authentication** to protect endpoints
3. **Implement webhook handling** for production
4. **Set up monitoring** and alerting
5. **Configure backup** and recovery procedures

## 🎉 Success!

Your payment service is now running! You can:

- Process payments through the API
- Manage payment methods
- Handle webhooks from Stripe
- Integrate with your frontend

For more information, see the full documentation in `docs/`.
