#!/bin/bash

cd $APP_DIR

if ! test "$(ls -A "/fieldkeys")"; then
  keyczart create --location=/fieldkeys --purpose=crypt
  keyczart addkey --location=/fieldkeys --status=primary --size=256
fi

#seret key
python manage.py generate_secret_key --replace

#style
python manage.py collectstatic --noinput
cp static_root/styles/$STYLE/favicon.ico .

#update database
python manage.py makemigrations manifests pkgsinfo process reports updates vault
python manage.py migrate --noinput

exec "$@"