FROM registry.access.redhat.com/ubi9/ubi
LABEL org.opencontainers.image.authors="int-eng@cofomo.com"

USER root

COPY lgr-base.sh .
RUN chmod +x ./lgr-base.sh
RUN ./lgr-base.sh && rm lgr-base.sh
