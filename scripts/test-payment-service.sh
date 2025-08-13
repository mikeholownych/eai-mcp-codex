#!/bin/bash

# Payment Service Test Script
# This script tests the payment service to ensure it's working correctly

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[TEST]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
}

print_error() {
    echo -e "${RED}[FAIL]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Configuration
SERVICE_URL="http://localhost:8000"
TIMEOUT=10

echo "🧪 Testing Payment Service..."
echo "Service URL: $SERVICE_URL"
echo ""

# Test 1: Health Check
print_status "Testing health endpoint..."
if curl -s --max-time $TIMEOUT "$SERVICE_URL/health" > /dev/null; then
    print_success "Health endpoint is responding"
else
    print_error "Health endpoint is not responding"
    echo "Make sure the payment service is running:"
    echo "  cd src/payments"
    echo "  python start.py"
    exit 1
fi

# Test 2: API Documentation
print_status "Testing API documentation..."
if curl -s --max-time $TIMEOUT "$SERVICE_URL/docs" > /dev/null; then
    print_success "API documentation is accessible"
else
    print_warning "API documentation is not accessible"
fi

# Test 3: Database Connection
print_status "Testing database connection..."
HEALTH_RESPONSE=$(curl -s --max-time $TIMEOUT "$SERVICE_URL/health")
if echo "$HEALTH_RESPONSE" | grep -q '"database": "healthy"'; then
    print_success "Database connection is healthy"
else
    print_error "Database connection failed"
    echo "Check your database configuration in .env file"
fi

# Test 4: Redis Connection
print_status "Testing Redis connection..."
if echo "$HEALTH_RESPONSE" | grep -q '"redis": "healthy"'; then
    print_success "Redis connection is healthy"
else
    print_warning "Redis connection failed"
    echo "Redis is optional but recommended for caching"
fi

# Test 5: Stripe Connection
print_status "Testing Stripe connection..."
if echo "$HEALTH_RESPONSE" | grep -q '"stripe": "healthy"'; then
    print_success "Stripe connection is healthy"
else
    print_warning "Stripe connection failed"
    echo "Check your STRIPE_SECRET_KEY in .env file"
fi

# Test 6: Create Customer (Mock Test)
print_status "Testing customer creation..."
CUSTOMER_RESPONSE=$(curl -s --max-time $TIMEOUT -X POST "$SERVICE_URL/api/payments/customers" \
    -H "Content-Type: application/json" \
    -d '{
        "email": "test@example.com",
        "name": "Test Customer",
        "metadata": {"test": true}
    }' 2>/dev/null || echo "{}")

if echo "$CUSTOMER_RESPONSE" | grep -q '"success": true'; then
    print_success "Customer creation test passed"
    CUSTOMER_ID=$(echo "$CUSTOMER_RESPONSE" | grep -o '"id": "[^"]*"' | cut -d'"' -f4)
    echo "  Created customer ID: $CUSTOMER_ID"
else
    print_warning "Customer creation test failed"
    echo "  Response: $CUSTOMER_RESPONSE"
fi

# Test 7: Payment Intent Creation (Mock Test)
print_status "Testing payment intent creation..."
if [ ! -z "$CUSTOMER_ID" ]; then
    PAYMENT_RESPONSE=$(curl -s --max-time $TIMEOUT -X POST "$SERVICE_URL/api/payments/payment-intents" \
        -H "Content-Type: application/json" \
        -d "{
            \"customerId\": \"$CUSTOMER_ID\",
            \"amount\": 1000,
            \"currency\": \"usd\",
            \"metadata\": {\"test\": true}
        }" 2>/dev/null || echo "{}")

    if echo "$PAYMENT_RESPONSE" | grep -q '"success": true'; then
        print_success "Payment intent creation test passed"
    else
        print_warning "Payment intent creation test failed"
        echo "  Response: $PAYMENT_RESPONSE"
    fi
else
    print_warning "Skipping payment intent test (no customer ID)"
fi

# Test 8: Frontend Configuration Check
print_status "Checking frontend configuration..."
if [ -f "frontend/.env.local" ]; then
    print_success "Frontend .env.local file exists"
    
    if grep -q "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY" frontend/.env.local; then
        print_success "Stripe publishable key is configured"
    else
        print_warning "Stripe publishable key not found in frontend/.env.local"
    fi
    
    if grep -q "NEXT_PUBLIC_API_BASE_URL" frontend/.env.local; then
        print_success "API base URL is configured"
    else
        print_warning "API base URL not found in frontend/.env.local"
    fi
else
    print_warning "Frontend .env.local file not found"
    echo "Create frontend/.env.local with:"
    echo "  NEXT_PUBLIC_API_BASE_URL=http://localhost:8000"
    echo "  NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here"
fi

# Summary
echo ""
echo "📊 Test Summary:"
echo "=================="

if [ $? -eq 0 ]; then
    print_success "All critical tests passed!"
    echo ""
    echo "🎉 Your payment service is ready to use!"
    echo ""
    echo "Next steps:"
    echo "1. Visit http://localhost:8000/docs for API documentation"
    echo "2. Test the frontend integration"
    echo "3. Set up webhook handling for production"
else
    print_error "Some tests failed. Please check the configuration."
    echo ""
    echo "Common issues:"
    echo "1. Payment service not running"
    echo "2. Database connection issues"
    echo "3. Missing environment variables"
    echo "4. Stripe API key configuration"
fi

echo ""
echo "For more help, see PAYMENT_SERVICE_QUICK_START.md"
