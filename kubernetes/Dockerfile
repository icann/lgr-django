# This Dockerfile is part of https://github.com/icann/lgr-django
# It is a container that builds LGR-django and LGR python deps and 
# also adds redis and apache for a complete and functional site.
# Refer to the README.md and k8s-lgrtool.yaml for pod details.
#   Thanks, -ptudor Dec 2017
FROM registry.fedoraproject.org/fedora:latest

ENV NAME=lgrtool COMPONENT=lgr-django VERSION=0 RELEASE=1 ARCH=x86_64
LABEL com.example.component="$COMPONENT" \
      name="$NAME" \
      version="$VERSION" \
      architecture="$ARCH" \
      summary="This container builds LGR packages and runs gunicorn with celery." \
      url="https://github.com/icann/lgr-django/" \
      vcs-type="git" vcs-url="git@github.com:icann/lgr-django.git" \
      authoritative-source-url="https://quay.io/ptudor/lgrtool-kubernetes" \
      usage="docker run -d -P 5000:5000 lgrtool-kubernetes"\
      run="/usr/bin/docker run -d -P 5000:5000 lgrtool-kubernetes"\
      maintainer="Patrick Tudor https://github.com/ptudor"

ENV commit_lgr_django="v2.0.1" \
    commit_lgr_core="v2.0.1" \
    commit_munidata="v2.0.0"

RUN echo "== prepare apache, redis, and others." \
    && echo not with fedora, only centos: yum -y install epel-release \
    && yum -y --setopt=tsflags=nodocs update \
    && yum -y install httpd httpd-devel httpd-tools mod_ssl openssl \
              redis python3-pip python3-devel make gcc redhat-rpm-config nc \
              libxml2-devel libxslt-devel gettext procps-ng httpd-tools \
              curl file unzip tar git ssmtp wget mailx xz patch supervisor \
    && yum clean all \
    && /sbin/alternatives --install /usr/bin/python python /usr/bin/python2.7 27 \
    && /sbin/alternatives --install /usr/bin/python python /usr/bin/python3.7 37 \
    && /sbin/alternatives --auto python \
    && /sbin/alternatives --display python \
    && python -V \
    && groupadd -g 4901 gunicorn \
    && useradd -s /sbin/nologin -d /var/www/lgr -u 4901 -g 4901 gunicorn \
    && chmod a+x /var/www/lgr

RUN echo "== apache settings:" \
    && echo "remove directory indexing from default configuration" \
    && sed -i -e "s/Options Indexes FollowSymLinks/Options FollowSymLinks/g" /etc/httpd/conf/httpd.conf \
    && echo "here we set the default to event instead of prefork." \
    && sed -i -e "s/^#LoadModule mpm_event_module/LoadModule mpm_event_module/g" /etc/httpd/conf.modules.d/00-mpm.conf \
    && sed -i -e "s/^LoadModule mpm_prefork_module/#LoadModule mpm_prefork_module/g" /etc/httpd/conf.modules.d/00-mpm.conf \
    && echo "also change the default ssl vhost port so we can use 443." \
    && sed -i -e "s/_default_:443/_default_:40443/g" /etc/httpd/conf.d/ssl.conf \
    && echo "Please ask your administrator to configure the secure redirect on the webserver" > /var/www/html/index.html \
    && date +%Y%m%d%H%M.%N > /var/www/html/health

# this value sets the CN of the self-signed localhost cert
ENV certificate_cn="lgrtool.example.com"

RUN echo "replace the default self-signed certificate for mod_ssl." \
    && mkdir -p /etc/pki/ca-trust/source/ \
    && openssl req -nodes -new -x509 -days 1096 -newkey rsa:4096 \
         -keyout /etc/pki/tls/private/localhost.key \
         -out /etc/pki/tls/certs/localhost.crt \
         -subj "/C=US/ST=California/L=Los Angeles/O=LGR Tool/OU=Org Unit Unset/CN=${certificate_cn}" \
    && cp /etc/pki/tls/certs/localhost.crt /etc/pki/ca-trust/source/anchors/localhost.pem \
    && openssl ecparam -name prime256v1 -genkey -param_enc explicit \
         -out /etc/pki/tls/private/localhost-ec256.key \
    && openssl ecparam -name secp384r1 -genkey \
         -out /etc/pki/tls/private/localhost-ec384.key \
    && openssl req -sha256 -nodes -new \
         -key /etc/pki/tls/private/localhost-ec384.key \
         -out /tmp/localhost-ec384.csr \
         -subj "/C=US/ST=California/L=Los Angeles/O=LGR Tool ECC/OU=Org Unit Unset/CN=${certificate_cn}" \
    && openssl req -x509 -sha256 -days 1087 \
         -key /etc/pki/tls/private/localhost-ec384.key \
         -in /tmp/localhost-ec384.csr \
         -out /etc/pki/tls/certs/localhost-ec384.crt \
    && cp /etc/pki/tls/certs/localhost-ec384.crt /etc/pki/ca-trust/source/anchors/localhost-ec384.pem \
    && /usr/bin/update-ca-trust extract

RUN echo "== for redis, strip out or replace configuration values" \
    && sed -i 's/^\(bind .*\)$/# \1/' /etc/redis.conf \
    && sed -i 's/^\(daemonize .*\)$/# \1/' /etc/redis.conf \
    && sed -i -e "s/^protected-mode.*/protected-mode no/g" /etc/redis.conf \
    && echo "rename-command SHUTDOWN f1b876f393d21b67ae83db5e60cd4e4217184237" >> /etc/redis.conf \
    && echo "rename-command CONFIG aa56b357fbca6dac0c466eccb372ad97a232a074" >> /etc/redis.conf \
    && echo "rename-command DEBUG dc45a7ca9398d5e069b72b27b00a5d9155c3db34" >> /etc/redis.conf \
    && echo "rename-command FLUSHALL dae0097a7e83b1a1e986831aec21770c35917fae" >> /etc/redis.conf \
    && echo "rename-command FLUSHDB a4c8acd99a10cd268a463c67f411bd208e289fc2" >> /etc/redis.conf \
    && echo "rename-command MONITOR cfdd0a67fba86f5c1ddf2c0afd041167e5284976" >> /etc/redis.conf \
    && echo "requirepass oce-6EA-zd2" >> /etc/redis.conf

ENV SHA256SUM_ICU442="8d3f5a0f7007b3863bfeeec4aa517e656b24972320995011e35bed45910144bd" \
    SHA256SUM_ICU461="07b862bc3ad7940445944ce2cd878d8e3386d119364d980bfc465d4ca096c74b" \
    SHA256SUM_ICU4912="7baea4a62db244267708947b52445fd11a69617180406734020a7991278a2bca" \
    SHA256SUM_ICU501="adbc30e891de409e1ff5c8a03ee925b60b3342742f6c6f41dc6684d821c18e6f" \
    SHA256SUM_ICU521="2a73302fa3556a113cd5e3de9c14cf6fc39e308fbe6970af6d84d723bf2c66a3" \
    SHA256SUM_ICU541="c5ff22b96ecda87f2dd6e424346bedc6a6321c0bd56d8ad925f273f8361c7dd6" \
    SHA256SUM_ICU561="c3f9f1d85d0f0d5e6416f28bf5bee833a01e48521b16a5f65760c025a4d4e18e" \
    SHA256SUM_ICU582="daf5ec865026613d3da5309b47041ae7b581f3b601efcd4ddc23ad3afde2534f" \
    SHA256SUM_ICU602="cbd8281ccfa2d70f72b5bd2d7a411ffe573c6684e9e23ee3b289f76de3a05e30" \
    LGR_HOME=/var/www/lgr

# primary section for lgr-django and dependencies
RUN export CFLAGS="-O2 -mtune=generic" \
    && mkdir ${LGR_HOME}/packages -p && mkdir /var/log/lgr \
    && echo "== 1. clone munidata and lgr-core to build required eggs." \
    && git clone -b "${target:-master}" https://github.com/icann/munidata.git ${LGR_HOME}/munidata \
    && cd ${LGR_HOME}/munidata && git pull && git checkout ${commit_munidata:-master} && git status \
    && git clone -b "${target:-master}" https://github.com/icann/lgr-core.git ${LGR_HOME}/lgr-core \
    && cd ${LGR_HOME}/lgr-core && git pull && git checkout ${commit_lgr_core:-master} && git status \
    && echo "== 2. First install munidata." \
    && cd ${LGR_HOME}/munidata && pip3 install -r requirements.txt && pip3 install . \
    && echo "== 3. Then install lgr-core." \
    && cd ${LGR_HOME}/lgr-core && pip3 install -r requirements.txt && pip3 install . \
    && echo "== 4. Now take care of lgr-django." \
    && git clone -b "${target:-master}" https://github.com/icann/lgr-django.git ${LGR_HOME}/lgr-django \
    && cd ${LGR_HOME}/lgr-django && git pull && git checkout ${commit_lgr_django:-master} && git status \
    && pip3 install -r etc/requirements.txt -f ${LGR_HOME}/lgr-django \
    && pip3 install gunicorn tornado Sphinx \
    && cd ${LGR_HOME}/lgr-django/doc && make html \
    && echo cd ${LGR_HOME}/lgr-django/doc && echo make html \
    && rm -Rf ${LGR_HOME}/lgr-core ${LGR_HOME}/munidata \
    && echo "chown to gunicorn uid" && chown -R 4901:4901 /var/log/lgr /var/www/lgr/lgr-django \
    && echo "== Now, going to download a bunch of ICU files" \
    && export SAFE_TMP=$(mktemp -d -t download.icu.XXXXXXXXXX) \
    && echo $SAFE_TMP && cd $SAFE_TMP \
    && curl -OL http://download.icu-project.org/files/icu4c/4.4.2/icu4c-4_4_2-RHEL52-x64.tgz \
    &&    echo $SHA256SUM_ICU442 icu4c-4_4_2-RHEL52-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-4_4_2-RHEL52-x64.tgz -C / --wildcards usr/local/lib/*.44* \
    && curl -OL http://download.icu-project.org/files/icu4c/4.6.1/icu4c-4_6_1-RHEL6-x64.tgz \
    &&    echo $SHA256SUM_ICU461 icu4c-4_6_1-RHEL6-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-4_6_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.46* \
    && curl -OL http://download.icu-project.org/files/icu4c/49.1.2/icu4c-49_1_2-RHEL6-x64.tgz \
    &&    echo $SHA256SUM_ICU4912 icu4c-49_1_2-RHEL6-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-49_1_2-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.49* \
    && curl -OL http://download.icu-project.org/files/icu4c/50.1/icu4c-50_1-RHEL6-x64.tgz \
    &&    echo $SHA256SUM_ICU501 icu4c-50_1-RHEL6-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-50_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.50* \
    && curl -OL http://download.icu-project.org/files/icu4c/52.1/icu4c-52_1-RHEL6-x64.tgz \
    &&    echo $SHA256SUM_ICU521 icu4c-52_1-RHEL6-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-52_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.52* \
    && curl -OL http://download.icu-project.org/files/icu4c/54.1/icu4c-54_1-RHEL6-x64.tgz \
    &&    echo $SHA256SUM_ICU541 icu4c-54_1-RHEL6-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-54_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.54* \
    && curl -OL http://download.icu-project.org/files/icu4c/56.1/icu4c-56_1-RHEL6-x64.tgz \
    &&    echo $SHA256SUM_ICU561 icu4c-56_1-RHEL6-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-56_1-RHEL6-x64.tgz -C / --wildcards usr/local/lib/*.56* \
    && curl -OL http://download.icu-project.org/files/icu4c/58.2/icu4c-58_2-Fedora24-x64.tgz \
    &&    echo $SHA256SUM_ICU582 icu4c-58_2-Fedora24-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-58_2-Fedora24-x64.tgz -C / --wildcards ./icu/usr/local/lib/*.58* --strip-components=2 \
    && curl -OL http://download.icu-project.org/files/icu4c/60.2/icu4c-60_2-Fedora27-x64.tgz \
    &&    echo $SHA256SUM_ICU602 icu4c-60_2-Fedora27-x64.tgz | sha256sum -c - \
    &&    tar -xz -f icu4c-60_2-Fedora27-x64.tgz -C / --wildcards ./icu/usr/local/lib/*.60* --strip-components=2 \
    && if [ -d $SAFE_TMP ]; then rm -Rf $SAFE_TMP; else echo "not a directory?"; fi \
    && echo "/usr/local/lib" > /etc/ld.so.conf.d/lgr.conf && ldconfig

# You must create this file site-specific/local.py or the build will fail.
# Refer to the README for a mandatory configuration option, SECRET_KEY
COPY site-specific/local.py ${LGR_HOME}/lgr-django/src/lgr_web/settings/local.py

# this only works because we're operating on the file lgr-sqlite3.db
WORKDIR ${LGR_HOME}/lgr-django
RUN python ./manage.py migrate \
    && python ./manage.py collectstatic --noinput \
    && mkdir /run/lgr; 

# insert apache configuration that proxies /lgr and serves /static
COPY apache-lgrtool.conf /etc/httpd/conf.d/99-apache-lgrtool.conf

COPY supervisord.conf /etc/supervisord.conf

# very useful if you exec into a shell. no one ever has to do that.
ENV TERM xterm-256color

EXPOSE 80 443 5000

CMD ["/usr/bin/supervisord"]
