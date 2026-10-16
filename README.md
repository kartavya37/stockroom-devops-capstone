# StockRoom — DevOps Capstone Project

StockRoom is a stock control application for a warehouse. A user can add an
item, change the quantity of an item and see the items that need a new order.

This repository contains the application and the complete DevOps chain:
tests, containers, a pipeline, a security scan, infrastructure as code,
Kubernetes, Helm and monitoring.

| | |
|---|---|
| Student | kartavya37 |
| Course | DevOps — Session 21 Final Capstone |
| Frontend | React 18 and Vite, Nginx sends the files |
| Backend | FastAPI, SQLAlchemy 2 and Alembic |
| Database | PostgreSQL 16 |
| Cloud | AWS VPC and EKS through Terraform |

---

## 1. The architecture

```text
Developer
   |
   v
GitHub  --->  GitHub Actions
                 |-- pytest                (12 tests)
                 |-- frontend build
                 |-- Docker build          (2 images)
                 |-- Trivy scan            (HIGH and CRITICAL)
                 `-- push to GHCR          (tag = commit SHA)
                           |
                           v
                      Terraform  --->  AWS VPC + EKS
                                            |
                                            v
                                          Helm
                                            |
                      +---------------------+---------------------+
                      |                     |                     |
                  Frontend              Backend               PostgreSQL
                  React/Nginx           FastAPI                  PVC
                      |                     |
                      +------ Ingress ------+
                                            |
                                   Prometheus  --->  Grafana
```

## 2. The repository

```text
.
├── backend/              FastAPI application, tests and migrations
│   ├── app/              config, database, models, schemas, routes
│   ├── alembic/          the migration that makes the items table
│   ├── tests/            12 pytest test cases
│   └── Dockerfile        non-root user, migration at the start
├── frontend/             React application
│   ├── src/              main.jsx and styles.css
│   ├── nginx.conf        static files and the /api proxy
│   └── Dockerfile        multi-stage build: Node, then Nginx
├── docker-compose.yml    the full local stack
├── .github/workflows/    the CI/CD pipeline
├── terraform/            AWS VPC and EKS
├── helm/stockroom/       the Kubernetes package
├── k8s/                  the namespace manifest
├── monitoring/           Prometheus values and a Grafana dashboard
├── scripts/              the smoke test and the load test
├── troubleshooting/      three broken manifests for the lab
└── docs/                 the operation guide and the submission notes
```

## 3. The API

| Method | Path | Function |
|---|---|---|
| GET | `/` | The name and the version of the service |
| GET | `/health` | The liveness check |
| GET | `/ready` | The readiness check. It makes a test of the database. |
| GET | `/metrics` | The metrics in the Prometheus format |
| GET | `/api/items` | All the items. The filters are `category` and `low_stock`. |
| GET | `/api/items/{id}` | One item |
| POST | `/api/items` | Make a new item |
| PUT | `/api/items/{id}` | Change an item |
| DELETE | `/api/items/{id}` | Delete an item |
| GET | `/api/items/stats` | The totals of the store |

The Swagger documentation is at `/docs`.

### The data model

One table with the name `items`.

| Column | Type | Function |
|---|---|---|
| `id` | integer | The primary key |
| `name` | text | The name of the item |
| `sku` | text | The unique code of the item |
| `category` | text | The group of the item |
| `quantity` | integer | The number of units in the store |
| `unit_price` | numeric | The price of one unit |
| `reorder_level` | integer | The low limit for a new order |
| `created_at` | timestamp | The time of the record |

## 4. Start the application

### Method 1 — Docker Compose (the fastest method)

```bash
docker compose up --build
```

| Address | Content |
|---|---|
| http://localhost:3000 | The application |
| http://localhost:8000/docs | The Swagger documentation |
| http://localhost:8000/health | The liveness endpoint |
| http://localhost:8000/metrics | The metrics |

Stop the stack:

```bash
docker compose down        # keep the data
docker compose down -v     # delete the data also
```

### Method 2 — the backend without a container

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export DATABASE_URL='postgresql+psycopg://stockroom:stockroom@localhost:5432/stockroom'
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### Method 3 — the frontend without a container

```bash
cd frontend
npm install
npm run dev
```

The development server sends each `/api` request to port 8000.

## 5. The tests

```bash
cd backend
pytest -v
```

The tests use an in-memory SQLite database. The tests do not touch the
PostgreSQL database. The fixture in `tests/conftest.py` replaces the
`get_db` dependency of the application.

The smoke test operates against a running stack:

```bash
./scripts/smoke-test.sh http://localhost:8000
```

## 6. The pipeline

The file is `.github/workflows/ci-cd.yml`. The pipeline starts at each push
to `main`.

| Stage | Job | Content |
|---|---|---|
| 1 | `test` | pytest and the frontend build |
| 2 | `build` | two images, two Trivy scans, then the push to GHCR |
| 3 | `deploy` | `helm upgrade --install` on the EKS cluster |

The image tag is the Git commit SHA:

```text
commit a1b2c3 → ghcr.io/kartavya37/<repo>-backend:a1b2c3
```

This gives traceability from the cluster back to the source code.

The push happens only after the two scans pass. A HIGH or a CRITICAL CVE
stops the pipeline, therefore no bad image goes to the registry.

## 7. The infrastructure

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply
```

Terraform makes a VPC with two public subnets and two private subnets, one
NAT gateway and one EKS cluster with a managed node group.

Configure kubectl with the command from the output:

```bash
aws eks update-kubeconfig --region ap-south-1 --name stockroom-dev-eks
```

**Delete the infrastructure after the evaluation.** An EKS cluster and a
NAT gateway have a high cost.

```bash
terraform destroy
```

## 8. Kubernetes and Helm

```bash
kubectl apply -f k8s/namespace.yaml

helm upgrade --install stockroom ./helm/stockroom \
  --namespace stockroom --create-namespace \
  -f helm/stockroom/values-dev.yaml
```

Look at the result:

```bash
kubectl get pods -n stockroom
kubectl get svc -n stockroom
kubectl get ingress -n stockroom
helm list -n stockroom
```

The chart makes these objects:

| Object | Name | Function |
|---|---|---|
| Deployment | `stockroom-backend` | 2 FastAPI Pods |
| Deployment | `stockroom-frontend` | 2 Nginx Pods |
| Deployment | `stockroom-postgres` | 1 database Pod |
| Service | `stockroom-backend` | ClusterIP, port 8000 |
| Service | `stockroom-frontend` | ClusterIP, port 80 |
| Service | `backend` | An alias for the Nginx proxy |
| Service | `stockroom-postgres` | ClusterIP, port 5432 |
| Secret | `stockroom-db` | The database connection string |
| PersistentVolumeClaim | `stockroom-postgres` | The database storage |
| Ingress | `stockroom` | `/` to the frontend, `/api` to the backend |
| HorizontalPodAutoscaler | `stockroom-backend` | CPU based |
| ServiceMonitor | `stockroom-backend` | The Prometheus target |

## 9. The autoscaler

The HPA needs the Metrics Server. See `k8s/metrics-server.md`.

```bash
kubectl get hpa -n stockroom --watch
./scripts/load-test.sh http://localhost:8000 60 20
```

A normal health request does not make enough CPU pressure. Use the load
script for the demonstration.

## 10. The monitoring

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring --create-namespace \
  -f monitoring/prometheus-values.yaml
```

Open Prometheus:

```bash
kubectl port-forward -n monitoring svc/monitoring-prometheus 9090:9090
```

Open Grafana. The user name is `admin` and the password is in the values file:

```bash
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80
```

Import the file `monitoring/grafana-dashboard.json` into Grafana.

## 11. The troubleshooting lab

| File | Error | Expected state |
|---|---|---|
| `troubleshooting/broken-image.yaml` | The image tag does not exist | `ImagePullBackOff` |
| `troubleshooting/broken-service.yaml` | The selector does not match a label | No endpoint |
| `troubleshooting/broken-probe.yaml` | The probe path gives 404 | `Running` but `0/1` ready |

The guide is in `docs/TROUBLESHOOTING.md`.

## 12. The security

- Both images run as a non-root user.
- The containers drop all the Linux capabilities.
- Trivy makes a check of both images in the pipeline.
- No secret is in the repository. The pipeline uses the automatic
  `GITHUB_TOKEN`.
- The file `.gitignore` excludes `.env`, `*.tfvars` and `*.tfstate`.

See `docs/SECURITY.md` for the Trivy explanation.
