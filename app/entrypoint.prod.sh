#!/bin/sh

NAME="MunkiWebAdmin"                          # Name of the application
DJANGODIR=/home/app/web                       # Django project directory
SOCKFILE=/home/app/gunicorn.sock              # we will communicte using this unix socket
USER=root                                     # the user to run as
GROUP=root                                    # the group to run as
NUM_WORKERS=3                                 # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=munkiwebadmin.settings # which settings file should Django use

# mount azure blob storage 
if [ "$AZURE_STORAGE_BLOB_ENDPOINT" != "" ]; then
  blobfuse2 mount /munkirepo/
fi

if [ "$DATABASE" == "postgres" ]; then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# migrate database
python manage.py makemigrations
python manage.py migrate --noinput

echo "Starting $NAME as `whoami`"

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

# Start your Django Unicorn
gunicorn munkiwebadmin.wsgi:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=unix:$SOCKFILE \
  --log-level=warn \
  --log-file=/home/app/gunicorn.log \
  --daemon

exec nginx -g "daemon off;"
