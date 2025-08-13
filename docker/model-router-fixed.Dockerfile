# =====================================
# MODEL ROUTER SERVICE (FIXED VERSION)
# =====================================
FROM mcp-base as base

ENV SERVICE_NAME=model-router \
    SERVICE_PORT=8001

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0\nopenai>=1.0.0" > requirements.txt; \
    fi && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base as model-router

WORKDIR /app

USER root

# Copy dependencies
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy common modules and config
COPY --chown=mcp:mcp src/common/ ./common/
COPY --chown=mcp:mcp config/ ./config/
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py

# Copy model router service source + entrypoint
COPY --chown=mcp:mcp src/model_router/ ./src/model_router/
COPY --chown=mcp:mcp scripts/start_model_router.py ./start.py

# Create logs directory and set ownership and permissions
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app && \
    chmod +x ./health_check.py

USER mcp

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=model-router --port=8001

CMD ["python", "start.py"]
