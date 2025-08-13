# =====================================
# SANDBOX ENVIRONMENT FOR ISOLATED TASKS
# =====================================
FROM mcp-base AS base

ENV HOME=/home/sandbox

# ---------- Dependencies Stage ----------
FROM base as deps

WORKDIR /app

USER root

# Copy requirements if it exists, otherwise create minimal one
COPY requirements.txt* ./
RUN if [ ! -f requirements.txt ]; then \
        echo "fastapi>=0.68.0\nuvicorn[standard]>=0.15.0\npydantic>=1.8.0" > requirements.txt; \
    fi && \
    pip install --no-cache-dir -r requirements.txt

# ---------- Final Runtime Stage ----------
FROM base AS sandbox

# Create secure sandbox user
USER root
RUN groupadd --system --gid 1001 sandbox && \
    useradd --system --uid 1001 --gid 1001 --create-home --shell /bin/bash sandbox

# Set working directory and permissions
WORKDIR /home/sandbox

# Copy dependencies
COPY --from=deps /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=deps /usr/local/bin /usr/local/bin

RUN chown -R sandbox:sandbox /home/sandbox

# Drop to sandbox user
USER sandbox

# Default command
CMD ["python", "-c", "print('sandbox ready')"]
