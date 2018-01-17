## Introduction
This is version 2 of MunkiWebAdmin, a web-based administration tool for Munki.

[report scripts](https://github.com/SteveKueng/mwa2_scripts)

## Getting started
```bash
docker run -d --name postgres_db -e POSTGRES_DB=munkiwebadmin_db -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgres:9.6
docker run -d -p 8000:80 --name munkiwebadmin -v /Users/Shared/munkirepo:/munkirepo -e DB_HOST=postgres_db -e DB_NAME=munkiwebadmin_db -e DB_USER=postgres -e DB_PASS=postgres --link postgres_db -h $HOSTNAME munkiwebadmin
```

### create superuser
```bash
docker exec -it munkiwebadmin bash
python manage.py createsuperuser
exit
```

### reposado
```bash
docker run --name reposado -d -p 8088:8088 -v Reposado:/reposado mscottblake/reposado
docker run -d -p 8000:80 --name munkiwebadmin -v /Users/Shared/munkirepo:/munkirepo -v Reposado:/reposado -h $HOSTNAME --link db munkiwebadmin
```


#custom style
```bash
docker run -d -p 8000:80 --name munkiwebadmin -v /Users/Shared/munkirepo:/munkirepo -v /Users/Shared/styles:/munkiwebadmin/munkiwebadmin/static/styles -h $HOSTNAME --link db munkiwebadmin
```
create a folder in your styles directory.

restart the munkiwebadmin docker image

## permissions


## create docker image
```bash
docker build -t munkiwebadmin:latest .
```

## API
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

#### GET:
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

#### POST:
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

#### PUT:
```bash
##Replace an existing pkginfo item##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -H "Content-Type: application/json" \
     -X PUT \
     --data '{"name": "fakepkg", "catalogs": ["testing"], "display_name": "Example pkg"}' \
     http://localhost:8080/api/pkgsinfo/fakepkg-1.0.plist
```

#### PATCH:
```bash
##Change the value of specific keys in an existing pkginfo item##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -H "Content-Type: application/json" \
     -X PATCH \
     --data '{ "version": "1.0" }' \
     http://localhost:8080/api/pkgsinfo/fakepkg-1.0.plist
```

#### DELETE:
```bash
##Delete a pkginfo item##
curl -H "Authorization: Basic dXNlcm5hbWU6cGFzc3dvcmQ=" \
     -X DELETE \
     http://localhost:8080/api/pkgsinfo/fakepkg-1.0.plist
```

#### UPLOADING A NEW PKG OR ICON:
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