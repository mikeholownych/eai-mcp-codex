# docker/base.Dockerfile - Base image for all MCP services
FROM python:3.11-slim as base

# Security hardening
USER root

# Install security updates and system dependencies
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y \
        curl \
        git \
        build-essential \
        ca-certificates \
        && rm -rf /var/lib/apt/lists/* \
        && apt-get clean

# Create non-root user with secure settings
RUN useradd --create-home --shell /bin/bash mcp && \
    # Remove unnecessary system users and groups
    userdel -f games && \
    userdel -f gnats && \
    groupdel games && \
    groupdel gnats

# Set up secure directory structure
WORKDIR /app
RUN chown mcp:mcp /app && \
    chmod 750 /app && \
    # Remove world-readable permissions from sensitive directories
    chmod 700 /root && \
    chmod 755 /tmp

# Security hardening for Python
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install Python dependencies securely
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    # Remove pip cache after installation
    rm -rf /root/.cache/pip

# Copy common utilities
COPY src/common/ ./common/
COPY config/ ./config/

# Set secure file permissions
RUN chown -R mcp:mcp /app && \
    find /app -type f -exec chmod 640 {} \; && \
    find /app -type d -exec chmod 750 {} \;

USER mcp

# Health check script
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py
RUN chmod +x ./health_check.py

# Security runtime configurations
ENV PATH="/app:$PATH" \
    HOME="/home/mcp"
