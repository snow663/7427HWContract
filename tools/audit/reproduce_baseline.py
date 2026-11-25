#!/usr/bin/env python3
"""Run the audit regressions against pinned pre-correction source.

A nonzero unittest result alone is not a reproduction: import/build errors are
rejected, and each suite must contain actual failed assertions. This wrapper
returns zero only when every selected suite has at least one assertion failure
and no unittest errors. It records the full failure counts and logs; it does not
check an exact manifest of failing test identities. The
individual test commands still return nonzero on the defective implementation.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SUITES = ("test_hc11_isa.py", "test_target_arithmetic.py",
          "test_artifact_integrity.py", "test_interrupt_scheduling.py")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, AUDIT_REPO=str(args.repo.resolve()))
    head = subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True).strip()
    rows = []
    for suite in SUITES:
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests/audit", "-p", suite, "-v"]
        process = subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (args.out / (suite + ".log")).write_text(process.stdout)
        summary = re.search(r"FAILED \(([^)]+)\)", process.stdout)
        counts = dict(re.findall(r"(\w+)=(\d+)", summary.group(1))) if summary else {}
        failures, errors = int(counts.get("failures", 0)), int(counts.get("errors", 0))
        run = re.search(r"Ran (\d+) tests?", process.stdout)
        reproduced = process.returncode == 1 and failures > 0 and errors == 0
        row = {"suite": suite, "tests": int(run.group(1)) if run else None,
               "failed_assertions_or_subtests": failures, "errors": errors,
               "exit_code": process.returncode, "reproduced": reproduced}
        rows.append(row)
        print(json.dumps(row), flush=True)
    result = {"schema": "7427-audit-baseline-reproduction-v1", "baseline_commit": head,
              "meaning": "observed expected regressions, not a passing firmware result", "suites": rows}
    (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return 0 if all(row["reproduced"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
