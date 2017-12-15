CONTAINERNAME = lgrtool-kubernetes
#CONTAINERVERSION = 8d8eaaa8475f
CONTAINERVERSION ?= $(shell date +%s )
LATEST ?= latest
REGISTRY = quay.io
ORGANIZATION = ptudor
PORT = 33001

.PHONY: build push local-run cert-rsa cert-ecdsa bash default

build:
	docker build -t $(CONTAINERNAME) .

tag:
	docker tag $(CONTAINERNAME) $(REGISTRY)/$(ORGANIZATION)/$(CONTAINERNAME):$(CONTAINERVERSION)
	docker tag $(CONTAINERNAME) $(REGISTRY)/$(ORGANIZATION)/$(CONTAINERNAME):$(LATEST)

push: tag
	docker push $(REGISTRY)/$(ORGANIZATION)/$(CONTAINERNAME):$(LATEST)
	docker push $(REGISTRY)/$(ORGANIZATION)/$(CONTAINERNAME)
	@echo $(CONTAINERVERSION)

local-run:
	docker run \
	--detach=true \
	--name="$(CONTAINERNAME)" \
	--publish="$(PORT):80" \
	--hostname="$(CONTAINERNAME)" \
	--read-only=false \
	--restart="always" \
	$(REGISTRY)/$(ORGANIZATION)/$(CONTAINERNAME):$(LATEST)

cert-rsa:
	@echo Size was intentionally set to 2048 instead of 4096 because google
	openssl req -nodes -new -x509 -sha256 -days 1096 -newkey rsa:2048 \
	-keyout lgr-rsa.key \
	-out lgr-rsa.crt \
	-subj "/C=US/ST=California/L=Los Angeles/O=LGR Tool/OU=Org Unit Unset/CN=localhost"
	openssl x509 -text -in lgr-rsa.crt

cert-ecdsa:
	@echo easier with cfssl, but let us try
	openssl ecparam -name prime256v1 -genkey -out lgr-ec256.key
	openssl req -new \
	-key lgr-ec256.key \
	-out lgr-ec.csr \
	-subj "/C=US/ST=California/L=Los Angeles/O=LGR Tool ECC/OU=Org Unit Unset/CN=localhost"
	openssl req -x509 -sha256 -days 1087 -key lgr-ec256.key -in lgr-ec.csr -out lgr-ec256.crt
	rm lgr-ec.csr
	openssl x509 -text -in lgr-ec256.crt

apply:
	kubectl apply -f k8s-lgrtool.yaml
	kubectl get svc --namespace=label-generation-ruleset

bash:
	docker exec -i -t $(CONTAINERNAME) bash

default: build
