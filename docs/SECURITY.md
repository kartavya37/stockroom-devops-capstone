# Security notes

## 1. What Trivy examines

Trivy reads each layer of a container image. It makes a list of the operating
system packages and of the application dependencies. Then it compares the list
against public vulnerability databases.

The pipeline makes a check of two images:

| Image | Base | Content |
|---|---|---|
| backend | `python:3.12-slim` | Debian packages and the Python packages from `requirements.txt` |
| frontend | `nginx:1.27-alpine` | Alpine packages and the static files |

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

## 2. The explanation for the grading (module M6)

> Trivy examined both container images. It compared each operating system
> package and each Python dependency against the vulnerability databases. The
> scan found no HIGH or CRITICAL vulnerability with an available correction,
> therefore the pipeline continued and pushed the images. A clean result does
> not prove that the application is secure. It proves only that the known
> package vulnerabilities are absent.

If the scan reports a CVE, replace the text above with this structure:

1. The identifier of the CVE, for example `CVE-2024-12345`.
2. The package and the version, for example `libxml2 2.9.14`.
3. The class, for example HIGH.
4. The correction, for example "the new base image contains version 2.9.15".

Find the details:

```bash
trivy image --severity HIGH,CRITICAL ghcr.io/kartavya37/<repo>-backend:<sha>
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

## 5. The known weak points of this project

The grading team gives points for an honest analysis. These points are open:

1. The database password is in the Helm values file. A real project uses AWS
   Secrets Manager or the External Secrets Operator.
2. PostgreSQL operates in the cluster. A real project uses Amazon RDS with
   automatic backups.
3. The CORS policy permits each origin. A real project gives a list.
4. The EKS API endpoint is public. A real project limits the addresses.
5. The Ingress uses HTTP. A real project uses TLS with cert-manager.
