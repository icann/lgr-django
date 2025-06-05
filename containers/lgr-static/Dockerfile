FROM container-registry-dev.icann.org/icann/lgr-django:latest
LABEL org.opencontainers.image.authors="int-eng@cofomo.com"

USER root
# Install nginx
RUN yum -y update; yum install -y nginx

# Set output to the stdout for easy grab for easy loggin
RUN sed -i 's|error_log /var/log/nginx/error.log;|error_log /dev/stdout info;|' /etc/nginx/nginx.conf
RUN sed -i 's|access_log  /var/log/nginx/access.log  main;|access_log /dev/stdout;|' /etc/nginx/nginx.conf

COPY staticInit.sh /usr/local/bin/
COPY lgr-static.conf.template /etc/nginx/templates/

WORKDIR $BASE_DIR/src
ENTRYPOINT ["staticInit.sh"]
CMD ["-g", "daemon off;"]
