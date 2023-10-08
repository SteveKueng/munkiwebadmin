#!/bin/sh

NAME="MunkiWebAdmin"                          # Name of the application
DJANGODIR=/home/app/web                       # Django project directory
SOCKFILE=/home/app/gunicorn.sock              # we will communicte using this unix socket
USER=root                                     # the user to run as
GROUP=root                                    # the group to run as
NUM_WORKERS=3                                 # how many worker processes should Gunicorn spawn
DJANGO_SETTINGS_MODULE=munkiwebadmin.settings # which settings file should Django use


if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

# migrate database
python manage.py makemigrations inventory manifests pkgsinfo process reports santa vault
python manage.py migrate

echo "Starting $NAME as `whoami`"

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

# Start your Django Unicorn
gunicorn munkiwebadmin.wsgi:application \
  --name $NAME \
  --workers $NUM_WORKERS \
  --user=$USER --group=$GROUP \
  --bind=$SOCKFILE \
  --log-level=warn \
  --log-file=/home/app/gunicorn.log \
  --daemon

exec nginx -g "daemon off;"
