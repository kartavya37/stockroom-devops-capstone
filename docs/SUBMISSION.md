# Grading map

Every line of `GRADING.md`, the file that proves it, and the screenshot in
`screenshots/`.

Student: Kartavya Panchal (24bcs10343) · Repository: `kartavya37/stockroom-devops-capstone`

## M1 — Application (10)

| Criterion | Evidence |
|---|---|
| Backend responds to `/health` | `backend/app/main.py`, `test_health_returns_healthy` |
| ≥ 4 REST endpoints (GET, POST, PUT, DELETE) | 6 item endpoints in `backend/app/main.py` |
| PostgreSQL table managed by Alembic | `backend/alembic/versions/0001_create_items.py` |
| Frontend renders and calls the API | `frontend/src/main.jsx` → `/api/items`, `/api/items/stats` |
| Responsive, usable UI | `frontend/src/styles.css` (breakpoints at 1000 px and 720 px) |
| Screenshot | `01-app-compose.png` |

## M2 — Testing (10)

| Criterion | Evidence |
|---|---|
| `pytest` runs without errors | 12 passed |
| ≥ 5 tests over ≥ 3 endpoints | 12 tests over 8 endpoints, `backend/tests/test_api.py` |
| Test DB, not production | in-memory SQLite, `backend/tests/conftest.py` |
| `pytest.ini` / `conftest.py` | both present |
| Screenshot | `02-pytest.png` |

## M3 — Git and GitHub (5)

| Criterion | Evidence |
|---|---|
| Public repository | repository URL in the form |
| Meaningful commit messages | conventional commits, 30+ |
| `.gitignore` covers `.env`, `__pycache__`, `node_modules`, `.venv` | `.gitignore` |
| Screenshot | `05-commits.png` |

## M4 — Docker (10)

| Criterion | Evidence |
|---|---|
| `backend/Dockerfile` builds | `backend/Dockerfile` |
| Multi-stage frontend (Node → Nginx) | `frontend/Dockerfile` |
| Non-root users | backend UID 10001, frontend UID 101 |
| `docker compose up --build` starts 3 services | `docker-compose.yml` |
| Screenshots | `03-compose-up.png`, `01-app-compose.png` |

## M5 — CI/CD (15)

| Criterion | Evidence |
|---|---|
| Workflow file | `.github/workflows/ci-cd.yml` |
| Triggers on push to `main` | `on.push.branches: [main]` |
| pytest fails the build | job 1, step "Run pytest" |
| Frontend built | job 1, step "Build frontend" |
| Both images built | job 2 |
| Pushed to GHCR | job 2, step "Push images" |
| SHA tags, not `latest` | `$GITHUB_SHA`; no `latest` tag is pushed |
| Screenshots | `06-actions.png`, `08-ghcr.png` |

## M6 — Trivy (5)

| Criterion | Evidence |
|---|---|
| Scan of both images in CI | job 2, two Trivy steps |
| Fails on HIGH / CRITICAL | `--exit-code 1 --severity HIGH,CRITICAL` |
| Explanation of a CVE | README "Trivy result", `docs/SECURITY.md` §2 |
| Screenshot | `07-trivy.png` |

## M7 — Terraform (15)

| Criterion | Evidence |
|---|---|
| Valid HCL in `terraform/` | `terraform validate` passes |
| `terraform init` | screenshot in the video |
| `terraform plan` with no errors | `14-terraform-plan.png` |
| VPC with ≥ 2 public subnets | `module.vpc` in `terraform/main.tf` |
| EKS with ≥ 1 node group | `module.eks`, node group `workers` |
| `terraform destroy` clean | `16-terraform-destroy.png` |
| `terraform.tfvars.example`, no credentials | `terraform/terraform.tfvars.example` |
| AWS proof | `15-aws.png` |

## M8 — Kubernetes + Helm (15)

| Criterion | Evidence |
|---|---|
| `k8s/namespace.yaml` | present |
| Chart with `Chart.yaml`, `values.yaml`, templates | `helm/stockroom/` (`helm lint` passes) |
| `helm upgrade --install` without errors | `09-helm-kubectl.png` |
| Backend and frontend ≥ 2 replicas | frontend `replicaCount: 2`, backend HPA `minReplicas: 2` |
| ClusterIP services | `stockroom-backend`, `stockroom-frontend`, `stockroom-postgres` |
| Ingress `/` → frontend, `/api` → backend | `templates/ingress.yaml` |
| All Pods `Running` | `09-helm-kubectl.png` |
| App through the Ingress | `10-ingress.png` |

## M9 — Observability (10)

| Criterion | Evidence |
|---|---|
| `/metrics` in Prometheus format | `04-metrics.png`, `test_metrics_endpoint_is_prometheus_format` |
| Prometheus scrapes the app | `templates/servicemonitor.yaml`, `12-prometheus.png` |
| Grafana accessible | `monitoring/prometheus-values.yaml` |
| Panel with live app metrics | `templates/grafana-dashboard.yaml`, `13-grafana.png` |

## M10 — Presentation + documentation (5)

| Criterion | Evidence |
|---|---|
| `README.md` with full technical docs | `README.md` |
| Video covering the walkthrough | `demo/video.mp4` |
| Slide deck (≥ 8 slides) | `demo/slides.pptx`, `demo/slides.pdf` |
