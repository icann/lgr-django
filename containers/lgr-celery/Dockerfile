FROM container-registry-dev.icann.org/icann/lgr-django:latest
LABEL MAINTAINER marc.blanchet@viagenie.ca

# Set gunicorn configuration
ENV APP="lgr_web"

COPY celeryInit.sh /usr/local/bin/

WORKDIR $BASE_DIR/src
ENTRYPOINT ["celeryInit.sh"]
CMD ["worker", "-c", "2"]
