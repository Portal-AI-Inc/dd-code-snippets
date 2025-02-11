# Prereq
* Create policy
** `aws --profile=prod iam create-policy --policy-name grafana-loki-s3-policy --policy-document file://aws/loki-s3-policy.json`
* Create Trust
** `aws --profile=prod iam create-role --role-name LokiServiceAccountRole --assume-role-policy-document file://aws/trust-policy.json`
* Attach Policy
** `aws --profile=prod iam attach-role-policy --role-name LokiServiceAccountRole --policy-arn arn:aws:iam::204443246822:policy/grafana-loki-s3-policy`

# Install Helm Loki Repo
```
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

kubectl create namespace loki
```

# install Loki via helm
```
helm --kube-context arn:aws:eks:us-east-1:204443246822:cluster/prod-eks \
install loki grafana/loki -f values.yml --namespace loki
```

## update via helm
```
helm --kube-context arn:aws:eks:us-east-1:204443246822:cluster/prod-eks \
upgrade loki grafana/loki -f values.yml --namespace loki
```

Output of original helm install
```
***********************************************************************
 Welcome to Grafana Loki
 Chart version: 5.40.1
 Loki version: 2.9.2
***********************************************************************
```

## uninstall cli
```
helm --kube-context arn:aws:eks:us-east-1:204443246822:cluster/prod-eks \
helm uninstall loki --namespace loki
```