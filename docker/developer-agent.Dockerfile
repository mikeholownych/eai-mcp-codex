# Developer Agent Service Dockerfile
FROM mcp-base as developer-agent

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
ENV SERVICE_NAME=developer-agent
ENV SERVICE_PORT=8015

# Expose port
EXPOSE 8015

# Run the agent
CMD ["python", "scripts/start_developer_agent.py"]