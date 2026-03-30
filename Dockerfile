FROM python:3.11-slim

LABEL maintainer="openenv-support-triage"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python deps — install in two layers for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY app/ ./app/
COPY tasks/ ./tasks/
COPY openenv.yaml .
COPY inference.py .

# HF Spaces requires port 7860
EXPOSE 7860

# Health check — wait up to 60s for startup
HEALTHCHECK --interval=15s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:7860/health || exit 1

# Run with single worker (stateful env), ensure immediate startup
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860", "--workers", "1", "--timeout-keep-alive", "30"]
