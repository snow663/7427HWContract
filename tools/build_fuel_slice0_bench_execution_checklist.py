#!/usr/bin/env python3
"""Build the FUEL SLICE-0 bench execution checklist artifacts.

This builder emits static bench-run checklist artifacts only. It does not
implement fuel code, mark proof rows as passed, or relax SLICE-1 gates.
"""
from __future__ import annotations

from pathlib import Path
import csv

ROOT = Path(__file__).resolve().parents[1]

MD_PATH = ROOT / "docs" / "bench" / "FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST.md"
CSV_PATH = ROOT / "maps" / "bench" / "fuel_slice0_bench_execution_checklist.csv"
TEST_PATH = ROOT / "docs" / "tests" / "FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST_TEST.md"

ROWS = [
    {
        "step_id": "PRE-001",
        "proof_gate": "precondition",
        "harness_entry": "none",
        "commanded_vector_hex": "",
        "expected_counts": "",
        "expected_pw_ms": "",
        "required_observation": "confirm harness cannot run engine; bench output/load only",
        "required_evidence": "photo or note of bench isolation; no engine-runnable connection",
        "pass_condition": "engine cannot run from harness and injector output is safely loaded/observed",
        "fail_condition": "harness can run engine or output is connected unsafely",
        "result_file_target": "docs/bench/FUEL_SLICE0_BENCH_RESULTS.md; maps/bench/fuel_slice0_bench_results.csv",
        "sl1_effect": "none; precondition only",
    },
    {
        "step_id": "FUEL-003-ZERO",
        "proof_gate": "FUEL-003 partial",
        "harness_entry": "FUEL_SLICE0_WRITE_ZERO",
        "commanded_vector_hex": "$0000",
        "expected_counts": "0",
        "expected_pw_ms": "0.000000",
        "required_observation": "no injector pulse / zero command path",
        "required_evidence": "scope or logic analyzer capture showing no pulse; debug counts if available",
        "pass_condition": "no output pulse and commanded/debug count is zero",
        "fail_condition": "any injector pulse appears or nonzero command/debug count is observed",
        "result_file_target": "FUEL-003 row and FUEL-001 zero row",
        "sl1_effect": "partial FUEL-003 only; does not prove dropout/unsafe path",
    },
    {
        "step_id": "FUEL-001-1MS",
        "proof_gate": "FUEL-001",
        "harness_entry": "FUEL_SLICE0_WRITE_1MS",
        "commanded_vector_hex": "$0042",
        "expected_counts": "66",
        "expected_pw_ms": "1.007080",
        "required_observation": "pulse width correlates to commanded count",
        "required_evidence": "scope/logic analyzer measured pulse width; debug counts if available",
        "pass_condition": "measured PW within ±0.05 ms or ±3%, whichever is larger",
        "fail_condition": "missing pulse, wrong polarity, unstable output, or out-of-tolerance pulse width",
        "result_file_target": "FUEL-001 one_ms row",
        "sl1_effect": "supports fixed-vector $3FCE path only",
    },
    {
        "step_id": "FUEL-001-2MS",
        "proof_gate": "FUEL-001",
        "harness_entry": "FUEL_SLICE0_WRITE_2MS",
        "commanded_vector_hex": "$0083",
        "expected_counts": "131",
        "expected_pw_ms": "1.998901",
        "required_observation": "pulse width correlates to commanded count",
        "required_evidence": "scope/logic analyzer measured pulse width; debug counts if available",
        "pass_condition": "measured PW within ±0.05 ms or ±3%, whichever is larger",
        "fail_condition": "missing pulse, wrong polarity, unstable output, or out-of-tolerance pulse width",
        "result_file_target": "FUEL-001 two_ms row",
        "sl1_effect": "supports fixed-vector $3FCE path only",
    },
    {
        "step_id": "FUEL-002-3MS",
        "proof_gate": "FUEL-002",
        "harness_entry": "FUEL_SLICE0_WRITE_3MS",
        "commanded_vector_hex": "$00C5",
        "expected_counts": "197",
        "expected_pw_ms": "3.005981",
        "required_observation": "$00C5 produces 2.956-3.056 ms pulse",
        "required_evidence": "scope/logic analyzer capture of measured pulse width; debug count 197 if available",
        "pass_condition": "measured PW is 2.956-3.056 ms and commanded/debug count is 197 if available",
        "fail_condition": "pulse is absent, out of 2.956-3.056 ms, unstable, or count is not 197",
        "result_file_target": "FUEL-002 three_ms row and FUEL-001 three_ms row",
        "sl1_effect": "proves key fixed-vector count-to-time case only",
    },
    {
        "step_id": "FUEL-001-4MS",
        "proof_gate": "FUEL-001",
        "harness_entry": "FUEL_SLICE0_WRITE_4MS",
        "commanded_vector_hex": "$0106",
        "expected_counts": "262",
        "expected_pw_ms": "3.997803",
        "required_observation": "pulse width correlates to commanded count",
        "required_evidence": "scope/logic analyzer measured pulse width; debug counts if available",
        "pass_condition": "measured PW within ±0.05 ms or ±3%, whichever is larger",
        "fail_condition": "missing pulse, wrong polarity, unstable output, or out-of-tolerance pulse width",
        "result_file_target": "FUEL-001 four_ms row",
        "sl1_effect": "supports fixed-vector $3FCE path only",
    },
    {
        "step_id": "FUEL-004-DROPOUT",
        "proof_gate": "FUEL-004",
        "harness_entry": "not proven by fixed-vector harness",
        "commanded_vector_hex": "$0000",
        "expected_counts": "0",
        "expected_pw_ms": "0.000000",
        "required_observation": "real dropout/unsafe/no-fuel path asserts zero and injector pulse stops/remains absent",
        "required_evidence": "dropout/unsafe trigger capture plus zero command/output evidence",
        "pass_condition": "actual dropout/unsafe path is invoked and forces/stays zero with no injector pulse",
        "fail_condition": "only zero-vector routine was called, or dropout path allows nonzero/pulse output",
        "result_file_target": "FUEL-004 dropout_zero row",
        "sl1_effect": "required before SLICE-1 under compact $3FCE route",
    },
    {
        "step_id": "POST-001",
        "proof_gate": "postcheck",
        "harness_entry": "none",
        "commanded_vector_hex": "",
        "expected_counts": "",
        "expected_pw_ms": "",
        "required_observation": "results CSV updated and verifier re-run",
        "required_evidence": "maps/bench/fuel_slice0_bench_results.csv plus verifier output",
        "pass_condition": "tools/verify_fuel_slice0_bench_results.py passes with measured evidence",
        "fail_condition": "verifier fails, required rows missing, pass claimed without measurements, or SLICE-1 allowed early",
        "result_file_target": "maps/bench/fuel_slice0_bench_results.csv",
        "sl1_effect": "SLICE-1 remains blocked unless FUEL-001 through FUEL-004 are pass",
    },
]

FIELDNAMES = [
    "step_id",
    "proof_gate",
    "harness_entry",
    "commanded_vector_hex",
    "expected_counts",
    "expected_pw_ms",
    "required_observation",
    "required_evidence",
    "pass_condition",
    "fail_condition",
    "result_file_target",
    "sl1_effect",
]


def write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(ROWS)


def write_md(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for row in ROWS:
        rows.append(
            f"| {row['step_id']} | {row['proof_gate']} | {row['harness_entry']} | "
            f"{row['commanded_vector_hex']} | {row['expected_counts']} | {row['expected_pw_ms']} | "
            f"{row['required_observation']} | {row['pass_condition']} |"
        )
    path.write_text(
        "# FUEL SLICE-0 Bench Execution Checklist\n\n"
        "## Purpose\n\n"
        "Turn the active compact `$3FCE` fuel route proof gates into an exact bench execution checklist.\n\n"
        "This checklist does not implement fuel code, does not mark any proof passed, and does not relax `SLICE-1`.\n\n"
        "## Active Route\n\n"
        "```text\n"
        "active_fuel_route: compact $3FCE SLICE-0 bench path\n"
        "FUEL-001 through FUEL-004: required before SLICE-1 under this route\n"
        "FUEL-004: requires real dropout/unsafe zero path, not a zero-vector call\n"
        "```\n\n"
        "## Local Precheck\n\n"
        "Run from repo root before bench execution:\n\n"
        "```bash\n"
        "python tools/verify_fuel_slice0_bench_harness.py\n"
        "python tools/verify_fuel_slice0_bench_results.py\n"
        "```\n\n"
        "Expected pre-bench interpretation:\n\n"
        "```text\n"
        "harness verifier PASS: static harness structure is valid\n"
        "results verifier PASS: result CSV structure is valid; proof rows still not_run\n"
        "no bench proof has passed until measured evidence is entered\n"
        "```\n\n"
        "## Bench Execution Order\n\n"
        "| Step | Gate | Harness entry | Vector | Counts | Expected ms | Required observation | Pass condition |\n"
        "|---|---|---|---|---:|---:|---|---|\n"
        + "\n".join(rows)
        + "\n\n"
        "## Evidence Recording\n\n"
        "Record only measured evidence in:\n\n"
        "```text\n"
        "maps/bench/fuel_slice0_bench_results.csv\n"
        "docs/bench/FUEL_SLICE0_BENCH_RESULTS.md\n"
        "```\n\n"
        "Required evidence should include scope/logic-analyzer pulse width, pulse-present state, commanded/debug counts if available, channel/probe information, and evidence filename or note.\n\n"
        "## Gate Interpretation\n\n"
        "```text\n"
        "FUEL-001 pass + FUEL-002 pass + FUEL-003 partial/pass:\n"
        "  fixed-vector $3FCE path proven only\n\n"
        "FUEL-004 not pass:\n"
        "  no SLICE-1\n\n"
        "FUEL-001 through FUEL-004 all pass:\n"
        "  SLICE-1 planning may begin under the compact $3FCE route\n"
        "```\n\n"
        "## Zero Vector vs Dropout Proof\n\n"
        "```text\n"
        "$0000 vector:\n"
        "  proves commanded zero / no-pulse path\n\n"
        "dropout/unsafe zero:\n"
        "  proves safety gate behavior\n"
        "```\n\n"
        "These are not the same proof.\n",
        encoding="utf-8",
    )


def write_test(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# FUEL SLICE-0 Bench Execution Checklist Test\n\n"
        "## Purpose\n\n"
        "Verify that the bench execution checklist remains a bench-proof planning artifact only.\n\n"
        "## Required Files\n\n"
        "```text\n"
        "tools/build_fuel_slice0_bench_execution_checklist.py\n"
        "docs/bench/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST.md\n"
        "maps/bench/fuel_slice0_bench_execution_checklist.csv\n"
        "docs/tests/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST_TEST.md\n"
        "```\n\n"
        "## Static Checks\n\n"
        "The checklist must state:\n\n"
        "```text\n"
        "active route = compact $3FCE SLICE-0 bench path\n"
        "FUEL-001 through FUEL-004 remain required before SLICE-1\n"
        "FUEL-004 requires real dropout/unsafe zero path\n"
        "$0000 vector proof is not dropout proof\n"
        "no implementation is created\n"
        "no proof is marked pass by default\n"
        "```\n\n"
        "The CSV must include rows for:\n\n"
        "```text\n"
        "PRE-001\n"
        "FUEL-003-ZERO\n"
        "FUEL-001-1MS\n"
        "FUEL-001-2MS\n"
        "FUEL-002-3MS\n"
        "FUEL-001-4MS\n"
        "FUEL-004-DROPOUT\n"
        "POST-001\n"
        "```\n\n"
        "## Non-Relaxation\n\n"
        "This checklist must not:\n\n"
        "```text\n"
        "create SLICE-1\n"
        "mark FUEL-001/FUEL-002/FUEL-003/FUEL-004 as passed\n"
        "replace maps/bench/fuel_slice0_bench_results.csv\n"
        "claim dropout proof from FUEL_SLICE0_WRITE_ZERO\n"
        "create runtime ASM or hardware writer code\n"
        "relax compact $3FCE bench proof requirements\n"
        "```\n\n"
        "## Pass Criteria\n\n"
        "The artifact passes if it gives a complete bench execution sequence and preserves all existing fuel gates.\n\n"
        "## Fail Criteria\n\n"
        "Fail if it permits SLICE-1 before FUEL-001 through FUEL-004 pass, treats the zero vector as dropout proof, or introduces implementation behavior.\n",
        encoding="utf-8",
    )


def main() -> None:
    write_csv(CSV_PATH)
    write_md(MD_PATH)
    write_test(TEST_PATH)
    print(f"wrote {CSV_PATH.relative_to(ROOT)}")
    print(f"wrote {MD_PATH.relative_to(ROOT)}")
    print(f"wrote {TEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
