# Planner Agent Service Dockerfile
FROM mcp-base as planner-agent

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
ENV SERVICE_NAME=planner-agent
ENV SERVICE_PORT=8013

# Expose port
EXPOSE 8013

# Run the agent
CMD ["python", "scripts/start_planner_agent.py"]