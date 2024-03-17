FROM python:3.11-slim

# set work directory
WORKDIR /usr/src/app
COPY . .

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ------ update and install software
# update 
RUN curl -sSL -O https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb
RUN dpkg -i packages-microsoft-prod.deb
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y gcc default-libmysqlclient-dev python3-dev \
    libxml2-dev libxslt1-dev zlib1g-dev libsasl2-dev libldap2-dev \
    build-essential libssl-dev libffi-dev libjpeg-dev \
    libpq-dev liblcms2-dev libblas-dev libatlas-base-dev pkg-config curl unzip \
    fuse3 blobfuse2 \
    && rm -rf /var/lib/apt/lists/*
# -------

# install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# create dirs
RUN mkdir /munkirepo
RUN mkdir /munkitools

# download munkitools
RUN curl -Lk -o /tmp/munkitools.zip `curl --silent https://api.github.com/repos/munki/munki/releases/latest | /usr/bin/awk '/zipball_url/ { print $2 }' | sed 's/[",]//g'` && unzip /tmp/munkitools.zip -d /tmp/munkitools && rm -rf /tmp/munkitools.zip 
RUN cp -r /tmp/munkitools/munki-munki*/code/client/* /munkitools && rm -rf /tmp/munkitools

VOLUME [ "/munkirepo" ]

# run entrypoint.sh
ENTRYPOINT ["/usr/src/app/entrypoint.sh"]