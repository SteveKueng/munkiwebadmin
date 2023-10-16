# MunkiWebAdmin
## Introduction
This is version 2 of MunkiWebAdmin, a web-based administration tool for Munki.

![MunkiWebAdmin ScreenShot](doc/ScreenShot1.png "")

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/stevekueng)

# Getting started

## Linux (dev server)
### 1. Preparation
install the following tools:
- Python 3
- Git
- Docker (optional for database)

### 2. Clone repo
```bash
git clone https://github.com/SteveKueng/munkiwebadmin.git
cd munkiwebadmin
```

### 3. Database (optional)
Create a database (MySQL/MariaDB or Postgres) or use the following script (docker)
If you don't create an specify a DB, django will use a sqlite3 DB.
```bash
./createDatabase.sh
```

### 4. Create virtualenv (optional)
```bash
pip install virtualenv
virtualenv mwa2_virtualenv
. mwa2_virtualenv/bin/activate
```

### 4. Install requirements
```bash
cd app
pip install -r requirements.txt
```

### 6. Init DB
```bash
python manage.py migrate
python manage.py createsuperuser
```

### 7. Edit variables
open startDevServer.sh and change the environment variables

### 8. Run munkiwebadmin
```bash
cd ..
./startDevServer.sh
```
[Install MunkiScripts](#install-munkiscripts)

## Docker
comming soon

docker exec -it munkiwebadmin sh -c "python manage.py createsuperuser"

### Docker variables

| Variable      | Usage         | Default|
| ------------- |-------------|:------:|
| APPNAME      | Django app name | _MunkiWebAdmin_ |
| ALLOWED_HOSTS | django allowed hosts. e.g. _[ munkiwebadmin.example.com ]_ |_[ * ]_|
| DEFAULT_MANIFEST | default manifest to use. _serail_number_ or _hostname_     |_serial_number_ |
| PROXY_ADDRESS | proxy server address     ||
| DB | Database type. currently only postgres possible | postgres |
| DB_NAME | Database name | _munkiwebadmin_db_ |
| DB_USER | Database user     | _postgres_ |
| DB_PASS | Database password | _postgres_ |
| DB_HOST | Database host     | _db_       |
| DB_PORT | Database port     | _5432_     |


## Install MunkiScripts
### 1. Download
Check out the dropdown and download the .pkg

![Download scripts screenshot](doc/ScreenShot2.png "")

### 2. Install munkiscripts
Double klick on the .pkg

### 3. Configure munkiscripts
```bash
defaults write /var/root/Library/Preferences/com.github.stevekueng.munkiwebadmin.plist ServerURL -string "http://munkiwebadmin.example.com"
#basic auth key created with: python python -c 'import base64; print "Basic %s" % base64.b64encode("USERNAME:PASSWORD")'
defaults write /var/root/Library/Preferences/com.github.stevekueng.munkiwebadmin.plist authKey -string "QmFzaWMgdGVzdDpwYXNz" 
```

# API
MWA2 supports a basic API for reading from and writing to the Munki repo.

manifests and pkgsinfo endpoints are supported. For these endpoints, the GET, POST, PUT, PATCH and DELETE methods are supported.

pkgs and icons endpoints are also supported: for these only GET, POST and DELETE are supported.

Authentication is shared with the rest of MWA2. Currently only HTTP BASIC auth is supported. You should use this only over https. Consider creating special API users with only those rights that are needed (if you only need to read from the repo, use a user with read-only rights, etc)

Create a Base64-encoded value to use with an authorization header:   
```bash
python -c 'import base64; print "Authorization: Basic %s" % base64.b64encode("username:password")'
Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=
```

Note: this encoding is easily reversible, thus the recommendation to use https and special API users.

Some examples of interacting with the API (where the server is running at http://localhost:8080):

## GET:
```bash
##Get all manifests##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" http://localhost:8080/api/manifests

##Get all manifests, returning just the filenames##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     "http://localhost:8080/api/manifests?api_fields=filename"

##Get all manifests that have testing in their catalogs##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     "http://localhost:8080/api/manifests?catalogs=testing"

##Get all manifests that have testing in their catalogs, returning the filename and the catalog list##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     "http://localhost:8080/api/manifests?catalogs=testing&api_fields=filename,catalogs"

##Get a specific manifest##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     "http://localhost:8080/api/manifests/site_default"

##Get all pkginfo items that have 'com.microsoft' in their receipts, returning only the filenames##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     "http://localhost:8080/api/pkgsinfo?receipts=com.microsoft&api_fields=filename"

##Get all pkginfo items that install configuration profiles, returning the filenames and the installer_item_location##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     "http://localhost:8080/api/pkgsinfo/?installer_item_location=.mobileconfig&api_fields=filename,installer_item_location"
```

## POST:
```bash
##Create a new pkginfo item##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -H "Content-Type: application/json" \
     -X POST \
     --data '{"filename": "fakepkg-1.0.plist", "name": "fakepkg", "catalogs": ["testing"], "display_name": "Example pkg"}' \
     http://localhost:8080/api/pkgsinfo
```
alternately:
```bash
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -H "Content-Type: application/json" \
     -X POST \
     --data '{"name": "fakepkg", "catalogs": ["testing"], "display_name": "Example pkg"}' \
     http://localhost:8080/api/pkgsinfo/fakepkg-1.0.plist
```

## PUT:
```bash
##Replace an existing pkginfo item##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -H "Content-Type: application/json" \
     -X PUT \
     --data '{"name": "fakepkg", "catalogs": ["testing"], "display_name": "Example pkg"}' \
     http://localhost:8080/api/pkgsinfo/fakepkg-1.0.plist
```

## PATCH:
```bash
##Change the value of specific keys in an existing pkginfo item##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -H "Content-Type: application/json" \
     -X PATCH \
     --data '{ "version": "1.0" }' \
     http://localhost:8080/api/pkgsinfo/fakepkg-1.0.plist
```

## DELETE:
```bash
##Delete a pkginfo item##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -X DELETE \
     http://localhost:8080/api/pkgsinfo/fakepkg-1.0.plist
```

## UPLOADING A NEW PKG OR ICON:
```bash
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -X POST \
     -F filename=apps/Firefox-52-0.dmg \
     -F filedata=@/path/to/local_file.dmg \
     http://localhost:8080/api/pkgs
```
alternately:
```bash
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -X POST \
     -F filedata=@/path/to/local_file.png \
     http://localhost:8080/api/icons/Firefox.png
```


# Special configurations
## Kerberos
add the spn to your service account and generate the keytab file (execute this commands on your windows server)
```
setspn.exe  -A HTTP/munkiwebadmin EXAMPLE\munkiwebadmin
setspn.exe  -A HTTP/munkiwebadmin.example.com EXAMPLE\munkiwebadmin
ktpass /princ HTTP/munkiwebadmin.example.com@EXAMPLE.COM /ptype krb5_nt_principal /crypto rc4-hmac-nt /mapuser EXAMPLE\munkiwebadmin /out krb5.keytab -kvno 0 /pass 
```

copy the krb5.keytab to your docker host
create the followning http conf on your docker host:
```
WSGIPythonPath /munkiwebadmin/munkiwebadmin
<VirtualHost *:80>
    <Location />
        AuthType Kerberos
        AuthName "Login"
        KrbMethodNegotiate On
        KrbMethodK5Passwd On
        KrbAuthRealms EXAMPLE.COM
        KrbServiceName HTTP/munkiwebadmin.example.com@EXAMPLE.COM
        Krb5KeyTab /etc/krb5.keytab
        require valid-user
    </Location>

    Alias /static /munkiwebadmin/static
    <Directory /munkiwebadmin/static>
        Require all granted
    </Directory>
    
    Alias "/media" "/munkirepo/icons"
    <Location "/media">
    	Require all granted
    </Location>

    <Directory /munkiwebadmin/munkiwebadmin >
        WSGIProcessGroup munkiwebadmin
        WSGIApplicationGroup %{GLOBAL}
        Require all granted
    </Directory>

    WSGIDaemonProcess munkiwebadmin python-path=/munkiwebadmin
    WSGIProcessGroup munkiwebadmin

    WSGIScriptAlias / /munkiwebadmin/munkiwebadmin/wsgi.py

    LimitRequestBody 0 
    ErrorLog ${APACHE_LOG_DIR}/error.log
    CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>
```

start the docker image with the following command:
```bash
docker run -d -p 8000:80 --name munkiwebadmin -v /Users/Shared/munkirepo:/munkirepo -v /Users/Shared/krb5.keytab:/etc/krb5.keytab -v /Users/Shared/http.conf:/etc/apache2/sites-enabled/000-default.conf -e KERBEROS_REALM=EXAMPLE.COM -e VIRTUAL_HOST=munkiwebadmin.example.com -e DB_HOST=postgres_db -e DB_NAME=munkiwebadmin_db -e DB_USER=postgres -e DB_PASS=postgres --link postgres_db -h "$HOSTNAME" stevekueng/munkiwebadmin
```

within the docker image you can test your kerberos conf with:
```bash
kinit -5 -V -k -t /etc/krb5.keytab HTTP/munkiwebadmin.example.com@EXAMPLE.COM
```

# Development

## create docker image
```bash
docker build -t munkiwebadmin:latest .
```
