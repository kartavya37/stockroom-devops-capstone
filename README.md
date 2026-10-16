# StockRoom — DevOps Capstone Project

StockRoom is a stock control app for a small warehouse. You add items with a SKU, a category, a quantity, a unit price and a reorder level. The dashboard shows the total stock value and flags every item at or below its reorder level, so you know what to order next.

The app is deliberately small. The project is the delivery chain around it: tests, containers, a CI/CD pipeline with a security gate, infrastructure as code on AWS, Kubernetes with Helm, GitOps with Argo CD, and monitoring with Prometheus and Grafana.

| | |
|---|---|
| Student | Kartavya Panchal |
| Roll number | 24bcs10343 |
| Demo video | [demo/video.mp4](demo/video.mp4) |
| Slides | [demo/slides.pdf](demo/slides.pdf) · [demo/slides.pptx](demo/slides.pptx) |
| Pipeline runs | [GitHub Actions](../../actions) |

---

## Architecture

```text
 Developer ── git push ──► GitHub (main)
                              │
                              ▼
                       GitHub Actions
    ┌─────────────┬───────────┴─────────┬──────────────────────────┐
    │ 1. test     │ 2. images           │ 3. gitops                │
    │ pytest (12) │ docker build ×2     │ yq writes the commit SHA │
    │ vite build  │ Trivy gate ×2       │ into helm values.yaml    │
    │             │ push to GHCR (SHA)  │ and commits it           │
    └─────────────┴─────────────────────┴────────────┬─────────────┘
                                                     │ Argo CD watches the repo
                                                     ▼
                         Kubernetes namespace "stockroom"
             Ingress ── /     ──► frontend  (React + Nginx, 2 Pods)
                     └─ /api  ──► backend   (FastAPI, 2–4 Pods, HPA)
                                       │
                                       ▼
                                  PostgreSQL 16 (PVC)
                                       ▲
             Prometheus ── scrapes /metrics via ServiceMonitor
                  │
                  ▼
              Grafana ── "StockRoom API" dashboard (loaded from a ConfigMap)

 Terraform ──► AWS ap-south-1: VPC, 2 public + 2 private subnets, NAT, EKS 1.36 + node group
```

## Tech stack

| Area | Tools |
|---|---|
| Backend | Python 3.12, FastAPI 0.143, SQLAlchemy 2, Alembic, PostgreSQL 16 |
| Frontend | React 18, Vite 5, Nginx 1.30 (non-root) |
| Tests | pytest with an in-memory SQLite database |
| Containers | Docker (multi-stage frontend, non-root users), Docker Compose |
| CI/CD | GitHub Actions, GitHub Container Registry (GHCR) |
| Security | Trivy 0.75 image scan, blocks fixable HIGH and CRITICAL CVEs |
| Infrastructure | Terraform, AWS VPC, AWS EKS |
| Kubernetes | Helm, ingress-nginx, HPA, Metrics Server, Argo CD |
| Observability | kube-prometheus-stack (Prometheus Operator, Prometheus, Grafana) |

## Repository layout

```text
backend/             FastAPI app, Alembic migration, 12 pytest tests, Dockerfile
frontend/            React app, Nginx config, multi-stage Dockerfile
docker-compose.yml   the whole stack on one machine
.github/workflows/   the CI/CD pipeline
terraform/           AWS VPC + EKS
k8s/                 namespace manifest, Metrics Server note
helm/stockroom/      Helm chart: deployments, services, ingress, HPA,
                     ServiceMonitor, Grafana dashboard ConfigMap, PostgreSQL
gitops/              Argo CD Application
monitoring/          kube-prometheus-stack values
scripts/             smoke test and load test
troubleshooting/     three deliberately broken manifests
docs/                runbook, security notes, troubleshooting lab, grading map
demo/                video and slides
screenshots/         evidence for every graded item
```

## API

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Liveness: the process is up |
| GET | `/ready` | Readiness: runs `SELECT 1` against the database |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/items` | List items. Filters: `?category=`, `?low_stock=true` |
| GET | `/api/items/{id}` | One item |
| POST | `/api/items` | Create an item (409 if the SKU exists) |
| PUT | `/api/items/{id}` | Partial update |
| DELETE | `/api/items/{id}` | Delete an item |
| GET | `/api/items/stats` | Item count, units, stock value, low-stock count, categories |

Swagger UI is at `/docs`. The `/stats` route is declared before `/{id}`, otherwise FastAPI would try to parse the word `stats` as an id.

**Data model.** One table, `items`, created by `backend/alembic/versions/0001_create_items.py`: `id`, `name`, `sku` (unique), `category`, `quantity`, `unit_price` (numeric 10,2), `reorder_level`, `created_at`. `stock_value` and `low_stock` are computed in the model, not stored.

## Local setup

Requirement: Docker with Docker Compose.

```bash
docker compose up --build
```

| URL | What |
|---|---|
| http://localhost:3000 | the app |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:8000/metrics | metrics |

`docker compose down` stops it; `docker compose down -v` also deletes the database volume.

The backend container runs `alembic upgrade head` and then starts Uvicorn. Nginx in the frontend container serves the static build and proxies `/api` to the backend, so the browser never needs the backend's address.

Smoke test against a running stack (10 checks, full CRUD):

```bash
./scripts/smoke-test.sh http://localhost:8000
```

## Tests

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
```

12 tests cover 8 endpoints, including the duplicate-SKU conflict, the 404 path, the low-stock filter and the stats arithmetic. `tests/conftest.py` overrides the `get_db` dependency with an in-memory SQLite database, so tests never touch PostgreSQL.

## CI/CD pipeline

`.github/workflows/ci-cd.yml` runs on every push and pull request to `main`.

| Job | Steps | Stops the pipeline when |
|---|---|---|
| **1. Test backend and build frontend** | `pytest -v`, `npm ci`, `npm run build` | a test fails or the build fails |
| **2. Build, scan and push images** | build both images, Trivy on each, push to GHCR | Trivy finds a fixable HIGH or CRITICAL CVE |
| **3. Update Helm image tag for Argo CD** | `yq` writes the SHA into `helm/stockroom/values.yaml`, commits with `[skip ci]` | — |

Images:

```text
ghcr.io/kartavya37/stockroom-backend:<full commit SHA>
ghcr.io/kartavya37/stockroom-frontend:<full commit SHA>
```

There is no `latest` tag. Every running Pod points to exactly one commit, and a rollback is a revert of one line in `values.yaml`. Pull requests run jobs 1 and 2 without pushing anything.

Job 3 uses `yq` with YAML paths rather than `sed`. A line-based replace of `tag:` would also hit the PostgreSQL image tag in the same file.

## Security scan — Trivy result

Trivy reads every layer of an image, lists the OS packages and the language libraries, and matches them against vulnerability databases. The pipeline runs it with `--severity HIGH,CRITICAL --ignore-unfixed --exit-code 1`, so only vulnerabilities that have an available fix can block a release.

**Our first scan failed both images** (Trivy 0.75.0, 16 Oct 2026):

| Image | Base | Fixable HIGH / CRITICAL | Examples |
|---|---|---|---|
| backend | `python:3.12-slim` (Debian 13.6) | 17 / 3 | **CVE-2026-13221** (CRITICAL, `perl-base` 5.40.1-6); CVE-2025-62727, CVE-2026-48818, CVE-2026-54283 (HIGH, `starlette` 0.41.3) |
| frontend | `nginx:1.27-alpine` (Alpine 3.21.3) | 41 / 2 | CVE-2026-31789 (CRITICAL, `libcrypto3`/`libssl3` 3.3.3) |

**The CVE we explain: CVE-2026-13221.** The slim Python base image ships `perl-base`, because Debian needs it to install packages. The 5.40.1-6 build mishandles very large regular expressions. StockRoom never runs Perl, so the flaw is not reachable through the API. But it is in the image, and Trivy reports what is present, not what is used. Debian had already published 5.40.1-6+deb13u1, so the fix was to run `apt-get upgrade` in the Dockerfile.

Fixes, in commit `fix(docker): …` and `fix(backend): …`:

1. `apt-get upgrade` in the backend image: clears the Debian packages, including `perl-base`.
2. FastAPI 0.115.6 → 0.143.2 and prometheus-fastapi-instrumentator 7.0.0 → 8.1.0, which moves Starlette to 1.8.0. The old instrumentator capped Starlette below 1.0.
3. Frontend base `nginx:1.27-alpine` → `nginx:1.30-alpine` plus `apk upgrade`.

**After the fixes both images scan clean: 0 fixable HIGH or CRITICAL.** A clean scan does not prove that the app is secure. It proves that no known, fixable package vulnerability ships in it. See [docs/SECURITY.md](docs/SECURITY.md) for the other security layers and the controls in this repo.

## Terraform

`terraform/` builds this in `ap-south-1`:

- a VPC `10.0.0.0/16` across two availability zones
- 2 public subnets (load balancers, NAT gateway) and 2 private subnets (worker nodes)
- an internet gateway and one NAT gateway (one, not one per AZ, to keep the cost down)
- an EKS 1.36 cluster with a managed node group of 2 × `t3.medium` (min 2, max 4)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform init
terraform plan
terraform apply                 # about 15–20 minutes
aws eks update-kubeconfig --region ap-south-1 --name stockroom-dev-eks
kubectl get nodes
terraform destroy
```

EKS 1.36 is used on purpose. Versions 1.31–1.33 are in extended support, and AWS bills the control plane at six times the standard rate for those versions. No credentials live in the repo: Terraform uses the AWS CLI profile on the machine, and `*.tfvars` and `*.tfstate` are git-ignored.

## Kubernetes and Helm

The demo cluster is Minikube with the `ingress` and `metrics-server` add-ons.

```bash
kubectl apply -f k8s/namespace.yaml
helm upgrade --install stockroom ./helm/stockroom -n stockroom -f helm/stockroom/values-dev.yaml
kubectl get pods,svc,ingress,hpa -n stockroom
helm list -n stockroom
```

What the chart creates (13 objects):

| Kind | Name | Notes |
|---|---|---|
| Deployment | `stockroom-backend` | 2 Pods at minimum (HPA), init container waits for PostgreSQL, liveness `/health`, readiness `/ready`, startup probe |
| Deployment | `stockroom-frontend` | 2 Pods, Nginx as UID 101 |
| Deployment | `stockroom-postgres` | 1 Pod with a PersistentVolumeClaim |
| Service | `stockroom-backend`, `stockroom-frontend`, `stockroom-postgres` | ClusterIP |
| Service | `backend` | ExternalName alias, so the Nginx `/api` proxy in the image works inside the cluster too |
| Ingress | `stockroom` | host `stockroom.local`: `/api` → backend, `/` → frontend |
| HorizontalPodAutoscaler | `stockroom-backend` | 2–4 Pods at 50% CPU |
| ServiceMonitor | `stockroom-backend` | Prometheus scrape config |
| ConfigMap | `stockroom-grafana-dashboard` | dashboard JSON for the Grafana sidecar |
| Secret, PVC | `stockroom-db`, `stockroom-postgres` | database URL and storage |

Both app containers run with `runAsNonRoot`, `allowPrivilegeEscalation: false` and all Linux capabilities dropped.

### GitOps with Argo CD

`gitops/argocd-application.yaml` points Argo CD at `helm/stockroom` on `main` with `values.yaml` + `values-dev.yaml`, auto sync, prune and self-heal. The flow:

```text
git push → pipeline → new images in GHCR → job 3 commits the new SHA → Argo CD syncs → new Pods
```

Nobody runs `helm upgrade` against the cluster after this point. Argo CD ignores `spec.replicas` on the backend Deployment because the HPA owns that field.

### Autoscaling

```bash
kubectl get hpa -n stockroom --watch                              # terminal 1
kubectl port-forward -n stockroom svc/stockroom-backend 8000:8000  # terminal 2
./scripts/load-test.sh http://localhost:8000 120 40                # terminal 3
```

## Observability

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  -n monitoring --create-namespace -f monitoring/prometheus-values.yaml
```

- The backend exposes `/metrics` through prometheus-fastapi-instrumentator (`http_requests_total`, `http_request_duration_seconds`, and more).
- The chart's ServiceMonitor makes Prometheus scrape every backend Pod every 15 s. It shows as `serviceMonitor/stockroom/stockroom-backend/0` on the Targets page.
- The chart's ConfigMap carries the **StockRoom API** dashboard. The Grafana sidecar loads it, so there is no manual import. Panels: requests per second by route, p95 latency, 5xx rate, backend Pods up, CPU per Pod.

## Troubleshooting lab

| Manifest | Fault | Symptom | Where the answer is |
|---|---|---|---|
| `troubleshooting/broken-image.yaml` | image tag does not exist | `ImagePullBackOff` | `kubectl describe pod` → Events |
| `troubleshooting/broken-service.yaml` | selector matches no label | Service has no endpoints | `kubectl get endpoints`, `--show-labels` |
| `troubleshooting/broken-probe.yaml` | readiness probe on a 404 path | `Running` but `0/1` ready | `kubectl describe pod` → Events |

Walkthrough: [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md).

## Problems found while building

| Problem | How we found it | Fix |
|---|---|---|
| Both images failed Trivy (20 and 43 fixable HIGH/CRITICAL CVEs) | local scan with the pipeline's flags | OS upgrades in both images, FastAPI 0.143.2, nginx 1.30 |
| Two backend Pods on an empty database crashed one of them: `UniqueViolation … pg_type_typname_nsp_index` on `alembic_version` | started two containers at once against a fresh PostgreSQL: one crashed in 5 of 5 runs | `pg_advisory_xact_lock` in `alembic/env.py`; afterwards 0 crashes in 5 runs |
| The non-root Nginx container exited: `open() "/var/run/nginx.pid" failed (13: Permission denied)` | first `docker compose up` | `/var/run` is a symlink to `/run`, so the `chown` missed it; PID file moved to `/tmp` |
| EKS 1.31 was in extended support (6× the control-plane price) | `aws eks describe-cluster-versions` | EKS 1.36 |
| The pipeline's tag edit would have reformatted the whole values file | dry run of `yq` on a copy | normalised `values.yaml` once, so each deploy commit changes exactly two lines |

## Screenshots

| Graded item | Screenshot |
|---|---|
| M1 / M4 — app at http://localhost:3000 | ![app](screenshots/01-app-compose.png) |
| M2 — `pytest -v`, all passing | ![pytest](screenshots/02-pytest.png) |
| M4 — `docker compose up --build` | ![compose](screenshots/03-compose-up.png) |
| M9 — `curl /metrics` | ![metrics](screenshots/04-metrics.png) |
| M3 — commit history | ![commits](screenshots/05-commits.png) |
| M5 — green pipeline run | ![actions](screenshots/06-actions.png) |
| M6 — Trivy output in the pipeline | ![trivy](screenshots/07-trivy.png) |
| M5 — GHCR packages with SHA tags | ![ghcr](screenshots/08-ghcr.png) |
| M8 — `helm list`, `kubectl get pods,svc,ingress` | ![k8s](screenshots/09-helm-kubectl.png) |
| M8 — app through the Ingress | ![ingress](screenshots/10-ingress.png) |
| GitOps — Argo CD synced and healthy | ![argocd](screenshots/11-argocd.png) |
| M9 — Prometheus targets `UP` | ![prometheus](screenshots/12-prometheus.png) |
| M9 — Grafana dashboard with data | ![grafana](screenshots/13-grafana.png) |
| M7 — `terraform plan` | ![plan](screenshots/14-terraform-plan.png) |
| M7 — VPC and EKS in AWS | ![aws](screenshots/15-aws.png) |
| M7 — `terraform destroy` | ![destroy](screenshots/16-terraform-destroy.png) |

A map of every rubric line to its file and screenshot is in [docs/SUBMISSION.md](docs/SUBMISSION.md).

## Known issues and limitations

- **The app runs on Minikube, not EKS.** The EKS cluster is created with Terraform to prove the AWS infrastructure, then destroyed to stop the cost. The pipeline deploys through Argo CD to the Minikube cluster.
- **`helm list` is empty once Argo CD manages the app.** Argo CD renders the chart and applies the manifests itself; it does not create a Helm release. The `helm list` screenshot is from a direct `helm upgrade --install` before Argo CD took over.
- **Plain database password.** It is a Helm value and becomes a Kubernetes Secret. A real setup would use AWS Secrets Manager with the External Secrets Operator.
- **Single PostgreSQL Pod.** The data survives Pod restarts (PVC), but there is no replica and no backup. Production would use Amazon RDS.
- **CORS allows every origin**, and the Ingress serves plain HTTP. Production would restrict origins and add TLS with cert-manager.
- **Public EKS API endpoint.** Fine for a demo; production would restrict the CIDRs or use a private endpoint.
- **The pipeline commits to `main`.** After every run there is one extra commit, so `git pull` before `git push`.
- **No login.** Anyone who can reach the app can change the stock. The Suppliers, Orders and Reports sidebar entries are placeholders.
