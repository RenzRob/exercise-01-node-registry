# syntax=docker/dockerfile:1.7

# ---- builder stage ----
FROM python:3.14-alpine AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-compile -r requirements.txt && \
    find /root/.local -depth \
      \( -type d \( -name '__pycache__' -o -name 'tests' -o -name 'test' \) \
         -o -type f \( -name '*.pyc' -o -name '*.pyo' \) \) \
      -prune -exec rm -rf {} +

# ---- runtime stage ----
FROM python:3.14-alpine

RUN addgroup -S -g 1001 appuser && \
    adduser -S -u 1001 -G appuser -h /home/appuser -s /bin/sh appuser

WORKDIR /app

COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local
COPY --chown=appuser:appuser src ./src

ENV PATH=/home/appuser/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

USER appuser

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8080/health', timeout=3).status == 200 else 1)" || exit 1

CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "8080"]
