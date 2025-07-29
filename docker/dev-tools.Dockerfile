# =====================================
# DEVELOPMENT TOOLS CONTAINER
# =====================================
# docker/dev-tools.Dockerfile
FROM python:3.11-slim as dev-tools

# Install core tools and docker-compose-plugin
RUN apt-get update && \
    apt-get install -y \
    ca-certificates \
    curl \
    git \
    vim \
    jq \
    httpie \
    postgresql-client \
    redis-tools \
    gnupg \
    lsb-release && \
    mkdir -p /etc/apt/keyrings && \
    curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg && \
    echo \
    "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
    https://download.docker.com/linux/debian \
    $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null && \
    apt-get update && \
    apt-get install -y docker-compose-plugin && \
    rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --upgrade pip && \
    pip install --no-cache-dir \
    "PyYAML==6.0.1" \
    ipython \
    pytest \
    black \
    flake8 \
    mypy \
    pre-commit \
    pydantic \
    pydantic-settings \
    httpx

WORKDIR /workspace

CMD ["/bin/bash"]
