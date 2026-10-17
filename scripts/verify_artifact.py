#!/usr/bin/env python3
import argparse,hashlib
from pathlib import Path
def main():
 a=argparse.ArgumentParser();a.add_argument("artifact");a.add_argument("--expected");x=a.parse_args();p=Path(x.artifact).expanduser().resolve(strict=True)
 if not p.is_file():raise SystemExit("BLOCKED: not regular file")
 h=hashlib.sha256()
 with p.open("rb") as f:
  for b in iter(lambda:f.read(4194304),b""):h.update(b)
 d=h.hexdigest();print("BYTES="+str(p.stat().st_size));print("SHA256="+d)
 if x.expected and d.lower()!=x.expected.lower():raise SystemExit("FAIL: checksum mismatch")
if __name__=="__main__":main()