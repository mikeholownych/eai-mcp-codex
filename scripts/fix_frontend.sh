#!/bin/bash

# Complete Frontend Fix Script
# Path: /opt/Tmux-Orchestrator/llm-stack/rag-agent/

set -e

echo "🔧 Complete Frontend Fix for new.ethical-ai-insider.com"
echo "======================================================"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${BLUE}ℹ️  $1${NC}"; }
log_success() { echo -e "${GREEN}✅ $1${NC}"; }
log_warning() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_error() { echo -e "${RED}❌ $1${NC}"; }

# Ensure we're in the right directory
PROJECT_ROOT="/opt/Tmux-Orchestrator/llm-stack/rag-agent"
cd "$PROJECT_ROOT" || { log_error "Cannot find project directory"; exit 1; }

log_info "Working in: $(pwd)"

# Step 1: Stop all containers
log_info "Stopping all containers..."
docker compose down --remove-orphans

# Step 2: Clean Docker system
log_info "Cleaning Docker system..."
docker system prune -f
docker volume prune -f

# Step 3: Backup and fix frontend configuration
log_info "Fixing frontend configuration..."

cd frontend || { log_error "Frontend directory not found"; exit 1; }

# Backup existing files
[ -f "next.config.js" ] && cp next.config.js next.config.js.backup
[ -f "package.json" ] && cp package.json package.json.backup

# Create a completely clean next.config.js
log_info "Creating clean next.config.js..."
cat > next.config.js << 'EOF'
/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://newapi.ethical-ai-insider.com',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'wss://newapi.ethical-ai-insider.com',
    NEXT_PUBLIC_SITE_URL: process.env.NEXTAUTH_URL || 'https://new.ethical-ai-insider.com',
  },

  images: {
    domains: ['avatars.githubusercontent.com'],
  },

  async redirects() {
    return [
      {
        source: '/dashboard',
        destination: '/',
        permanent: false,
      },
    ];
  },

  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
        ],
      },
    ];
  },
};

module.exports = nextConfig;
EOF

log_success "Created clean next.config.js"

# Step 4: Create clean package.json
log_info "Creating clean package.json..."
cat > package.json << 'EOF'
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev -p 3000",
    "build": "next build",
    "start": "next start -p 3000",
    "lint": "next lint"
  },
  "dependencies": {
    "@headlessui/react": "^2.2.6",
    "@heroicons/react": "^2.2.0",
    "@hookform/resolvers": "^5.2.1",
    "@monaco-editor/react": "^4.7.0",
    "@radix-ui/react-dialog": "^1.1.14",
    "@radix-ui/react-dropdown-menu": "^2.1.15",
    "@radix-ui/react-tabs": "^1.1.12",
    "@radix-ui/react-toast": "^1.2.14",
    "@tanstack/react-query": "^5.83.0",
    "@types/uuid": "^10.0.0",
    "axios": "^1.11.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.534.0",
    "monaco-editor": "^0.52.2",
    "next": "15.4.5",
    "next-auth": "^4.24.11",
    "react": "19.1.0",
    "react-dom": "19.1.0",
    "react-hook-form": "^7.61.1",
    "recharts": "^3.1.0",
    "socket.io-client": "^4.8.1",
    "tailwind-merge": "^3.3.1",
    "uuid": "^11.1.0",
    "zod": "^4.0.13",
    "zustand": "^5.0.6"
  },
  "devDependencies": {
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "eslint": "^9",
    "eslint-config-next": "15.4.5",
    "tailwindcss": "^4",
    "typescript": "^5"
  }
}
EOF

log_success "Created clean package.json"

# Step 5: Create simple Dockerfile
log_info "Creating optimized Dockerfile..."
cat > Dockerfile << 'EOF'
FROM node:18-alpine AS base

# Dependencies
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci

# Builder
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .

ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

RUN npm run build

# Runner
FROM base AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000

CMD ["node", "server.js"]
EOF

log_success "Created optimized Dockerfile"

# Step 6: Clean build artifacts
log_info "Cleaning build artifacts..."
rm -rf .next node_modules package-lock.json

# Step 7: Go back to project root
cd "$PROJECT_ROOT"

# Step 8: Check main .env file
log_info "Checking main .env file..."
if [ -f ".env" ]; then
    log_success "Main .env file exists"
    
    # Show relevant variables (without secrets)
    echo "Current environment variables:"
    grep -E "^(NEXT_PUBLIC_|NEXTAUTH_URL|NODE_ENV)" .env || log_warning "No Next.js variables found in .env"
else
    log_warning "Main .env file not found"
    log_info "Creating basic .env file..."
    cat > .env << 'EOF'
# Backend Configuration
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here

# Database
DATABASE_URL=postgresql://postgres:postgres@postgres:5432/codex
REDIS_URL=redis://redis:6379/0

# Security
SIGNING_SECRET=your-super-secret-signing-key-at-least-32-chars
NEXTAUTH_SECRET=your-nextauth-secret-32-chars-minimum

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
ALLOWED_GITHUB_USER=your-github-username

# Frontend URLs
NEXT_PUBLIC_API_URL=https://newapi.ethical-ai-insider.com
NEXT_PUBLIC_WS_URL=wss://newapi.ethical-ai-insider.com
NEXTAUTH_URL=https://new.ethical-ai-insider.com

# Environment
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1

# Cloudflare Tunnel
CLOUDFLARE_TUNNEL_TOKEN=your-cloudflare-tunnel-token
EOF
    log_warning "Please update .env with your actual values"
fi

# Step 9: Create frontend-specific .env.local
log_info "Creating frontend .env.local..."
cat > frontend/.env.local << 'EOF'
NEXT_PUBLIC_API_URL=https://newapi.ethical-ai-insider.com
NEXT_PUBLIC_WS_URL=wss://newapi.ethical-ai-insider.com
NEXTAUTH_URL=https://new.ethical-ai-insider.com
NODE_ENV=production
NEXT_TELEMETRY_DISABLED=1
EOF

log_success "Created frontend .env.local"

# Step 10: Test local build first
log_info "Testing local build..."
cd frontend

if command -v node >/dev/null 2>&1; then
    log_info "Node version: $(node --version)"
    
    log_info "Installing dependencies locally..."
    npm install --legacy-peer-deps
    
    log_info "Testing build locally..."
    if npm run build; then
        log_success "Local build successful!"
        cd ..
    else
        log_error "Local build failed"
        cd ..
        exit 1
    fi
else
    log_warning "Node.js not available locally, skipping local test"
    cd ..
fi

# Step 11: Build Docker image
log_info "Building Docker image..."
if docker compose build frontend --no-cache --pull; then
    log_success "Docker build successful!"
else
    log_error "Docker build failed"
    log_info "Checking for syntax errors in next.config.js..."
    node -c frontend/next.config.js && log_success "Config syntax OK" || log_error "Config syntax error"
    exit 1
fi

# Step 12: Start services
log_info "Starting services..."
docker compose up -d

# Wait for startup
log_info "Waiting for services to start..."
sleep 30

# Step 13: Health checks
log_info "Performing health checks..."

# Check if frontend container is running
if docker compose ps frontend | grep -q "Up"; then
    log_success "Frontend container is running"
else
    log_error "Frontend container failed to start"
    log_info "Container logs:"
    docker compose logs frontend
    exit 1
fi

# Check if frontend is responding
log_info "Testing frontend connectivity..."
if curl -f http://localhost:3000 >/dev/null 2>&1; then
    log_success "Frontend responding on localhost:3000"
else
    log_warning "Frontend not responding on localhost:3000"
    log_info "Checking logs..."
    docker compose logs frontend | tail -20
fi

# Step 14: Start with tunnel if available
if [ -f "docker-compose.tunnel.yml" ]; then
    log_info "Starting with Cloudflare tunnel..."
    docker compose -f docker-compose.yml -f docker-compose.tunnel.yml up -d
    
    sleep 10
    
    if docker compose ps cloudflare-tunnel | grep -q "Up"; then
        log_success "Cloudflare tunnel is running"
    else
        log_warning "Cloudflare tunnel failed to start"
        docker compose logs cloudflare-tunnel | tail -10
    fi
else
    log_warning "Tunnel configuration not found"
fi

# Step 15: Final status
echo ""
log_success "Frontend fix completed!"
echo ""
echo "Status Summary:"
echo "==============="
docker compose ps

echo ""
echo "Next Steps:"
echo "1. Update .env with your actual API keys and secrets"
echo "2. Update frontend/.env.local if needed"
echo "3. Test locally: http://localhost:3000"
echo "4. Check external site: https://new.ethical-ai-insider.com"
echo ""
echo "Troubleshooting:"
echo "- Frontend logs: docker compose logs frontend"
echo "- Tunnel logs: docker compose logs cloudflare-tunnel"
echo "- Rebuild if needed: docker compose build frontend --no-cache"
echo ""

# Test external connectivity
log_info "Testing external site..."
if curl -f -I https://new.ethical-ai-insider.com >/dev/null 2>&1; then
    log_success "🎉 Site is accessible at https://new.ethical-ai-insider.com"
else
    log_warning "External site not yet accessible"
    echo "This may be due to:"
    echo "- DNS propagation (can take up to 48 hours)"
    echo "- Cloudflare tunnel configuration"
    echo "- Firewall settings"
    echo ""
    echo "Check tunnel status with: docker compose logs cloudflare-tunnel"
fi
