# docker/base.Dockerfile - Base image for all MCP services
FROM python:3.11-slim as base

# Install system dependencies
USER root
RUN apt-get update && apt-get install -y     curl     git     build-essential     && rm -rf /var/lib/apt/lists/*

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
