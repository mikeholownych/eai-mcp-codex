# Security Agent Service Dockerfile
FROM llm-stack-base as security-agent

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY scripts/ ./scripts/

# Create logs directory
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONPATH=/app
ENV SERVICE_NAME=security-agent
ENV SERVICE_PORT=8014

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8014/health || exit 1

# Expose port
EXPOSE 8014

# Run the agent
CMD ["python", "scripts/start_security_agent.py"]