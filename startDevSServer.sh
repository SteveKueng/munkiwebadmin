#!/bin/bash

# run munkiwebadmin dev server

# change dir
cd "$(dirname "$0")"

# default style
curl -Lk -o /tmp/mwa2-style.zip https://github.com/SteveKueng/mwa2-style/archive/master.zip && unzip /tmp/mwa2-style.zip -d /tmp && rm -rf /tmp/mwa2-style.zip
mkdir -p ./munkiwebadmin/static/styles/default
cp -r /tmp/mwa2-style-master/* ./munkiwebadmin/static/styles/default && rm -rf /tmp/mwa2-style-master

docker-compose up