# ---------- Base Image ----------
FROM node:18-alpine AS base

LABEL org.opencontainers.image.source="https://github.com/mikeholownych/mcp"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

# Security hardening and dependencies
RUN apk add --no-cache --update \
    libc6-compat \
    dumb-init \
    && apk upgrade

# Environment setup
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000

# ---------- Dependencies ----------
FROM base AS deps
WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./

# Install production dependencies only
RUN npm ci --omit=dev --frozen-lockfile && \
    npm cache clean --force

# ---------- Builder ----------
FROM base AS builder
WORKDIR /app

# Install all dependencies for build (including dev)
COPY package.json package-lock.json* ./
RUN npm ci --frozen-lockfile

# Copy source code
COPY . .

# Build Next.js application
RUN npm run build

# ---------- Final Runner ----------
FROM base AS runner

WORKDIR /app

# Create non-root user with proper security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs --ingroup nodejs

# Copy only necessary runtime artifacts
COPY --from=builder --chown=nextjs:nodejs /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static
COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --from=builder --chown=nextjs:nodejs /app/package.json ./package.json

# Switch to non-root user
USER nextjs

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD wget --no-verbose --tries=1 --spider http://localhost:3000/api/health || exit 1

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]
CMD ["npm", "start"]
