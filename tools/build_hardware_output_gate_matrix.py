#!/usr/bin/env python3
"""Build the 7427 hardware-output gate matrix.

This script emits a project-level single source of truth for the current
hardware-output subsystem routes. It is a planning/static-gate artifact only;
it does not emit runtime ASM, implementation code, bench results, or any
subsystem writer.
"""

from __future__ import annotations

import csv
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "maps" / "contracts" / "hardware_output_gate_matrix.csv"
DOC_PATH = ROOT / "docs" / "contracts" / "HARDWARE_OUTPUT_GATE_MATRIX.md"
TEST_PATH = ROOT / "docs" / "tests" / "HARDWARE_OUTPUT_GATE_MATRIX_TEST.md"

FIELDS = [
    "row_id",
    "subsystem",
    "current_route",
    "preservation_status",
    "bench_status",
    "implementation_permission",
    "blocked_conditions",
    "next_required_proof",
    "decision_state",
]

ROWS = [
    {
        "row_id": "fuel_compact_3FCE",
        "subsystem": "fuel",
        "current_route": "active compact direct $3FCE SLICE-0 bench route",
        "preservation_status": "not stock-preserved route",
        "bench_status": "bench proof required; FUEL-001 through FUEL-004 not yet passed",
        "implementation_permission": "bench-only fixed-vector harness/result capture only; no engine-runnable SLICE-1",
        "blocked_conditions": "SLICE-1 blocked until FUEL-001 through FUEL-004 pass unless complete stock fuel output-driver preservation supersedes this path",
        "next_required_proof": "run local verifiers, bench fixed vectors, enter measured evidence, keep FUEL-004 not_run until real dropout/unsafe path is invoked",
        "decision_state": "active_bench_route",
    },
    {
        "row_id": "fuel_stock_output_driver",
        "subsystem": "fuel",
        "current_route": "candidate preserved stock fuel scheduler/output-driver route",
        "preservation_status": "contract defined; static proof index decision incomplete_continue_3FCE_bench_route",
        "bench_status": "per-register bench discovery deferred only if preservation is later accepted; not accepted now",
        "implementation_permission": "no fuel implementation; no SLICE-1 relaxation; compact $3FCE route remains active",
        "blocked_conditions": "cannot supersede compact $3FCE bench path while range, inputs, writes, scheduler/timer dependencies, and dropout/no-fuel paths remain incomplete",
        "next_required_proof": "complete stock fuel driver static proof index to accepted_static_route or reject and continue $3FCE bench route",
        "decision_state": "candidate_incomplete",
    },
    {
        "row_id": "spark_stock_handoff",
        "subsystem": "spark",
        "current_route": "accepted preserved stock ASIC handoff route",
        "preservation_status": "stock handoff preservation contract complete enough for static-proof route",
        "bench_status": "physical ASIC spark semantics deferred/not blocking for preserved stock handoff",
        "implementation_permission": "clean spark state may feed preserved stock handoff after static completeness/input/side-effect proof; no custom writer",
        "blocked_conditions": "must not change write order, delay/interrupt assumptions, rolling state, EST monitor/mirror behavior, or required inputs",
        "next_required_proof": "pin complete preserved stock handoff routine range, inputs, state seeding, side effects, and no alternate direct writer",
        "decision_state": "accepted_static_route",
    },
    {
        "row_id": "spark_custom_writer",
        "subsystem": "spark",
        "current_route": "custom direct ASIC spark writer",
        "preservation_status": "not preserved stock driver",
        "bench_status": "bench proof required before use",
        "implementation_permission": "blocked",
        "blocked_conditions": "no direct $3FE8/$3FE6/$3FF6/$3FDC writer; no simplified raw-angle writer; no physical semantics claim without bench/trace proof",
        "next_required_proof": "only possible after explicit bench proof of ASIC-facing spark semantics and safe first-event/dropout behavior",
        "decision_state": "blocked_bench_required",
    },
    {
        "row_id": "iac_stock_driver",
        "subsystem": "iac",
        "current_route": "candidate preserved stock IAC output-driver route",
        "preservation_status": "contract defined; preservation proof not complete",
        "bench_status": "per-port physical semantics deferred only if complete stock IAC driver preservation is later accepted; not accepted now",
        "implementation_permission": "no IAC implementation; no direct writer permission yet",
        "blocked_conditions": "cannot bypass custom IAC bench proof until complete driver range, state seeding, writes, order/delays, reset/park/dropout behavior, and side effects are proven",
        "next_required_proof": "complete IAC stock-driver static proof index or bench-prove a custom A/B/Enable/park writer",
        "decision_state": "contract_defined_not_proven",
    },
    {
        "row_id": "iac_custom_writer",
        "subsystem": "iac",
        "current_route": "custom direct A/B/Enable/park writer",
        "preservation_status": "not preserved stock driver",
        "bench_status": "bench proof required before use",
        "implementation_permission": "blocked",
        "blocked_conditions": "no direct L3062/L3060/L3FFC writer without bench proof or complete stock-driver preservation",
        "next_required_proof": "bench-prove physical A/B/Enable/phase/park behavior, including reset/park/dropout safety",
        "decision_state": "blocked_bench_required",
    },
]


def write_csv() -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ROWS)


def write_doc() -> None:
    DOC_PATH.parent.mkdir(parents=True, exist_ok=True)
    table_rows = "\n".join(
        f"| `{row['row_id']}` | {row['subsystem']} | {row['current_route']} | {row['decision_state']} | {row['next_required_proof']} |"
        for row in ROWS
    )
    DOC_PATH.write_text(
        dedent(
            f"""
            # Hardware Output Gate Matrix

            Purpose: record the current route, preservation status, bench status, implementation permission, blocked conditions, and next required proof for each hard hardware-output subsystem.

            This is a planning/static-gate artifact only. It does not implement runtime ASM, does not create a hardware writer, does not record bench results, and does not relax any existing engine-runnable gate.

            ## Repo-wide rule

            ```text
            Preserve complete stock hardware driver:
              static-proof route possible

            Write hardware directly/custom:
              bench-proof route required
            ```

            ## Current route stack

            ```text
            Spark:
              stock handoff preservation accepted as the working route
              custom direct spark writer remains bench-required
              physical ASIC spark semantics deferred

            Fuel:
              stock output-driver preservation considered
              decision = incomplete_continue_3FCE_bench_route
              compact $3FCE SLICE-0 bench path remains active
              SLICE-1 still blocked by FUEL-001 through FUEL-004

            IAC:
              stock driver preservation contract defined
              preservation proof not complete
              custom direct A/B/Enable/park writer remains bench-required
            ```

            ## Gate matrix

            | row_id | subsystem | current route | decision state | next required proof |
            |---|---|---|---|---|
            {table_rows}

            ## Hard decisions

            ```text
            fuel_compact_3FCE:
              active_bench_route
              FUEL-001 through FUEL-004 still gate SLICE-1

            fuel_stock_output_driver:
              candidate_incomplete
              cannot supersede compact $3FCE bench path yet

            spark_stock_handoff:
              accepted_static_route
              clean spark state may feed preserved stock handoff after static completeness proof

            spark_custom_writer:
              blocked_bench_required

            iac_stock_driver:
              contract_defined_not_proven
              cannot bypass IAC bench proof yet

            iac_custom_writer:
              blocked_bench_required
            ```

            ## Non-relaxation clauses

            ```text
            This matrix does not make SLICE-1 legal.
            This matrix does not mark FUEL-001 through FUEL-004 passed.
            This matrix does not accept fuel stock-driver preservation.
            This matrix does not accept IAC stock-driver preservation.
            This matrix does not permit a custom direct spark writer.
            This matrix does not permit a custom direct IAC writer.
            This matrix does not create any runtime ASM.
            ```
            """
        ).lstrip(),
        encoding="utf-8",
    )


def write_test() -> None:
    TEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_PATH.write_text(
        dedent(
            """
            # Hardware Output Gate Matrix Test

            Goal: verify that `HARDWARE_OUTPUT_GATE_MATRIX` remains a single-source-of-truth planning artifact and does not relax subsystem gates or create implementation.

            ## Required files

            ```text
            tools/build_hardware_output_gate_matrix.py
            docs/contracts/HARDWARE_OUTPUT_GATE_MATRIX.md
            maps/contracts/hardware_output_gate_matrix.csv
            docs/tests/HARDWARE_OUTPUT_GATE_MATRIX_TEST.md
            ```

            ## Required CSV rows

            ```text
            fuel_compact_3FCE
            fuel_stock_output_driver
            spark_stock_handoff
            spark_custom_writer
            iac_stock_driver
            iac_custom_writer
            ```

            ## Required decisions

            ```text
            fuel_compact_3FCE: active_bench_route
            fuel_stock_output_driver: candidate_incomplete
            spark_stock_handoff: accepted_static_route
            spark_custom_writer: blocked_bench_required
            iac_stock_driver: contract_defined_not_proven
            iac_custom_writer: blocked_bench_required
            ```

            ## Static checks

            PASS requires:

            ```text
            no runtime ASM emitted
            no subsystem implementation emitted
            no custom writer emitted
            no bench result claimed
            no SLICE-1 gate relaxed
            fuel compact $3FCE remains active bench route
            fuel stock output-driver preservation remains incomplete
            spark stock handoff remains static-proof route only
            custom spark writer remains bench-required
            IAC stock-driver preservation remains not proven
            custom IAC writer remains bench-required
            ```

            FAIL if any wording implies:

            ```text
            FUEL-001 through FUEL-004 passed without bench evidence
            compact $3FCE bench path bypassed by an incomplete stock fuel proof
            IAC stock-driver preservation accepted without proof index
            custom direct ASIC spark writes allowed
            custom direct IAC A/B/Enable/park writes allowed
            runtime ASM created by this matrix
            ```
            """
        ).lstrip(),
        encoding="utf-8",
    )


def main() -> None:
    write_csv()
    write_doc()
    write_test()
    print(f"wrote {CSV_PATH.relative_to(ROOT)}")
    print(f"wrote {DOC_PATH.relative_to(ROOT)}")
    print(f"wrote {TEST_PATH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
