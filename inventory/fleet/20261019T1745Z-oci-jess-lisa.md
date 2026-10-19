# Fleet inventory (Barry Q0 adjacent) — 2026-10-19 America/New_York

Captured read-only from Phoenix via SSH. No env secrets.

## OCI (7) — hardware reference typhoon

| node | OS | kernel | arch | CPU | vCPU | RAM | free~ | swap | disk |
|---|---|---|---|---|---|---|---|---|---|
| typhoon | Ubuntu 24.04.5 LTS | 7.0.0-1012-oracle | aarch64 | Neoverse-N1 | 1 | 5.8Gi | ~5.1Gi avail | none | 45G ext4 BlockVolume (~25G free) |
| valkyrie | Ubuntu 24.04.5 LTS | 7.0.0-1012-oracle | aarch64 | Neoverse-N1 | 1 | 5.8Gi | ~5.1Gi avail | none | 45G (~32G free) |
| orion | Ubuntu 26.04.1 LTS | 7.0.0-1013-oracle | aarch64 | Neoverse-N1 | 1 | 5.8Gi | ~4.9Gi avail | none | 45G (~33G free) |
| domyngo | Ubuntu 26.04.1 LTS | 7.0.0-1009-oracle | aarch64 | Neoverse-N1 | 1 | 5.8Gi | ~5.1Gi avail | none | 45G (~35G free) |
| vidalyia | Ubuntu 26.04.1 LTS | 7.0.0-1009-oracle | aarch64 | Neoverse-N1 | 1 | 5.8Gi | ~5.1Gi avail | none | 45G (~35G free) |
| onyx | Ubuntu 26.04.1 LTS | 7.0.0-1013-oracle | aarch64 | Neoverse-N1 | 1 | 5.8Gi | ~5.0Gi avail | none | 45G (~25G free) |
| nebula | Ubuntu 26.04.1 LTS | 7.0.0-1013-oracle | aarch64 | Neoverse-N1 | 1 | 5.8Gi | ~4.9Gi avail | none | 45G (~28G free) |

## Contabo

| node | public | OS | kernel | arch | CPU | vCPU | RAM | swap | disk |
|---|---|---|---|---|---|---|---|---|---|
| jess | 207.180.212.64 | Ubuntu 24.04.5 LTS | 6.8.0-147-generic | x86_64 | Broadwell vCPU | 4 | 7.8Gi | none | 96G (~70G free) SSD |
| lisa | 207.180.198.75 | Ubuntu 24.04.5 LTS | 6.8.0-147-generic | x86_64 | Broadwell vCPU | 4 | 7.8Gi | none | 96G (~84G free) SSD |

## Q0 consent
OWNER_CONFIRMATIONS.md: hashing PENDING, overnight PENDING, telemetry PENDING.
Q0 runs used metadata-only inventory-models (HASHING=NOT_REQUESTED).
