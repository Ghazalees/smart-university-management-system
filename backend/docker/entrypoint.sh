#!/bin/sh
# Prepares the database, optional seed data, and application server before the backend container starts.

set -eu

if [ "${AUTO_MIGRATE:-1}" = "1" ]; then
  python manage.py migrate --noinput
fi

if [ "${AUTO_SEED_SYSTEM:-1}" = "1" ]; then
  python manage.py seed_initial_data --system-only
fi

if [ "${AUTO_SEED_DEMO:-1}" = "1" ] && [ "${DJANGO_DEBUG:-0}" = "1" ]; then
  python manage.py seed_initial_data
fi

python manage.py collectstatic --noinput >/dev/null
exec "$@"
