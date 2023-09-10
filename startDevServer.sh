#!/bin/bash

export APPNAME='MunkiWebAdmin'
export TIME_ZONE='UTC'
export LANGUAGE_CODE='en-us'
export SIMPLEMDMKEY=''
export ALLOWED_HOSTS='[*]'
export DEFAULT_MANIFEST='serail_number'
export PROXY_ADDRESS=''
export VAULT_USERNAME='admin'
export CONVERT_TO_QWERTZ=''
export DEBUG='True'
export MUNKI_REPO_DIR='/tmp/munkirepo'
export MAKECATALOGS_PATH='/usr/local/munki/makecatalogs'
export FIELD_ENCRYPTION_KEY='VDKEyIzST-hbtX7rvA7LPue63E0XB0m3pZEFWKk0BKI='
export REPO_MANAGEMENT_ONLY='False'

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

cd app

python manage.py makemigrations manifests pkgsinfo process reports vault inventory
python manage.py migrate --noinput

# Start the development server
python manage.py runserver 0.0.0.0:8000