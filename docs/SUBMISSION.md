# The submission guide

This document maps each grading criterion to the file in this repository and
to the screenshot that you must make.

The repository is `https://github.com/kartavya37/<repository>`.

---

## M1 — Application (10 points)

| Criterion | The proof | State |
|---|---|---|
| The backend answers at `/health` | `backend/app/main.py` | Complete |
| Four or more REST endpoints | Six item endpoints | Complete |
| PostgreSQL with an Alembic migration | `backend/alembic/versions/0001_create_items.py` | Complete |
| The frontend makes API calls | `frontend/src/main.jsx` | Complete |
| A responsive and usable screen | `frontend/src/styles.css` | Complete |

**Screenshot 1:** the browser at `http://localhost:3000` with items in the table.

---

## M2 — Tests (10 points)

| Criterion | The proof | State |
|---|---|---|
| `pytest` operates | 12 tests pass | Complete |
| Five tests on three endpoints | 12 tests on 8 endpoints | Complete |
| A test database, not the production database | `backend/tests/conftest.py` | Complete |
| `pytest.ini` is present | `backend/pytest.ini` | Complete |

**Screenshot 2:** the terminal with `pytest -v` and 12 green lines.

```bash
cd backend && pytest -v
```

---

## M3 — Git and GitHub (5 points)

| Criterion | Your action |
|---|---|
| A public repository | Make the repository on GitHub. |
| Ten or more clear commit messages | The local history has 14 commits. |
| A correct `.gitignore` | Complete. See `.gitignore`. |

**Screenshot 3:** the commit list on GitHub.

---

## M4 — Docker (10 points)

| Criterion | The proof | State |
|---|---|---|
| The backend image builds | `backend/Dockerfile` | Complete |
| A multi-stage frontend build | `frontend/Dockerfile` | Complete |
| Non-root users | UID 10001 and UID 101 | Complete |
| Compose starts three services | `docker-compose.yml` | Complete |

**Screenshot 4:** the terminal with `docker compose up --build`.
**Screenshot 5:** the output of these two commands:

```bash
docker compose exec backend id
docker compose exec frontend id
```

---

## M5 — The pipeline (15 points)

| Criterion | The proof | State |
|---|---|---|
| A workflow file | `.github/workflows/ci-cd.yml` | Complete |
| A trigger on `main` | The `on.push.branches` key | Complete |
| pytest stops the build | The `test` job | Complete |
| The frontend build | The `test` job | Complete |
| Two Docker images | The `build` job | Complete |
| A push to GHCR | The `build` job | Complete |
| The commit SHA as the tag | `${{ github.sha }}` | Complete |

**Screenshot 6:** the green pipeline run on GitHub.
**Screenshot 7:** the GHCR package page with the SHA tag.

---

## M6 — Trivy (5 points)

| Criterion | The proof | State |
|---|---|---|
| A scan of both images | Two Trivy steps | Complete |
| The build stops at HIGH or CRITICAL | `exit-code: "1"` | Complete |
| An explanation of the result | `docs/SECURITY.md` section 2 | Complete |

**Screenshot 8:** the Trivy step output in the pipeline log.

---

## M7 — Terraform (15 points)

| Criterion | The proof | State |
|---|---|---|
| Valid HCL files | `terraform/*.tf` | Complete. `terraform validate` passes. |
| `terraform init` | — | Complete on this machine |
| A plan with no error | — | **Your action.** This needs AWS credentials. |
| A VPC with two public subnets | `terraform/main.tf` | Complete |
| An EKS cluster with a node group | `terraform/main.tf` | Complete |
| A clean `terraform destroy` | — | **Your action** |
| A `terraform.tfvars.example` file | `terraform/terraform.tfvars.example` | Complete |

**Screenshot 9:** the `terraform plan` output.
**Screenshot 10:** the AWS console with the VPC and the EKS cluster.
**Screenshot 11:** the `terraform destroy` completion.

---

## M8 — Kubernetes and Helm (15 points)

| Criterion | The proof | State |
|---|---|---|
| `k8s/namespace.yaml` | Complete | Complete |
| A chart with templates | `helm/stockroom/` | Complete. `helm lint` passes. |
| `helm upgrade --install` with no error | — | **Your action** |
| Two replicas for each deployment | `values.yaml` | Complete |
| ClusterIP Services | Four Services | Complete |
| An Ingress for `/` and `/api` | `templates/ingress.yaml` | Complete |
| Each Pod is `Running` | — | **Your action** |

**Screenshot 12:** `kubectl get pods -n stockroom`.
**Screenshot 13:** `kubectl get svc -n stockroom`.
**Screenshot 14:** `helm list -n stockroom`.
**Screenshot 15:** the browser with the Ingress address.

---

## M9 — The monitoring (10 points)

| Criterion | The proof | State |
|---|---|---|
| The `/metrics` endpoint | `app/main.py`, 118 metric lines | Complete |
| Prometheus reads the application | `templates/servicemonitor.yaml` | Complete |
| Grafana operates | `monitoring/prometheus-values.yaml` | Complete |
| One panel with live data | `monitoring/grafana-dashboard.json` | Complete |

**Screenshot 16:** the `curl .../metrics` output.
**Screenshot 17:** the Prometheus Targets page with the state `UP`.
**Screenshot 18:** the Grafana panel with data.

---

## M10 — The presentation (5 points)

| Criterion | The proof | State |
|---|---|---|
| A `README.md` file | `README.md`, 308 lines | Complete |
| A live demonstration | — | **Your action** |

The order of the demonstration is in section "The demonstration" below.

---

## The demonstration order

Make a small change. Then show the full chain.

1. Open the application. Add an item.
2. Open `/docs`. Make a `GET`, a `POST` and a `DELETE` request.
3. Show the `items` table in PostgreSQL.
4. Change one line in the frontend. Commit the change.
5. Push the commit. Show the pipeline in GitHub Actions.
6. Show the two images in GHCR with the new SHA tag.
7. Show the Trivy step in the log.
8. Show the Terraform code and the AWS console.
9. Show `kubectl get pods` and `helm list`.
10. Open the application through the Ingress address.
11. Start the load script. Show `kubectl get hpa --watch`.
12. Show the Grafana panel. The request rate increases.
13. Apply a broken manifest. Find the error with `kubectl describe`.

## The database command for step 3

```bash
# Local
docker compose exec postgres psql -U stockroom -d stockroom -c 'SELECT * FROM items;'

# In the cluster
kubectl exec -n stockroom deploy/stockroom-postgres -- \
  psql -U stockroom -d stockroom -c 'SELECT * FROM items;'
```
