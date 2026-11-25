#!/usr/bin/env python3
"""Record observed audit logs without promoting pending or missing runs to pass.

Input filenames are the integration command log names documented in the audit.
This is a report collector, not a test runner or an equivalence certificate.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = "f2f493f4df5843d37baf23d27a460dbd7d890476"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def unittest_result(path, command):
    if not path.exists():
        return {"command": command, "status": "NOT_RUN"}
    data = path.read_text()
    result = {"command": command, "log_sha256": sha(path.read_bytes()), "status": "IN_PROGRESS"}
    match = re.search(r"Ran (\d+) tests? in ([\d.]+)s", data)
    if match:
        result.update(tests=int(match[1]), seconds=float(match[2]))
        final = data[match.end():].strip()
        result["status"] = "PASS" if final == "OK" else "FAIL_OR_SKIP"
        result["summary"] = final
    return result


def ctest_rows(text):
    rows = []
    for line in text.splitlines():
        # CTest prints failed outcomes immediately after its dotted padding.
        match = re.match(r"\s*\d+/\d+ Test\s+#\d+:\s+(\S+)\s+\.{2,}\s*(.*?)\s+([\d.]+) sec", line)
        if match:
            rows.append({"test": match[1], "result": match[2], "seconds": float(match[3])})
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--logs", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    suites = {
        "audit_unit": "python3 -m unittest discover -s tests/audit -v",
        "audit_factory_tests": "python3 -m unittest discover -s tests -p 'test_factory_*.py' -v",
        "audit_legacy_tests": "PYTHONPATH=hac31_romsim HAC31_BMHM_BIN=<hash-verified-BMHM> python3 -m unittest discover -s hac31_romsim/tests -v",
        "audit_modern_tests": "PYTHONPATH=7427_simulator python3 -m unittest discover -s 7427_simulator/tests -v",
    }
    results = {name: unittest_result(args.logs / (name + ".log"), command) for name, command in suites.items()}
    log = args.logs / "audit_all_ctest.log"
    text = log.read_text() if log.exists() else ""
    rows = ctest_rows(text)
    finished = "Total Test time" in text
    configuration_path = args.logs / "audit_build_configuration.json"
    configuration = json.loads(configuration_path.read_text()) if configuration_path.exists() else {}
    results["ctest"] = {
        "command": "ctest --test-dir <audit-build> --output-on-failure --parallel 4",
        "configure": "cmake -S pseudo-source -B <audit-build> -DBUILD_TESTING=ON -DCMAKE_BUILD_TYPE= -DCMAKE_C_FLAGS=-O2",
        "assertions_enabled": configuration.get("assertions_enabled"),
        "build_configuration_sha256": sha(configuration_path.read_bytes()) if configuration_path.exists() else None,
        "expected_tests": 122,
        "status": ("PASS" if len(rows) == 122 and all(r["result"] == "Passed" for r in rows) else "FAIL_OR_INCOMPLETE") if finished else "IN_PROGRESS",
        "completed_tests": len(rows), "entries": rows,
        "log_sha256": sha(text.encode()),
    }
    knock_source = "pseudo-source/tests/compare_knock_rom.py"
    original_knock = subprocess.check_output(["git", "show", BASE + ":" + knock_source], cwd=ROOT)
    results["ctest"]["knock_harness_during_full_run"] = {
        "path": knock_source, "sha256": sha(original_knock),
        "meaning": "original pinned harness with the corrected audit CPU; its failure is retained in the full-run log",
    }
    rerun_path = args.logs / "audit_knock_rerun.json"
    rerun = json.loads(rerun_path.read_text()) if rerun_path.exists() else {"status": "IN_PROGRESS_OR_NOT_RUN"}
    results["knock_corrected_harness_rerun"] = rerun
    completion_path = args.logs / "audit_completion_results.json"
    completion = json.loads(completion_path.read_text()) if completion_path.exists() else {"status": "NOT_RUN", "results": []}
    results["unrecorded_suite_completion_runs"] = completion
    if completion_path.exists() and not finished:
        results["ctest"]["status"] = "INCOMPLETE_SESSION_UNAVAILABLE"
        results["ctest"]["collection_note"] = "The original session could no longer be accessed with 119 completion records. The three unrecorded commands were started separately; no completion is inferred from a missing process handle."
    latest = {row["test"]: row["result"] for row in rows}
    rerun_applied = False
    if (rerun.get("status") == "PASS" and rerun.get("test") == "knock_rom_differential"
            and rerun.get("sources_unchanged_during_run") and "knock_rom_differential" in latest):
        latest["knock_rom_differential"] = "Passed"
        rerun_applied = True
    completion_applied = []
    for row in completion.get("results", []):
        if row.get("status") == "PASS" and row.get("sources_unchanged_during_run"):
            latest[row["test"]] = "Passed"
            completion_applied.append(row["test"])
        else:
            latest[row["test"]] = row.get("status", "FAIL_OR_INCOMPLETE")
    collection_ready = finished or completion.get("status") in {"PASS", "FAIL"}
    results["current_registered_test_results"] = {
        "status": ("PASS" if len(latest) == 122 and all(value == "Passed" for value in latest.values())
                   else "FAIL_OR_INCOMPLETE") if collection_ready else "IN_PROGRESS",
        "passed": sum(value == "Passed" for value in latest.values()),
        "expected": 122,
        "targeted_rerun_applied": rerun_applied,
        "completion_runs_applied": sorted(completion_applied),
        "meaning": "latest result for each registered test across the original batch, the corrected knock rerun, and the explicitly recorded completion runs; not a single all-pass full run",
        "remaining_failures": [name for name, value in sorted(latest.items()) if value != "Passed"],
    }
    baseline_path = args.logs / "audit_baseline_results/summary.json"
    baseline = json.loads(baseline_path.read_text()) if baseline_path.exists() else {"status": "NOT_RUN"}
    readiness_path = args.logs / "audit_output_irq_readiness.log"
    readiness = readiness_path.read_text() if readiness_path.exists() else "NOT_RUN"
    inventory_path = args.logs / "audit_inventory_readiness.log"
    inventory_readiness = inventory_path.read_text() if inventory_path.exists() else "NOT_RUN"
    changed = subprocess.check_output(["git", "diff", "--name-only", BASE], cwd=ROOT, text=True).splitlines()
    fingerprint = {p: sha((ROOT / p).read_bytes()) for p in changed
                   if (ROOT / p).is_file() and Path(p).suffix in {".py", ".c", ".h"}}
    result = {
        "schema": "7427-independent-audit-integration-v1",
        "recorded_utc": datetime.now(timezone.utc).isoformat(),
        "baseline_main": "56a3145477291dd7c6bfee15db98414c983b1b2f",
        "baseline_development": BASE, "python": platform.python_version(),
        "meaning": "bounded observed checks; no complete firmware, target compiler or hardware certificate",
        "factory_bin_sha256": "6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004",
        "factory_bin_origin": "reconstructed committed evidence, not independently acquired hardware dump",
        "results": results, "baseline_reproductions": baseline,
        "open_readiness": {"output_irq_probe": readiness,
            "complete_inventory": inventory_readiness,
            "native_hc11_compile_execute": "NOT_RUN: native HC11 compiler and complete linked reconstructed BIN unavailable",
            "real_dual_bin_pcm_comparison": "NOT_RUN: only synthetic comparator adapter demonstrated",
            "physical_hardware": "NOT_RUN"},
        "source_fingerprints_scope": "current integrated source; the original full-run knock harness and targeted rerun hashes are recorded separately above",
        "source_sha256": fingerprint,
    }
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"ctest": results["ctest"]["status"], "completed_ctests": len(rows),
                      "audit_tests": results["audit_unit"].get("tests"), "audit_status": results["audit_unit"]["status"]}))


if __name__ == "__main__":
    main()
