#!/bin/bash

# Payment Service Setup Script
# This script sets up the payment service with all necessary dependencies

set -e

echo "🚀 Setting up Payment Service..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   print_error "This script should not be run as root"
   exit 1
fi

# Check if Python 3.11+ is installed
print_status "Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
    if python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
        print_success "Python $PYTHON_VERSION found"
    else
        print_error "Python 3.11+ is required. Found: $PYTHON_VERSION"
        exit 1
    fi
else
    print_error "Python 3 is not installed"
    exit 1
fi

# Check if pip is installed
print_status "Checking pip..."
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed"
    exit 1
fi

# Check if Docker is installed (optional)
if command -v docker &> /dev/null; then
    print_success "Docker found"
    DOCKER_AVAILABLE=true
else
    print_warning "Docker not found. You can still run the service locally."
    DOCKER_AVAILABLE=false
fi

# Create virtual environment
print_status "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_status "Virtual environment already exists"
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install Python dependencies
print_status "Installing Python dependencies..."
cd src/payments
pip install --upgrade pip
pip install -r requirements.txt
print_success "Python dependencies installed"

# Create .env file if it doesn't exist
print_status "Setting up environment configuration..."
if [ ! -f ".env" ]; then
    cat > .env << EOF
# Payment Service Environment Configuration
ENVIRONMENT=development
LOG_LEVEL=INFO

# Database Configuration
DATABASE_URL=postgresql://postgres:password@localhost:5432/payments

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# Stripe Configuration (Replace with your actual keys)
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
EOF
    print_success "Environment file created (.env)"
    print_warning "Please update the .env file with your actual Stripe keys"
else
    print_status "Environment file already exists"
fi

# Create logs directory
print_status "Creating logs directory..."
mkdir -p logs
print_success "Logs directory created"

# Initialize database (if PostgreSQL is available)
print_status "Checking database connection..."
if command -v psql &> /dev/null; then
    print_status "PostgreSQL found. You can initialize the database manually:"
    echo "  cd src/payments"
    echo "  python -c \"from database import init_db; init_db()\""
else
    print_warning "PostgreSQL not found. You can use Docker to run the database:"
    echo "  docker-compose up postgres redis -d"
fi

# Setup instructions
echo ""
print_success "Payment Service setup completed!"
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Update the .env file with your Stripe keys:"
echo "   - Get your keys from https://dashboard.stripe.com/apikeys"
echo "   - Update STRIPE_SECRET_KEY and STRIPE_WEBHOOK_SECRET"
echo ""
echo "2. Start the database (choose one option):"
if [ "$DOCKER_AVAILABLE" = true ]; then
    echo "   Option A (Docker): docker-compose up postgres redis -d"
fi
echo "   Option B (Local): Install PostgreSQL and Redis locally"
echo ""
echo "3. Initialize the database:"
echo "   cd src/payments"
echo "   python -c \"from database import init_db; init_db()\""
echo ""
echo "4. Start the payment service:"
echo "   cd src/payments"
echo "   python start.py"
echo ""
echo "5. Test the service:"
echo "   curl http://localhost:8000/health"
echo ""
echo "6. For frontend integration, update your .env.local:"
echo "   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000"
echo "   NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_test_your_key_here"
echo ""
print_success "Setup complete! 🎉"
