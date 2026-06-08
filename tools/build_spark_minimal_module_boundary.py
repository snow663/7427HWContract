#!/usr/bin/env python3
"""Build the spark minimal module-boundary contract.

This is a non-code boundary artifact. It defines required, optional, and
bench-gated spark-side modules before any spark writer or handoff stub exists.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROWS = [
    {
        "module": "spark",
        "submodule": "SPARK_RUN_QUALIFY",
        "input": "REF/DRP event and period",
        "input_source": "ASIC $3FC0 / event latch path",
        "output": "engine-running permission",
        "output_target": "L004F bit7 / run-state gate",
        "state_variable": "L0044 bit3, L0050 bit2, L0210, L004F bit7",
        "required_static": "yes",
        "bench_gate": "verify exact event count and first-run ordering",
        "can_disable": "no",
        "risk_if_wrong": "EST authority too early or never enabled; wild first spark or no run spark",
        "source_contract": "SPARK_BYPASS_EST_TRANSITION.md",
        "notes": "Owns first DRP valid, recent DRP valid, 450 RPM threshold candidate, qualifying event count, engine-running flag.",
    },
    {
        "module": "spark",
        "submodule": "SPARK_BYPASS_EST_AUTHORITY",
        "input": "run-qualified state plus safe seed state",
        "input_source": "SPARK_RUN_QUALIFY + SPARK_INIT_STATE",
        "output": "EST authority permit / bypass-safe crank behavior",
        "output_target": "physical bypass/EST authority path, not fully mapped",
        "state_variable": "L004F bit7, startup/bypass state, possible ASIC mode state",
        "required_static": "yes",
        "bench_gate": "physical bypass/EST wire and coil authority timing",
        "can_disable": "no",
        "risk_if_wrong": "module/base timing and PCM/ASIC timing fight or first EST event occurs with invalid rolling state",
        "source_contract": "SPARK_INIT_STATE.md; SPARK_BYPASS_EST_TRANSITION.md",
        "notes": "Keeps crank safe and transitions from module/base timing to PCM/ASIC timing only after valid period/rolling-state conditions.",
    },
    {
        "module": "spark",
        "submodule": "SPARK_CONVERT_DEGREES_TO_TIME",
        "input": "desired spark degrees, REF/DRP period basis, latency, anchor/sign terms",
        "input_source": "future spark table/math; L005F/L0060; L0201; L3FC0; L004F bit0",
        "output": "D_AB97 timing-domain input",
        "output_target": "LA906 timing bridge entry",
        "state_variable": "L01FD/L01EE, L005F/L0060, L0201, L3FC0, L004F bit0",
        "required_static": "yes",
        "bench_gate": "L0201/L3FC0 final postprocess units and sign/high-nibble packing",
        "can_disable": "no",
        "risk_if_wrong": "spark angle produces wrong time offset; timing moves wrong direction or wrong magnitude",
        "source_contract": "SPARK_CONVERSION_EQUATION.md; MATH_HELPER_LF550.md; SPARK_TIMEBASE_PERIOD_CONTRACT.md; SPARK_MAGNITUDE_SCALE_CONTRACT.md",
        "notes": "Owns A_count = round(deg*256/90), LF550-style multiply, latency/anchor/sign postprocess.",
    },
    {
        "module": "spark",
        "submodule": "SPARK_ROLLING_STATE",
        "input": "D_AB97, period/work terms, previous rolling state",
        "input_source": "SPARK_CONVERT_DEGREES_TO_TIME + previous $3FF6/$3FDC + L01EC",
        "output": "continuous timing state for LA906 sequence",
        "output_target": "$3FF6 and $3FDC updates",
        "state_variable": "$3FF6/$3FF7, $3FDC/$3FDD, L01EC/L01ED",
        "required_static": "yes",
        "bench_gate": "$3FF6/$3FDC first-event seed behavior and recompute-vs-persist behavior",
        "can_disable": "no",
        "risk_if_wrong": "event-to-event timing discontinuity, jitter, wrong dwell/edge relationship, wild first run spark",
        "source_contract": "SPARK_ROLLING_STATE_MODEL.md; SPARK_INIT_STATE.md",
        "notes": "Owns persistence/continuity model and first-event rolling-state validity.",
    },
    {
        "module": "spark",
        "submodule": "SPARK_ASIC_HANDOFF",
        "input": "LA906 timing values and rolling-state outputs",
        "input_source": "SPARK_CONVERT_DEGREES_TO_TIME + SPARK_ROLLING_STATE",
        "output": "paired timing commands",
        "output_target": "$3FE8 and $3FE6",
        "state_variable": "$3FE8/$3FE9, $3FE6/$3FE7",
        "required_static": "yes",
        "bench_gate": "which register is primary vs paired edge, and measured EST output effect",
        "can_disable": "no",
        "risk_if_wrong": "no EST timing control or wrong paired edge/dwell behavior",
        "source_contract": "SPARK_LA906_OUTPUT_SEQUENCE.md; SPARK_ASIC_HANDOFF_CONTRACT.md",
        "notes": "Owns the paired ASIC timing writes; writer still not created until bench gates are explicit.",
    },
    {
        "module": "spark",
        "submodule": "SPARK_ASIC_MIRROR_ACK",
        "input": "ASIC status/capture source",
        "input_source": "$3FEC",
        "output": "mirror/ack/status sync",
        "output_target": "$3FE4",
        "state_variable": "$3FEC/$3FED, $3FE4/$3FE5",
        "required_static": "bench_gated",
        "bench_gate": "skip/freeze $3FEC->$3FE4 and observe authority, monitor, LA906 continuity",
        "can_disable": "unknown_pending_bench",
        "risk_if_wrong": "lost ACK/status sync, EST monitor false trip, broken LA906 event continuity",
        "source_contract": "SPARK_LA906_OUTPUT_SEQUENCE.md; SPARK_EST_FAULT_MONITOR_CONTRACT.md",
        "notes": "Shared by LA906 post-event path and EST monitor path; treat required until bench disproves.",
    },
    {
        "module": "spark",
        "submodule": "SPARK_EST_MONITOR",
        "input": "monitor enable, current/prior ref sample, fault threshold",
        "input_source": "L004F bit6, L3FCA, L0205, L4E72",
        "output": "Error 42 state / diagnostic counter",
        "output_target": "L022C, L0044 bit7 candidate, diagnostic/status path",
        "state_variable": "L004F bit6, L0205, L022C, L0044 bit7",
        "required_static": "optional_or_disabled_pending_bench",
        "bench_gate": "MON-A vs MON-B/MON-C/MON-D classification",
        "can_disable": "yes_if_MON_A_bench_proven",
        "risk_if_wrong": "false Error 42, possible authority/fallback side effects if monitor is not diagnostic-only",
        "source_contract": "SPARK_EST_FAULT_MONITOR_CONTRACT.md",
        "notes": "Optional/diagnostic unless bench proves it gates authority, fallback, or required ACK behavior.",
    },
    {
        "module": "spark",
        "submodule": "SPARK_DROPOUT_SAFE_STATE",
        "input": "missing REF/invalid period/dropout indication",
        "input_source": "recent DRP gate, period validity, run qualifier",
        "output": "safe hold/disable/fallback behavior",
        "output_target": "bypass/EST authority and handoff permission",
        "state_variable": "L0050 bit2, L0044 bit3, L005F/L0060, L004F bit7",
        "required_static": "yes_conceptually",
        "bench_gate": "exact stock behavior during missing REF/dropout",
        "can_disable": "no",
        "risk_if_wrong": "free-running spark output after REF loss or invalid period",
        "source_contract": "SPARK_BYPASS_EST_TRANSITION.md; SPARK_EST_FAULT_MONITOR_CONTRACT.md",
        "notes": "May be implemented simpler than stock, but the minimal OS must define safe behavior for invalid/missing timing basis.",
    },
]

FIELDS = [
    "module", "submodule", "input", "input_source", "output", "output_target",
    "state_variable", "required_static", "bench_gate", "can_disable", "risk_if_wrong",
    "source_contract", "notes",
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def require(path: str | Path) -> None:
    p = resolve(path)
    if not p.exists():
        raise FileNotFoundError(p)


def write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ROWS)


def write_md(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Spark Minimal Module Boundary",
        "",
        "## Purpose",
        "",
        "Define the minimal spark-control module boundary for the clean 7427 hardware-contract OS.",
        "",
        "This contract does not create a spark writer. It defines the required submodules, their inputs, outputs, state, and bench gates.",
        "",
        "## Source Contracts",
        "",
        "- `SPARK_CONVERSION_EQUATION.md`",
        "- `SPARK_LA906_OUTPUT_SEQUENCE.md`",
        "- `SPARK_ROLLING_STATE_MODEL.md`",
        "- `SPARK_INIT_STATE.md`",
        "- `SPARK_BYPASS_EST_TRANSITION.md`",
        "- `SPARK_EST_FAULT_MONITOR_CONTRACT.md`",
        "",
        "## Required Runtime Inputs",
        "",
        "| Input | Meaning | Source |",
        "|---|---|---|",
        "| REF/DRP period | timing basis | ASIC `$3FC0`, software `L005F` |",
        "| RPM/run state | crank/run qualification | `SPARK_RUN_QUALIFY` |",
        "| desired spark degrees | final desired advance | future spark table/math |",
        "| latency correction | EST/module delay correction | `L0201` path |",
        "| bypass/EST state | authority gate | `SPARK_BYPASS_EST_AUTHORITY` |",
        "| rolling state | continuity state | `$3FF6/$3FDC/L01EC` |",
        "| monitor state | diagnostic/fault state | `L004F bit6/L0205/L022C` if retained |",
        "",
        "## Required Hardware Outputs",
        "",
        "| Output | Role | Required? |",
        "|---|---|---|",
        "| `$3FE8` | paired timing command 1 | likely yes |",
        "| `$3FE6` | paired timing command 2 | likely yes |",
        "| `$3FF6` | rolling anchor update | likely yes |",
        "| `$3FDC` | rolling paired-edge/prior-state update | likely yes |",
        "| `$3FE4` | mirror/ack target from `$3FEC` | bench-gated |",
        "| bypass/EST authority output | physical authority transfer | not fully mapped |",
        "",
        "## Module Boundary Table",
        "",
        "| Submodule | Required static | Can disable? | Bench gate | Risk if wrong |",
        "|---|---|---|---|---|",
    ]
    for row in ROWS:
        lines.append(f"| `{row['submodule']}` | {row['required_static']} | {row['can_disable']} | {row['bench_gate']} | {row['risk_if_wrong']} |")
    lines += [
        "",
        "## Required Static Modules",
        "",
        "```text",
        "SPARK_RUN_QUALIFY",
        "SPARK_BYPASS_EST_AUTHORITY",
        "SPARK_CONVERT_DEGREES_TO_TIME",
        "SPARK_ROLLING_STATE",
        "SPARK_ASIC_HANDOFF",
        "SPARK_DROPOUT_SAFE_STATE",
        "```",
        "",
        "These cannot be removed from a minimal OS. They may be simplified, but the hardware contract they cover still has to exist.",
        "",
        "## Bench-Gated Pieces",
        "",
        "```text",
        "$3FEC->$3FE4 mirror / ACK / status-sync requirement",
        "$3FF6/$3FDC first-event seed behavior",
        "physical bypass/EST authority trigger",
        "L0201/L3FC0 final postprocess units and sign/packing",
        "exact paired role of $3FE8/$3FE6",
        "dropout/missing-REF safe behavior",
        "```",
        "",
        "These stay in the boundary as explicit gates. Do not hide them inside a writer stub.",
        "",
        "## Optional / Disabled Pending Bench",
        "",
        "```text",
        "SPARK_EST_MONITOR",
        "Error 42 accumulation through L022C",
        "locked ERR42A behavior through L0044 bit7 candidate",
        "diagnostic-only monitor behavior",
        "```",
        "",
        "The EST monitor can be omitted or kept disabled only if MON-A is bench-proven. If MON-B, MON-C, or MON-D is proven, the relevant monitor behavior becomes required.",
        "",
        "## Design Rule",
        "",
        "```text",
        "spark_math produces desired spark degrees",
        "        ↓",
        "SPARK_RUN_QUALIFY says whether EST control is allowed",
        "        ↓",
        "SPARK_BYPASS_EST_AUTHORITY permits physical/ASIC authority only when safe",
        "        ↓",
        "SPARK_CONVERT_DEGREES_TO_TIME produces D_AB97",
        "        ↓",
        "SPARK_ROLLING_STATE applies continuity model",
        "        ↓",
        "SPARK_ASIC_HANDOFF writes $3FE8/$3FE6 and mirror/ack if required",
        "        ↓",
        "SPARK_EST_MONITOR remains optional/diagnostic unless bench proves authority side effects",
        "```",
        "",
        "## Current Boundary Position",
        "",
        "```text",
        "required:",
        "  run qualify",
        "  bypass/EST authority",
        "  conversion equation",
        "  rolling state",
        "  $3FE8/$3FE6 paired write",
        "  dropout safe state",
        "",
        "bench-gated:",
        "  $3FEC->$3FE4 mirror",
        "  EST monitor/fault behavior",
        "  exact first-event seed",
        "  exact physical authority trigger",
        "  final postprocess units",
        "",
        "optional if MON-A:",
        "  Error 42 accumulation path",
        "  diagnostic-only EST monitor behavior",
        "```",
        "",
        "## Stop Condition",
        "",
        "No ASM spark handoff stub until this boundary can be exercised against bench traces and each bench-gated item is classified.",
        "",
        "The next safe artifact is documentation under:",
        "",
        "```text",
        "source/minimal_os/spark/README.md",
        "```",
        "",
        "That README may define module layout and API contracts. It must not implement `SPARK_WRITE` yet.",
    ]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-md", required=True)
    parser.add_argument("--out-csv", required=True)
    parser.add_argument("--require", action="append", default=[
        "docs/contracts/SPARK_CONVERSION_EQUATION.md",
        "docs/contracts/SPARK_LA906_OUTPUT_SEQUENCE.md",
        "docs/contracts/SPARK_ROLLING_STATE_MODEL.md",
        "docs/contracts/SPARK_INIT_STATE.md",
        "docs/contracts/SPARK_BYPASS_EST_TRANSITION.md",
        "docs/contracts/SPARK_EST_FAULT_MONITOR_CONTRACT.md",
    ])
    args = parser.parse_args()

    for dep in args.require:
        require(dep)
    write_csv(resolve(args.out_csv))
    write_md(resolve(args.out_md))
    print(f"spark minimal module boundary rows: {len(ROWS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
