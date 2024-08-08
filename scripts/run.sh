#!/bin/sh

set -e

python manage.py wait_for_db
python manage.py collectstatic --noinput
python manage.py migrete

uwsgi --socket :9000 --workers 4 --master --entable-threads --module app.wsgi