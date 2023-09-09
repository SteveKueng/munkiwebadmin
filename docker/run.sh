#!/bin/bash

cd $APP_DIR

update-ca-certificates

cp /etc/hosts /etc/hosts.bak
virtual_host_short=$(echo $VIRTUAL_HOST | cut -d. -f1)
sed -i "s/127.0.0.1.*/127.0.0.1 localhost $virtual_host_short $VIRTUAL_HOST/" /etc/hosts.bak
cp /etc/hosts.bak /etc/hosts

# seret key
python manage.py generate_secret_key --replace

# collect static files
python manage.py collectstatic --noinput

#u pdate database
python manage.py makemigrations manifests pkgsinfo process reports vault
python manage.py migrate --noinput

chown -R www-data:www-data $APP_DIR
exec "$@"