# The operation guide

This guide gives the exact command order from an empty machine to a monitored
cluster. Follow the parts in sequence.

---

## Part 1 — the local stack (10 minutes)

```bash
docker compose up --build -d
./scripts/smoke-test.sh http://localhost:8000
open http://localhost:3000
```

Stop:

```bash
docker compose down
```

---

## Part 2 — GitHub (10 minutes)

```bash
git remote add origin https://github.com/kartavya37/<repository>.git
git push -u origin main
```

Then:

1. Go to **Settings → Actions → General**.
2. Set **Workflow permissions** to **Read and write permissions**.
3. Push a commit. The pipeline starts.
4. After the first run, go to your profile, then **Packages**.
5. Make both packages public.

---

## Part 3 — a local Kubernetes test (20 minutes)

This part needs no AWS account. Use it for a test before the cloud work.

```bash
minikube start --cpus 4 --memory 6144
minikube addons enable ingress
minikube addons enable metrics-server

kubectl apply -f k8s/namespace.yaml

helm upgrade --install stockroom ./helm/stockroom \
  -n stockroom -f helm/stockroom/values-dev.yaml --wait

kubectl get pods -n stockroom
```

Open the application:

```bash
echo "$(minikube ip)  stockroom.local" | sudo tee -a /etc/hosts
open http://stockroom.local
```

---

## Part 4 — AWS (45 minutes, and this part has a cost)

```bash
aws configure                       # the key, the secret and ap-south-1
aws sts get-caller-identity         # a check of the credentials

cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan -out=tfplan          # SCREENSHOT
terraform apply tfplan              # 15 to 20 minutes
```

Configure kubectl:

```bash
aws eks update-kubeconfig --region ap-south-1 --name stockroom-dev-eks
kubectl get nodes
```

---

## Part 5 — the Ingress controller on EKS

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update

helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx --create-namespace \
  --set controller.service.type=LoadBalancer

kubectl get svc -n ingress-nginx --watch
```

Wait for the address of the load balancer. Then put the address in the
values file, or use the address directly.

---

## Part 6 — the Metrics Server

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl top nodes
```

---

## Part 7 — the application on EKS

```bash
kubectl apply -f k8s/namespace.yaml

helm upgrade --install stockroom ./helm/stockroom \
  -n stockroom -f helm/stockroom/values-prod.yaml \
  --set backend.image.tag=<commit-sha> \
  --set frontend.image.tag=<commit-sha> \
  --wait --timeout 10m

kubectl get pods -n stockroom     # SCREENSHOT
kubectl get svc -n stockroom      # SCREENSHOT
helm list -n stockroom            # SCREENSHOT
```

---

## Part 8 — the monitoring

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml --wait
```

Prometheus:

```bash
kubectl port-forward -n monitoring svc/monitoring-prometheus 9090:9090
# Open http://localhost:9090/targets        SCREENSHOT
```

Grafana:

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
# Open http://localhost:3001
# The user name is admin. The password is in monitoring/prometheus-values.yaml.
# Import monitoring/grafana-dashboard.json   SCREENSHOT
```

---

## Part 9 — the autoscaler demonstration

Terminal 1:

```bash
kubectl get hpa -n stockroom --watch
```

Terminal 2:

```bash
kubectl port-forward -n stockroom svc/stockroom-backend 8000:8000
```

Terminal 3:

```bash
./scripts/load-test.sh http://localhost:8000 120 40
```

The replica count increases after one or two minutes.

---

## Part 10 — the troubleshooting lab

See `docs/TROUBLESHOOTING.md`.

---

## Part 11 — delete the infrastructure

**Do this part immediately after the evaluation.**

```bash
helm uninstall stockroom -n stockroom
helm uninstall monitoring -n monitoring
helm uninstall ingress-nginx -n ingress-nginx

# Wait for the load balancer to disappear. Terraform cannot delete a VPC
# that still contains a load balancer.
kubectl get svc -A | grep LoadBalancer

cd terraform
terraform destroy                 # SCREENSHOT
```

Make a check in the AWS console:

- EC2 → Load Balancers: the list is empty.
- EKS → Clusters: the list is empty.
- VPC → NAT Gateways: the list is empty.
- EC2 → Elastic IPs: the list is empty.
