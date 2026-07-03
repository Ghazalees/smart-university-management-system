# Builds the container image defined by backend/Dockerfile with only the dependencies required for its target runtime.

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN groupadd --system app && useradd --system --gid app --home /app app
COPY requirements /tmp/requirements
RUN python -m pip install --upgrade pip && \
    python -m pip install -r /tmp/requirements/production.txt
COPY . .
RUN mkdir -p /app/data /app/staticfiles && \
    chmod +x /app/docker/entrypoint.sh && \
    chown -R app:app /app
USER app
ENV SQLITE_DB_PATH=/app/data/db.sqlite3
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=4s --retries=5 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/v1/health', timeout=3)" || exit 1
ENTRYPOINT ["/app/docker/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "--access-logfile", "-"]
