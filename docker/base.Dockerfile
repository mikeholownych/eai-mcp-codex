# docker/base.Dockerfile - Base image for all MCP services
FROM python:3.11-slim AS base

LABEL org.opencontainers.image.source="https://github.com/mikeholownych/mcp"
LABEL org.opencontainers.image.licenses="MIT"
LABEL org.opencontainers.image.version="1.0.0"

# Security hardening - run as root temporarily to set up system
USER root

# Install security updates and system dependencies
RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        git \
        build-essential \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user with consistent pattern
RUN groupadd --system --gid 1001 mcp && \
    useradd --system --uid 1001 --gid 1001 --create-home --shell /bin/bash mcp

# Secure directory structure
WORKDIR /app
RUN chown mcp:mcp /app && chmod 750 /app

# Python runtime env
ENV PYTHONPATH=/app \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/app:$PATH" \
    HOME="/home/mcp"

# Switch to non-root user for remaining operations
USER mcp
