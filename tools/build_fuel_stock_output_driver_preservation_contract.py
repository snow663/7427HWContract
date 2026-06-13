#!/usr/bin/env python3
"""Build the fuel stock-output-driver preservation contract artifacts.

This builder emits a static policy/contract package only. It does not create
runtime ASM, does not implement a fuel writer, and does not mark the stock fuel
output driver as proven. The contract defines the proof gates required to use a
preserved stock fuel scheduler/output driver instead of the compact $3FCE bench
path.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_MD = ROOT / "docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT.md"
CONTRACT_CSV = ROOT / "maps/contracts/fuel_stock_output_driver_preservation_contract.csv"
TEST_MD = ROOT / "docs/tests/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT_TEST.md"

ROWS = [
    {
        "gate_id": "FUEL-STOCK-001",
        "topic": "complete_stock_driver_range",
        "requirement": "Identify the complete preserved stock fuel scheduler/output-driver routine range before use.",
        "status": "required_not_proven",
        "bench_required": "no_if_complete_stock_preserved",
        "fallback_if_incomplete": "compact_$3FCE_SLICE0_bench_path",
    },
    {
        "gate_id": "FUEL-STOCK-002",
        "topic": "required_inputs_and_state",
        "requirement": "Identify every required BPW, fuel-mode, enable, timer, crank/run, dropout, async/sync, and no-fuel input/state value consumed by the preserved routine.",
        "status": "required_not_proven",
        "bench_required": "no_if_complete_stock_preserved",
        "fallback_if_incomplete": "compact_$3FCE_SLICE0_bench_path",
    },
    {
        "gate_id": "FUEL-STOCK-003",
        "topic": "output_writes_and_side_effects",
        "requirement": "Identify all ASIC/hardware-facing writes and RAM side effects performed by the preserved routine, including $3FCE and any scheduler/timer/no-fuel state it owns.",
        "status": "required_not_proven",
        "bench_required": "no_if_complete_stock_preserved",
        "fallback_if_incomplete": "compact_$3FCE_SLICE0_bench_path",
    },
    {
        "gate_id": "FUEL-STOCK-004",
        "topic": "order_delay_interrupt_assumptions",
        "requirement": "Preserve write order, delay calls, interrupt/update-window assumptions, and atomicity expected by the stock fuel output driver.",
        "status": "required_not_proven",
        "bench_required": "no_if_complete_stock_preserved",
        "fallback_if_incomplete": "compact_$3FCE_SLICE0_bench_path",
    },
    {
        "gate_id": "FUEL-STOCK-005",
        "topic": "reset_crank_dropout_seed_state",
        "requirement": "Prove reset, first-event, crank/run, dropout, unsafe, and no-fuel seed states are initialized before the preserved driver can command output.",
        "status": "required_not_proven",
        "bench_required": "no_if_complete_stock_preserved",
        "fallback_if_incomplete": "compact_$3FCE_SLICE0_bench_path",
    },
    {
        "gate_id": "FUEL-STOCK-006",
        "topic": "no_alternate_custom_writer",
        "requirement": "Prove no alternate direct custom $3FCE/ASIC fuel writer exists outside the preserved stock driver path unless it remains bench-proof gated.",
        "status": "required_not_proven",
        "bench_required": "no_if_complete_stock_preserved",
        "fallback_if_incomplete": "compact_$3FCE_SLICE0_bench_path",
    },
    {
        "gate_id": "FUEL-STOCK-007",
        "topic": "physical_semantics_deferred",
        "requirement": "Mark physical meaning of individual fuel ASIC/scheduler registers as deferred and not blocking only for a complete preserved stock driver.",
        "status": "required_not_proven",
        "bench_required": "no_if_complete_stock_preserved",
        "fallback_if_incomplete": "compact_$3FCE_SLICE0_bench_path",
    },
    {
        "gate_id": "FUEL-STOCK-FALLBACK",
        "topic": "compact_direct_writer_fallback",
        "requirement": "If complete stock-driver preservation is not proven, retain the existing compact $3FCE writer path and require FUEL-001 through FUEL-004 bench proof before SLICE-1.",
        "status": "active_fallback",
        "bench_required": "yes",
        "fallback_if_incomplete": "current_required_path",
    },
]


def write_csv() -> None:
    CONTRACT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with CONTRACT_CSV.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(ROWS[0].keys()))
        writer.writeheader()
        writer.writerows(ROWS)


def write_contract() -> None:
    CONTRACT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT",
        "",
        "## Purpose",
        "",
        "Define the decision seam for using the stock `$31` fuel scheduler/output driver as a preserved black-box hardware driver.",
        "",
        "This contract does not implement fuel code, does not replace the existing SLICE-0 `$3FCE` bench path, and does not claim the fuel stock-driver preservation proof is complete.",
        "",
        "It defines when fuel may follow the stock-driver preservation model instead of requiring per-register bench discovery or a compact direct `$3FCE` writer proof.",
        "",
        "## Fuel hardware authority model",
        "",
        "```text",
        "1. Clean OS may calculate desired fuel mass / BPW / enrichment state.",
        "2. Clean OS may feed stock-compatible fuel state into a preserved stock fuel scheduler/output driver.",
        "3. Preserved stock fuel scheduler/output driver owns all hardware-facing fuel writes.",
        "4. Direct custom fuel ASIC / $3FCE writers remain bench-proof gated.",
        "```",
        "",
        "## Critical distinction",
        "",
        "```text",
        "preserved stock fuel output driver:",
        "  static completeness proof required before use",
        "  no per-register physical bench proof required before use if complete",
        "",
        "compact direct $3FCE writer:",
        "  bench proof required before engine-runnable use",
        "```",
        "",
        "Preserving the stock fuel output driver is not the same thing as writing `$3FCE` from clean code.",
        "",
        "## What this can bypass",
        "",
        "If a complete stock fuel scheduler/output driver is preserved behavior-for-behavior, the project does not need to first prove the physical meaning of every fuel scheduler / ASIC support register before using that preserved path.",
        "",
        "The stock routine is treated as the already-proven hardware driver. The proof burden shifts to preserving the complete stock routine and feeding compatible state.",
        "",
        "## What this cannot bypass",
        "",
        "```text",
        "static proof that the preserved routine range is complete",
        "static proof that all required inputs/state are seeded",
        "static proof that side effects, write order, delay calls, and interrupt assumptions are preserved",
        "static proof that reset, first-event, crank/run, dropout, unsafe, and no-fuel states are safe",
        "static proof that no alternate direct custom fuel writer exists outside the gated path",
        "eventual real-hardware validation before engine trust",
        "```",
        "",
        "## Contract gates",
        "",
    ]
    for row in ROWS:
        lines.extend([
            f"### {row['gate_id']} — {row['topic']}",
            "",
            f"Requirement: {row['requirement']}",
            "",
            f"Status: `{row['status']}`",
            "",
            f"Bench requirement: `{row['bench_required']}`",
            "",
            f"Fallback if incomplete: `{row['fallback_if_incomplete']}`",
            "",
        ])
    lines.extend([
        "## Current decision state",
        "",
        "```text",
        "Fuel stock-driver preservation:",
        "  contract defined",
        "  preservation proof not complete",
        "  no implementation emitted",
        "",
        "Current active fuel route:",
        "  compact $3FCE SLICE-0 bench path remains active",
        "  FUEL-001 through FUEL-004 still required before SLICE-1 unless stock-driver preservation is completed and accepted",
        "```",
        "",
        "## Explicitly forbidden by this contract",
        "",
        "```text",
        "new runtime fuel ASM",
        "custom direct fuel ASIC writer",
        "custom direct $3FCE writer promoted to engine-runnable without bench proof",
        "partial stock output driver treated as complete",
        "unseeded BPW/fuel-mode/timer/dropout state entering preserved driver",
        "deleting stock side effects because their physical meaning is unknown",
        "claiming final engine safety from this contract alone",
        "```",
        "",
    ])
    CONTRACT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_test() -> None:
    TEST_MD.parent.mkdir(parents=True, exist_ok=True)
    TEST_MD.write_text(
        "# FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT_TEST\n\n"
        "## Purpose\n\n"
        "Verify that the fuel stock-output-driver preservation contract remains a static decision seam and does not create a runtime implementation.\n\n"
        "## Required files\n\n"
        "```text\n"
        "tools/build_fuel_stock_output_driver_preservation_contract.py\n"
        "docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT.md\n"
        "maps/contracts/fuel_stock_output_driver_preservation_contract.csv\n"
        "docs/tests/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT_TEST.md\n"
        "```\n\n"
        "## Static checks\n\n"
        "The contract must state:\n\n"
        "```text\n"
        "no fuel implementation is emitted\n"
        "no custom direct writer is created\n"
        "preserved stock fuel driver is static-proof gated\n"
        "compact $3FCE path remains bench-proof gated unless preservation is proven\n"
        "physical per-register semantics may be deferred only for a complete preserved stock driver\n"
        "partial stock-driver preservation falls back to the compact $3FCE bench path\n"
        "```\n\n"
        "## Required gates\n\n"
        "The CSV must include:\n\n"
        "```text\n"
        "FUEL-STOCK-001 complete_stock_driver_range\n"
        "FUEL-STOCK-002 required_inputs_and_state\n"
        "FUEL-STOCK-003 output_writes_and_side_effects\n"
        "FUEL-STOCK-004 order_delay_interrupt_assumptions\n"
        "FUEL-STOCK-005 reset_crank_dropout_seed_state\n"
        "FUEL-STOCK-006 no_alternate_custom_writer\n"
        "FUEL-STOCK-007 physical_semantics_deferred\n"
        "FUEL-STOCK-FALLBACK compact_direct_writer_fallback\n"
        "```\n\n"
        "## Pass criteria\n\n"
        "```text\n"
        "Contract package exists.\n"
        "No runtime ASM is added.\n"
        "No fuel writer implementation is added.\n"
        "No SLICE-1 gate is relaxed by this contract alone.\n"
        "Fuel stock-driver preservation remains required_not_proven until static proof is added.\n"
        "Compact $3FCE bench proof remains active fallback.\n"
        "```\n\n"
        "## Fail criteria\n\n"
        "```text\n"
        "Any new runtime fuel implementation appears.\n"
        "Any custom direct $3FCE writer is promoted without FUEL-001 through FUEL-004 proof.\n"
        "Any partial stock routine is treated as complete.\n"
        "Any physical fuel ASIC register meaning is claimed without trace or bench evidence.\n"
        "Any SLICE-1 allowance is created from this contract alone.\n"
        "```\n",
        encoding="utf-8",
    )


def main() -> int:
    write_csv()
    write_contract()
    write_test()
    print(f"wrote {CONTRACT_MD.relative_to(ROOT)}")
    print(f"wrote {CONTRACT_CSV.relative_to(ROOT)}")
    print(f"wrote {TEST_MD.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
