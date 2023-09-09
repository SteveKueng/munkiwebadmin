FROM python:3.11-slim

ENV APP_DIR /munkiwebadmin

#munkiwebadmin config
ENV APPNAME 'MunkiWebAdmin'
ENV TIME_ZONE 'UTC'
ENV LANGUAGE_CODE 'en-us'
ENV SIMPLEMDMKEY ''
ENV ALLOWED_HOSTS '[*]'
ENV DEFAULT_MANIFEST 'serail_number'
ENV PROXY_ADDRESS ''
ENV VAULT_USERNAME 'admin'
ENV CONVERT_TO_QWERTZ ''
ENV DEBUG 'False'
ENV MUNKI_REPO_DIR '/munkirepo'
ENV MAKECATALOGS_PATH '/munkitools/makecatalogs'
ENV FIELD_ENCRYPTION_KEY 'VDKEyIzST-hbtX7rvA7LPue63E0XB0m3pZEFWKk0BKI='

#database
ENV DB 'postgres'
ENV DB_NAME 'munkiwebadmin_db'
ENV DB_USER 'postgres'
ENV DB_PASS 'postgres'
ENV DB_HOST 'db'
ENV DB_PORT '5432'

# ------ update and install software
ENV DEBIAN_FRONTEND 'noninteractive'
# update 
RUN apt-get update
RUN apt-get upgrade -y
# install tools
RUN apt-get install -y apt-utils vim curl unzip python-pip net-tools dnsutils git libldap2-dev libssl-dev gcc g++ libsasl2-dev
# install apache
RUN apt-get install -y apache2 apache2-utils libapache2-mod-wsgi libapache2-mod-auth-kerb
# install database clients
RUN apt-get install -y unixodbc-dev tdsodbc mariadb-client libmariadbclient-dev sqlite3
# install necessary locales
RUN apt-get clean && apt-get update && apt-get install -y locales
RUN sed -i '/^#.* en_US.* /s/^#//' /etc/locale.gen
RUN locale-gen
# -------

# create dirs
RUN mkdir ${APP_DIR}
RUN mkdir /munkirepo
RUN mkdir /munkitools
RUN mkdir /config

# download munkitools
RUN curl -Lk -o munkitools.zip `curl --silent https://api.github.com/repos/munki/munki/releases/latest | /usr/bin/awk '/zipball_url/ { print $2 }' | sed 's/[",]//g'` && unzip munkitools.zip -d . && rm -rf /munkitools.zip 
RUN cp -r /munki-munki*/code/client/* /munkitools && rm -rf /munki-munki*

# Copy all source files to the container's working directory
COPY . ${APP_DIR}
WORKDIR ${APP_DIR}

# clean pyc
RUN find ${APP_DIR} -name '*.pyc' -delete

# Install all python dependency libs
RUN pip install -r requirements.txt

# configure git
RUN git config --global core.preloadindex true
RUN git config --global core.fscache true
RUN git config --global gc.auto 256

# apache conf
ADD ./docker/munkiwebadmin.conf /etc/apache2/sites-available/000-default.conf
RUN chown -R www-data:www-data ${APP_DIR}

# permissions for www-data
RUN usermod -u 1000 www-data
RUN usermod -G staff www-data

VOLUME [ "/munkirepo" ]

# Exposed port
EXPOSE 80
ENTRYPOINT ["/bin/sh", "docker/run.sh"]
CMD ["apache2ctl", "-D","FOREGROUND"]
