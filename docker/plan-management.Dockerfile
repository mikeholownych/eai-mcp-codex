# =====================================
# PLAN MANAGEMENT SERVICE
# =====================================
FROM llm-stack-base as plan-management

# Set working directory and Python module path
WORKDIR /app
ENV PYTHONPATH=/app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install additional dependencies
RUN pip install --no-cache-dir sqlalchemy alembic

# Copy source and migration files
COPY --chown=mcp:mcp src/common/ ./src/common/
COPY --chown=mcp:mcp src/plan_management/ ./src/plan_management/
COPY --chown=mcp:mcp scripts/start_plan_management.py ./start.py
COPY --chown=mcp:mcp database/migrations/ ./migrations/
COPY --chown=mcp:mcp database/migrations/alembic.ini ./alembic.ini

# Entrypoint to apply migrations then start app
RUN printf '#!/bin/bash\nalembic -c alembic.ini upgrade head\nexec python start.py\n' > entrypoint.sh && \
    chmod +x entrypoint.sh

EXPOSE 8002

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=plan-management --port=8002

ENTRYPOINT ["./entrypoint.sh"]
