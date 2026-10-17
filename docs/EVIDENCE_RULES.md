# Evidence Rules

Runs are append-only once sealed. Preserve first failures/retries under separate IDs. Record command/version/exit, timestamps, artifact/build identity, verifier, and bundle hash. Model output cannot verify itself.

Raw output may contain secrets/private data. Review before submission. Never upload credentials, keys, owner-private tasks, or unredacted secrets. Evidence is input to canonical review, not automatic qualification/promotion.

Q0 bundle includes machine manifest, software inventory, cache inventory, evidence.json, SHA256SUMS, deterministic tar, and tar SHA-256.