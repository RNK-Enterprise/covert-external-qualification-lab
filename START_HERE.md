# START HERE

Tell your local coding agent: “Read START_HERE.md and execute the currently assigned qualification mission exactly.” The active assignment is Q0 on Phoenix and Atlas only.

1. Read AGENTS.md, DEVELOPER_WAY.md, SECURITY_AND_SCOPE.md, docs/OPERATOR_SOP.md, docs/EVIDENCE_RULES.md, and missions/q0/README.md.
2. Review OWNER_CONFIRMATIONS.md. Static Q0 inventory can proceed. Do not run long artifact hashing or time-series telemetry until applicable consent is recorded.
3. Create branch lab/barry/q0/<run-id>. Never commit to main.
4. On Phoenix, run ./scripts/qualify-machine --node phoenix; note RUN_DIR. Then ./scripts/inventory-models --node phoenix --run-dir <RUN_DIR>. Repeat on Atlas with --node atlas.
5. Only known cache roots and exact extra --root paths are scanned. No whole-disk scan, download, install, model load, or inference.
6. If consent for hashing is confirmed before the inventory, add --hash to inventory-models. It reads each artifact fully and may take a long time. If you already made a metadata-only run, do not rerun into that run directory: create a new Q0 run with qualify-machine, then inventory-models --hash. Keep both runs.
7. Compare observed values with device profiles; preserve differences. No models is a valid observation; do not download duplicates.
8. Run ./scripts/verify-run <RUN_DIR>; run ./scripts/bundle-run <RUN_DIR>; then run verify-run again to check sealed hashes.
9. Review every bundle file for secrets/private data. Commit only Q0 evidence on the lab branch and open a PR. Preserve failed runs; corrections use a new run ID.
10. Stop after Q0. Success does not activate Q1.

PR record: node/run IDs, OS/CPU/RAM/GPU/storage, cache roots, model count, hashes computed/pending, discrepancies, failures/retries, consent, verifier result, bundle path/hash.

Stop on identity mismatch, unsupported environment, privilege need, secret exposure, resource pressure, ambiguous cache root, or scope expansion. Never work around a stop.