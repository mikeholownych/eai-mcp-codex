# =====================================
# MODEL ROUTER SERVICE
# =====================================
# docker/model-router.Dockerfile
FROM base as model-router

COPY --chown=mcp:mcp src/model_router/ ./
COPY --chown=mcp:mcp scripts/start_model_router.py ./start.py

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=model-router --port=8001

CMD ["python", "start.py"]
