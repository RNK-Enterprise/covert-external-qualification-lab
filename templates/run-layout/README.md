# Future Q1+ Run Layout — TEMPLATE

Q0 currently emits its machine/software/cache manifests, evidence.json and sealed bundle. Later experiment runs should use an immutable run directory equivalent to:

    runs/<run-id>/
      machine.json
      covert-build.json
      model.json
      mission.json
      prompts/                 reviewed prompt identity or hashes
      raw-output/              only if disclosure/privacy review permits
      logs/                    sanitized logs
      measurements.json
      verification.json
      failures.json
      evidence.json
      SHA256SUMS

Do not add prompts, raw output, logs, or owner data by default. Each later mission defines retention and submission policy. Never include credentials, device private identity, internal Covert source, or private owner tasks.