# MunkiWebAdmin
## Introduction
This is version 2 of MunkiWebAdmin, a web-based administration tool for Munki.

![MunkiWebAdmin ScreenShot](doc/ScreenShot1.png "")

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/stevekueng)

# Getting started

Check the wiki for getting started

### docker-compose
depending on your needs there is a compose file for a complete setup (munkiwebadmin, DB, munkirepo) or one for just munkiwebadmin with a DB.

#### complete setup
check out the docker-compose.prod.repo.yml and change the URL to something usefull for you.
Run docker compose:
```bash
docker-compose up -f docker-compose.prod.repo.yml 
```

#### only munkiwebadmin with DB
check out the docker-compose.prod.yml, change the URL to something usefull for you and also change the munkirepo.
Run docker compose:
```bash
docker-compose up -f docker-compose.prod.yml 
```


### Docker variables

| Variable      | Usage         | Default|
| ------------- |-------------|:------:|
| APPNAME      | Django app name | _MunkiWebAdmin_ |
| ALLOWED_HOSTS | django allowed hosts. e.g. _[ munkiwebadmin.example.com ]_ |_[ * ]_|
| DEFAULT_MANIFEST | default manifest to use. _serail_number_ or _hostname_     |_serial_number_ |
| DB | Database type. currently only postgres possible | postgres |
| DB_NAME | Database name | _munkiwebadmin_db_ |
| DB_USER | Database user     | _postgres_ |
| DB_PASS | Database password | _postgres_ |
| DB_HOST | Database host     | _db_       |
| DB_PORT | Database port     | _5432_     |


