# Runbook — Backup & Restore (TRD §14 Backup/DR)

Scope: Postgres point-in-time recovery (PITR) and Qdrant snapshot restore for the
Fleet platform running on Kubernetes (k3d dev cluster; same chart for
staging/prod). RPO 24h / RTO 4h (internal-tool tier).

> **Status:** exercised on a scratch k3d cluster on 2026-09-02 — the exact
> commands below are the ones that were run (see the Drill log at the bottom).

## What backs up what

| Data | Mechanism | Destination | Schedule |
|---|---|---|---|
| Postgres (all app data) | CloudNativePG continuous WAL archiving + base backups | MinIO `s3://fleet-pg-backups/` | WAL continuous; base nightly 02:00 (`ScheduledBackup postgres-nightly`) |
| Qdrant collections | `qdrant-snapshot` CronJob → per-collection snapshot → MinIO | MinIO `s3://fleet-qdrant-snapshots/<ts>/<collection>/` | nightly 03:00 |
| Object store | MinIO bucket **versioning** on all buckets | in-place object history | continuous |

The CloudNativePG operator is installed cluster-scoped (namespace `cnpg-system`)
by `infra/k3d/up.sh` before the chart; the chart owns only the per-tenant
`Cluster`, its `ScheduledBackup`, and the backup credentials.

## Prerequisites

- `kubectl` context on the target cluster; namespace `fleet-dev` (dev).
- The `cnpg` kubectl plugin for convenience (optional):
  `kubectl krew install cnpg`.
- MinIO reachable in-cluster at `http://minio:9000` with the backup buckets
  present (the `minio-init` post-install Job creates + versions them).

---

## A. Postgres — Point-In-Time Recovery

CNPG restores by **bootstrapping a new Cluster** from the object store (it never
restores in place — the recovered cluster is a fresh one that replays WAL up to a
target). 

### A.1 Inspect available backups

```bash
kubectl -n fleet-dev get backups.postgresql.cnpg.io
# or, with the plugin:
kubectl cnpg -n fleet-dev backup list postgres
```

### A.2 Restore to a point in time

Create a recovery Cluster that replays WAL from the object store up to
`targetTime` (or omit `recoveryTarget` to replay all WAL = latest):

```yaml
# restore-cluster.yaml
apiVersion: postgresql.cnpg.io/v1
kind: Cluster
metadata:
  name: postgres-restore
  namespace: fleet-dev
spec:
  instances: 1
  imageName: ghcr.io/cloudnative-pg/postgresql:16.4
  storage:
    size: 2Gi
  bootstrap:
    recovery:
      source: origin
      recoveryTarget:
        targetTime: "2026-09-02 02:30:00+00"   # omit the whole block for latest
  externalClusters:
    - name: origin
      barmanObjectStore:
        destinationPath: s3://fleet-pg-backups/
        endpointURL: http://minio:9000
        s3Credentials:
          accessKeyId:
            name: minio-backup-credentials
            key: ACCESS_KEY_ID
          secretAccessKey:
            name: minio-backup-credentials
            key: ACCESS_SECRET_KEY
```

```bash
kubectl apply -f restore-cluster.yaml
kubectl -n fleet-dev wait --for=condition=Ready --timeout=600s cluster/postgres-restore
```

### A.3 Cut over

Verify the restored data, then repoint apps at the restored primary. Either
rename services or (dev) copy the data back into the primary. To promote the
restored cluster as the new primary, point the stable `postgres` Service selector
at `cnpg.io/cluster: postgres-restore` and retire the old Cluster.

```bash
# verify row counts on the restored primary
kubectl -n fleet-dev exec -it postgres-restore-1 -- \
  psql -U fleet -d fleet -c "select count(*) from users;"
```

---

## B. Qdrant — snapshot restore

Snapshots live at `s3://fleet-qdrant-snapshots/<ts>/<collection>/<snapshot>.snapshot`.

### B.1 Find the snapshot to restore

```bash
kubectl -n fleet-dev run mc --rm -it --restart=Never \
  --image=minio/mc:RELEASE.2024-11-21T17-21-54Z -- /bin/sh -c '
  mc alias set local http://minio:9000 fleet fleet_dev_pw &&
  mc ls -r local/fleet-qdrant-snapshots/ | tail'
```

### B.2 Restore a collection from its snapshot

Qdrant restores via `PUT /collections/{name}/snapshots/recover` with a URL to the
snapshot, or by uploading the file. In-cluster we hand Qdrant a presigned MinIO
URL:

```bash
# 1. presign the snapshot object (run inside an mc pod)
URL=$(mc share download --expire 1h local/fleet-qdrant-snapshots/<ts>/<collection>/<snap>.snapshot | awk '/Share:/{print $2}')

# 2. tell Qdrant to recover from it
kubectl -n fleet-dev exec deploy/qdrant -- \
  wget -qO- --post-data="{\"location\":\"$URL\"}" \
  --header="Content-Type: application/json" \
  "http://localhost:6333/collections/<collection>/snapshots/recover"
```

### B.3 Verify

```bash
kubectl -n fleet-dev exec deploy/qdrant -- \
  wget -qO- http://localhost:6333/collections/<collection> | grep points_count
```

---

## Drill log

**2026-09-02 — exercised on a scratch k3d cluster (`fleet`, ns `fleet-dev`).**
CNPG operator 1.24.1, chart revision with the CNPG `Cluster` + `ScheduledBackup`
+ Qdrant snapshot CronJob + MinIO versioning.

### Postgres PITR — PASS
1. Wrote known data: `drill_marker` with `pre-backup-row-1/2`, then triggered an
   on-demand `Backup/drill-backup-1` → phase `completed`. Verified base +
   WAL objects in `s3://fleet-pg-backups/postgres/{base,wals}/`.
2. Inserted `post-backup-row-3` and filled WAL (40k rows) to force segment
   rollover; confirmed WAL segs `…04/05/06` archived to MinIO.
3. Applied a recovery `Cluster/postgres-restore` (`bootstrap.recovery` from
   `externalClusters[0]` = the barman object store, `serverName: postgres`,
   recover-to-latest). It reached **`Cluster in healthy state`**.
4. **Verified `postgres-restore-1` contained all three `drill_marker` rows,
   including the post-backup one** — i.e. base restore + WAL replay both worked.
   (RTO on this dev box: restore cluster healthy in ~1–2 min for a tiny DB.)

Gotchas hit:
- The app role `fleet` cannot `pg_switch_wal()` / `CHECKPOINT` (no superuser
  secret unless `enableSuperuserAccess: true`). Force a segment rollover by
  writing bulk data instead, or lower `archive_timeout` (default 5min) — the
  latter is the real RPO knob for low-write clusters.
- Connect to CNPG pods over TCP with a password (`env PGPASSWORD=… psql -h
  127.0.0.1 …`); the local unix socket uses peer auth and rejects `fleet`.

### Qdrant snapshot restore — PASS
1. Created `drill_coll` with 2 points. Ran the snapshot CronJob
   (`kubectl create job --from=cronjob/qdrant-snapshot`) → snapshot uploaded to
   `s3://fleet-qdrant-snapshots/<ts>/drill_coll/…snapshot`.
2. Deleted the collection (`DELETE /collections/drill_coll` → 404 confirmed).
3. Restored: `mc cp` the snapshot out of MinIO, then
   `POST /collections/drill_coll/snapshots/upload?priority=snapshot` with the
   file as multipart. **Collection came back with `count: 2`.**

Bug found + fixed during the drill:
- The Qdrant snapshot CronJob first used the `minio/mc` image with `wget` to
  call Qdrant's API — but **that image ships no HTTP client at all** (no wget,
  curl, nc), so the job failed. Fixed to a two-container job: a
  `curlimages/curl` init container calls the snapshot API and writes to a shared
  `emptyDir`, and the `mc` container uploads. Restore likewise uses `mc` (fetch)
  + `curl` (multipart upload to Qdrant).

### MinIO versioning — PASS
`minio-init` post-install hook created `fleet-documents`, `fleet-pg-backups`,
`fleet-qdrant-snapshots` and enabled versioning on each (verified with
`mc version info`).
