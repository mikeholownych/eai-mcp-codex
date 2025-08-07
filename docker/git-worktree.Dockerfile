# =====================================
# GIT WORKTREE MANAGER SERVICE
# =====================================
FROM mcp-base as base

ENV SERVICE_NAME=git-worktree \
    SERVICE_PORT=8003

# ---------- Dependency Layer ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npsycopg2-binary>=2.9.0\npydantic>=1.8.0\ngitpython>=3.1.0" > requirements.txt; \
    fi && \
    python -m pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Layer ----------
FROM base as git-worktree

WORKDIR /app

USER root

# Copy installed Python dependencies
COPY --from=deps /usr/local/lib/python*/site-packages /usr/local/lib/python*/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

# Set up directories and ownership
RUN mkdir -p /app/repositories /app/src /app/scripts && \
    chown -R mcp:mcp /app

USER mcp

# Git identity config (per user)
RUN git config --global user.name "MCP Git Manager" && \
    git config --global user.email "mcp@ethical-ai-insider.com" && \
    git config --global init.defaultBranch main

# Copy application code
COPY --chown=mcp:mcp src/common/ ./src/common/
COPY --chown=mcp:mcp src/git_worktree/ ./src/git_worktree/
COPY --chown=mcp:mcp scripts/start_git_worktree.py ./start.py
COPY --chown=mcp:mcp scripts/health_check.py ./health_check.py

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=git-worktree --port=8003

# Expose port
EXPOSE 8003

# Run the service
CMD ["python", "start.py"]
