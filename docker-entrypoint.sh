#!/usr/bin/env bash

mkdir /code/static/ -p

echo "Waiting for database..."
while ! nc -z ${DB_HOST} ${DB_PORT}; do sleep 1; done
echo "Connected to database."

python manage.py migrate --noinput
if [[ $? -ne 0 ]]; then
    echo "Migration failed." >&2
    exit 1
fi

python manage.py collectstatic --noinput

echo "Starting Gunicorn..."
exec gunicorn mdcp_panel.wsgi:application -w ${GUNICORN_WORKERS:-12} --bind 0.0.0.0:${SERVER_PORT:-8000}
