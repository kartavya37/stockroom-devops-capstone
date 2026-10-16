# The troubleshooting lab

Each exercise has one error. Find the error with the Kubernetes commands.
Do not read the correction first.

---

## Exercise 1 — the broken image

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n stockroom
```

The Pod state is `ImagePullBackOff` or `ErrImagePull`.

### The investigation

```bash
kubectl describe pod -n stockroom -l app=broken-image
kubectl get events -n stockroom --sort-by=.lastTimestamp | tail -20
```

The `Events` section at the end of the describe output gives the cause:

```text
Failed to pull image "...:v9.9.9-does-not-exist": not found
```

### The method

```text
ImagePullBackOff
      ↓
kubectl describe pod
      ↓
read the Events section
      ↓
the tag or the registry permission is wrong
      ↓
correct the image reference
```

### The three usual causes

1. The tag does not exist. This is the cause in this exercise.
2. The name of the registry or of the repository has an error.
3. The package is private and the Pod has no `imagePullSecret`.

### The correction

```bash
kubectl delete -f troubleshooting/broken-image.yaml
```

---

## Exercise 2 — the broken Service

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get pods -n stockroom -l app=working-api
```

The Pod is `Running`, but the Service sends no traffic.

### The investigation

```bash
kubectl get svc -n stockroom broken-service
kubectl get endpoints -n stockroom broken-service
kubectl get pods -n stockroom --show-labels
```

The endpoint list is empty:

```text
NAME             ENDPOINTS   AGE
broken-service   <none>      30s
```

### The cause

A Service finds its Pods with labels. The Pods have the label
`app=working-api`. The Service looks for `app=wrong-label`. No Pod matches.

```text
no label match
      ↓
no endpoint
      ↓
no traffic
```

### The correction

Change the `selector` in the Service to `app: working-api`. Then apply the
file again and look at the endpoints.

```bash
kubectl delete -f troubleshooting/broken-service.yaml
```

---

## Exercise 3 — the broken probe

```bash
kubectl apply -f troubleshooting/broken-probe.yaml
kubectl get pods -n stockroom -l app=broken-probe
```

The `STATUS` column shows `Running`. The `READY` column shows `0/1`.

### The investigation

```bash
kubectl describe pod -n stockroom -l app=broken-probe
```

The Events section shows:

```text
Readiness probe failed: HTTP probe failed with statuscode: 404
```

### The cause

The container operates correctly. The probe asks the wrong path. A Pod
with a failed readiness probe gets no traffic from the Service.

This state is different from a crash:

| State | The container | The traffic |
|---|---|---|
| `CrashLoopBackOff` | Stopped | None |
| `Running` and `0/1` | Operates | None |
| `Running` and `1/1` | Operates | Yes |

### The correction

Change the probe path to a path that gives the code 200.

```bash
kubectl delete -f troubleshooting/broken-probe.yaml
```

---

## The general command list

```bash
# The state
kubectl get pods -n stockroom -o wide
kubectl get all -n stockroom

# The details
kubectl describe pod -n stockroom <pod>
kubectl get events -n stockroom --sort-by=.lastTimestamp

# The logs
kubectl logs -n stockroom <pod>
kubectl logs -n stockroom <pod> --previous     # the log of the stopped container

# Inside the Pod
kubectl exec -it -n stockroom <pod> -- sh

# The network
kubectl get endpoints -n stockroom
kubectl get pods -n stockroom --show-labels

# The resources
kubectl top pods -n stockroom
kubectl get hpa -n stockroom
```
