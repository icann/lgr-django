FROM centos:7
MAINTAINER ICANN 

# System configuration
#RUN setenforce 0
RUN yum update; yum install -y epel-release
RUN yum update; yum install -y nginx python-pip python-devel \
                               make gcc libxml2-devel libxslt-devel
ENV HOME=/var/www/lgr
RUN mkdir ${HOME}/packages -p; mkdir /var/log/lgr/
COPY picu-*.tar.gz munidata-*.tar.gz lgr-core-*.tar.gz lgr-django-*.tar.gz ${HOME}/packages/
RUN mkdir ${HOME}/lgr-django; tar xvf ${HOME}/packages/lgr-django-*.tar.gz -C ${HOME}/lgr-django --strip-components=1
WORKDIR ${HOME}/lgr-django
RUN pip install -r etc/requirements.txt -f ${HOME}/packages; pip install gunicorn

# ICU installation
RUN mkdir /root/icu
WORKDIR /root/icu
# TODO add md5sum checking 
RUN curl -L http://download.icu-project.org/files/icu4c/4.4.2/icu4c-4_4_2-RHEL52-x64.tgz \
       | tar xz -C / --wildcards usr/local/lib/*.44*; \
    curl -L http://download.icu-project.org/files/icu4c/4.6.1/icu4c-4_6_1-RHEL6-x64.tgz \
       | tar xz -C / --wildcards usr/local/lib/*.46*; \
    curl -L http://download.icu-project.org/files/icu4c/49.1.2/icu4c-49_1_2-RHEL6-x64.tgz \
       | tar xz -C / --wildcards usr/local/lib/*.49*; \
    curl -L http://download.icu-project.org/files/icu4c/50.1/icu4c-50_1-RHEL6-x64.tgz \
       | tar xz -C / --wildcards usr/local/lib/*.50*; \
    curl -L http://download.icu-project.org/files/icu4c/52.1/icu4c-52_1-RHEL6-x64.tgz \
       | tar xz -C / --wildcards usr/local/lib/*.52*; \
    echo "/usr/local/lib" > /etc/ld.so.conf.d/lgr.conf; ldconfig

# Django, Gunicorn and nginx configuration
ARG hosts=""
ARG email_srv=""
ARG email_from=""
# TODO allow adjusting the following values as well
 #SUPPORTED_UNICODE_VERSIONS
 #UNICODE_DATABASES
 #REPERTOIRE_STORAGE_LOCATION
 #LGR_STORAGE_LOCATION
 #LGR_RNG_FILE
 #SESSION_COOKIE_SECURE
 #CSRF_COOKIE_SECURE

WORKDIR ${HOME}/lgr-django
COPY start.sh .
RUN sed -i "s#WORKDIR_TO_REPLACE#${HOME}/lgr-django#" start.sh; \
    cp ${HOME}/lgr-django/src/lgr_web/settings/deploy.py.template \
       ${HOME}/lgr-django/src/lgr_web/settings/local.py; \
    sed -i "s/ALLOWED_HOSTS = \[\]/ALLOWED_HOSTS = \[\"${hosts}\"\]/g" \
       ${HOME}/lgr-django/src/lgr_web/settings/local.py; \
    # TODO the following field are actually in comment so we can do that
    echo "EMAIL_HOST = \"${email_srv}\"" >> ${HOME}/lgr-django/src/lgr_web/settings/local.py; \
    echo "DEFAULT_FROM_EMAIL = \"${email_from}\"" >> ${HOME}/lgr-django/src/lgr_web/settings/local.py; \
    echo "SESSION_COOKIE_SECURE = False" >> ${HOME}/lgr-django/src/lgr_web/settings/local.py; \
    echo "CSRF_COOKIE_SECURE = False" >> ${HOME}/lgr-django/src/lgr_web/settings/local.py; \
    python ./manage.py migrate; python ./manage.py collectstatic --noinput; \
    mkdir /run/lgr; \
    cp ${HOME}/lgr-django/etc/nginx/lgr-django.conf /etc/nginx/conf.d/nginx-django.conf; \
    sed -i "s/server_name.*/server_name ${hosts};/g" /etc/nginx/conf.d/nginx-django.conf

EXPOSE 80
#EXPOSE 443
CMD ["/bin/bash", "start.sh"]

