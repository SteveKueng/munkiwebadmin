#!/bin/bash

. virtualexport-python3.7/bin/activate

export APPNAME='MunkiWebAdmin'
export TIME_ZONE='UTC'
export LANGUAGE_CODE='en-us'
export SIMPLEMDMKEY=''
export ALLOWED_HOSTS='[*]'
export DEFAULT_MANIFEST='serail_number'
export PROXY_ADDRESS=''
export STYLE='default'
export VAULT_USERNAME='admin'
export CONVERT_TO_QWERTZ=''
export DEBUG='True'
export MUNKI_REPO_DIR='/tmp/munkirepo'
export MAKECATALOGS_PATH='/usr/local/munki/makecatalogs'
export FIELD_ENCRYPTION_KEY='VDKEyIzST-hbtX7rvA7LPue63E0XB0m3pZEFWKk0BKI='

#database
export DB='postgres'
export DB_NAME='postgres'
export DB_USER='postgres'
export DB_PASS='postgres'
export DB_HOST='localhost'
export DB_PORT='5432'

# Create the munki repo directory
if [ ! -d $MUNKI_REPO_DIR ]; then
    mkdir -p $MUNKI_REPO_DIR
fi

# Create the key directory
if [ ! -d $ENCRYPTED_FIELDS_KEYDIR ]; then
    mkdir -p $ENCRYPTED_FIELDS_KEYDIR
fi
if [ ! -f $ENCRYPTED_FIELDS_KEYDIR/meta ]; then
    keyczart create --location=$ENCRYPTED_FIELDS_KEYDIR --purpose=crypt
    keyczart addkey --location=$ENCRYPTED_FIELDS_KEYDIR --status=primary --size=256
fi

python manage.py makemigrations manifests pkgsinfo process reports vault inventory
python manage.py migrate --noinput

python manage.py createsuperuser --username admin

# Start the development server
python manage.py runserver 0.0.0.0:8000