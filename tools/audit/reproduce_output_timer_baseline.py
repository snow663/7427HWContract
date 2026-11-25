#!/usr/bin/env python3
"""Reproduce both missing output-timer C bodies at the public development base.

Build pinned f2f493f4 production C in a temporary detached worktree with
BUILD_TESTING=OFF, -O2, and assertions enabled. Link the CURRENT output-timer
test driver against that baseline's vector bridge and production library.
First require both zero-input vectors to return exactly PCM_UNIMPLEMENTED,
no native return, unchanged zero state/I/O and no hardware transactions. Then
run the CURRENT actual-ROM comparator separately for FFE0 and FFE2, accepting
only each exact missing-first-acknowledgment witness.

This proves the old missing-body defect only. It does not execute the old CPU,
prove native C/HC11 semantics, or replace the full corrected-code CTest gate.

Default exit: 1 when the exact known defect is reproduced; 2 for setup errors
or unexpected results. --expect-mismatch returns 0 only for the known defect.
--out names a directory for the JSON report, command logs and comparator JSON.
Full Git history containing the pinned commit, CMake and a C compiler are
required. CC may name a safely tokenized compiler/wrapper command; no shell is
used. The temporary worktree is removed in finally, including on failure.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[2]
BASELINE = "f2f493f4df5843d37baf23d27a460dbd7d890476"
DRIVER = "pseudo-source/tests/output_timer_test.c"
BRIDGE = "pseudo-source/platform/hc11_vector_contract.c"
COMPARATOR = "pseudo-source/tests/compare_output_timer_rom.py"
CPU = "hac31_romsim/romsim/hc11_core.py"
FACTORY_SHA256 = "6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004"
VECTORS = (0xFFE0, 0xFFE2)


class ReproductionError(Exception):
    """A setup failure or any result other than the exact missing-body defect."""


def require(condition, message):
    if not condition:
        raise ReproductionError(message)


def canonical(value):
    # Serialization distinguishes JSON true from 1 and 0.0 from 0; ordinary
    # Python container equality would incorrectly accept those substitutions.
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def exact(actual, expected, message):
    require(canonical(actual) == canonical(expected), message)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def literal_line(vector):
    return " ".join(map(str, (1, *([0] * 16), vector))) + "\n"


def missing_body():
    return {"steps": [{"status": 1, "action": 0, "state": [0] * 7,
                       "io": [0] * 6, "events": []}]}


def factory_literal(vector):
    # Independent literal instruction witness: the set-action/near path for
    # zero PORTA, TCNT and armed deadline. This is not imported from the
    # comparator whose mismatch report is being checked.
    bank_b = vector == 0xFFE2
    mask, action, compare = (0x10, 4, 0x301C) if bank_b else (8, 1, 0x301E)
    return {"steps": [{"status": 0, "action": 1, "state": [0] * 7,
                       "io": [0, 0, 0, action, 2 if bank_b else 0, 0 if bank_b else 2],
                       "events": [["W", 8, 0x3023, mask], ["R", 8, 0x3000, 0],
                                  ["R", 8, 0x3020, 0], ["W", 8, 0x3020, action],
                                  ["R", 16, 0x300E, 0], ["W", 16, compare, 2]]}]}


def run_command(argv, output, label, report, *, cwd=None, input_text=None,
                timeout=60, env=None):
    """Use argv directly; record every nonzero result before classifying it."""
    argv = [str(item) for item in argv]
    log = output / (label + ".log")
    record = {"name": label, "argv": argv, "cwd": str(cwd or ROOT),
              "log": str(log)}
    report.setdefault("commands", []).append(record)
    try:
        result = subprocess.run(argv, cwd=cwd or ROOT, env=env,
                                input=input_text, text=True, capture_output=True,
                                timeout=timeout, check=False)
    except (OSError, subprocess.TimeoutExpired) as error:
        record["error"] = str(error)
        log.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        raise ReproductionError(f"{label}: {error}") from error
    record["returncode"] = result.returncode
    log.write_text(json.dumps({"argv": argv, "cwd": str(cwd or ROOT),
                               "returncode": result.returncode}, indent=2) +
                   "\n\nSTDOUT\n" + result.stdout + "\nSTDERR\n" + result.stderr,
                   encoding="utf-8")
    return result


def checked(argv, output, label, report, **kwargs):
    result = run_command(argv, output, label, report, **kwargs)
    require(result.returncode == 0,
            f"{label} exited {result.returncode}; see {output / (label + '.log')}")
    return result


def validate_comparator_report(value, vector):
    require(isinstance(value, dict), "Comparator report is not a JSON object")
    require(set(value) == {"status", "case", "index", "first_divergence",
                           "reproduce_stdin", "expected_factory", "actual_c",
                           "factory_trace"}, "Comparator failure report schema changed")
    mask = 16 if vector == 0xFFE2 else 8
    start = 0x78D9 if vector == 0xFFE2 else 0x7875
    difference = ("result.steps[0].events[0]: expected "
                  f"[['W', 8, 12323, {mask}]], got [] (length 6 != 0)")
    exact({key: value[key] for key in ("status", "case", "index", "first_divergence",
                                      "reproduce_stdin")},
          {"status": "FAIL", "case": f"literal_ack_{vector:04X}", "index": 0,
           "first_divergence": difference, "reproduce_stdin": literal_line(vector)},
          f"{vector:04X}: comparator did not report the exact first acknowledgment gap")
    exact(value["actual_c"], missing_body(),
          f"{vector:04X}: comparator's C result differs from the exact missing body")
    exact(value["expected_factory"], factory_literal(vector),
          f"{vector:04X}: comparator's factory result differs from the literal instructions")
    exact(value["factory_trace"], [{"vector": f"{vector:04X}",
          "retired_pcs": [f"{start + offset:04X}" for offset in
                          (0, 3, 5, 7, 80, 83, 85, 88, 92, 97, 99)],
          "failed_pc": None}], f"{vector:04X}: factory did not complete the expected RTI path")


def reproduce(arguments, output, report):
    compiler = shlex.split(os.environ.get("CC", "cc"))
    require(bool(compiler), "CC must name a compiler command")
    report["compiler_argv"] = compiler
    checked(["git", "cat-file", "-e", BASELINE + "^{commit}"],
            output, "baseline_available", report)
    report["current_commit"] = checked(["git", "rev-parse", "HEAD"], output,
                                       "current_commit", report).stdout.strip()
    for name in (DRIVER, COMPARATOR, CPU):
        require((ROOT / name).is_file(), f"Current required source missing: {name}")
    report["current_sources_sha256"] = {name: digest(ROOT / name)
                                        for name in (DRIVER, COMPARATOR, CPU)}

    with tempfile.TemporaryDirectory(prefix="7427-output-timer-baseline-") as temporary:
        temporary = Path(temporary)
        baseline, build = temporary / "baseline", temporary / "build"
        added = False
        try:
            checked(["git", "worktree", "add", "--detach", str(baseline), BASELINE],
                    output, "worktree_add", report, timeout=60)
            added = True
            baseline_head = checked(["git", "rev-parse", "HEAD"], output,
                                    "baseline_commit", report, cwd=baseline).stdout.strip()
            require(baseline_head == BASELINE, "Detached worktree is not the pinned baseline")
            report["baseline_bridge_sha256"] = digest(baseline / BRIDGE)
            environment = os.environ.copy()
            environment["CC"] = shlex.join(compiler)
            checked([arguments.cmake, "-S", str(baseline / "pseudo-source"), "-B", str(build),
                     "-DBUILD_TESTING=OFF", "-DCMAKE_BUILD_TYPE=",
                     "-DCMAKE_C_FLAGS=-O2 -UNDEBUG"], output, "cmake_configure", report,
                    env=environment, timeout=120)
            checked([arguments.cmake, "--build", str(build), "--target", "pcm_pseudo_source",
                     "--parallel", str(arguments.jobs)], output, "cmake_build", report,
                    env=environment, timeout=600)
            library = build / "libpcm_pseudo_source.a"
            require(library.is_file(), "CMake did not produce libpcm_pseudo_source.a")
            report["baseline_library_sha256"] = digest(library)
            binary = temporary / "output_timer_before"
            checked([*compiler, "-std=c11", "-O2", "-UNDEBUG", "-Wall", "-Wextra",
                     "-Wpedantic", "-Werror", "-I", str(baseline / "pseudo-source/include"),
                     str(ROOT / DRIVER), str(baseline / BRIDGE), str(library), "-o", str(binary)],
                    output, "link_current_driver_to_baseline", report, timeout=120)
            report["baseline_driver_sha256"] = digest(binary)

            direct = checked([str(binary)], output, "direct_zero_literals", report,
                             input_text="".join(literal_line(v) for v in VECTORS), timeout=30)
            require(not direct.stderr.strip(), "Baseline driver wrote unexpected diagnostics")
            lines = direct.stdout.splitlines()
            require(len(lines) == 2, "Baseline driver did not emit exactly two literal results")
            actual = [json.loads(line) for line in lines]
            for vector, result in zip(VECTORS, actual):
                exact(result, missing_body(),
                      f"{vector:04X}: baseline differs from UNIMPLEMENTED/no-return/no-effects")
            report["direct_literals"] = [{"vector": f"{vector:04X}",
                                           "stdin": literal_line(vector), "actual": value}
                                          for vector, value in zip(VECTORS, actual)]

            comparisons = []
            for vector in VECTORS:
                comparison_path = output / f"comparator_{vector:04X}.json"
                # Never accept a stale report if setup fails before it is written.
                comparison_path.unlink(missing_ok=True)
                result = run_command([sys.executable, str(ROOT / COMPARATOR), str(binary),
                                      "--literal-only", "--literal-vector", f"{vector:04X}",
                                      "--report", str(comparison_path)], output,
                                     f"compare_factory_{vector:04X}", report, timeout=90)
                require(result.returncode == 1,
                        f"{vector:04X}: expected comparator mismatch exit1, got {result.returncode}")
                require(comparison_path.is_file(),
                        f"{vector:04X}: comparator failed without a structured mismatch report")
                comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
                validate_comparator_report(comparison, vector)
                require(not result.stdout.strip(),
                        f"{vector:04X}: unexpected successful comparator output")
                exact(json.loads(result.stderr), comparison,
                      f"{vector:04X}: stderr does not contain exactly the accepted mismatch report")
                comparisons.append({"vector": f"{vector:04X}", "report": str(comparison_path),
                                    "report_sha256": digest(comparison_path),
                                    "first_divergence": comparison["first_divergence"]})
            report["factory_comparisons"] = comparisons
            # Do not let a concurrently edited driver or reference script turn
            # one result into evidence for a different source snapshot.
            require(report["current_sources_sha256"] ==
                    {name: digest(ROOT / name) for name in (DRIVER, COMPARATOR, CPU)},
                    "Current comparison sources changed during reproduction")
            report["known_defect_reproduced"] = True
        finally:
            if added:
                removal = run_command(["git", "worktree", "remove", "--force", str(baseline)],
                                      output, "worktree_remove", report, timeout=60)
                report["temporary_worktree_removed"] = removal.returncode == 0
                require(removal.returncode == 0, "Could not unregister the temporary baseline worktree")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("output-timer-baseline-results"),
                        help="report/log directory (default: ./output-timer-baseline-results)")
    parser.add_argument("--cmake", default="cmake", help="CMake executable path")
    parser.add_argument("--jobs", type=int, default=4, help="parallel build jobs (default: 4)")
    parser.add_argument("--expect-mismatch", action="store_true",
                        help="exit0 only when both exact known missing-body defects are reproduced")
    arguments = parser.parse_args()
    output = arguments.out.resolve()
    report = {"status": "ERROR", "baseline_commit": BASELINE,
              "scope": "missing output-timer C bodies at the pinned public development baseline",
              "factory_sha256": FACTORY_SHA256, "known_defect_reproduced": False,
              "limits": ["The pre-fix baseline CPU is not executed",
                         "The factory witness uses the current corrected CPU and literal fixture",
                         "This proves two missing C bodies; it is not native HC11 or timing validation",
                         "Corrected-code verification is the separate full output_timer_rom_differential CTest"]}
    try:
        require(arguments.jobs > 0, "--jobs must be positive")
        output.mkdir(parents=True, exist_ok=True)
        reproduce(arguments, output, report)
        report["status"] = "EXPECTED_MISMATCH"
        code = 0 if arguments.expect_mismatch else 1
    except (ReproductionError, OSError, ValueError, subprocess.SubprocessError) as error:
        report["error"] = str(error)
        code = 2
    report["exit_code"] = code
    report_path = output / "output_timer_baseline.json"
    try:
        report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    except OSError as error:
        print(f"ERROR: cannot save reproduction report: {error}", file=sys.stderr)
        return 2
    if code == 2:
        print(f"ERROR: {report.get('error', 'unexpected reproduction result')}; report {report_path}",
              file=sys.stderr)
    else:
        print("EXPECTED MISMATCH: FFE0 and FFE2 baseline bodies return UNIMPLEMENTED "
              "and omit their first TFLG1 acknowledgment. Corrected-code verification is separate. "
              f"Report: {report_path}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
