FROM python:3.11-slim

# set work directory
WORKDIR /usr/src/app
COPY . .

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# ------ update and install software
# update 
RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y gcc default-libmysqlclient-dev python3-dev \
    libxml2-dev libxslt1-dev zlib1g-dev libsasl2-dev libldap2-dev \
    build-essential libssl-dev libffi-dev libjpeg-dev \
    libpq-dev liblcms2-dev libblas-dev libatlas-base-dev pkg-config curl unzip \
    git fuse3 libfuse3-dev golang \
    && rm -rf /var/lib/apt/lists/*
# -------

# set work directory
WORKDIR /tmp

# build blobfuse
RUN git clone https://github.com/Azure/azure-storage-fuse/
WORKDIR /tmp/azure-storage-fuse
RUN ./build.sh
RUN cp blobfuse2 /usr/local/bin
RUN rm -rf /tmp/azure-storage-fuse

# set work directory
WORKDIR /usr/src/app

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