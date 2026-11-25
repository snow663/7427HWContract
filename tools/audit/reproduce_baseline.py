#!/usr/bin/env python3
"""Run the focused CPU, arithmetic and scheduling regressions against the base.

A nonzero unittest result alone is not a reproduction. This wrapper requires
the exact pinned baseline HEAD, the recorded method and assertion-failure
counts for every selected suite, and zero errors, skips or other result classes.
It records full logs, but does not check an exact manifest of failed identities:
an unrelated failure with precisely the same counts is not ruled out by this
gate alone. Individual tests remain usable with AUDIT_REPO and return nonzero
on the defective implementation.
"""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASELINE = "f2f493f4df5843d37baf23d27a460dbd7d890476"
EXPECTED = {
    "test_hc11_isa.py": (357, 493),
    "test_target_arithmetic.py": (14, 9),
    "test_interrupt_scheduling.py": (6, 4),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    environment = dict(os.environ, AUDIT_REPO=str(args.repo.resolve()))
    head = subprocess.check_output(["git", "-C", str(args.repo), "rev-parse", "HEAD"], text=True).strip()
    if head != BASELINE:
        result = {"schema": "7427-audit-baseline-reproduction-v1",
                  "baseline_commit": head, "expected_baseline_commit": BASELINE,
                  "reproduced": False, "suites": [],
                  "error": "Refusing to run: checkout HEAD is not the pinned baseline"}
        (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result), flush=True)
        return 2
    rows = []
    for suite, (expected_tests, expected_failures) in EXPECTED.items():
        command = [sys.executable, "-m", "unittest", "discover", "-s", "tests/audit", "-p", suite, "-v"]
        process = subprocess.run(command, cwd=ROOT, env=environment, text=True,
                                 stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (args.out / (suite + ".log")).write_text(process.stdout)
        summary = re.search(r"FAILED \(([^)]+)\)", process.stdout)
        counts = {name.strip(): int(value) for name, value in
                  re.findall(r"([A-Za-z ]+)=(\d+)", summary.group(1))} if summary else {}
        failures, errors, skipped = (counts.get(name, 0) for name in ("failures", "errors", "skipped"))
        other_counts = {name: value for name, value in counts.items()
                        if name not in {"failures", "errors", "skipped"} and value}
        run = re.search(r"Ran (\d+) tests?", process.stdout)
        tests = int(run.group(1)) if run else None
        reproduced = (process.returncode == 1 and tests == expected_tests and
                      failures == expected_failures and errors == 0 and skipped == 0 and
                      not other_counts)
        row = {"suite": suite, "tests": tests, "expected_tests": expected_tests,
               "failed_assertions_or_subtests": failures,
               "expected_failed_assertions_or_subtests": expected_failures,
               "errors": errors, "skipped": skipped, "other_result_counts": other_counts,
               "exit_code": process.returncode, "reproduced": reproduced}
        rows.append(row)
        print(json.dumps(row), flush=True)
    result = {"schema": "7427-audit-baseline-reproduction-v1", "baseline_commit": head,
              "expected_baseline_commit": BASELINE,
              "meaning": "exact expected counts, not a failed-identity manifest or passing firmware result",
              "suites": rows}
    (args.out / "summary.json").write_text(json.dumps(result, indent=2) + "\n")
    return 0 if all(row["reproduced"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
