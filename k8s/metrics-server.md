# The Metrics Server

The HPA reads the CPU use from the Metrics Server. Amazon EKS does not
install the Metrics Server automatically.

Install it with this command:

```bash
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
```

Make a test:

```bash
kubectl top nodes
kubectl top pods -n stockroom
```

On Minikube, use the add-on instead:

```bash
minikube addons enable metrics-server
```
