# =====================================
# GIT WORKTREE MANAGER SERVICE
# =====================================
# docker/git-worktree.Dockerfile
FROM base as git-worktree

# Install Git and SSH for repository operations
RUN apt-get update && apt-get install -y \
    git \
    openssh-client \
    && rm -rf /var/lib/apt/lists/*

# Configure Git
RUN git config --global user.name "MCP Git Manager" && \
    git config --global user.email "mcp@example.com" && \
    git config --global init.defaultBranch main

COPY --chown=mcp:mcp src/git_worktree/ ./
COPY --chown=mcp:mcp scripts/start_git_worktree.py ./start.py

# Create directory for repositories
RUN mkdir -p /app/repositories && chown mcp:mcp /app/repositories

EXPOSE 8003

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=git-worktree --port=8003

CMD ["python", "start.py"]
