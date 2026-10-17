#!/usr/bin/env python3
"""Read-only Q0 hardware and relevant software inventory for assigned Linux nodes."""
import argparse
import datetime
import importlib.metadata
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def cmd(argv, timeout=6, limit=2000000):
    executable = shutil.which(argv[0])
    if not executable:
        return {"status": "NOT_INSTALLED", "path": None, "output": None, "exit_code": None, "truncated": False}
    try:
        result = subprocess.run([executable, *argv[1:]], capture_output=True, text=True, timeout=timeout, check=False)
        raw = (result.stdout + result.stderr).strip()
        return {
            "status": "AVAILABLE" if result.returncode == 0 else "ERROR",
            "path": str(Path(executable).resolve()),
            "output": raw[:limit],
            "exit_code": result.returncode,
            "truncated": len(raw) > limit,
        }
    except subprocess.TimeoutExpired:
        return {"status": "TIMEOUT", "path": str(Path(executable).resolve()), "output": None, "exit_code": None, "truncated": False}

def os_release():
    values = {}
    try:
        for line in Path("/etc/os-release").read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                values[key] = value.strip().strip('"')
    except OSError:
        pass
    return values

def mem_total():
    try:
        for line in Path("/proc/meminfo").read_text().splitlines():
            if line.startswith("MemTotal:"):
                return int(line.split()[1]) * 1024
    except OSError:
        pass
    return None

def disk(path):
    try:
        usage = shutil.disk_usage(path)
        return {"path": str(path), "total_bytes": usage.total, "free_bytes": usage.free}
    except OSError:
        return {"path": str(path), "status": "UNKNOWN"}

def lscpu_fields(output):
    fields = {}
    for line in output.splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            fields[key.strip().lower()] = value.strip()
    return fields

def compare_report(report, observed, os_name):
    expected_release = report.get("os", "").split()[-1] if report.get("os") else ""
    if observed["os"]["id"] != "ubuntu":
        os_status = "MISMATCH" if observed["os"]["id"] else "UNKNOWN"
    elif expected_release and expected_release in os_name:
        os_status = "MATCH"
    elif expected_release and expected_release.rsplit(".", 1)[0] in os_name:
        os_status = "MATCH_BASE_RELEASE_PATCH_UNCONFIRMED"
    else:
        os_status = "MISMATCH" if os_name else "UNKNOWN"

    match = re.search(r"(Ryzen\s+\d\s+\d{4,5}U|i[3579]-\d{4,5}[A-Z]?)", report.get("cpu", ""), re.I)
    cpu_key = match.group(1) if match else None
    cpu_model = observed["cpu"]["model"] or ""
    cpu_status = "MATCH" if cpu_key and cpu_key.lower() in cpu_model.lower() else ("MISMATCH" if cpu_model and cpu_key else "UNKNOWN")

    expected_ram = report.get("usable_ram_gib", report.get("ram_gib"))
    actual_ram = observed.get("memory_total_bytes")
    if expected_ram and actual_ram:
        actual_gib = actual_ram / (1024 ** 3)
        ram_status = "WITHIN_REPORTED_RANGE" if 0.85 * expected_ram <= actual_gib <= 1.15 * expected_ram else "MISMATCH"
    else:
        ram_status = "UNKNOWN"

    gpu_text = " ".join(observed.get("display_devices", [])) + " " + str(observed["nvidia_smi"].get("output") or "")
    expected_gpu = report.get("gpu", "")
    token = "Barcelo" if "Barcelo" in expected_gpu else None
    if token is None:
        gpu_match = re.search(r"\b\d{4}\b", expected_gpu)
        token = gpu_match.group(0) if gpu_match else None
    gpu_status = "MATCH" if token and token.lower() in gpu_text.lower() else ("UNKNOWN" if not gpu_text.strip() else "NOT_CONFIRMED")

    core_statuses = (os_status, cpu_status, ram_status)
    overall = "MATCH_REPORTED_CORE" if os_status == "MATCH" and cpu_status == "MATCH" and ram_status == "WITHIN_REPORTED_RANGE" else "REVIEW_REQUIRED"
    return {"os": os_status, "cpu": cpu_status, "memory": ram_status, "gpu": gpu_status}, overall

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--node", choices=["phoenix", "atlas"], required=True)
    args = parser.parse_args()
    if not sys.platform.startswith("linux"):
        raise SystemExit("BLOCKED: inventory assigned Ubuntu nodes on-host")

    report_path = ROOT / "devices" / args.node / "manifest.template.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))["reported_profile"]
    now = datetime.datetime.now(datetime.timezone.utc)
    run_id = now.strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    run_dir = ROOT / "runs" / "q0" / args.node / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    release = os_release()
    os_name_result = cmd(["lsb_release", "-ds"], timeout=5, limit=3000)
    os_name = os_name_result.get("output") or release.get("PRETTY_NAME") or ""
    cpu_result = cmd(["lscpu"], timeout=5, limit=12000)
    cpu_fields = lscpu_fields(cpu_result.get("output") or "")
    pci_result = cmd(["lspci", "-nn"], timeout=5, limit=20000)
    nvidia = cmd(["nvidia-smi", "--query-gpu=name,memory.total,driver_version,pci.bus_id", "--format=csv,noheader"], timeout=5, limit=4000)

    cpu_model = cpu_fields.get("model name")
    if not cpu_model:
        try:
            cpu_model = next((line.split(":", 1)[1].strip() for line in Path("/proc/cpuinfo").read_text().splitlines() if line.lower().startswith("model name")), None)
        except OSError:
            pass
    display_devices = [line.strip() for line in (pci_result.get("output") or "").splitlines() if re.search(r"VGA|3D controller|Display controller", line, re.I)]
    sockets = int(cpu_fields["socket(s)"]) if cpu_fields.get("socket(s)", "").isdigit() else None
    cores_per_socket = int(cpu_fields["core(s) per socket"]) if cpu_fields.get("core(s) per socket", "").isdigit() else None
    physical_cores = sockets * cores_per_socket if sockets and cores_per_socket else None
    observed = {
        "os": {"id": release.get("ID"), "name": os_name, "version_id": release.get("VERSION_ID"), "kernel": platform.release(), "architecture": platform.machine()},
        "cpu": {"model": cpu_model, "physical_cores": physical_cores, "logical_cpus": os.cpu_count()},
        "memory_total_bytes": mem_total(),
        "display_devices": display_devices,
        "nvidia_smi": {key: nvidia[key] for key in ("status", "path", "output", "exit_code")},
        "storage": [disk(Path("/")), disk(Path.home())],
        "kvm_device_present": Path("/dev/kvm").exists(),
        "identity_capture": "hostname, serial, MAC, environment, and process command lines omitted",
    }
    comparisons, comparison_status = compare_report(report, observed, os_name)

    captured = now.isoformat().replace("+00:00", "Z")
    manifest = {
        "schema_version": "1.0", "run_id": run_id, "node_id": args.node, "captured_at_utc": captured,
        "reported_profile": report,
        "observed_profile": {**observed, "component_comparisons": comparisons},
        "comparison_status": comparison_status,
        "limitations": [
            "Static inventory only; no model load or inference.",
            "A core match compares reported OS/CPU/RAM only; GPU status is separate.",
            "No network, credentials, personal identifiers, or time-series telemetry inspected.",
        ],
    }

    tools = {}
    commands = {
        "python3": [sys.executable, "--version"], "git": ["git", "--version"],
        "ollama": ["ollama", "--version"], "llama-server": ["llama-server", "--version"],
        "llama-cli": ["llama-cli", "--version"], "vllm": ["vllm", "--version"],
        "lms": ["lms", "--version"], "opencode": ["opencode", "--version"],
        "rocminfo": ["rocminfo"],
        "nvidia-smi": ["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
    }
    for name, command in commands.items():
        result = cmd(command, timeout=5, limit=3000)
        tools[name] = {"status": result["status"], "path": result["path"], "version_or_summary": result["output"], "exit_code": result["exit_code"]}

    try:
        python_packages = sorted(
            [{"name": dist.metadata.get("Name"), "version": dist.version} for dist in importlib.metadata.distributions() if dist.metadata.get("Name")],
            key=lambda item: item["name"].lower(),
        )
    except Exception:
        python_packages = []
    package_result = cmd(["dpkg-query", "-W"], timeout=20, limit=2000000)
    software = {
        "schema_version": "1.0", "node_id": args.node, "captured_at_utc": captured,
        "scope": "AI/runtime executable presence, active Python distributions, and dpkg package name/version list",
        "python_executable": sys.executable, "python_version": platform.python_version(), "python_packages": python_packages,
        "tools": tools,
        "package_inventory_status": "TRUNCATED" if package_result["truncated"] else package_result["status"],
        "os_packages": (package_result["output"] or "").splitlines(),
        "limitations": [
            "No arbitrary environment variables, user files, browser profiles, credentials, process command lines, or network state inspected.",
            "Python packages describe only this interpreter; dpkg list is truncated only if explicitly marked TRUNCATED.",
        ],
    }

    (run_dir / ("BARRY_NODE_MANIFEST_" + args.node.upper() + ".json")).write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (run_dir / ("SOFTWARE_INVENTORY_" + args.node.upper() + ".json")).write_text(json.dumps(software, indent=2) + "\n", encoding="utf-8")
    evidence = {
        "schema_version": "1.0", "run_id": run_id, "phase": "Q0", "node_id": args.node,
        "status": "PARTIAL", "captured_at_utc": captured, "covert_build_identity": None,
        "model_artifact_identity": None, "artifacts": [], "failures": [],
        "verification": {"verifier_id": "q0-structure-and-sha256/1.0", "result": "NOT_RUN", "verifier_sha256": None},
        "owner_acceptance": False,
    }
    (run_dir / "evidence.json").write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")
    print("RUN_ID=" + run_id)
    print("RUN_DIR=" + str(run_dir))
    print("COMPARISON_STATUS=" + comparison_status)

if __name__ == "__main__":
    main()