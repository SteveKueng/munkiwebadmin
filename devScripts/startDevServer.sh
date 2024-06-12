#!/bin/bash

export APPNAME='MunkiWebAdmin'
export TIME_ZONE='Europe/Zurich'
export LANGUAGE_CODE='en-us'
export ALLOWED_HOSTS='localhost 127.0.0.1 [::1]'
export DEFAULT_MANIFEST=''
export DEBUG=1
export MUNKI_REPO_DIR='https://munkiumb.blob.core.windows.net/munkirepo'
export MUNKI_REPO_PLUGIN='AzureRepo'
export MUNKITOOLS_DIR='/usr/local/munki'
export REPO_MANAGEMENT_ONLY='False'


# Create the munki repo directory
if [ ! -d $MUNKI_REPO_DIR ]; then
    mkdir -p $MUNKI_REPO_DIR
fi

cd app

python manage.py makemigrations manifests pkgsinfo process reports inventory
python manage.py migrate --noinput

# Start the development server
python manage.py runserver