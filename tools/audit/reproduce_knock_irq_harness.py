#!/usr/bin/env python3
"""Reproduce the pinned knock harness's lost post-CLI IRQ request.

This runs only the definition prefix of the f2f493f4 development harness, loaded
with git show, against the CURRENT audited CPU and the same-hash factory ROM.
It does not run the old CPU or the lengthy original comparison sweep.

Default: the exact known mismatch returns 1; an unexpected result/setup error
returns 2. --expect-mismatch returns 0 only for that exact known mismatch, making
the defect reproduction usable in CI. This is not a passing firmware result.
The corresponding corrected gate is compare_knock_rom.py --irq-literal-witness.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
import inspect
import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[2]
BASELINE = "f2f493f4df5843d37baf23d27a460dbd7d890476"
HARNESS = "pseudo-source/tests/compare_knock_rom.py"
CORE = "hac31_romsim/romsim/hc11_core.py"
AUDIT_RECORD = "docs/audit/hc11_validation_results.json"
FACTORY_SHA256 = "6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004"
OUTPUT_ADDRESSES = [
    0x02, 0x06, 0x16, 0x19, 0x1A, 0x3A, 0x62, 0x63, 0x6E, 0x1EE, 0x1EF,
    0x203, 0x204, 0x207, 0x20C, 0x20D, 0x284, 0x843, 0x844, 0x3008,
    0x3030, 0x3034, 0x3023,
]


class ReproductionError(Exception):
    """A setup failure or result other than the exact known harness defect."""


def require(condition, message):
    if not condition:
        raise ReproductionError(message)


def expected_results(case4):
    mask_events = [["M", 0, 0, 1, 0], ["M", 0, 0, 0, 1]]
    if case4:
        host_state = [8, 120, 159, 165, 173, 238, 100, 100, 129, 18, 32,
                      0, 64, 159, 40, 98, 2, 64, 180, 255, 0, 128, 127]
        rom_state = [8, 120, 159, 165, 173, 238, 100, 100, 129, 18, 32,
                     255, 254, 159, 40, 0, 2, 64, 180, 255, 0, 128, 255]
        sample = 64
    else:
        host_state = [0] * len(OUTPUT_ADDRESSES)
        host_state[OUTPUT_ADDRESSES.index(0x204)] = 1
        rom_state = [0] * len(OUTPUT_ADDRESSES)
        sample = 1
    host = {"status": 0, "state": host_state, "masked": 0,
            "events": mask_events + [["W", 8, 0x3023, 0x80, 1],
                                      ["R", 16, 0x3FC8, sample, 1]]}
    old_harness = {"status": 0, "state": rom_state, "masked": 0,
                   "events": mask_events}
    return host, old_harness


def reproduce(arguments, report):
    binary = arguments.host_binary.resolve(strict=True)
    require(binary.is_file(), "--host-binary must name the compiled pcm_knock_tests executable")
    report["host_binary"] = {"path": str(binary), "sha256": sha256(binary.read_bytes()).hexdigest()}

    baseline = subprocess.run(
        ["git", "-C", str(ROOT), "show", f"{BASELINE}:{HARNESS}"],
        capture_output=True, check=True, timeout=15,
    ).stdout
    report["baseline_harness"] = {"commit": BASELINE, "path": HARNESS,
                                  "sha256": sha256(baseline).hexdigest()}
    prefix, marker, _ = baseline.decode("utf-8").partition("\ncounts = {}\n")
    require(bool(marker), "pinned harness definition boundary was not found")

    core_path = (ROOT / CORE).resolve(strict=True)
    core_hash = sha256(core_path.read_bytes()).hexdigest()
    audit = json.loads((ROOT / AUDIT_RECORD).read_text())
    recorded_hash = audit["runs"]["corrected"]["cpu_source_sha256"][CORE]
    report["audited_cpu"] = {"path": str(core_path), "sha256": core_hash,
                             "recorded_sha256": recorded_hash, "record": AUDIT_RECORD}
    require(core_hash == recorded_hash, "current CPU differs from the recorded corrected audit CPU")

    # __file__ intentionally names the current comparison path: the pinned
    # harness resolves its dependencies from this audit checkout, not the base.
    namespace = {"__file__": str(ROOT / HARNESS), "__name__": "pinned_knock_harness"}
    saved_argv = sys.argv
    try:
        sys.argv = [str(ROOT / HARNESS), str(binary)]
        exec(compile(prefix, f"{BASELINE}:{HARNESS}", "exec"), namespace)
    finally:
        sys.argv = saved_argv

    loaded_source = Path(inspect.getsourcefile(namespace["HC11CPU"])).resolve(strict=True)
    report["audited_cpu"]["loaded_source"] = str(loaded_source)
    require(loaded_source == core_path, "pinned harness imported a CPU outside the current audit checkout")
    require(type(namespace["cpu"]) is namespace["HC11CPU"], "harness CPU instance has an unexpected implementation")
    require(sha256(loaded_source.read_bytes()).hexdigest() == core_hash, "CPU source changed while loading the witness")
    require(namespace["OUTPUTS"] == OUTPUT_ADDRESSES, "pinned harness output contract changed")
    image = bytes([255]) * 0x4000 + namespace["rom"].read(0x4000, 0xC000)
    report["factory_rom_sha256"] = sha256(image).hexdigest()
    require(report["factory_rom_sha256"] == FACTORY_SHA256, "factory ROM identity differs from the audited image")

    if arguments.case4:
        item = namespace["case"](edits={0x20D: 0}, point=3, masked=0)
        fields = list(item[:7]) + [len(item[7])]
        for address, value in item[7].items():
            fields.extend((address, value))
        host_input = " ".join(map(str, fields)) + "\n"
    else:
        edits = {address: 0 for address in namespace["BASE"]} | {0x3FC9: 1}
        item = namespace["case"](edits=edits, point=3, masked=0)
        host_input = "3 0 0 1 -1 3 0 1 16329 1\n"
    report["host_input"] = host_input.strip()

    process = subprocess.run([str(binary)], input=host_input, text=True,
                             capture_output=True, check=True, timeout=15)
    host_result = json.loads(process.stdout)
    attempts = []
    cpu = namespace["cpu"]
    original_interrupt = cpu.interrupt

    def observe_interrupt(vector, *args, **kwargs):
        pc = cpu.s.pc
        admitted = original_interrupt(vector, *args, **kwargs)
        attempts.append({"pc": f"{pc:04X}", "vector": f"{vector:04X}", "admitted": admitted})
        return admitted

    cpu.interrupt = observe_interrupt
    try:
        old_harness_result = namespace["execute"](item)
    finally:
        cpu.interrupt = original_interrupt

    report["host_result"] = host_result
    report["baseline_harness_result"] = old_harness_result
    report["irq_attempts"] = attempts
    expected_host, expected_rom = expected_results(arguments.case4)
    require(host_result == expected_host, "host result is not the exact expected witness output")
    require(old_harness_result == expected_rom, "baseline harness result is not the exact lost-request output")
    require(attempts == [{"pc": "AA89", "vector": "FFE8", "admitted": False}],
            "witness did not make exactly one rejected post-CLI attempt at AA89")
    require(host_result != old_harness_result, "known harness mismatch was not reproduced")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host-binary", type=Path, required=True,
                        help="compiled current pcm_knock_tests executable")
    parser.add_argument("--case4", action="store_true",
                        help="use original IRQ case 4 instead of the literal one-byte witness")
    parser.add_argument("--expect-mismatch", action="store_true",
                        help="return 0 only when the exact known mismatch is reproduced")
    arguments = parser.parse_args()
    report = {"schema": "7427-knock-irq-harness-reproduction-v1",
              "witness": "original_case4" if arguments.case4 else "literal_one_byte",
              "meaning": "known harness defect reproduction, not a passing firmware result"}
    try:
        reproduce(arguments, report)
    except Exception as error:
        report.update(outcome="unexpected_result_or_error", exit_code=2,
                      error=f"{type(error).__name__}: {error}")
    else:
        report.update(outcome="expected_lost_request_mismatch",
                      exit_code=0 if arguments.expect_mismatch else 1)
    print(json.dumps(report, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    raise SystemExit(main())
