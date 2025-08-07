# ---------- Base Image ----------
FROM mcp-base AS base

ENV SERVICE_NAME=agent-monitor \
    SERVICE_PORT=8016

# ---------- Dependency Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0" > requirements.txt; \
    fi && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Application Stage ----------
FROM base as agent-monitor

WORKDIR /app

USER root

# Copy installed deps
COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source
COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp scripts/ ./scripts/

# Create logs directory and set ownership
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app

# Set user
USER mcp

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8016/health || exit 1

# Expose port
EXPOSE 8016

# Run the service
CMD ["python", "scripts/start_agent_monitor.py"]
