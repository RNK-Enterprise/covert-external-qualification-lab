#!/usr/bin/env python3
"""Read-only inventory of model artifacts beneath explicit bounded cache roots."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEIGHT_SUFFIXES = {".gguf", ".safetensors", ".bin", ".pt", ".pth", ".onnx", ".tflite", ".model"}
TOKENIZER_NAMES = {"tokenizer.json", "tokenizer.model", "vocab.json", "vocab.txt", "merges.txt", "spiece.model"}

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def default_roots():
    home = Path.home()
    values = [
        os.environ.get("HUGGINGFACE_HUB_CACHE"), os.environ.get("HF_HOME"),
        os.environ.get("TRANSFORMERS_CACHE"), str(home / ".cache" / "huggingface" / "hub"),
        str(home / ".ollama" / "models"), str(home / ".cache" / "ollama" / "models"),
        str(home / ".lmstudio" / "models"), str(home / ".cache" / "lm-studio" / "models"),
    ]
    return list(dict.fromkeys(Path(value).expanduser().resolve() for value in values if value))

def model_name(group):
    for part in group.parts:
        if part.startswith("models--"):
            return part[len("models--"):].replace("--", "/"), "HUGGING_FACE_CACHE"
    return "UNKNOWN_LOCAL_ARTIFACT:" + group.name, "UNKNOWN_LOCAL_CACHE"

def config_for(group):
    try:
        path = group / "config.json"
        return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else {}
    except Exception:
        return {}

def add_ollama_manifests(root, records, models, do_hash, hash_cache):
    manifests = root / "manifests"
    blobs = root / "blobs"
    if not manifests.is_dir():
        return
    try:
        candidates = [path for path in manifests.rglob("*") if path.is_file()]
    except OSError:
        records.append({"path": str(manifests), "status": "ERROR", "error_code": "READ_FAILED"})
        return
    for manifest_path in candidates:
        try:
            document = json.loads(manifest_path.read_text(encoding="utf-8"))
            layers = document.get("layers", [])
            if not isinstance(layers, list) or not layers:
                continue
            artifacts = []
            complete = True
            total = 0
            for layer in layers:
                declared = layer.get("digest", "")
                if not declared.startswith("sha256:"):
                    complete = False
                    continue
                blob = blobs / ("sha256-" + declared.split(":", 1)[1])
                if not blob.is_file():
                    complete = False
                    artifacts.append({"path": str(blob), "actual_bytes": 0, "sha256": None, "declared_sha256": declared, "sha256_status": "MISSING"})
                    continue
                size = blob.stat().st_size
                total += size
                actual = None
                if do_hash:
                    if blob.resolve() not in hash_cache:
                        hash_cache[blob.resolve()] = sha256(blob)
                    actual = hash_cache[blob.resolve()]
                    if actual != declared.split(":", 1)[1]:
                        complete = False
                artifacts.append({
                    "path": str(blob), "actual_bytes": size, "sha256": actual,
                    "declared_sha256": declared, "sha256_status": "COMPUTED" if actual else "NOT_REQUESTED",
                    "last_modified_utc": datetime.datetime.fromtimestamp(blob.stat().st_mtime, datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                })
            model_id = manifest_path.relative_to(manifests).as_posix()
            models.append({
                "model_id": model_id, "source": "OLLAMA_LOCAL_MANIFEST", "local_path": str(manifest_path),
                "actual_bytes": total, "complete_or_partial": "COMPLETE_MANIFEST_BLOBS" if complete else "PARTIAL_OR_HASH_MISMATCH",
                "format": ["ollama-layered"], "architecture": "UNKNOWN", "parameter_class": "UNKNOWN",
                "quantization": "UNKNOWN", "revision": "MANIFEST_DECLARED",
                "sha256": [item["sha256"] for item in artifacts] if do_hash else None,
                "artifact_files": artifacts, "tokenizer": "RUNTIME_OR_EMBEDDED_UNKNOWN",
                "license": "UNKNOWN", "last_modified_utc": max((item.get("last_modified_utc", "") for item in artifacts), default=None),
                "runtime_compatibility_status": "NOT_TESTED",
            })
        except (OSError, ValueError, TypeError):
            records.append({"path": str(manifest_path), "status": "ERROR", "error_code": "MALFORMED_OR_UNREADABLE_MANIFEST"})

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", choices=["phoenix", "atlas"], required=True)
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--root", action="append", default=[], help="exact additional model-cache root; repeatable")
    parser.add_argument("--hash", action="store_true", help="read each artifact fully and compute/verify SHA-256")
    parser.add_argument("--max-files", type=int, default=20000)
    args = parser.parse_args()
    run_dir = Path(args.run_dir).resolve()
    q0_root = (ROOT / "runs" / "q0" / args.node).resolve()
    if q0_root not in run_dir.parents or not run_dir.is_dir():
        raise SystemExit("BLOCKED: run directory must be under this node's runs/q0")

    roots = list(dict.fromkeys(default_roots() + [Path(value).expanduser().resolve() for value in args.root]))
    root_records = []
    models = []
    hash_cache = {}
    group_signatures = set()
    visited = 0

    for root in roots:
        if not root.exists():
            root_records.append({"path": str(root), "status": "ABSENT"})
            continue
        if not root.is_dir():
            root_records.append({"path": str(root), "status": "ERROR", "error_code": "NOT_DIRECTORY"})
            continue
        root_records.append({"path": str(root), "status": "SCANNED"})
        groups = {}
        try:
            for path in root.rglob("*"):
                if not path.is_file() or path.suffix.lower() not in WEIGHT_SUFFIXES:
                    continue
                visited += 1
                if visited > args.max_files:
                    raise SystemExit("BLOCKED: max-files safety cap reached; narrow the root")
                group = path.parent
                for parent in (path.parent, *path.parents):
                    if parent == root.parent:
                        break
                    if (parent / "config.json").is_file():
                        group = parent
                        break
                    if parent == root:
                        break
                groups.setdefault(group, []).append((path, path.resolve(), path.stat()))
        except PermissionError:
            root_records[-1].update(status="ERROR", error_code="PERMISSION_DENIED")
        except OSError:
            root_records[-1].update(status="ERROR", error_code="READ_FAILED")

        for group, entries in groups.items():
            signature = (str(group), tuple(sorted(str(real) for _, real, _ in entries)))
            if signature in group_signatures:
                continue
            group_signatures.add(signature)
            artifacts = []
            total_bytes = 0
            for path, real, stat in entries:
                total_bytes += stat.st_size
                actual_hash = None
                if args.hash:
                    if real not in hash_cache:
                        hash_cache[real] = sha256(real)
                    actual_hash = hash_cache[real]
                artifacts.append({
                    "path": str(path), "actual_bytes": stat.st_size, "sha256": actual_hash,
                    "sha256_status": "COMPUTED" if actual_hash else "NOT_REQUESTED",
                    "last_modified_utc": datetime.datetime.fromtimestamp(stat.st_mtime, datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
                })
            config = config_for(group)
            tokenizer = any((group / name).is_file() for name in TOKENIZER_NAMES)
            has_gguf = any(path.suffix.lower() == ".gguf" for path, _, _ in entries)
            model_id, source = model_name(group)
            revision = next((part for part in group.parts if len(part) == 40 and all(ch in "0123456789abcdef" for ch in part.lower())), "UNKNOWN")
            models.append({
                "model_id": model_id, "source": source, "local_path": str(group), "actual_bytes": total_bytes,
                "complete_or_partial": "SINGLE_FILE_CANDIDATE" if has_gguf else ("COMPLETE_CANDIDATE" if config and tokenizer else "PARTIAL_OR_UNVERIFIED"),
                "format": sorted({path.suffix.lower().lstrip(".") for path, _, _ in entries}),
                "architecture": config.get("model_type", config.get("architectures", "UNKNOWN")),
                "parameter_class": "UNKNOWN", "quantization": config.get("quantization_config", "UNKNOWN"),
                "revision": revision, "sha256": [item["sha256"] for item in artifacts] if args.hash else None,
                "artifact_files": artifacts, "tokenizer": "PRESENT" if tokenizer else "NOT_FOUND",
                "license": config.get("license", "UNKNOWN"),
                "last_modified_utc": max(item["last_modified_utc"] for item in artifacts),
                "runtime_compatibility_status": "NOT_TESTED",
            })
        add_ollama_manifests(root, root_records, models, args.hash, hash_cache)

    output = run_dir / "MODEL_CACHE_INVENTORY.json"
    if output.exists():
        raise SystemExit("BLOCKED: inventory exists; use a new run directory")
    result = {
        "schema_version": "1.0", "node_id": args.node,
        "captured_at_utc": datetime.datetime.now(datetime.timezone.utc).isoformat().replace("+00:00", "Z"),
        "hashing": "COMPUTED" if args.hash else "NOT_REQUESTED",
        "roots": root_records, "models": models,
        "limitations": [
            "Only known/default and explicitly supplied roots were scanned.",
            "No download, load, or inference occurred.",
            "UNKNOWN fields are not qualification.",
            "Ollama manifests are cross-checked against their local blob files when --hash is used.",
        ],
    }
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("MODEL_CACHE_INVENTORY=" + str(output))
    print("ROOTS=" + str(len(root_records)) + " MODELS=" + str(len(models)) + " HASHING=" + result["hashing"])

if __name__ == "__main__":
    main()