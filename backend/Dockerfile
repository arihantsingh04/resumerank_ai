# ResumeRank API ??? CPU-only image (D-20, D-28). Not built on the dev laptop (no Docker there).
FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DATA_DIR=/app/data \
    HF_HUB_DISABLE_TELEMETRY=1 \
    EMBEDDING_BACKEND=onnx

WORKDIR /app

# No PyTorch: embeddings run through ONNX Runtime (same model, D-46), keeping the image small.
COPY requirements.txt .
RUN pip install -r requirements.txt

RUN useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser app ./app
RUN mkdir -p /app/data/models && chown -R appuser:appuser /app/data

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health')"

# Stateless (D-35): scale by adding containers. One worker per container keeps RAM at one model copy.
# The backend is reachable only through the nginx container, so its X-Forwarded-For is trusted
# (the per-IP rate limiter and AI budget need the real client IP).
CMD ["sh", "-c", "uvicorn app.main:create_app --factory --host 0.0.0.0 --port 8000 --workers 1 --proxy-headers --forwarded-allow-ips='*'"]
