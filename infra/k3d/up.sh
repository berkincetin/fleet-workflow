#!/usr/bin/env bash
# Create the local k3d cluster and install the Fleet umbrella chart.
set -euo pipefail

CLUSTER=fleet
NS=fleet-dev

if ! k3d cluster list | grep -q "^${CLUSTER} "; then
  k3d cluster create --config infra/k3d/cluster.yaml
fi

# On Docker Desktop (esp. Windows/macOS) k3d writes the API server as
# host.docker.internal, which does not always resolve to the loopback the API
# port is actually published on. The port is published on localhost, so pin the
# kubeconfig server to 127.0.0.1:<mapped-port> to make kubectl reach the cluster.
API_PORT="$(docker port "k3d-${CLUSTER}-serverlb" 6443/tcp 2>/dev/null | head -1 | sed 's/.*://')"
if [ -n "${API_PORT}" ]; then
  kubectl config set-cluster "k3d-${CLUSTER}" --server="https://127.0.0.1:${API_PORT}" >/dev/null
fi

kubectl create namespace "${NS}" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install fleet infra/helm/fleet \
  -f infra/helm/fleet/values-dev.yaml \
  --namespace "${NS}"

echo "waiting for pods..."
kubectl -n "${NS}" wait --for=condition=available --timeout=300s deploy --all || true
kubectl -n "${NS}" get pods
