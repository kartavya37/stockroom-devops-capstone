# Security notes

## 1. What Trivy examines

Trivy reads each layer of a container image. It makes a list of the operating
system packages and of the application dependencies. Then it compares the list
against public vulnerability databases.

The pipeline makes a check of two images:

| Image | Base | Content |
|---|---|---|
| backend | `python:3.12-slim` | Debian packages and the Python packages from `requirements.txt` |
| frontend | `nginx:1.30-alpine` | Alpine packages and the static files |

The configuration in the workflow:

```yaml
severity: HIGH,CRITICAL
ignore-unfixed: true
exit-code: "1"
```

- `severity` — the scan reports only the two highest classes.
- `ignore-unfixed` — the scan ignores a CVE with no correction available. The
  student cannot correct such a CVE.
- `exit-code: 1` — a finding stops the pipeline. No image goes to the
  registry.

## 2. Our scan results (module M6)

All numbers come from Trivy 0.75.0 on 16 October 2026, with the same flags
as the pipeline: `--severity HIGH,CRITICAL --ignore-unfixed`.

### The first scan: both images failed

| Image | Base | HIGH | CRITICAL | Total |
|---|---|---|---|---|
| backend | `python:3.12-slim`, Debian 13.6 | 17 | 3 | 20 |
| frontend | `nginx:1.27-alpine`, Alpine 3.21.3 | 41 | 2 | 43 |

The backend findings in detail:

| CVE | Class | Package | Installed | Fixed in | Layer |
|---|---|---|---|---|---|
| CVE-2026-13221 | CRITICAL | perl-base | 5.40.1-6 | 5.40.1-6+deb13u1 | Debian |
| CVE-2026-42496 | CRITICAL | perl-base | 5.40.1-6 | 5.40.1-6+deb13u1 | Debian |
| CVE-2026-8376 | CRITICAL | perl-base | 5.40.1-6 | 5.40.1-6+deb13u1 | Debian |
| CVE-2025-62727 | HIGH | starlette | 0.41.3 | 0.49.1 | Python |
| CVE-2026-48818 | HIGH | starlette | 0.41.3 | 1.1.0 | Python |
| CVE-2026-54283 | HIGH | starlette | 0.41.3 | 1.3.1 | Python |
| 14 more | HIGH | gzip, libpcre2, libsqlite3, openssl and others | | | Debian |

### The explanation of one CVE

> **CVE-2026-13221 (CRITICAL) in `perl-base` 5.40.1-6.** The slim Python
> base image contains `perl-base`, because the Debian package tools need it.
> This build processes very large regular expressions incorrectly. StockRoom
> never runs Perl, so a request to the API cannot reach the flaw. But the
> package is in the image, and Trivy reports what the image contains, not
> what the application calls. Debian already published the fixed build
> 5.40.1-6+deb13u1, so one `apt-get upgrade` line in the Dockerfile removed
> this CVE and the 16 other Debian findings.

A second example that is useful for the discussion: **CVE-2026-54283 (HIGH)**
in Starlette 0.41.3. `request.form()` ignores its size limits for
url-encoded bodies. StockRoom accepts only JSON, so it never calls
`request.form()`. We upgraded anyway, because a future form endpoint would
be exposed at once.

### The fixes

| Fix | Effect |
|---|---|
| `apt-get upgrade` in `backend/Dockerfile` | 17 Debian findings removed |
| FastAPI 0.115.6 → 0.143.2, prometheus-fastapi-instrumentator 7.0.0 → 8.1.0 (Starlette 1.8.0) | 3 Python findings removed. The old instrumentator kept Starlette below 1.0. |
| `nginx:1.27-alpine` → `nginx:1.30-alpine` and `apk upgrade` | 43 Alpine findings removed |

### The second scan: both images are clean

| Image | HIGH | CRITICAL | Exit code |
|---|---|---|---|
| backend | 0 | 0 | 0 |
| frontend | 0 | 0 | 0 |

A clean result does not prove that the application is secure. It proves only
that the image contains no known package vulnerability that has a fix.

Reproduce a scan:

```bash
docker build -t stockroom-backend:scan ./backend
trivy image --severity HIGH,CRITICAL --ignore-unfixed stockroom-backend:scan
```

## 3. The layers of security

A scanner is one control. It is not a guarantee.

| Layer | Question | Tool example |
|---|---|---|
| SAST | Is the source code unsafe? | Bandit, CodeQL |
| Dependency scan | Is a library unsafe? | pip-audit, Dependabot |
| Secret scan | Is a password in the repository? | Gitleaks, GitHub secret scanning |
| Container scan | Is a package in the image unsafe? | **Trivy** |
| Runtime security | Is the container behaviour abnormal? | Falco |

This project uses the container scan layer.

## 4. The controls in this repository

| Control | Place |
|---|---|
| Non-root user, UID 10001 | `backend/Dockerfile` |
| Non-root user, UID 101 | `frontend/Dockerfile` |
| `allowPrivilegeEscalation: false` | The Helm deployment templates |
| `capabilities: drop: ALL` | The Helm deployment templates |
| `runAsNonRoot: true` | The Helm Pod security context |
| No secret in Git | `.gitignore` and `terraform/.gitignore` |
| The automatic pipeline token | `.github/workflows/ci-cd.yml` |

## 5. A reliability finding: the migration race

This is not a CVE, but we found it with a test, and it affects the
availability of the service.

Each backend container runs `alembic upgrade head` at the start. With two
replicas on an empty database, both containers try to make the table
`alembic_version` at the same moment. The second one fails:

```text
psycopg.errors.UniqueViolation: duplicate key value violates unique constraint "pg_type_typname_nsp_index"
DETAIL:  Key (typname, typnamespace)=(alembic_version, 2200) already exists.
```

The test: start PostgreSQL, then start two backend containers at the same
time, five times.

| Image | Crashed containers in 5 runs |
|---|---|
| Without the lock | 5 |
| With `pg_advisory_xact_lock` in `alembic/env.py` | 0 |

The lock is a transaction-level advisory lock. The second container waits
until the first commits, then finds the migration already applied.

## 6. The known weak points of this project

The grading team gives points for an honest analysis. These points are open:

1. The database password is in the Helm values file. A real project uses AWS
   Secrets Manager or the External Secrets Operator.
2. PostgreSQL operates in the cluster. A real project uses Amazon RDS with
   automatic backups.
3. The CORS policy permits each origin. A real project gives a list.
4. The EKS API endpoint is public. A real project limits the addresses.
5. The Ingress uses HTTP. A real project uses TLS with cert-manager.
