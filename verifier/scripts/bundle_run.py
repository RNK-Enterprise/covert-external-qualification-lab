#!/usr/bin/env python3
import argparse
import hashlib
import io
import json
import re
import tarfile
from pathlib import Path

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("run_dir")
    parser.add_argument("--output-dir", default="submissions")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    run = Path(args.run_dir).resolve()
    q0_root = (repo / "runs" / "q0").resolve()
    if q0_root not in run.parents or not run.is_dir():
        raise SystemExit("BLOCKED: input must be beneath runs/q0")
    if (run / "SHA256SUMS").exists():
        raise SystemExit("BLOCKED: run already sealed")
    evidence = json.loads((run / "evidence.json").read_text(encoding="utf-8"))
    run_id = evidence.get("run_id", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", run_id):
        raise SystemExit("BLOCKED: unsafe run ID")

    submissions = (repo / "submissions").resolve()
    output = Path(args.output_dir)
    output = (repo / output).resolve() if not output.is_absolute() else output.resolve()
    if submissions not in output.parents and output != submissions:
        raise SystemExit("BLOCKED: output must remain under submissions")
    output.mkdir(parents=True, exist_ok=True)
    archive = output / (run_id + ".tar")
    if archive.exists() or archive.with_suffix(".tar.sha256").exists():
        raise SystemExit("BLOCKED: output exists")

    entries = list(run.rglob("*"))
    if any(path.is_symlink() for path in entries):
        raise SystemExit("BLOCKED: symlink in run")
    files = sorted(path for path in entries if path.is_file())
    (run / "SHA256SUMS").write_text(
        "".join(sha(path) + "  " + path.relative_to(run).as_posix() + "\n" for path in files),
        encoding="utf-8",
    )
    with tarfile.open(archive, "x") as tar:
        for path in sorted(run.rglob("*")):
            if not path.is_file():
                continue
            data = path.read_bytes()
            info = tarfile.TarInfo(run_id + "/" + path.relative_to(run).as_posix())
            info.size = len(data)
            info.mtime = 0
            info.uid = 0
            info.gid = 0
            info.uname = ""
            info.gname = ""
            info.mode = 0o644
            tar.addfile(info, io.BytesIO(data))
    archive_hash = sha(archive)
    archive.with_suffix(".tar.sha256").write_text(archive_hash + "  " + archive.name + "\n", encoding="ascii")
    print("BUNDLE=" + str(archive))
    print("SHA256=" + archive_hash)
    print("SEALED=true; corrections require a new run ID")

if __name__ == "__main__":
    main()