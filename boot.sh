#!/bin/sh
CRTFILE="$1"
KEYFILE="$2"

if [ -f "$CRTFILE" ] && [ -f "$KEYFILE" ];
then
   exec gunicorn --certfile localhost.crt --keyfile localhost.key -b :4000 --access-logfile - --error-logfile - wsgi:app
else
   exec gunicorn -b :4000 --access-logfile - --error-logfile - wsgi:app
fi

