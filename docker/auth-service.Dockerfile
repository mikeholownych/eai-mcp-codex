# ---------- Base Image ----------
FROM mcp-base AS base

ENV SERVICE_NAME=auth-service \
    SERVICE_PORT=8007

# ---------- Dependencies Stage ----------
FROM base AS deps

WORKDIR /app

USER root

# Install additional system dependencies needed for this service
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic[email]>=1.8.0" > requirements.txt; \
    fi && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base AS auth-service

WORKDIR /app

USER root

# Copy dependencies
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy source code
COPY --chown=mcp:mcp src/common/ ./src/common/
COPY --chown=mcp:mcp src/auth_service/ ./src/auth_service/
COPY --chown=mcp:mcp scripts/start_auth_service.py ./start.py

# Create logs directory with proper permissions
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app

USER mcp

# Healthcheck for service
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8007/health || exit 1

EXPOSE 8007

CMD ["python", "start.py"]
