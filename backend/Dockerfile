# ---------------------------------------------------------------------------
# StockRoom backend image.
# The image runs the Alembic migrations and then starts Uvicorn.
# The image runs as a non-root user.
# ---------------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install the dependencies first. This layer stays in the cache.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the migrations and the application code.
COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app

# Make the start script.
RUN printf '%s\n' \
    '#!/bin/sh' \
    'set -e' \
    'echo "StockRoom: apply the database migrations"' \
    'alembic upgrade head' \
    'echo "StockRoom: start the API"' \
    'exec uvicorn app.main:app --host 0.0.0.0 --port 8000' \
    > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Make a non-root user and give it the application directory.
RUN useradd --create-home --uid 10001 stockroom \
    && chown -R stockroom:stockroom /app
USER stockroom

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"

ENTRYPOINT ["/app/entrypoint.sh"]
