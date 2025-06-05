FROM container-registry.icann.org/base-images/openshift-icann:202503
LABEL org.opencontainers.image.authors="int-eng@cofomo.com"

USER root

COPY lgr-base.sh .
RUN chmod +x ./lgr-base.sh
RUN ./lgr-base.sh && rm lgr-base.sh
