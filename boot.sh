#!/bin/sh
source venv/bin/activate
exec gunicorn -b :4000 --access-logfile - --error-logfile - wsgi:app