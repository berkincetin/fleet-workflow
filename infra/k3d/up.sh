#!/usr/bin/env bash
# Create the local k3d cluster and install the Fleet umbrella chart.
set -euo pipefail

CLUSTER=fleet
NS=fleet-dev

if ! k3d cluster list | grep -q "^${CLUSTER} "; then
  k3d cluster create --config infra/k3d/cluster.yaml
fi

kubectl create namespace "${NS}" --dry-run=client -o yaml | kubectl apply -f -
helm upgrade --install fleet infra/helm/fleet \
  -f infra/helm/fleet/values-dev.yaml \
  --namespace "${NS}"

echo "waiting for pods..."
kubectl -n "${NS}" wait --for=condition=available --timeout=300s deploy --all || true
kubectl -n "${NS}" get pods
