FROM container-registry.icann.org/base-images/openshift-icann:202306
LABEL MAINTAINER int-eng@cofomo.com
USER root

COPY lgr-base.sh .
RUN ./lgr-base.sh && rm lgr-base.sh
