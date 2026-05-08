FROM node:24-alpine AS web-build

WORKDIR /web
COPY apps/web/package*.json ./
RUN npm ci
COPY apps/web ./
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN adduser --disabled-password --gecos "" appuser
RUN mkdir -p /app/data && chown -R appuser:appuser /app/data

COPY --chown=appuser:appuser apps ./apps
COPY --chown=appuser:appuser alembic.ini ./alembic.ini
COPY --chown=appuser:appuser alembic ./alembic
COPY --from=web-build --chown=appuser:appuser /web/dist ./apps/web/dist

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"PORT\", \"8000\")}/health').read()"

CMD ["sh", "-c", "alembic upgrade head && uvicorn apps.api.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
