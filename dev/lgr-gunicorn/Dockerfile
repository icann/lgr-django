FROM lgr-django:latest
LABEL MAINTAINER marc.blanchet@viagenie.ca

# Install gunicorn
RUN pip install gunicorn

# Set gunicorn configuration
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0"
ENV GUNICORN_CMD_ARGS="$GUNICORN_CMD_ARGS -w 3"
ENV GUNICORN_CMD_ARGS="$GUNICORN_CMD_ARGS -t 300"
ENV GUNICORN_CMD_ARGS="$GUNICORN_CMD_ARGS --max-requests 100"

COPY gunicornInit.sh /usr/local/bin/

EXPOSE 8000
WORKDIR $BASE_DIR/src
ENTRYPOINT ["gunicornInit.sh"]
CMD ["lgr_web.wsgi:application"]
