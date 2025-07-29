# =====================================
# GIT WORKTREE MANAGER SERVICE
# =====================================
FROM base as git-worktree

USER root

# Install Git + SSH
RUN apt-get update && apt-get install -y \
    git \
    openssh-client && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

USER mcp

# Set working dir and Python path
WORKDIR /app
ENV PYTHONPATH=/app

# Git identity config
RUN git config --global user.name "MCP Git Manager" && \
    git config --global user.email "mcp@ethical-ai-insider.com" && \
    git config --global init.defaultBranch main

# Copy source
COPY --chown=mcp:mcp src/common ./src/common
COPY --chown=mcp:mcp src/git_worktree/ ./src/git_worktree/
COPY --chown=mcp:mcp scripts/start_git_worktree.py ./start.py

# Ensure repo directory exists
RUN mkdir -p /app/repositories && chown mcp:mcp /app/repositories

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=git-worktree --port=8003

CMD ["python", "start.py"]
