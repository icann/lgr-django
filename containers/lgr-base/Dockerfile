FROM container-registry.icann.org/base-images/centos8-icann:latest
LABEL MAINTAINER marc.blanchet@viagenie.ca
USER root

COPY lgr-base.sh .
COPY Python-3.10.12.tar.xz .
RUN ./lgr-base.sh && rm lgr-base.sh Python-3.10.12.tar.xz
