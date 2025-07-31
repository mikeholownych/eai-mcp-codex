# =====================================
# MODEL ROUTER SERVICE
# =====================================
# docker/model-router.Dockerfile
FROM mcp-base as model-router

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Fix the path so `src/model_router/...` is preserved
COPY --chown=mcp:mcp src/ ./src
COPY --chown=mcp:mcp scripts/start_model_router.py ./start.py

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=model-router --port=8001

CMD ["python", "start.py"]
