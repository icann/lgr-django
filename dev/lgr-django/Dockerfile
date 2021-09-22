FROM lgr-base:latest
LABEL MAINTAINER marc.blanchet@viagenie.ca

# Set used variables
ENV BASE_DIR=/var/www/lgr
ENV LOG_DIR=/var/log/lgr

# Create lgr user and base directory
USER root
RUN useradd -r -d $BASE_DIR -M -g 0 -u 30404 lgr
RUN mkdir -p $BASE_DIR && chown lgr:0 $BASE_DIR
RUN mkdir -p $LOG_DIR && chown lgr:0 $LOG_DIR

# Copy files directory
COPY files $BASE_DIR
RUN mkdir $BASE_DIR/src/lgr_web/storage; chown -R lgr:0 $BASE_DIR

# Start LGR installation

USER lgr
WORKDIR $BASE_DIR

# Copy local setting
RUN mv 'local.py' 'src/lgr_web/settings'

# Prepare python virtual environement
RUN /usr/local/bin/python -m venv venv
ENV PATH="$BASE_DIR/venv/bin:$PATH"
ENV LD_LIBRARY_PATH="/usr/local/lib"

# Install/upgrade pip
RUN python -m pip install --upgrade pip

# Install lgr-django requirements
RUN pip install -r requirements.txt && rm requirements.txt

# Install mysql requirement
RUN pip install mysqlclient

# Set Django SUPERUSER password
# NEVER DO THIS IN PRODUCTION ENVIRONMENT
ENV DJANGO_SUPERUSER_PASSWORD=1234
