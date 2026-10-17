#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
from pathlib import Path

HEX = re.compile(r"^[0-9a-f]{64}$")

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    root = Path(parser.parse_args().run_dir).resolve()
    repo = Path(__file__).resolve().parents[2]
    q0_root = (repo / "runs" / "q0").resolve()
    if q0_root not in root.parents or not root.is_dir():
        raise SystemExit("BLOCKED: run must be beneath runs/q0")
    if any(path.is_symlink() for path in root.rglob("*")):
        raise SystemExit("FAIL: symlink in run")

    evidence = json.loads((root / "evidence.json").read_text(encoding="utf-8"))
    if evidence.get("phase") != "Q0" or evidence.get("node_id") not in ("phoenix", "atlas"):
        raise SystemExit("FAIL: invalid Q0 identity")
    node = evidence["node_id"].upper()
    manifest_path = root / ("BARRY_NODE_MANIFEST_" + node + ".json")
    software_path = root / ("SOFTWARE_INVENTORY_" + node + ".json")
    model_path = root / "MODEL_CACHE_INVENTORY.json"
    for path in (manifest_path, software_path, model_path):
        if not path.is_file():
            raise SystemExit("FAIL: missing " + path.name)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    software = json.loads(software_path.read_text(encoding="utf-8"))
    model_inventory = json.loads(model_path.read_text(encoding="utf-8"))
    if any(item.get("node_id") != evidence["node_id"] for item in (manifest, software, model_inventory)):
        raise SystemExit("FAIL: node identity differs across Q0 evidence")
    if manifest.get("run_id") != evidence.get("run_id"):
        raise SystemExit("FAIL: run ID differs across Q0 evidence")
    for path in root.rglob("*.json"):
        json.loads(path.read_text(encoding="utf-8"))

    sums = root / "SHA256SUMS"
    if not sums.exists():
        print("PASS: structure valid; hash seal not present")
        return
    seen = set()
    for line in sums.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        digest, relative = line.split("  ", 1)
        relpath = Path(relative)
        target = root / relpath
        resolved = target.resolve()
        if (not HEX.fullmatch(digest) or relpath.is_absolute() or ".." in relpath.parts
                or relative in seen or target.is_symlink() or root not in resolved.parents):
            raise SystemExit("FAIL: malformed or unsafe SHA256SUMS")
        seen.add(relative)
        if not target.is_file() or sha(target) != digest:
            raise SystemExit("FAIL: hash mismatch " + relative)

    actual = {path.relative_to(root).as_posix() for path in root.rglob("*") if path.is_file() and path != sums}
    if actual != seen:
        raise SystemExit("FAIL: SHA256SUMS file set mismatch")
    print("PASS: Q0 structure and " + str(len(seen)) + " hashes verified")

if __name__ == "__main__":
    main()