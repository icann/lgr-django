FROM container-registry.icann.org/base-images/centos8-icann:latest
LABEL MAINTAINER marc.blanchet@viagenie.ca
USER root

COPY lgr-redis.sh .
RUN ./lgr-redis.sh && rm lgr-redis.sh

EXPOSE 6379
CMD ["redis-server"]
