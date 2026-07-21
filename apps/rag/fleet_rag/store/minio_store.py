"""MinIO object store for uploaded documents (TRD §3 tech stack, task 3.1).

Object keys are namespaced by collection and content hash
(`{collection_id}/{sha256}{ext}`) so uploading the same file into the same
collection twice always resolves to the same object — the ingestion pipeline
uses this alongside the `documents` unique (collection_id, sha256) index to
make re-upload a no-op (AC: costs 0 new embeddings).
"""

from __future__ import annotations

import hashlib
import os

from minio import Minio

DEFAULT_BUCKET = "fleet-documents"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def object_key(*, collection_id: int, sha256: str, filename: str) -> str:
    dot = filename.rfind(".")
    ext = filename[dot:].lower() if dot != -1 else ""
    return f"{collection_id}/{sha256}{ext}"


def minio_client_from_env() -> Minio:
    endpoint = os.environ.get("FLEET_MINIO_ENDPOINT", "localhost:9000")
    access_key = os.environ.get("MINIO_ROOT_USER", "fleet")
    secret_key = os.environ.get("MINIO_ROOT_PASSWORD", "fleet_dev_pw")
    secure = os.environ.get("FLEET_MINIO_SECURE", "false").lower() == "true"
    return Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)


def ensure_bucket(client: Minio, bucket: str = DEFAULT_BUCKET) -> None:
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
