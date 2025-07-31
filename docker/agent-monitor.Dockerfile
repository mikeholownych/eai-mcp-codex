# Agent Monitor Service Dockerfile
FROM llm-stack-base as agent-monitor

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
ENV SERVICE_NAME=agent-monitor
ENV SERVICE_PORT=8016

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8016/health || exit 1

# Expose port
EXPOSE 8016

# Run the service
CMD ["python", "scripts/start_agent_monitor.py"]