"""Right-to-erasure subject hashing (task 8.3, TRD §8).

A pure, deterministic hash of a stable subject identifier (a Keycloak
`kc_sub`, a candidate's email, ...) — never the identifier itself — so
`documents.subject_hash`/`conversations.subject_hash` and the
`DELETE /v1/subjects/{hash}` URL path never carry raw PII. Callers normalize
their own identifier (e.g. lowercase + strip an email) before hashing;
this function only hashes, it does not know what kind of identifier it was
given.
"""

from __future__ import annotations

import hashlib


def subject_hash(identifier: str) -> str:
    return hashlib.sha256(identifier.strip().lower().encode("utf-8")).hexdigest()
