FROM python:2.7-slim

ENV APP_DIR /munkiwebadmin

#munkiwebadmin config
ENV APPNAME 'MunkiWebAdmin'
ENV TIME_ZONE 'UTC'
ENV LANGUAGE_CODE 'en-us'
ENV SIMPLEMDMKEY ''
ENV ALLOWED_HOSTS '[*]'
ENV DEFAULT_MANIFEST 'serail_number'
ENV PROXY_ADDRESS ''
ENV STYLE 'default'
ENV VAULT_USERNAME 'admin'
ENV CONVERT_TO_QWERTZ ''

#database
ENV DB 'postgres'
ENV DB_NAME 'munkiwebadmin_db'
ENV DB_USER 'postgres'
ENV DB_PASS 'postgres'
ENV DB_HOST 'db'
ENV DB_PORT '5432'

# Install all debian packages
RUN apt-get update && apt-get install -y \
		gcc \
		g++ \
		unixodbc-dev \
		mariadb-client \
		#libmysqlclient-dev \
		libmariadbclient-dev \
		libpq-dev \
		sqlite3 \
		net-tools \
		supervisor \
		unzip \
		tdsodbc \
		git \
		gnupg \
		curl \
		nginx \
		apt-transport-https \
		libsasl2-dev \
		python-dev \
		libldap2-dev \
		libssl-dev \
		dnsutils \
	--no-install-recommends && rm -rf /var/lib/apt/lists/*

# install necessary locales
RUN apt-get clean && apt-get update && apt-get install -y locales
RUN sed -i '/^#.* en_US.* /s/^#//' /etc/locale.gen
RUN locale-gen

# install mssql
RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
RUN curl https://packages.microsoft.com/config/debian/9/prod.list > /etc/apt/sources.list.d/mssql-release.list

RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

# create dirs
RUN mkdir ${APP_DIR}
RUN mkdir /munkirepo
RUN mkdir /munkitools
RUN mkdir /config
RUN mkdir /fieldkeys

# download munkitools
RUN curl -Lk -o munkitools.zip `curl --silent https://api.github.com/repos/munki/munki/releases/latest | /usr/bin/awk '/zipball_url/ { print $2 }' | sed 's/[",]//g'` && unzip munkitools.zip -d . && rm -rf /munkitools.zip 
RUN cp -r /munki-munki*/code/client/* /munkitools && rm -rf /munki-munki*

# Copy all source files to the container's working directory
COPY . ${APP_DIR}
WORKDIR ${APP_DIR}

#load default style
RUN curl -Lk -o /tmp/mwa2-style.zip https://github.com/SteveKueng/mwa2-style/archive/master.zip && unzip /tmp/mwa2-style.zip -d /tmp && rm -rf /tmp/mwa2-style.zip
RUN mkdir -p /munkiwebadmin/munkiwebadmin/static/styles/default
RUN cp -r /tmp/mwa2-style-master/* /munkiwebadmin/munkiwebadmin/static/styles/default && rm -rf /tmp/mwa2-style-master

# clean pyc
RUN find ${APP_DIR} -name '*.pyc' -delete

# Install all python dependency libs
RUN pip install -r requirements.txt

# Configure Nginx, uWSGI and supervisord
COPY docker/nginx.conf /etc/nginx/nginx.conf
RUN mkdir /var/log/uwsgi
COPY docker/supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# configure git
RUN git config --global core.preloadindex true
RUN git config --global core.fscache true
RUN git config --global gc.auto 256

VOLUME [ "/munkirepo", "/fieldkeys", "/reposado" ]

# Exposed port
EXPOSE 80
ENTRYPOINT ["/bin/sh", "docker/run.sh"]
CMD ["/usr/bin/supervisord"]
