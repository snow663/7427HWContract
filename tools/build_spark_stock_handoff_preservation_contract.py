#!/usr/bin/env python3
"""Build the stock spark handoff preservation contract.

This is a static seam contract only. It does not implement spark ASM, does not
create a spark writer, and does not claim physical semantics of each ASIC spark
register. It preserves the stock handoff routine as the proven hardware driver.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

FIELDS = [
    "gate_id", "category", "object", "source_symbol_or_range", "clean_os_responsibility",
    "preserved_stock_responsibility", "allowed_status", "blocked_status",
    "physical_semantics_status", "proof_method", "implementation_gate",
    "confidence", "notes",
]

ROWS = [
    ["SPARK-STOCK-001", "routine_range", "complete preserved handoff routine", "LA906 output bridge; exact byte/range to be pinned before extraction", "identify call entry, exit, local preconditions, and complete contiguous/branched routine footprint", "own all ASIC-facing spark writes in preserved path", "allowed_after_static_contract", "new_spark_writer; simplified_raw_angle_writer", "deferred_not_blocking", "static_trace_required", "must identify complete routine range before extraction/link", "high_policy", "This row changes spark from ASIC bench discovery to stock driver preservation only."],
    ["SPARK-STOCK-002", "required_inputs", "stock-compatible spark state inputs", "L01FD; L01EE; L004F bit0; L0201; L005F/L0060; L3FC0/L3FC1; L3FDC; L3FF6; L01EC; EST/bypass/monitor flags", "produce or seed stock-compatible input/state variables", "consume stock-compatible inputs exactly as stock routine expects", "allowed_after_static_contract", "unseeded_inputs; deleted_state", "deferred_not_blocking", "static_dependency_trace", "all required inputs must be present before preserved routine can be used", "high_static", "Clean spark decision must feed stock state, not raw ASIC registers."],
    ["SPARK-STOCK-003", "output_writes", "ASIC-facing writes performed by preserved routine", "$3FE8; $3FE6; $3FDC; $3FF6; $3FEC->$3FE4", "do not write these directly outside preserved routine", "perform conversion, write sequence, rolling updates, and mirror/ack/status behavior", "allowed_only_inside_preserved_stock_handoff", "direct_custom_asic_writes", "deferred_not_blocking", "static_write_trace", "no alternate direct writer may exist", "high_static", "Physical meaning is not claimed; sequence preservation is claimed."],
    ["SPARK-STOCK-004", "preservation_invariants", "write order, delay calls, interrupt assumptions, side effects", "LA906 output sequence and companion delay/monitor code", "preserve call timing, ordering, short delays, CCR/interrupt assumptions, RAM side effects", "own timing-domain write order and side effects", "allowed_if_behavior_preserved", "changed_order; removed_delay; reordered_status_mirror", "deferred_not_blocking", "static_equivalence_review", "behavior-for-behavior preservation required", "medium_high_static", "No simplification until proven equivalent."],
    ["SPARK-STOCK-005", "seed_state", "first-event / reset / dropout seed state", "SPARK_INIT_STATE; SPARK_ROLLING_STATE_MODEL; SPARK_BYPASS_EST_TRANSITION", "initialize rolling anchors, period basis, EST authority state, and dropout-safe state before handoff call", "use seeded state without inventing alternate hardware semantics", "allowed_after_seed_contract", "uninitialized_first_event; unsafe_dropout_restart", "deferred_not_blocking", "static_boot_dropout_trace plus eventual hardware validation", "must be safe before engine use", "medium_static", "Stock routine can be preserved only if its expected initial state is also preserved."],
    ["SPARK-STOCK-006", "writer_exclusion", "no alternate direct custom spark ASIC writer", "repository-wide spark output files", "forbid direct $3FE8/$3FE6/$3FF6/$3FDC writes outside preserved stock routine", "remain sole owner of spark ASIC writes", "custom_spark_writer_blocked_bench_required", "direct $3FE8/$3FE6/$3FF6/$3FDC writer; SPARK_WRITE", "deferred_not_blocking", "static_scan_required", "fails if direct writer exists", "high_policy", "Bench required only to invent a new handoff."],
    ["SPARK-STOCK-007", "physical_semantics", "ASIC spark register physical meaning", "$3FE8; $3FE6; $3FDC; $3FF6; $3FEC; $3FE4", "do not claim physical meaning is known", "preserve stock sequence that already operates hardware", "deferred_bench_optional", "physical_semantics_required_before_preservation", "deferred_not_blocking", "explicit_deferral", "not blocking for preserved stock handoff; still required for custom writer", "high_policy", "Per-register physical discovery is optional/deferred for stock preservation, mandatory for custom writer."],
    ["SPARK-STOCK-008", "classification", "repo labels", "custom_spark_writer; stock_spark_handoff_preservation; spark_physical_semantics", "classify future work using the correct label", "n/a", "stock_spark_handoff_preservation_allowed_after_static_contract", "custom_spark_writer_blocked_bench_required", "spark_physical_semantics_deferred_bench_optional", "policy_classification", "used to prevent future regression to wrong gate", "high_policy", "Spark gate changes category, not safety discipline."],
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(FIELDS)
        writer.writerows(ROWS)


def write_md(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Spark Stock Handoff Preservation Contract",
        "",
        "## Purpose",
        "",
        "Lock the stock 7427 / `$31` spark ASIC handoff routine as the required spark hardware driver seam.",
        "",
        "This document does not implement spark code, does not create a spark writer, and does not claim physical semantics for each ASIC spark register.",
        "",
        "It changes the proof category from:",
        "",
        "```text",
        "bench-blocked because ASIC meaning is unknown",
        "```",
        "",
        "to:",
        "",
        "```text",
        "static-proof-gated because stock ASIC handoff is preserved",
        "```",
        "",
        "## Spark Hardware Authority Model",
        "",
        "```text",
        "1. Clean OS may calculate desired spark.",
        "2. Clean OS may feed stock-compatible spark state.",
        "3. Preserved stock handoff routine owns all ASIC-facing spark writes.",
        "4. Direct custom ASIC spark writes remain forbidden.",
        "```",
        "",
        "## Critical Interpretation",
        "",
        "```text",
        "We are not claiming to understand each ASIC spark register physically.",
        "We are claiming the stock handoff routine is already the proven hardware driver.",
        "Therefore the proof burden shifts from bench-discovering ASIC semantics",
        "to statically preserving the complete stock handoff path.",
        "```",
        "",
        "## Allowed Path",
        "",
        "```text",
        "clean spark calculation",
        "→ stock-compatible final spark state",
        "→ preserved stock spark handoff routine",
        "→ ASIC writes handled by preserved routine",
        "```",
        "",
        "## Forbidden Path",
        "",
        "```text",
        "clean spark calculation",
        "→ direct $3FE8 / $3FE6 / $3FDC / $3FF6 writes",
        "```",
        "",
        "## Required Inputs to Preserve",
        "",
        "```text",
        "L01FD final spark accumulator",
        "L01EE signed/current retard-advance working value, or its upstream equivalent",
        "L004F bit0 sign convention",
        "L0201 latency correction",
        "L005F / L3FC0 period basis",
        "L3FDC rolling state",
        "L3FF6 EST fall / rolling anchor",
        "L01EC or companion rolling value if used by the handoff",
        "EST/bypass/monitor flags expected by the routine",
        "```",
        "",
        "## Preserved Stock Routine Owns",
        "",
        "```text",
        "conversion into timing-domain values",
        "add/subtract against rolling anchor",
        "L3FE8 write",
        "L3FE6 write",
        "L3FDC update",
        "L3FF6 update",
        "L3FEC -> L3FE4 mirror/ack/status behavior",
        "EST monitor side effects",
        "```",
        "",
        "## What This Bypasses",
        "",
        "For stock handoff preservation only, this bypasses bench proof of:",
        "",
        "```text",
        "exact physical meaning of L3FE8",
        "exact physical meaning of L3FE6",
        "whether L3FDC is dwell/rolling offset/next event",
        "whether L3FEC -> L3FE4 is ack or diagnostic",
        "```",
        "",
        "## What This Does Not Bypass",
        "",
        "```text",
        "static proof that the preserved routine is complete",
        "static proof that all required inputs are seeded",
        "static proof that all side effects are preserved",
        "static proof that write order and delays are preserved",
        "static proof that first-event/dropout state is initialized safely",
        "static proof that no alternate direct custom spark ASIC writer exists",
        "eventual real-hardware validation before trusting it on an engine",
        "```",
        "",
        "## Gate Rows",
        "",
        "| Gate | Category | Object | Allowed | Blocked | Semantics | Gate |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in ROWS:
        lines.append(f"| `{r[0]}` | {r[1]} | {r[2]} | {r[6]} | {r[7]} | {r[8]} | {r[10]} |")
    lines += [
        "",
        "## Repo Classification",
        "",
        "```text",
        "custom_spark_writer:",
        "  blocked_bench_required",
        "",
        "stock_spark_handoff_preservation:",
        "  allowed_after_static_contract",
        "",
        "spark_physical_semantics:",
        "  deferred_bench_optional",
        "```",
        "",
        "## Discipline",
        "",
        "No spark implementation is created by this contract. First lock the seam: clean spark decision in, preserved stock hardware driver out.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out-md", required=True)
    p.add_argument("--out-csv", required=True)
    args = p.parse_args()
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT: wrote {len(ROWS)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
