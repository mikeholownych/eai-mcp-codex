# =====================================
# PLAN MANAGEMENT SERVICE  
# =====================================
# docker/plan-management.Dockerfile
FROM base as plan-management

# Install additional dependencies for plan management
RUN pip install --no-cache-dir sqlalchemy alembic

COPY --chown=mcp:mcp src/plan_management/ ./
COPY --chown=mcp:mcp scripts/start_plan_management.py ./start.py
COPY --chown=mcp:mcp database/migrations/ ./migrations/

EXPOSE 8002

# Run database migrations on startup
RUN echo '#!/bin/bash\npython -m alembic upgrade head\nexec python start.py' > entrypoint.sh && \
    chmod +x entrypoint.sh

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=plan-management --port=8002

CMD ["./entrypoint.sh"]
