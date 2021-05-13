FROM container-registry.icann.org/base-images/centos8-icann:latest
LABEL MAINTAINER marc.blanchet@viagenie.ca
USER root

COPY lgr-base.sh .
RUN ./lgr-base.sh && rm lgr-base.sh
