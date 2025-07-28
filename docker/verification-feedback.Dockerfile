# =====================================
# VERIFICATION & FEEDBACK SERVICE
# =====================================
# docker/verification-feedback.Dockerfile
FROM base as verification-feedback

# Install additional dependencies for verification
RUN pip install --no-cache-dir \
    nltk \
    textstat \
    pylint

COPY --chown=mcp:mcp src/verification_feedback/ ./
COPY --chown=mcp:mcp scripts/start_verification_feedback.py ./start.py

EXPOSE 8005

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python health_check.py --service=verification-feedback --port=8005

CMD ["python", "start.py"]p
