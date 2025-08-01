# =====================================
# DEVELOPMENT TOOLS CONTAINER
# =====================================
# docker/dev-tools.Dockerfile
FROM mcp-base as dev-tools

USER root

# Install core tools and docker-compose-plugin
RUN mkdir -p /var/lib/apt/lists/partial && apt-get update && apt-get install -y     ca-certificates     vim     jq     httpie     postgresql-client     redis-tools     gnupg     lsb-release &&     mkdir -p /etc/apt/keyrings &&     curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg &&     echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null &&     apt-get update &&     apt-get install -y docker-compose-plugin &&     rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1

# Install Python development tools
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt && pip freeze

USER mcp

WORKDIR /workspace

CMD ["/bin/bash"]
