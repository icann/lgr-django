FROM container-registry-dev.icann.org/icann/lgr-django:latest
LABEL org.opencontainers.image.authors="int-eng@cofomo.com"

# Install gunicorn
RUN pip install \
  -i https://artifactory.icann.org/artifactory/api/pypi/pypi/simple \
  gunicorn

# Set gunicorn configuration
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0"
ENV GUNICORN_CMD_ARGS="$GUNICORN_CMD_ARGS -w 3"
ENV GUNICORN_CMD_ARGS="$GUNICORN_CMD_ARGS -t 300"
ENV GUNICORN_CMD_ARGS="$GUNICORN_CMD_ARGS --max-requests 100"
ENV GUNICORN_CMD_ARGS="$GUNICORN_CMD_ARGS --log-level=debug"

COPY gunicornInit.sh /usr/local/bin/

EXPOSE 8000
WORKDIR $BASE_DIR/src
ENTRYPOINT ["gunicornInit.sh"]
CMD ["lgr_web.wsgi:application"]
