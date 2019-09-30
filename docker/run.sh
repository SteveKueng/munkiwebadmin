#!/bin/bash

cd $APP_DIR

if ! test "$(ls -A "/fieldkeys")"; then
  keyczart create --location=/fieldkeys --purpose=crypt
  keyczart addkey --location=/fieldkeys --status=primary --size=256
fi

update-ca-certificates

virtual_host_short=$(echo $VIRTUAL_HOST | cut -d. -f1)
sed "s/127.0.0.1.*/127.0.0.1 localhost $virtual_host_short $VIRTUAL_HOST/" /etc/hosts

#seret key
python manage.py generate_secret_key --replace

#style
python manage.py collectstatic --noinput
cp static_root/styles/$STYLE/favicon.ico .

#update database
python manage.py makemigrations manifests pkgsinfo process reports updates vault
python manage.py migrate --noinput

chown -R www-data:www-data $APP_DIR
exec "$@"