#!/bin/bash

export APPNAME='MunkiWebAdmin'
export TIME_ZONE='Europe/Zurich'
export LANGUAGE_CODE='en-us'
export ALLOWED_HOSTS='localhost 127.0.0.1 [::1]'
export DEFAULT_MANIFEST='serail_number'
export PROXY_ADDRESS=''
export VAULT_USERNAME='admin'
export DEBUG=1
export MUNKI_REPO_DIR='/tmp/munkirepo'
export MAKECATALOGS_PATH='/usr/local/munki/makecatalogs'
export FIELD_ENCRYPTION_KEY='VDKEyIzST-hbtX7rvA7LPue63E0XB0m3pZEFWKk0BKI='
export REPO_MANAGEMENT_ONLY='False'

# Create the munki repo directory
if [ ! -d $MUNKI_REPO_DIR ]; then
    mkdir -p $MUNKI_REPO_DIR
fi

cd app

python manage.py makemigrations manifests pkgsinfo process reports vault inventory
python manage.py migrate --noinput

# Start the development server
python manage.py runserver