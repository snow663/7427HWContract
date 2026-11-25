#!/usr/bin/env python3
"""Reproduce the exact native-artifact and bus acceptance failures at 2696d9d.

The CURRENT independent eight-test suite runs against a temporary detached
checkout of the pinned pre-correction development commit. Accept only the six
native ``ImageError not raised`` failures, the literal EEPROM-crossing bus
failure, and the passing valid-bundle control. Errors, skips, missing compiler,
wrong module paths and unrelated failures cannot count as reproductions.

All machine bytes in these tests are synthetic; the C bus probe uses a host
compiler. This does not qualify a real firmware image, target ABI or device.

Default exit: 1 for the exact historical failures; 2 for setup/unexpected
results. --expect-mismatch returns 0 only for the expected failures. --out
receives command logs and JSON evidence. Full Git history, Python and the host
C compiler selected by CC (one executable name/path) are required. No network
or shell command execution is used. The temporary worktree is removed finally.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
BASELINE = "2696d9d1a58d55fa913a967e18761d051e0b87b2"
TEST = "tests/audit/test_artifact_integrity.py"
NATIVE = "pseudo-source/native"
NATIVE_FAILURES = {
    "test_artifact_integrity.NativeArtifactIntegrity." + name
    for name in (
        "test_code_changed_without_new_inspection_rejected",
        "test_consistent_but_stale_bss_report_rejected",
        "test_missing_reset_body_rejected",
        "test_missing_trap_body_rejected",
        "test_nm_changed_without_new_inspection_rejected",
        "test_unbound_report_rejected",
    )
}
BUS_FAILURE = ("test_artifact_integrity.BusApertureIntegrity."
               "test_every_address_in_a_window_has_the_declared_resource")
VALID_CONTROL = ("test_artifact_integrity.NativeArtifactIntegrity."
                 "test_valid_synthetic_bundle_still_composes")
BUS_MESSAGE = ("AssertionError: 1 != 0 : accepted 0400..1fff across "
               "conditional EEPROM 0e00..0fff")


# A fresh interpreter prevents current implementation imports from qualifying
# the old baseline by accident. Explicit module paths are recorded and checked.
CHILD = r'''
import hashlib, importlib.util, json, pathlib, subprocess, sys, unittest
test_path, baseline, output = map(pathlib.Path, sys.argv[1:])
spec = importlib.util.spec_from_file_location("test_artifact_integrity", test_path)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
class Result(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.passes = []
    def addSuccess(self, test):
        self.passes.append(test.id())
        super().addSuccess(test)
suite = unittest.defaultTestLoader.loadTestsFromModule(module)
result = unittest.TextTestRunner(verbosity=2, resultclass=Result).run(suite)
record = {
    "tests_run": result.testsRun,
    "failures": [{"id": t.id(), "traceback": trace} for t, trace in result.failures],
    "errors": [{"id": t.id(), "traceback": trace} for t, trace in result.errors],
    "skips": [{"id": t.id(), "reason": reason} for t, reason in result.skipped],
    "unexpected_successes": [t.id() for t in result.unexpectedSuccesses],
    "expected_failures": [t.id() for t, _ in result.expectedFailures],
    "passes": result.passes,
    "baseline_head": subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=baseline, text=True).strip(),
    "loaded_paths": {
        "test": str(pathlib.Path(module.__file__).resolve()),
        "root": str(module.ROOT.resolve()),
        "rom": str(pathlib.Path(module.ROM.__file__).resolve()),
        "boot": str(pathlib.Path(module.BOOT.__file__).resolve()),
    },
    "test_sha256": hashlib.sha256(test_path.read_bytes()).hexdigest(),
}
output.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
sys.exit(0 if result.wasSuccessful() else 1)
'''


class ReproductionError(Exception):
    """Setup failed or the suite did not reproduce exactly the known defects."""


def require(condition, message):
    if not condition:
        raise ReproductionError(message)


def exact(actual, expected, message):
    # Distinguish e.g. 8.0 from 8; accept no coercion in evidence accounting.
    canonical = lambda value: json.dumps(value, sort_keys=True,
        separators=(",", ":"), allow_nan=False)
    require(canonical(actual) == canonical(expected), message)


def command(argv, output, label, report, *, cwd=ROOT, env=None, check=True):
    argv = list(map(str, argv))
    record = {"name": label, "argv": argv, "cwd": str(cwd)}
    report.setdefault("commands", []).append(record)
    log = output / (label + ".log")
    try:
        result = subprocess.run(argv, cwd=cwd, env=env, text=True,
            capture_output=True, timeout=120, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        record["error"] = str(error)
        log.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        raise ReproductionError(f"{label}: {error}") from error
    record["returncode"] = result.returncode
    log.write_text(json.dumps(record, indent=2) + "\n\nSTDOUT\n" + result.stdout +
                   "\nSTDERR\n" + result.stderr, encoding="utf-8")
    if check:
        require(result.returncode == 0, f"{label} exited {result.returncode}; see {log}")
    return result


def validate_result(value, *, baseline, test_path, test_hash, returncode):
    require(isinstance(value, dict), "Test report is not a JSON object")
    exact(returncode, 1, "The historical suite did not exit with test failure")
    exact(value.get("baseline_head"), BASELINE, "Test checkout HEAD is not pinned baseline")
    exact(value.get("loaded_paths"), {
        "test": str(test_path.resolve()), "root": str(baseline.resolve()),
        "rom": str((baseline / NATIVE / "compose_hc11_rom.py").resolve()),
        "boot": str((baseline / NATIVE / "compose_hc11_linked_boot.py").resolve()),
    }, "Tests loaded code or fixtures from an unexpected checkout")
    exact(value.get("test_sha256"), test_hash, "Regression source changed during reproduction")
    exact({name: value.get(name) for name in (
        "tests_run", "errors", "skips", "unexpected_successes", "expected_failures", "passes")},
        {"tests_run": 8, "errors": [], "skips": [], "unexpected_successes": [],
         "expected_failures": [], "passes": [VALID_CONTROL]},
        "Test counts, error/skip state or valid-bundle control changed")
    failures = value.get("failures")
    require(isinstance(failures, list) and len(failures) == 7,
            "Expected exactly seven historical assertion failures")
    require(all(isinstance(item, dict) and set(item) == {"id", "traceback"}
                and isinstance(item["id"], str) and isinstance(item["traceback"], str)
                for item in failures), "Malformed failed-test record")
    identities = [item["id"] for item in failures]
    require(len(set(identities)) == 7 and set(identities) == NATIVE_FAILURES | {BUS_FAILURE},
            "Failed-test identities differ from the seven historical failures")
    for item in failures:
        lines = [line.strip() for line in item["traceback"].splitlines() if line.strip()]
        expected = BUS_MESSAGE if item["id"] == BUS_FAILURE else "AssertionError: ImageError not raised"
        require(bool(lines) and lines[-1] == expected,
                "Unexpected assertion evidence for " + item["id"])


def reproduce(output, report):
    test_path = ROOT / TEST
    require(test_path.is_file(), "Current independent regression file is missing")
    test_hash = sha256(test_path.read_bytes()).hexdigest()
    report["regression_sha256"] = test_hash
    command(["git", "cat-file", "-e", BASELINE + "^{commit}"],
            output, "baseline_available", report)
    container = Path(tempfile.mkdtemp(prefix="7427-artifact-baseline-"))
    baseline = container / "checkout"
    report["temporary_worktree"] = str(baseline)
    registered = False
    try:
        command(["git", "worktree", "add", "--detach", baseline, BASELINE],
                output, "create_worktree", report)
        registered = True
        head = command(["git", "rev-parse", "HEAD"], output, "pinned_head",
                       report, cwd=baseline).stdout.strip()
        exact(head, BASELINE, "Detached worktree is not the pinned baseline")
        report["baseline_tree"] = command(["git", "rev-parse", "HEAD^{tree}"],
            output, "pinned_tree", report, cwd=baseline).stdout.strip()
        env = os.environ.copy()
        env["AUDIT_REPO"] = str(baseline)
        observed = output / "observed_tests.json"
        observed.unlink(missing_ok=True)
        result = command([sys.executable, "-c", CHILD, test_path, baseline, observed],
            output, "baseline_tests", report, env=env, check=False)
        require(observed.is_file(), "The regression process did not produce its result report")
        value = json.loads(observed.read_text(encoding="utf-8"))
        report["observed"] = value
        validate_result(value, baseline=baseline, test_path=test_path,
                        test_hash=test_hash, returncode=result.returncode)
        exact(sha256(test_path.read_bytes()).hexdigest(), test_hash,
              "Regression source changed during reproduction")
    finally:
        # Remove only this runner's detached worktree; never prune repository
        # branches or another agent's worktrees. Failure remains a setup error.
        if registered or (baseline / ".git").is_file():
            command(["git", "worktree", "remove", "--force", baseline],
                    output, "remove_worktree", report)
        shutil.rmtree(container)
        report["temporary_worktree_removed"] = not baseline.exists()
        require(report["temporary_worktree_removed"], "Temporary worktree cleanup failed")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--expect-mismatch", action="store_true")
    args = parser.parse_args(argv)
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = {"schema": "7427-artifact-bus-baseline-reproduction-v1",
              "baseline_revision": BASELINE,
              "scope": "synthetic native-artifact acceptance and compiled host C bus binding",
              "temporary_worktree_removed": False}
    code = 2
    try:
        reproduce(output, report)
        report["status"] = "EXPECTED_BASELINE_FAILURES"
        code = 0 if args.expect_mismatch else 1
    except Exception as error:
        report["status"] = "UNEXPECTED_RESULT_OR_SETUP_ERROR"
        report["error"] = f"{type(error).__name__}: {error}"
    report["exit_code"] = code
    (output / "artifact_bus_baseline.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "status", "baseline_revision", "temporary_worktree_removed", "exit_code")}, indent=2))
    if "error" in report:
        print(report["error"], file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
