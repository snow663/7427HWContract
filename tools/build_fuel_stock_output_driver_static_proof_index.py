#!/usr/bin/env python3
"""Build the fuel stock-output-driver static proof index.

This is a planning/static-proof artifact only. It does not emit runtime ASM,
create a fuel writer, or relax the existing compact $3FCE bench gate.
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "maps" / "contracts" / "fuel_stock_output_driver_static_proof_index.csv"
MD_PATH = ROOT / "docs" / "contracts" / "FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX.md"
TEST_PATH = ROOT / "docs" / "tests" / "FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX_TEST.md"

FIELDNAMES = [
    "proof_id",
    "category",
    "item",
    "source_reference",
    "evidence_summary",
    "requirement",
    "status",
    "decision_impact",
    "notes",
]

ROWS = [
    {
        "proof_id": "FUEL-STOCK-PROOF-001",
        "category": "routine_range",
        "item": "candidate stock normal-TBI fuel output path",
        "source_reference": "source/31/BMHM_HAC_ORG_7100_to_end.asm:83FB-858A",
        "evidence_summary": "Candidate path includes mode gating, async flag handling, zero command, async accumulation, sync BPW normalization, low-BPW offset/min clamp, normal TBI $3FCE write, CPI/PFI delay branch, async output helper, and port-D strobes.",
        "requirement": "Complete preserved driver range must be bounded before it can supersede compact $3FCE bench route.",
        "status": "partial_identified",
        "decision_impact": "incomplete_continue_3FCE_bench_route",
        "notes": "Candidate range is useful but not yet proven complete against all callers, modes, first-event, dropout, and timer dependencies.",
    },
    {
        "proof_id": "FUEL-STOCK-PROOF-002",
        "category": "hardware_writes",
        "item": "normal fuel hardware-facing writes inside candidate range",
        "source_reference": "source/31/BMHM_HAC_ORG_7100_to_end.asm:8426,8512,8571,857F,8587",
        "evidence_summary": "Candidate path writes $3FCE for zero and normal sync BPW, writes $3FF2 for async PW, and strobes $3FFC around async delivery helper behavior.",
        "requirement": "All hardware-facing writes must be enumerated and owned by the preserved stock driver if accepted.",
        "status": "partial_identified",
        "decision_impact": "incomplete_continue_3FCE_bench_route",
        "notes": "Output writes are identified for the candidate slice, but downstream timer/interrupt support and side effects remain unresolved.",
    },
    {
        "proof_id": "FUEL-STOCK-PROOF-003",
        "category": "excluded_path",
        "item": "output cycling $3FCE writes",
        "source_reference": "source/31/BMHM_HAC_ORG_7100_to_end.asm:FAEE,FB44",
        "evidence_summary": "Output-cycling/test path writes #197 to $3FCE for 3 ms pulses and later writes zero to $3FCE while toggling I/O state.",
        "requirement": "Production preserved fuel driver proof must exclude output-cycling/test behavior from engine-runnable fuel authority.",
        "status": "identified_excluded",
        "decision_impact": "no_acceptance_by_itself",
        "notes": "This path can help bench understanding but is not a production fuel scheduler/output driver route.",
    },
    {
        "proof_id": "FUEL-STOCK-PROOF-004",
        "category": "required_inputs",
        "item": "stock-compatible fuel state inputs",
        "source_reference": "source/31/BMHM_HAC_ORG_7100_to_end.asm:83FB-858A; docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT.md",
        "evidence_summary": "Candidate path depends on sync BPW, async BPW, BPW bias, async flags, short-BPW flag, mode bytes, idle flag, MAP/RPM thresholds, current MAP, RPM/25, last REF period, min/max constants, and major-loop segment state.",
        "requirement": "Clean OS must prove it can seed every required stock-compatible input before entering preserved driver.",
        "status": "incomplete",
        "decision_impact": "incomplete_continue_3FCE_bench_route",
        "notes": "Input list is not yet complete enough to mark stock driver preservation accepted.",
    },
    {
        "proof_id": "FUEL-STOCK-PROOF-005",
        "category": "scheduler_timer_dependencies",
        "item": "TOC4/TOC5/TIC4 timer support dependencies",
        "source_reference": "docs/contracts/FUEL_SCHED_TIMER_CONTRACT.md",
        "evidence_summary": "Existing timer contract says FUEL_SCHED_TIMER is not the final EFI PW handoff; it schedules/services TOC4/TOC5 events and should be reproduced only if $3FCE alone is insufficient.",
        "requirement": "Static proof must decide whether preserved stock fuel driver requires timer service path or whether compact $3FCE remains sufficient.",
        "status": "unresolved",
        "decision_impact": "incomplete_continue_3FCE_bench_route",
        "notes": "This unresolved dependency prevents fuel stock-driver preservation from superseding the compact bench route.",
    },
    {
        "proof_id": "FUEL-STOCK-PROOF-006",
        "category": "enable_disable_dropout_paths",
        "item": "fuel no-pulse / clear / dropout behavior",
        "source_reference": "source/31/BMHM_HAC_ORG_7100_to_end.asm:8424-8429,8469-84BC,84F8-8515,FB39-FB47",
        "evidence_summary": "Candidate path contains commanded zero, async flag clear, async state reset, zero-BPW branch, and output-cycling zero path; true dropout/unsafe zero behavior is not yet proven as a preserved production path.",
        "requirement": "Accepted stock driver route must statically prove safe reset/first-event/dropout zero state or keep FUEL-004 active under compact route.",
        "status": "incomplete",
        "decision_impact": "incomplete_continue_3FCE_bench_route",
        "notes": "Commanded zero and dropout/unsafe zero remain distinct proofs.",
    },
    {
        "proof_id": "FUEL-STOCK-PROOF-007",
        "category": "direct_writer_exclusion",
        "item": "no alternate custom fuel writer",
        "source_reference": "repo policy contracts",
        "evidence_summary": "Static proof index does not create runtime ASM and does not install a custom $3FCE writer.",
        "requirement": "No direct custom fuel ASIC/$3FCE writer may supersede stock driver preservation without FUEL-001 through FUEL-004 bench proof.",
        "status": "pass_for_this_artifact",
        "decision_impact": "no_route_change",
        "notes": "This artifact is a proof index only.",
    },
    {
        "proof_id": "FUEL-STOCK-DECISION",
        "category": "route_decision",
        "item": "fuel stock driver preservation decision",
        "source_reference": "this proof index",
        "evidence_summary": "Candidate stock fuel output-driver range and several writes/dependencies are identified, but complete static preservation proof is not yet present.",
        "requirement": "Decision must be one of accepted_static_route, incomplete_continue_3FCE_bench_route, rejected_3FCE_bench_route_required.",
        "status": "incomplete_continue_3FCE_bench_route",
        "decision_impact": "active_route_unchanged",
        "notes": "Active fuel route remains compact $3FCE SLICE-0 bench path. FUEL-001 through FUEL-004 still gate SLICE-1 under active route.",
    },
]


def write_csv() -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(ROWS)


def write_markdown() -> None:
    MD_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX",
        "",
        "## Purpose",
        "",
        "This proof index decides whether the stock fuel scheduler/output-driver route can supersede the compact `$3FCE` SLICE-0 bench path.",
        "",
        "This is a static proof index only. It does not implement fuel ASM, does not create a fuel writer, and does not relax the current SLICE-1 gate.",
        "",
        "## Current decision",
        "",
        "```text",
        "fuel_stock_driver_preservation:",
        "  incomplete_continue_3FCE_bench_route",
        "",
        "active_fuel_route:",
        "  compact $3FCE SLICE-0 bench path",
        "",
        "SLICE-1:",
        "  still blocked under active compact route until FUEL-001 through FUEL-004 pass",
        "```",
        "",
        "## Candidate stock driver model",
        "",
        "```text",
        "clean fuel math",
        "→ stock-compatible BPW / fuel state",
        "→ preserved stock fuel scheduler/output driver",
        "→ stock driver owns hardware-facing writes",
        "```",
        "",
        "This route is only accepted if the static proof shows the preserved stock driver is complete and all required inputs, side effects, ordering, timer dependencies, and dropout/no-fuel paths are preserved.",
        "",
        "## Existing fallback route",
        "",
        "```text",
        "compact $3FCE writer",
        "→ FUEL SLICE-0 bench proof required",
        "```",
        "",
        "The fallback remains active because this proof index does not yet accept the preserved stock fuel output-driver route.",
        "",
        "## Proof rows",
        "",
    ]
    for row in ROWS:
        lines.extend([
            f"### {row['proof_id']} — {row['item']}",
            "",
            f"- Category: `{row['category']}`",
            f"- Source reference: `{row['source_reference']}`",
            f"- Evidence: {row['evidence_summary']}",
            f"- Requirement: {row['requirement']}",
            f"- Status: `{row['status']}`",
            f"- Decision impact: `{row['decision_impact']}`",
            f"- Notes: {row['notes']}",
            "",
        ])
    lines.extend([
        "## Accepted decision values",
        "",
        "```text",
        "fuel_stock_driver_preservation:",
        "  accepted_static_route",
        "",
        "fuel_stock_driver_preservation:",
        "  incomplete_continue_3FCE_bench_route",
        "",
        "fuel_stock_driver_preservation:",
        "  rejected_3FCE_bench_route_required",
        "```",
        "",
        "## Locked interpretation",
        "",
        "```text",
        "Fuel preservation contract exists",
        "≠ fuel preservation proof is complete",
        "≠ compact $3FCE bench gate is bypassed",
        "```",
        "",
        "Until this proof index is upgraded to `accepted_static_route`, the compact `$3FCE` bench route remains the active route and FUEL-001 through FUEL-004 still gate SLICE-1.",
        "",
    ])
    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def write_test_doc() -> None:
    TEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    TEST_PATH.write_text(
        "# FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX_TEST\n\n"
        "## Scope\n\n"
        "This test verifies that the fuel stock-output-driver static proof index is a decision/proof artifact only.\n\n"
        "It must not create runtime ASM, a fuel writer, a stock-driver implementation, an ALDL/debug packet, or an engine-runnable SLICE-1 path.\n\n"
        "## Required files\n\n"
        "```text\n"
        "tools/build_fuel_stock_output_driver_static_proof_index.py\n"
        "docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX.md\n"
        "maps/contracts/fuel_stock_output_driver_static_proof_index.csv\n"
        "docs/tests/FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX_TEST.md\n"
        "```\n\n"
        "## Required decision state\n\n"
        "The current decision must remain:\n\n"
        "```text\n"
        "fuel_stock_driver_preservation:\n"
        "  incomplete_continue_3FCE_bench_route\n"
        "```\n\n"
        "The test fails if this artifact claims `accepted_static_route` without proving all required stock-driver range, inputs, outputs, scheduler/timer dependencies, side effects, reset state, first-event state, dropout/no-fuel paths, and direct-writer exclusion.\n\n"
        "## Static requirements\n\n"
        "The proof index must include rows for:\n\n"
        "```text\n"
        "complete preserved stock fuel output-driver range\n"
        "required input RAM/state variables\n"
        "hardware-facing fuel writes\n"
        "scheduler/timer/interrupt dependencies\n"
        "enable/disable/DFCO/clear/dropout paths\n"
        "clean-OS stock-compatible state feasibility\n"
        "route decision\n"
        "```\n\n"
        "## Guardrails\n\n"
        "The proof index must preserve this distinction:\n\n"
        "```text\n"
        "Fuel preservation contract exists\n"
        "≠ fuel preservation proof is complete\n"
        "≠ compact $3FCE bench gate is bypassed\n"
        "```\n\n"
        "## Pass criteria\n\n"
        "The artifact passes if it identifies the candidate stock driver route and records the current decision as `incomplete_continue_3FCE_bench_route`.\n\n"
        "## Fail criteria\n\n"
        "The artifact fails if it emits fuel implementation code, promotes a partial stock driver as complete, bypasses FUEL-001 through FUEL-004 under the compact route, or creates a custom direct $3FCE writer.\n",
        encoding="utf-8",
    )


def main() -> int:
    write_csv()
    write_markdown()
    write_test_doc()
    print(f"wrote {CSV_PATH.relative_to(ROOT)}")
    print(f"wrote {MD_PATH.relative_to(ROOT)}")
    print(f"wrote {TEST_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
