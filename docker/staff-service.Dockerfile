# =====================================
# STAFF SERVICE
# =====================================
FROM mcp-base as base

ENV SERVICE_NAME=staff-service \
    SERVICE_PORT=8006

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0" > requirements.txt; \
    fi && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base as staff-service

WORKDIR /app

USER root

# Copy dependencies
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy service source code and scripts
COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp scripts/start_staff_service.py ./start.py
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py

# Ensure logs directory is secure
RUN mkdir -p /app/logs && chown -R mcp:mcp /app

# Use non-root user
USER mcp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=staff-service --port=8006

# Expose service port
EXPOSE 8006

# Run the service
CMD ["python", "start.py"]
