FROM centos:7
MAINTAINER ICANN

# System configuration
#RUN setenforce 0
RUN yum makecache \
  && yum install -y epel-release \
  && yum makecache \
  && yum install -y nginx python-pip python-devel make gcc libxml2-devel libxslt-devel redis \
  && yum clean all

ENV HOME=/var/www/lgr
RUN mkdir ${HOME}/packages -p; mkdir /var/log/lgr/
COPY picu-*.tar.gz munidata-*.tar.gz lgr-core-*.tar.gz lgr-django-*.tar.gz ${HOME}/packages/
RUN mkdir ${HOME}/lgr-django; tar xvf ${HOME}/packages/lgr-django-*.tar.gz -C ${HOME}/lgr-django --strip-components=1
WORKDIR ${HOME}/lgr-django
RUN pip install -r etc/requirements.txt -f ${HOME}/packages; pip install gunicorn

# ICU installation
RUN mkdir /root/icu
WORKDIR /root/icu
ENV SHA256SUM_ICU442="8d3f5a0f7007b3863bfeeec4aa517e656b24972320995011e35bed45910144bd" \
    SHA256SUM_ICU461="07b862bc3ad7940445944ce2cd878d8e3386d119364d980bfc465d4ca096c74b" \
    SHA256SUM_ICU4912="7baea4a62db244267708947b52445fd11a69617180406734020a7991278a2bca" \
    SHA256SUM_ICU501="adbc30e891de409e1ff5c8a03ee925b60b3342742f6c6f41dc6684d821c18e6f" \
    SHA256SUM_ICU521="2a73302fa3556a113cd5e3de9c14cf6fc39e308fbe6970af6d84d723bf2c66a3"
RUN curl -OL http://download.icu-project.org/files/icu4c/4.4.2/icu4c-4_4_2-RHEL52-x64.tgz && \
       echo $SHA256SUM_ICU442 icu4c-4_4_2-RHEL52-x64.tgz | sha256sum -c - && \
       tar -xz -f icu4c-4_4_2-RHEL52-x64.tgz -C / --wildcards usr/local/lib/*.44* && \
    curl -OL http://download.icu-project.org/files/icu4c/4.6.1/icu4c-4_6_1-RHEL6-x64.tgz && \
       echo $SHA256SUM_ICU461 icu4c-4_6_1-RHEL6-x64.tgz | sha256sum -c - && \
       tar -xz -f icu4c-4_6_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.46* && \
    curl -OL http://download.icu-project.org/files/icu4c/49.1.2/icu4c-49_1_2-RHEL6-x64.tgz && \
       echo $SHA256SUM_ICU4912 icu4c-49_1_2-RHEL6-x64.tgz | sha256sum -c - && \
       tar -xz -f icu4c-49_1_2-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.49* && \
    curl -OL http://download.icu-project.org/files/icu4c/50.1/icu4c-50_1-RHEL6-x64.tgz && \
       echo $SHA256SUM_ICU501 icu4c-50_1-RHEL6-x64.tgz | sha256sum -c - && \
       tar -xz -f icu4c-50_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.50* && \
    curl -OL http://download.icu-project.org/files/icu4c/52.1/icu4c-52_1-RHEL6-x64.tgz && \
       echo $SHA256SUM_ICU521 icu4c-52_1-RHEL6-x64.tgz | sha256sum -c - && \
       tar -xz -f icu4c-52_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.52* && \
    echo "/usr/local/lib" > /etc/ld.so.conf.d/lgr.conf && ldconfig

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

