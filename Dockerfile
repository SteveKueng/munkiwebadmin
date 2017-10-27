FROM python:2.7

ENV PYTHONUNBUFFERED 1
ENV APP_DIR /munkiwebadmin
ENV DJANGO_ENV dev
ENV SIMPLEMDMKEY ''

RUN apt-get update && apt-get install -y zip git

RUN mkdir ${APP_DIR}
RUN mkdir /munkirepo
RUN mkdir /munkitools
RUN mkdir /fieldkeys

RUN curl -Lk -o munkitools.zip `curl --silent https://api.github.com/repos/munki/munki/releases/latest | /usr/bin/awk '/zipball_url/ { print $2 }' | sed 's/[",]//g'` && unzip munkitools.zip -d . && rm -rf /munkitools.zip 
RUN cp -r /munki-munki*/code/client/* /munkitools && rm -rf /munki-munki*

WORKDIR ${APP_DIR}
COPY . ${APP_DIR}/
RUN cp munkiwebadmin/settings_template.py munkiwebadmin/settings.py 

RUN pip install -r requirements.txt
VOLUME [ "/munkirepo", "/fieldkeys" ]
ENTRYPOINT ["/bin/sh", "docker/run.sh"]