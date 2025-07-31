# Sandbox environment for running isolated tasks
FROM python:3.11-slim AS sandbox

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash sandbox
WORKDIR /home/sandbox

# Install Python dependencies as root
COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Drop privileges for runtime
USER sandbox

CMD ["python", "-c", "print('sandbox ready')"]
