# =====================================
# DEVELOPMENT TOOLS CONTAINER
# =====================================
# docker/dev-tools.Dockerfile

FROM mcp-base as dev-tools

USER root

# Update system and install dev utilities
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ca-certificates \
    vim \
    nano \
    jq \
    httpie \
    git \
    postgresql-client \
    redis-tools \
    curl \
    gnupg \
    lsb-release \
    bash-completion \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Docker CLI and Compose Plugin
RUN curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh && \
    DOCKER_CONFIG=/usr/lib/docker/cli-plugins && \
    mkdir -p $DOCKER_CONFIG && \
    curl -SL https://github.com/docker/compose/releases/download/v2.27.0/docker-compose-linux-x86_64 -o $DOCKER_CONFIG/docker-compose && \
    chmod +x $DOCKER_CONFIG/docker-compose && \
    ln -s $DOCKER_CONFIG/docker-compose /usr/local/bin/docker-compose

# Install Python developer tools
COPY requirements.txt .
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip freeze > /app/dev-tools-requirements.txt

# Set up secure user context
USER mcp

# Create writable dev workspace
WORKDIR /workspace

# Useful ENV for local usage
ENV PYTHONUNBUFFERED=1 \
    PATH="/workspace/.local/bin:$PATH"

# Default to bash shell
CMD ["/bin/bash"]
