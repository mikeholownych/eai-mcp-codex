# =====================================
# WORKFLOW ORCHESTRATOR SERVICE
# =====================================
# docker/workflow-orchestrator.Dockerfile
FROM base as workflow-orchestrator

# Install additional dependencies for workflow management
RUN pip install --no-cache-dir \
    celery \
    redis \
    requests

COPY --chown=mcp:mcp src/ ./src/
COPY --chown=mcp:mcp src/common/ ./src/common/
COPY --chown=mcp:mcp src/workflow_orchestrator/ ./src/workflow_orchestrator/
COPY --chown=mcp:mcp scripts/start_workflow_orchestrator.py ./start.py

EXPOSE 8004

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=workflow-orchestrator --port=8004

CMD ["python", "start.py"]
