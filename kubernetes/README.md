# LGR Tool in Kubernetes

If you already have a Kubernetes cluster, just apply the yaml and see what happens. The website immediately starts with GKE in December 2017.


## Getting Started Quickly

After cloning the repo or downloading this file, apply it to your cluster.

```
kubectl apply -f k8s-lgrtool.yaml
kubectl get svc --namespace=label-generation-ruleset
```

The website will run in its own dedicated namespace and a create a loadbalancer service. Continue reading to discover how to build your own container.

The Service is a Loadbalancer type for its external address; your environment might require a NodePort or Ingress to be configured instead before the internal endpoint is available on a global address.

The container this pod pulls is only suitable for testing. Your website will share critical secrets with the public. Please build a local image with the copy-and-paste steps below and push it to your own private image repository.


## What Is The End Result?

This Kubernetes deployment pulls a container and runs it three times with four processes among them. Apache will be listening on port 443, forwarding to gunicorn on 5000, with celery reaching out to a redis container.

## What Files Are Here?

The utilities in this folder will help you get up-and-running with your own copy of the LGR Tool in Kubernetes.

There are four key files:

- __k8s-lgrtool.yaml__  
Framework for a deployment of three containers
- __Makefile__  
Defines the registry to push the image to and Docker shortcuts
- __Dockerfile__  
Builds all LGR related packages and installs dependencies
- __apache-lgrtool.conf__  
Passes requests to Django via gunicorn

There is also a configuration template you must copy to a local file and review:

- site-specific/__template-local.py__
- site-specific/__local.py__

Finally, celery and gunicorn run together in a container with the configuration in supervisord.conf. 

- __supervisord.conf__

## Getting Started from Scratch

#### local.py

Customizing the container begins with creating a configuration file for Django.

```
cp site-specific/template-local.py site-specific/local.py
```

After creating our gitignored file, replace the secret key with a unique value.

```
export NEWSECRET=$(openssl rand 48 -base64)
sed -i -e "s|^SECRET_KEY =.*|SECRET_KEY = \'${NEWSECRET}\'|" site-specific/local.py
```

Please review the file for other important variables including:

- `ALLOWED_HOSTS`
- `DEFAULT_FROM_EMAIL `
- `EMAIL_HOST `
- `DATABASES`

This container uses a sqlite database without persistent storage. You will lose data when upgrading the containers in the cluster.

#### apache-lgrtool.conf

If you have configured a hostname in DNS, consider updating the hostname in the Apache configuration. Look for `ServerName` and the port 80 virtualhost with its simple Redirect instruction. (Also search for the variable `certificate_cn` in the Dockerfile.)

#### Docker Build

Now that we have created the required file locally, it is time to build the container. We can use the Makefile shortcut here.

```
make build
```

#### Push Local Image

You must set the location of your repository in the Makefile. At the top is a list of a variables to update. Unless you instruct the Makefile otherwise, the default tag for each new revision is epoch seconds.

```
make push
```

#### Update YAML for Your Environment

```
grep example k8s-lgrtool.yaml
perl -pi -e "s/example/acmewidgets/g" k8s-lgrtool.yaml
```

#### Update YAML for New Image

The make steps echoed the new version tag to your Terminal. Find the old version with a grep and then replace the old string with the new string.

```
grep image: k8s-lgrtool.yaml | cut -f3 -d: | uniq
perl -pi -e "s/lgrtool-kubernetes:4ff164d18ec0/lgrtool-kubernetes:1513158532/g" k8s-lgrtool.yaml
```

#### Registry Authentication to Pull Images

If your container registry requires authentication, create a secret for it and uncomment the relevant line in the yaml:

```
kubectl create secret docker-registry lgrtool-pull-secret \
    --docker-server=quay.io \
    --docker-username=ptudor \
    --docker-password='ocbxYtCU7ydpQTNkzmJmkw' \
    --docker-email='ptudor@example.com' \
    --dry-run -o yaml > k8s-secret-registry.yaml
cat k8s-secret-registry.yaml
kubectl apply -f k8s-secret-registry.yaml --namespace=label-generation-ruleset
```

## Special Docker Details

#### Volumes
By default, all storage is lost on container restart. This will include the sqlite3 database, the redis database, the apache logs, and any active sessions and associated files. 

If you need persistent storage, look toward these files and paths:

- /var/www/lgr/lgr-django/src/lgr_web/lgr-sqlite3.db
- /var/lib/redis/
- /var/log/httpd/

#### Ports

While this container is meant to be run with Kubernetes for a complete environment, it is possible to run the site directly. Port 5000, for gunicorn launched by supervisord, is exposed and can be published for standalone localhost development or troubleshooting. If you modify the supervisord.conf to also launch redis and httpd, disabled by default, you can map ports 80 and 443 as well.

#### Requirements

This container is able to consume memory and cpu quickly in bursts. The limits defined in the k8s-lgrtool.yaml are likely insufficient.  If you have available capacity, allow a large ceiling or run without limits and monitor with `docker stats`.

#### Configuration

The file local.py should be customized for your installation.

## Any Other Special Details?

Redis requires authentication just in case it is accidentially exposed externally.

Apache supports [HTTP/2](https://httpd.apache.org/docs/2.4/howto/http2.html) with ECDSA.

## Can I Just Build From Your Image?

Sure. Something like this should get you started:

```
FROM quay.io/ptudor/lgrtool-kubernetes
COPY local.py ${LGR_HOME}/lgr-django/src/lgr_web/settings/local.py
RUN cd ${LGR_HOME}/lgr-django && python ./manage.py migrate
CMD ["/run-lgr.sh"]
```

You might want to overwrite the Apache config and TLS certificates too.

--

## Extra tips for various service providers

#### Google Cloud Platform

To run a new cluster on the Google Cloud Platform, after [downloading the SDK](https://cloud.google.com/sdk/downloads) and adding its bin directory to your PATH you can create and authenticate to a new cluster. You might find their [Quickstart](https://cloud.google.com/kubernetes-engine/docs/quickstart) useful and the [Guestbook Tutorial](https://cloud.google.com/kubernetes-engine/docs/tutorials/guestbook) is a nice guide through the vendor-specific steps required before you can apply the yaml.

````
export PATH=$PATH:~/bin/google-cloud-sdk/bin
gcloud components install kubectl
gcloud container clusters create lgrcluster
gcloud container clusters get-credentials lgrcluster
````

If you choose to use the [Ingress controller](https://cloud.google.com/kubernetes-engine/docs/tutorials/http-balancer) instead of the LoadBalancer Service, you can upload a key. The default configuration is not to use a NodePort and Ingress, but instead an ephemeral global address with TLS handled directly by the container.

````
make cert-ecdsa
gcloud compute ssl-certificates create lgrtool-ecdsa --certificate lgr-ec256.crt --private-key lgr-ec256.key
make cert-rsa
gcloud compute ssl-certificates create lgrtool-rsa --certificate lgr-rsa.crt --private-key lgr-rsa.key
````

## Credits and Blame
Work on Kubernetes for LGR Tool by:  
[Patrick Tudor](https://github.com/ptudor)   
[Chris Dower](https://github.com/cdower)   
