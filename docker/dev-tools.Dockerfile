# =====================================
# DEVELOPMENT TOOLS CONTAINER
# =====================================
# docker/dev-tools.Dockerfile
FROM python:3.11-slim as dev-tools

# Install development tools
RUN apt-get update && apt-get install -y \
    curl \
    git \
    vim \
    jq \
    httpie \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python development tools
RUN pip install --no-cache-dir \
    ipython \
    pytest \
    black \
    flake8 \
    mypy \
    pre-commit \
    docker-compose

WORKDIR /workspace

CMD ["/bin/bash"]
