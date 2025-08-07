# =====================================
# SECURITY AGENT SERVICE
# =====================================
FROM mcp-base as base

ENV SERVICE_NAME=security-agent \
    SERVICE_PORT=8014

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0\nbandit>=1.7.0\nsafety>=2.0.0" > requirements.txt; \
    fi && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base as security-agent

WORKDIR /app

USER root

# Copy dependencies
COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy service source code
COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp scripts/ ./scripts/
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py

# Create and secure logs directory
RUN mkdir -p /app/logs && chown -R mcp:mcp /app

# Switch to non-root user
USER mcp

# Expose service port
EXPOSE 8014

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=security-agent --port=8014

# Run the agent
CMD ["python", "scripts/start_security_agent.py"]
