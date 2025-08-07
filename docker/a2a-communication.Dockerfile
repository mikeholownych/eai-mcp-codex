# ---------- Base Python Image ----------
FROM mcp-base as base

ENV SERVICE_NAME=a2a-communication \
    SERVICE_PORT=8010

# ---------- Stage: Build Dependencies ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\nredis>=4.0.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0" > requirements.txt; \
    fi && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Stage: Application ----------
FROM base as a2a-communication

WORKDIR /app

USER root

# Copy dependencies from deps stage
COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy application source code
COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp scripts/ ./scripts/

# Create logs directory with correct permissions
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app

# Health check for the service
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8010/health || exit 1

# Set non-root user
USER mcp

# Expose port
EXPOSE 8010

# Run the service using Uvicorn
CMD ["python", "-m", "uvicorn", "src.a2a_communication.app:app", "--host", "0.0.0.0", "--port", "8010"]
