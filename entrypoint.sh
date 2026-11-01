#!/bin/bash
set -e
python manage.py migrate --noinput
exec gunicorn velunt.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 2 \
    --access-logformat '%({x-forwarded-for}i)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"' \
    --access-logfile - \
    --error-logfile -
