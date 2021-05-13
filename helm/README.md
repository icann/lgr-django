# LGR Toolset Helm Chart

Before installing the name chart into your namespace, it is essential to
execute those two steps.

# Preinstall

## Manually install your secret
All secrets value must never been in the git, so any secret must be install
manually. In the preinstall directory there is a secret template that can be
use to enter desired value.
```
helmEnv={The environement name}
mkdir helm/secrets
cp helm/preinstall/secret.yaml helm/secrets/$helmEnv.yaml
vi helm/secrets/$helmEnv.yaml

kubectl apply -f helm/secrets/$helmEnv.yaml
```

## Install the ServiceAccount
So the ingress can be use a Serivce Account must be first created to give it
the right access.The file is located in the preinstall directory and someone
with the right permissions must manually install it before the helm chart is
install.
```
helmEnv={The environement name}
vi helm/preinstall/ServiceAccount/$helmEnv.yaml

kubectl apply -f helm/preinstall/ServiceAccount/$helmEnv.yaml
```

# Usage

## Create super user
To create super user, you need to log in the lgr-gunicorn pod and create the
user manually.
```
kubectl exec -it $(kubectl get pod -l "srv=gunicorn" -o jsonpath='{.items[0].metadata.name}') -- /bin/bash
# Inside the gunicorn pods
../manage.py createsuperuser --noinput --email=<EMAIL>
```
