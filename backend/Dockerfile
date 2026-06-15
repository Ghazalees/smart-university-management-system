FROM python:3.12-slim
WORKDIR /app
COPY requirements /tmp/requirements
RUN pip install --no-cache-dir -r /tmp/requirements/development.txt
COPY . .
RUN mkdir -p /app/data
ENV SQLITE_DB_PATH=/app/data/db.sqlite3
EXPOSE 8000
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
