#!/usr/bin/env python3
import argparse,json
from pathlib import Path
def main():
 a=argparse.ArgumentParser();a.add_argument("mission");m=json.loads(Path(a.parse_args().mission).read_text())
 if m.get("phase")!="Q0_RUNNER_TEST":raise SystemExit("BLOCKED: later phases are not activated; Q0 uses inventory commands")
 raise SystemExit("BLOCKED: this gate never runs inference; use qualify-machine/inventory-models")
if __name__=="__main__":main()