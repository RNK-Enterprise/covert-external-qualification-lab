# Pathway A/B/C + fleet copy — 2026-10-19
Times America/New_York (UTC-4).
## Copy verification
- Rsync `/home/odinn/lab/pipeline-stage/` → all 7 OCI `~/pipeline-stage/` (253M)
- KEYFILE_SHA256: **36/36 match** on typhoon valkyrie orion domyngo vidalyia onyx nebula
- Spot `E.N.G.L.I.S.H.M.A.N./js/index.js` = `c69414c6582494b7fb19b7c827a819a2d1dbecb897dbe90e50829c36e78dc18e`

## Cactus freeze
- freeze_id `cactus-needle3-20261019T1751Z`
- needle3.cact sha256 `c9d915eca282ed42d1a09b143b592adb4cc6744ffe2d294adf5cfc5548170c38` (35335380 bytes)
- config.json sha256 `d65e8e076d42b26ed473313e4890dfd8397274a238fd6c1715fff539b464c04e` (1273 bytes)
- Repo `inventory/fleet/CACTUS_FREEZE.json` identical to Phoenix on-disk freeze

## Typhoon medians (1 warmup + 5 reps × 3 prompts)
| Variant | median wall_s | median inference_s | pathway overhead_s | model_load_s |
|---|---:|---:|---:|---:|
| A PY FULL | 0.056104 | 0.056030 | 0.000036 | 0.245238 |
| B JS SKELETON | 0.405792 | 0.405751 | 0.000025 | 0.234199 |
| C JS FULL | 0.399755 | 0.399687 | 0.000057 | 0.229723 |

## B variance across 7 (overall_median_wall_s)
| Node | wall_s | inference_s | model_load_s |
|---|---:|---:|---:|
| typhoon | 0.402025 | 0.401968 | 0.228222 |
| valkyrie | 0.399222 | 0.399162 | 0.260252 |
| orion | 0.200884 | 0.200815 | 0.335486 |
| domyngo | 0.200727 | 0.200654 | 0.353345 |
| vidalyia | 0.201076 | 0.201010 | 0.268327 |
| onyx | 0.199432 | 0.199375 | 0.468435 |
| nebula | 0.200721 | 0.200654 | 0.291938 |

Fleet wall: min=0.199432 median=0.200884 max=0.402025 pstdev=0.090380

## Notes
- Needle3 is a tool-calling model; tools={} yields function_calls=[] with reasoning 'no tools declared' — sample_output [] is expected for this control pin.
- A uses Python needle 3.2.8 + tongue lossless roundtrip; B imports JS seat indexes only; C uses tongueTokenize/tongueJoin like A.
- Brain (Cerebrum) not copied; cerebrum-relay/hunter-crawl/axyum-camofox/shelf untouched; Atlas seats not stopped.
- Q0 PR #1 not recreated; evidence under evidence/pathway-ab/20261019/
- Node runtime for JS: v20.20.2 (package engines ask >=22.18; cactus-needle 0.3.0 ran successfully).
