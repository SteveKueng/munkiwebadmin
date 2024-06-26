#!/bin/bash

export APPNAME='MunkiWebAdmin'
export TIME_ZONE='Europe/Zurich'
export LANGUAGE_CODE='en-us'
export ALLOWED_HOSTS='localhost 127.0.0.1 [::1]'
export DEFAULT_MANIFEST=''
export PROXY_ADDRESS=''
export DEBUG=1
export FIELD_ENCRYPTION_KEY='VDKEyIzST-hbtX7rvA7LPue63E0XB0m3pZEFWKk0BKI='
export REPO_MANAGEMENT_ONLY='False'
export MUNKI_REPO_URL='file:///Users/Shared/munkirepo'
export MUNKITOOLS_DIR='/usr/local/munki'


python manage.py makemigrations manifests pkgsinfo process reports inventory
python manage.py migrate --noinput

# Start the development server
python manage.py runserver