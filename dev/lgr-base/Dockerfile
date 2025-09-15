#TODO: Every dockerfiles in dev/ must be updated
FROM centos:8
LABEL MAINTAINER marc.blanchet@viagenie.ca
USER root

COPY lgr-base.sh .
RUN ./lgr-base.sh && rm lgr-base.sh
