FROM lgr-base:latest
LABEL org.opencontainers.image.authors="int-eng@cofomo.com"

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
RUN chown -R lgr:0 $BASE_DIR

# Start LGR installation
USER lgr
WORKDIR $BASE_DIR

# Copy local settings file
RUN mv 'local.py' 'src/lgr_web/settings'
RUN mv 'test.py' 'src/lgr_web/settings'
ENV DJANGO_SETTINGS_MODULE=lgr_web.settings.local

# Prepare Python virtual environement
RUN python3.12 -m venv venv
ENV PATH="$BASE_DIR/venv/bin:$PATH"
ENV LD_LIBRARY_PATH="/usr/local/lib"

# Install lgr-django Python requirements
RUN source $BASE_DIR/venv/bin/activate \
    && python -m pip install -i https://artifactory.icann.org/artifactory/api/pypi/pypi/simple --upgrade pip \
    && pip install -i https://artifactory.icann.org/artifactory/api/pypi/pypi/simple --upgrade setuptools \
    && pip install -i https://artifactory.icann.org/artifactory/api/pypi/pypi/simple -r requirements.txt  \
    && rm requirements.txt
