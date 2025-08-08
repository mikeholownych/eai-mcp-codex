# =====================================
# PLAN MANAGEMENT SERVICE
# =====================================
FROM mcp-base as base

ENV SERVICE_NAME=plan-management \
    SERVICE_PORT=8002

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0\nsqlalchemy>=1.4.0\nalembic>=1.7.0" > requirements.txt; \
    fi && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base as plan-management

WORKDIR /app

# Copy dependencies
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

USER root

# Copy source code and migrations
COPY --chown=mcp:mcp src/common/ ./src/common/
COPY --chown=mcp:mcp src/plan_management/ ./src/plan_management/
COPY --chown=mcp:mcp scripts/start_plan_management.py ./start.py
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py
COPY --chown=mcp:mcp copy_optional.sh /copy_optional.sh
RUN chmod +x /copy_optional.sh && /copy_optional.sh

# Create logs directory and set ownership
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app

# Ensure correct user
USER mcp

# Expose service port
EXPOSE 8002

# Healthcheck for Docker
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=plan-management --port=8002

# Start the service (skip migrations for now)
CMD ["python", "start.py"]
