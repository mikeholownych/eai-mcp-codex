# =====================================
# STAFF SERVICE
# =====================================
# docker/staff-service.Dockerfile
FROM base as staff-service

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Fix the path so `src/staff/...` is preserved
COPY --chown=mcp:mcp src/ ./src
COPY --chown=mcp:mcp scripts/start_staff_service.py ./start.py

EXPOSE 8006

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=staff-service --port=8006

CMD ["python", "start.py"]