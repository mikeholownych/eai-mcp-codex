# Production Dockerfile for Staff Frontend

# Stage 1: Build the application
FROM node:18-alpine AS builder

LABEL org.opencontainers.image.source="https://github.com/mikeholownych/mcp"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

ENV NODE_ENV=production

WORKDIR /app

# Install dependencies
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile --production && npm cache clean --force

# Copy source code and build
COPY . .
RUN npm run build

# Stage 2: Run the application
FROM node:18-alpine AS runner

# Install system dependencies
RUN apk add --no-cache dumb-init curl

# Create non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs --ingroup nodejs

WORKDIR /app

# Copy necessary files from the builder stage
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./package.json

# Switch to non-root user
USER nextjs

EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
  CMD curl -f http://localhost:3001/api/health || exit 1

ENTRYPOINT ["dumb-init", "--"]
CMD ["npm", "run", "start"]