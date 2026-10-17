# Operator SOP

Q0 runs on each assigned physical node. Confirm the node before commands. Scripts create a unique runs/q0 directory and refuse overwrite. Q0 does not install, download, or execute models.

The repository is public so Q0 does not require a collaborator invitation. Use a personal fork and a `lab/barry/<mission-or-run>` branch; submit evidence by pull request to the owner repository. Never push directly to `main`. The owner reviews and merges accepted evidence. Do not request or use collaborator write access for Q0.

Collect static machine/software facts and cache metadata. --hash reads each artifact fully and may take a long time; use after expected read duration is approved. Add only exact known cache roots. Missing roots are recorded absent; never scan the whole disk.

Review observations; run verify-run; bundle-run; then verify-run again. Inspect the archive before PR. Preserve failures and retries as new run IDs.

Later phases need a pinned mission/artifact/build/battery/scorer, independent verifier, effects/resource/egress policy, budgets, telemetry consent, and cleanup contract. A phase folder never activates itself.
