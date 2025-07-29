# =====================================
# MODEL ROUTER SERVICE (FIXED)
# =====================================
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash mcp
WORKDIR /app
RUN chown mcp:mcp /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy common utilities
COPY src/common/ ./common/
COPY config/ ./config/

USER mcp

# Health check script
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py
RUN chmod +x ./health_check.py

FROM base as model-router

COPY --chown=mcp:mcp src/model_router/ ./
COPY --chown=mcp:mcp scripts/start_model_router.py ./start.py

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=model-router --port=8001

CMD ["python", "start.py"]