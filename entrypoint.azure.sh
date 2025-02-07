#!/bin/sh

# migrate database
python manage.py makemigrations catalogs pkgsinfo reports manifests inventory icons santa process
python manage.py migrate

python manage.py collectstatic --noinput

gunicorn --bind=0.0.0.0 --timeout 600 --workers=4 munkiwebadmin.wsgi
