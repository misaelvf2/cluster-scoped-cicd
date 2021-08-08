# EXTERNAL_DNS=<DNS from ngrok or other external domain for routing>
# Use tekton dashboard
# kubectl --namespace tekton-pipelines port-forward svc/tekton-dashboard 9097:9097
PASSWORD=en60573181su21


all: cluster tekton \
	ingress	ambassador webhook pipeline-resources pipeline listener redis postgresql-db harbor

cluster:
	kind create cluster --config=YAML/kind-config.yaml

tekton:
	kubectl apply -f \
		https://storage.googleapis.com/tekton-releases/pipeline/latest/release.yaml
	kubectl apply -f \
		https://github.com/tektoncd/dashboard/releases/latest/download/tekton-dashboard-release.yaml
	kubectl apply -f \
		https://storage.googleapis.com/tekton-releases/triggers/latest/release.yaml
	kubectl apply -f \
		https://storage.googleapis.com/tekton-releases/triggers/latest/interceptors.yaml
	kubectl apply -f \
	    YAML/tekton-triggers-clusterroles.yaml
	kubectl apply -f \
		YAML/rbac.yaml

webhook:
	kubectl apply -f YAML/webhook-secret.yaml
	kubectl apply -f YAML/create-webhook.yaml
	kubectl apply -f YAML/create-webhook-run.yaml
	sleep 30

ingress:
	kubectl apply -f YAML/webhook-role.yaml
	kubectl apply -f YAML/create-ingress.yaml
	kubectl apply -f YAML/create-ingress-run.yaml

ambassador:
	sleep 90
	kubectl apply -f \
		https://github.com/datawire/ambassador-operator/releases/latest/download/ambassador-operator-crds.yaml
	kubectl apply -n ambassador -f \
		https://github.com/datawire/ambassador-operator/releases/latest/download/ambassador-operator-kind.yaml
	kubectl wait --timeout=180s -n \
		ambassador --for=condition=deployed ambassadorinstallations/ambassador
	kubectl annotate ingress el-github-listener kubernetes.io/ingress.class=ambassador

pipeline:
	kubectl apply -f YAML/registry-sa.yaml
	kubectl apply -f YAML/build-with-asylo-and-push.yaml
	kubectl apply -f YAML/deploy-using-kubectl.yaml
	kubectl apply -f YAML/secure-pipeline.yaml

pipeline-resources:
	kubectl apply -f YAML/hello-world-git-pr.yaml
	kubectl apply -f YAML/hello-world-image-pr.yaml

listener:
	kubectl apply -f YAML/pipeline-github-listener.yaml

# Testing Harbor integration
helm:
	curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/master/scripts/get-helm-3
	chmod 700 get_helm.sh
	./get_helm.sh
	-helm init

postgresql:
	-helm repo add bitnami https://charts.bitnami.com/bitnami
	-helm install postgresql  \
		--set postgresql.username=${PASSWORD} \
		--set postgresql.password=${PASSWORD} \
		bitnami/postgresql-ha
	echo "TEST"

postgresql-db: postgresql
	sleep 60
	kubectl run postgresql-postgresql-ha-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql:11 \
		--env="PGPASSWORD=$(PASSWORD)" --command -- psql -h postgresql-postgresql-ha-pgpool -p 5432 -U ${PASSWORD} -d postgres \
		-c "CREATE DATABASE registry"
	kubectl run postgresql-postgresql-ha-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql:11 \
		--env="PGPASSWORD=$(PASSWORD)" --command -- psql -h postgresql-postgresql-ha-pgpool -p 5432 -U ${PASSWORD} -d postgres \
		-c "CREATE DATABASE clair"
	kubectl run postgresql-postgresql-ha-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql:11 \
		--env="PGPASSWORD=$(PASSWORD)" --command -- psql -h postgresql-postgresql-ha-pgpool -p 5432 -U ${PASSWORD} -d postgres \
		-c "CREATE DATABASE notary_server"
	kubectl run postgresql-postgresql-ha-client --rm --tty -i --restart='Never' --namespace default --image bitnami/postgresql:11 \
		--env="PGPASSWORD=$(PASSWORD)" --command -- psql -h postgresql-postgresql-ha-pgpool -p 5432 -U ${PASSWORD} -d postgres \
		-c "CREATE DATABASE notary_signer"

redis:
	-helm repo add bitnami https://charts.bitnami.com/bitnami
	helm install redis \
		--set usePassword=false \
		bitnami/redis

harbor:
	-helm repo add harbor https://helm.goharbor.io
	#helm fetch harbor/harbor --untar
	helm install harbor harbor/harbor --version 1.4.0 \
		--set externalURL=https://demo.goharbor.io \
		--set expose.type=ingress \
		--set expose.loadBalancer.ports.httpPort=80 \
		--set expose.loadBalancer.ports.httpsPort=443 \
		--set expose.ingress.hosts.core=demo.goharbor.io \
		--set expose.ingress.hosts.notary=demo.goharbor.io \
		--set expose.tls.secretName=harbor-cert \
		--set expose.nodePort.name=harbor \
		--set database.type=external \
		--set database.external.host=postgresql-postgresql-ha-pgpool.default.svc.cluster.local \
		--set database.external.username=${PASSWORD} \
		--set database.external.password=${PASSWORD} \
		--set redis.type=external \
		--set redis.external.host=redis-master.default.svc.cluster.local
	#kubectl annotate ingress harbor-harbor-ingress \
	#	cert-manager.io/cluster-issuer=letsencrypt-prod
