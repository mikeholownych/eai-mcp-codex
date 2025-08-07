# =====================================
# VERIFICATION & FEEDBACK SERVICE
# =====================================
FROM mcp-base as base

ENV SERVICE_NAME=verification-feedback \
    SERVICE_PORT=8005

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one with NLP tools
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0\nnltk>=3.7.0\ntextstat>=0.7.0\npylint>=2.14.0" > requirements.txt; \
    fi && \
    python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base as verification-feedback

WORKDIR /app

USER root

# Copy dependencies
COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Copy service-specific and shared source files
COPY --chown=mcp:mcp src/common/ ./src/common/
COPY --chown=mcp:mcp src/verification_feedback/ ./src/verification_feedback/
COPY --chown=mcp:mcp scripts/start_verification_feedback.py ./start.py
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py

# Create logs directory and set ownership
RUN mkdir -p /app/logs && \
    chown -R mcp:mcp /app

# Ensure non-root runtime
USER mcp

# Expose internal port
EXPOSE 8005

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=verification-feedback --port=8005

# Start the service
CMD ["python", "start.py"]
