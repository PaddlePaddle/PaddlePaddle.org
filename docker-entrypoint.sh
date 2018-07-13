#!/bin/bash

export WORKER_TIMEOUT=120

python manage.py collectstatic --noinput  # collect static files
python manage.py compilemessages -l zh    # compile chinese messages

# Prepare log files and start outputting logs to stdout
touch /var/log/gunicorn.log
touch /var/log/access.log
tail -n 0 -f /var/log/*.log &
echo Starting nginx
# Start Gunicorn processes
echo Starting Gunicorn.
exec gunicorn portal.wsgi:application \
    --name paddlepaddle_portal \
    --bind unix:django_app.sock \
    --workers 5 \
    --timeout $WORKER_TIMEOUT \
    --log-level=info \
    --log-file=/var/log/gunicorn.log \
    --access-logfile=/var/log/access.log &
exec service nginx start
