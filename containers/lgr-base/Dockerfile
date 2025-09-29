FROM artifactory.icann.org/docker/ubi9/icann-python312:2025-09-122-6a2bd9
LABEL org.opencontainers.image.authors="int-eng@cofomo.com"

USER root

COPY lgr-base.sh .
RUN chmod +x ./lgr-base.sh
RUN ./lgr-base.sh && rm lgr-base.sh
