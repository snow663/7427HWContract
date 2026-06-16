#!/usr/bin/env python3
"""Build subsystem isolation index from hardware gate decisions and static maps."""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

WRITE_MAP = Path("maps/contracts/write_target_network_index.csv")
DISPATCH_MAP = Path("maps/contracts/dispatcher_reverse_map.csv")
OUT_CSV = Path("maps/contracts/subsystem_isolation_index.csv")
OUT_MD = Path("docs/contracts/SUBSYSTEM_ISOLATION_INDEX.md")
OUT_TEST = Path("docs/tests/SUBSYSTEM_ISOLATION_INDEX_TEST.md")


def read_counter(path: Path, field: str) -> Counter[str]:
    c: Counter[str] = Counter()
    if not path.exists():
        return c
    with path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            c[row.get(field, "")] += 1
    return c


def write_targets_for(role_text: str) -> list[str]:
    if not WRITE_MAP.exists():
        return []
    targets: list[str] = []
    with WRITE_MAP.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            role = f"{row.get('candidate_role','')} {row.get('notes','')} {row.get('target_symbol','')}".lower()
            if role_text.lower() in role:
                targets.append(row.get("target_symbol", ""))
    return sorted(set(t for t in targets if t))


def build_rows() -> list[dict[str, str]]:
    spark_targets = [t for t in ["L3FE8", "L3FE6", "L3FDC", "L3FF6", "L3FEC", "L3FE4"]]
    iac_targets = [t for t in ["L3062", "L3060", "L3FFC"]]
    fuel_targets = ["L3FCE"]
    rows = [
        {
            "subsystem_key": "fuel_compact_3FCE",
            "current_route": "compact direct fuel PW handoff",
            "current_decision": "active_bench_route",
            "hardware_sinks_or_state": " ".join(fuel_targets),
            "preservation_status": "not_using_stock_driver",
            "bench_status": "required_pending_FUEL_001_through_FUEL_004",
            "implementation_permission": "bench_only_SLICE0_harness_and_result_capture_only",
            "blocked_conditions": "SLICE-1 blocked until FUEL-001 through FUEL-004 pass unless stock-driver preservation is later accepted",
            "must_implement": "$3FCE write path only after proof; zero/no-fuel behavior; scheduler/timer interaction enough; dropout/unsafe zero path",
            "may_ignore_after_proof": "stock fuel scheduler/output driver if compact route remains chosen and bench proofs pass",
            "must_preserve_if_stock_driver": "not applicable to active compact route",
            "dispatcher_dependency": "fuel scheduler/timer unresolved enough that compact route remains bench-proof gated",
            "next_required_proof": "run FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST and fill fuel_slice0_bench_results.csv",
            "notes": "active fuel route remains compact $3FCE bench proof",
        },
        {
            "subsystem_key": "fuel_stock_output_driver",
            "current_route": "candidate preserved stock fuel scheduler/output driver",
            "current_decision": "incomplete_continue_3FCE_bench_route",
            "hardware_sinks_or_state": "normal TBI path around $83FB-$858A includes L3FCE and related scheduler/output state",
            "preservation_status": "considered_not_accepted",
            "bench_status": "bench not bypassed",
            "implementation_permission": "no fuel stock-driver implementation until static proof complete",
            "blocked_conditions": "complete range inputs side effects scheduler/timer dependencies and dropout/no-fuel paths not proven complete",
            "must_implement": "none until preservation accepted",
            "may_ignore_after_proof": "output-cycling-only $3FCE paths, diagnostics-only mirrors, stock-only branches not feeding chosen route",
            "must_preserve_if_stock_driver": "complete stock output-driver routine, inputs, state, side effects, no-fuel gates, timer/scheduler path",
            "dispatcher_dependency": "requires proving entry path into stock fuel driver remains reachable under clean OS scheduler",
            "next_required_proof": "complete stock fuel output-driver static proof or continue compact $3FCE bench route",
            "notes": "contract exists but proof is not complete",
        },
        {
            "subsystem_key": "spark_stock_handoff",
            "current_route": "clean spark state -> preserved stock spark handoff routine",
            "current_decision": "accepted_static_route_after_contract_proof",
            "hardware_sinks_or_state": " ".join(spark_targets),
            "preservation_status": "accepted_as_working_route",
            "bench_status": "physical ASIC register semantics deferred/not blocking for stock preservation",
            "implementation_permission": "allowed only through preserved stock handoff seam; no custom ASIC writer",
            "blocked_conditions": "changing write order, delays, rolling state, EST monitor/mirror behavior, or direct ASIC writes",
            "must_implement": "clean spark calculation and stock-compatible input/state seeding",
            "may_ignore_after_proof": "per-register physical semantics if stock handoff is preserved behavior-for-behavior",
            "must_preserve_if_stock_driver": "L01FD/L01EE/sign/latency/period basis/rolling anchors/EST-bypass-monitor expectations",
            "dispatcher_dependency": "preserved routine must remain reachable from chosen spark scheduling path",
            "next_required_proof": "static preservation of complete handoff and input seeding before implementation",
            "notes": "custom direct writer remains bench-required",
        },
        {
            "subsystem_key": "spark_custom_writer",
            "current_route": "custom direct ASIC spark writer",
            "current_decision": "blocked_bench_required",
            "hardware_sinks_or_state": " ".join(spark_targets),
            "preservation_status": "not stock preservation",
            "bench_status": "required before any use",
            "implementation_permission": "forbidden",
            "blocked_conditions": "ASIC physical semantics not fully proven; raw-angle writer not accepted",
            "must_implement": "none",
            "may_ignore_after_proof": "none until bench proof exists",
            "must_preserve_if_stock_driver": "not applicable",
            "dispatcher_dependency": "not applicable",
            "next_required_proof": "bench discovery if direct writer is ever reconsidered",
            "notes": "do not create direct writes to L3FE8/L3FE6/L3FDC/L3FF6 outside stock handoff",
        },
        {
            "subsystem_key": "iac_stock_driver",
            "current_route": "candidate preserved stock IAC driver",
            "current_decision": "contract_defined_preservation_not_proven",
            "hardware_sinks_or_state": " ".join(iac_targets),
            "preservation_status": "defined_not_proven",
            "bench_status": "custom writer bench proof not bypassed",
            "implementation_permission": "no IAC stock-driver implementation until complete preservation proof exists",
            "blocked_conditions": "complete driver range, input state, phase/park/enable behavior, reset/dropout not proven",
            "must_implement": "none yet",
            "may_ignore_after_proof": "physical A/B/Enable/park semantics only if complete stock driver is preserved",
            "must_preserve_if_stock_driver": "complete IAC output driver, inputs, side effects, phase state, park/reset/dropout behavior",
            "dispatcher_dependency": "IAC driver reachability and scheduler ownership must be proven",
            "next_required_proof": "IAC stock-driver static proof index or custom IAC bench proof",
            "notes": "contract exists but preservation proof incomplete",
        },
        {
            "subsystem_key": "iac_custom_writer",
            "current_route": "custom direct A/B/Enable/park writer",
            "current_decision": "blocked_bench_required",
            "hardware_sinks_or_state": " ".join(iac_targets),
            "preservation_status": "not stock preservation",
            "bench_status": "required before use",
            "implementation_permission": "forbidden",
            "blocked_conditions": "physical A/B/Enable/park mapping not bench-proven",
            "must_implement": "none",
            "may_ignore_after_proof": "none until bench proof exists",
            "must_preserve_if_stock_driver": "not applicable",
            "dispatcher_dependency": "not applicable",
            "next_required_proof": "bench proof of A/B/Enable/phase/park or complete stock-driver preservation",
            "notes": "no direct L3062/L3060/L3FFC writer without proof",
        },
        {
            "subsystem_key": "whole_rom_write_sweep",
            "current_route": "static dependency discovery",
            "current_decision": "supporting_index",
            "hardware_sinks_or_state": "see write_target_network_index.csv",
            "preservation_status": "n/a",
            "bench_status": "n/a",
            "implementation_permission": "analysis_only",
            "blocked_conditions": "does not itself authorize deletion or implementation",
            "must_implement": "none",
            "may_ignore_after_proof": "diagnostics-only mirrors, unused branches, stock-only reporting only after network proves no hardware/safety/dispatch/preserved-driver dependency",
            "must_preserve_if_stock_driver": "all input/state/side effects consumed/produced by preserved driver",
            "dispatcher_dependency": "fed into dispatcher reverse map and subsystem isolation decisions",
            "next_required_proof": "review targets with hardware/safety/dispatch roles before deleting anything",
            "notes": "write does not equal importance; downstream reads decide role",
        },
        {
            "subsystem_key": "dispatcher_reverse_map",
            "current_route": "static indirect-control-flow discovery",
            "current_decision": "supporting_index",
            "hardware_sinks_or_state": "see dispatcher_reverse_map.csv",
            "preservation_status": "n/a",
            "bench_status": "n/a",
            "implementation_permission": "analysis_only",
            "blocked_conditions": "linear call-tree assumptions are insufficient",
            "must_implement": "none",
            "may_ignore_after_proof": "unreachable or irrelevant dispatch entries only after reverse-map proof",
            "must_preserve_if_stock_driver": "dispatch path that reaches preserved stock driver",
            "dispatcher_dependency": "selector variables/table entries/landing routine roles",
            "next_required_proof": "resolve indirect dispatchers that land on hardware-output or safety routines",
            "notes": "state bits/math/mode bytes can route into subsystem routines non-linearly",
        },
    ]
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SUBSYSTEM_ISOLATION_INDEX",
        "",
        "## Purpose",
        "",
        "Link the write-target network and dispatcher reverse map into subsystem-level decisions for the minimal 7427 OS.",
        "",
        "This artifact is static-only. It does not create runtime ASM, does not relax fuel/IAC bench gates, and does not allow SLICE-1.",
        "",
        "## Isolation rule",
        "",
        "Do not delete a variable because it looks unimportant. Delete only after its read/write network proves it does not feed hardware, safety, dispatch, or a preserved stock driver.",
        "",
        "## Current subsystem route decisions",
        "",
        "| subsystem | current decision | next required proof |",
        "|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| `{r['subsystem_key']}` | `{r['current_decision']}` | {r['next_required_proof']} |")
    lines.extend([
        "",
        "## Must preserve if using stock driver",
        "",
        "A preserved stock driver route must preserve the complete routine range, every input/state variable consumed, every side effect produced, write ordering, timing/delay assumptions, reset/dropout seed state, and any dispatcher path required to reach the routine.",
        "",
        "## May ignore only after proof",
        "",
        "Emissions strategy, diagnostics-only mirrors, unused transmission branches, calibration bookkeeping, and redundant monitors are not removable by name. They become removable only after the network proves they do not feed hardware, safety, dispatch, or preserved-driver state.",
        "",
        "## Active bottleneck",
        "",
        "Fuel remains on the compact `$3FCE` SLICE-0 bench path. `FUEL-001` through `FUEL-004` still block SLICE-1 under that route.",
        "",
    ])
    path.write_text("\n".join(lines), encoding="utf-8")


def write_test(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = """# SUBSYSTEM_ISOLATION_INDEX_TEST

## Scope

Static test definition for subsystem isolation after write-target and dispatcher indexing.

The artifact must:

- summarize fuel compact `$3FCE`, fuel stock driver, spark stock handoff, spark custom writer, IAC stock driver, and IAC custom writer
- include the current route, preservation status, bench status, implementation permission, blocked conditions, and next required proof
- keep fuel compact `$3FCE` on the active bench route
- keep `SLICE-1` blocked until `FUEL-001` through `FUEL-004` pass under the compact route
- keep custom spark and custom IAC writers bench-required
- treat write-target and dispatcher maps as supporting analysis, not implementation permission

## Required output files

```text
maps/contracts/subsystem_isolation_index.csv
docs/contracts/SUBSYSTEM_ISOLATION_INDEX.md
```

## Non-relaxation clause

This artifact must not create runtime ASM, permit deleting variables without network proof, mark fuel/IAC preservation accepted, mark bench proofs passed, or relax any hardware-output gate.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build subsystem isolation index")
    parser.parse_args()
    rows = build_rows()
    write_csv(OUT_CSV, rows)
    write_md(OUT_MD, rows)
    write_test(OUT_TEST)
    print(f"wrote {len(rows)} subsystem isolation rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
