# Runbook

The order of commands from an empty machine to a monitored cluster that
Argo CD keeps in sync. Tested on macOS with Docker Desktop and Minikube.

## 1. Local stack

```bash
docker compose up --build -d
./scripts/smoke-test.sh http://localhost:8000
open http://localhost:3000
docker compose down -v
```

## 2. GitHub

```bash
git remote add origin https://github.com/kartavya37/stockroom-devops-capstone.git
git push -u origin main
```

1. **Settings → Actions → General → Workflow permissions → Read and write.**
   Job 3 needs it to commit the image tag.
2. Wait for the first green run.
3. Profile → **Packages** → `stockroom-backend` and `stockroom-frontend` →
   **Package settings → Change visibility → Public.** The cluster pulls
   without credentials.
4. `git pull`. The pipeline added a commit with the new tag.

## 3. Cluster and monitoring

```bash
minikube start -p stockroom --driver=docker --cpus=4 --memory=6144
minikube -p stockroom addons enable ingress
minikube -p stockroom addons enable metrics-server

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml --wait
```

## 4. Helm install

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install stockroom ./helm/stockroom -n stockroom \
  -f helm/stockroom/values-dev.yaml --wait
helm list -n stockroom
kubectl get pods,svc,ingress,hpa -n stockroom
```

## 5. Hand over to Argo CD

Argo CD applies rendered manifests and does not keep a Helm release, so
remove the release first.

```bash
helm uninstall stockroom -n stockroom

kubectl create namespace argocd
kubectl apply -n argocd --server-side --force-conflicts \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
kubectl wait -n argocd --for=condition=Available deploy --all --timeout=5m

kubectl apply -f gitops/argocd-application.yaml
kubectl get applications -n argocd        # wait for Synced / Healthy
```

Admin password:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d; echo
```

## 6. Port-forwards

| Terminal | Command | URL |
|---|---|---|
| A | `kubectl port-forward -n ingress-nginx svc/ingress-nginx-controller 8080:80` | http://stockroom.local:8080 |
| B | `kubectl port-forward -n argocd svc/argocd-server 8443:443` | https://localhost:8443 |
| C | `kubectl port-forward -n monitoring svc/monitoring-prometheus 9090:9090` | http://localhost:9090/targets |
| D | `kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80` | http://localhost:3001 |

The Ingress rule matches the host `stockroom.local`. Add it once:

```bash
echo "127.0.0.1 stockroom.local" | sudo tee -a /etc/hosts
```

Grafana password:

```bash
kubectl get secret -n monitoring monitoring-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo
```

## 7. Traffic for the dashboards

```bash
for i in $(seq 1 300); do
  curl -s http://stockroom.local:8080/api/items > /dev/null
  curl -s http://stockroom.local:8080/api/items/stats > /dev/null
  sleep 0.2
done
```

## 8. AWS

```bash
aws sts get-caller-identity
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
aws eks update-kubeconfig --region ap-south-1 --name stockroom-dev-eks
kubectl get nodes
kubectl config use-context stockroom      # back to Minikube
terraform destroy
```

After the destroy, these lists must be empty for `stockroom`:

```bash
aws eks list-clusters --region ap-south-1
aws ec2 describe-vpcs --region ap-south-1 --filters Name=tag:Project,Values=stockroom --query 'Vpcs[].VpcId'
aws ec2 describe-nat-gateways --region ap-south-1 --filter Name=tag:Project,Values=stockroom Name=state,Values=available --query 'NatGateways[].NatGatewayId'
```

## 9. Troubleshooting lab

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
