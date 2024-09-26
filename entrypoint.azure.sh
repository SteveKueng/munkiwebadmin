#!/bin/sh

# migrate database
python manage.py makemigrations catalogs, process, pkgsinfo, reports, manifests, inventory, icons, santa
python manage.py migrate

gunicorn --bind=0.0.0.0 --timeout 600 --workers=4 munkiwebadmin.wsgi
