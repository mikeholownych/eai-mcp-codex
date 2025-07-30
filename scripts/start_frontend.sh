#!/bin/bash

# Start Frontend Services Script
# This script starts both customer and staff frontend applications

set -e

echo "=== MCP Frontend Services Startup ==="

# Change to the project directory
cd /opt/llm-stack/rag-agent

# Check if Node.js and npm are available
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    exit 1
fi

if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Build the application
echo "Building frontend application..."
npm run build

# Function to start customer frontend
start_customer_frontend() {
    echo "Starting Customer Frontend on port 3000..."
    PORT=3000 npm start &
    CUSTOMER_PID=$!
    echo "Customer Frontend PID: $CUSTOMER_PID"
}

# Function to start staff frontend
start_staff_frontend() {
    echo "Starting Staff Frontend on port 3001..."
    PORT=3001 npm start &
    STAFF_PID=$!
    echo "Staff Frontend PID: $STAFF_PID"
}

# Function to handle cleanup on exit
cleanup() {
    echo "Shutting down frontend services..."
    if [ ! -z "$CUSTOMER_PID" ]; then
        kill $CUSTOMER_PID 2>/dev/null || true
    fi
    if [ ! -z "$STAFF_PID" ]; then
        kill $STAFF_PID 2>/dev/null || true
    fi
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Start both frontends
start_customer_frontend
start_staff_frontend

# Wait for processes to start
sleep 3

# Check if both services are running
echo "Checking frontend services..."

if curl -f http://localhost:3000/api/health >/dev/null 2>&1; then
    echo "✅ Customer Frontend (port 3000) - HEALTHY"
else
    echo "❌ Customer Frontend (port 3000) - UNHEALTHY"
fi

if curl -f http://localhost:3001/api/health >/dev/null 2>&1; then
    echo "✅ Staff Frontend (port 3001) - HEALTHY"
else
    echo "❌ Staff Frontend (port 3001) - UNHEALTHY"
fi

echo "=== Frontend Services Started ==="
echo "Customer Frontend: http://localhost:3000"
echo "Staff Frontend: http://localhost:3001"
echo "Press Ctrl+C to stop all services"

# Wait for any process to exit
wait