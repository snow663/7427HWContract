#!/usr/bin/env python3
"""Build the LA906 spark output sequence contract.

This tool documents the downstream output sequence from the LA906 timing-domain
input to ASIC writes/rolling state/handshake candidates. It does not generate a
spark writer.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

SEQUENCE_ROWS = [
    {
        "stage": "entry_input",
        "pc": "0xAB97",
        "mnemonic": "ADDD",
        "operands": "L3FF6",
        "input_value": "D_AB97 from SPARK_CONVERSION_EQUATION + L3FF6 rolling anchor",
        "operation": "D = D_AB97 + L3FF6",
        "output_register": "D",
        "output_value": "first rolling-anchor-adjusted timing value",
        "candidate_role": "event_anchor_update",
        "required_for_minimal_os": "yes_if_la906_path_retained",
        "bench_test": "force D_AB97 delta and observe downstream $3FE8/$3FE6 movement",
        "confidence": "medium_static",
        "notes": "first LA906 arithmetic after conversion equation sink",
    },
    {
        "stage": "first_timing_compute",
        "pc": "0xABA4",
        "mnemonic": "SUBD",
        "operands": "L3FF6",
        "input_value": "D and L3FF6",
        "operation": "D = D - L3FF6 after intermediate stack/control flow",
        "output_register": "D",
        "output_value": "value written to $3FE8",
        "candidate_role": "timing_command_1",
        "required_for_minimal_os": "bench_classify",
        "bench_test": "freeze/force $3FE8; compare EST timing movement",
        "confidence": "medium_static",
        "notes": "$3FE8 write follows this subtract",
    },
    {
        "stage": "write_3fe8",
        "pc": "0xABAA",
        "mnemonic": "STD",
        "operands": "L3FE8",
        "input_value": "D from first_timing_compute",
        "operation": "write first ASIC timing command candidate",
        "output_register": "$3FE8/$3FE9",
        "output_value": "D",
        "candidate_role": "timing_command_1",
        "required_for_minimal_os": "likely_yes_pending_bench",
        "bench_test": "freeze $3FE8 or force known delta at fixed RPM",
        "confidence": "medium_static",
        "notes": "first direct spark/EST timing ASIC write candidate",
    },
    {
        "stage": "second_timing_compute",
        "pc": "0xABB0",
        "mnemonic": "ADDD",
        "operands": "L3FDC",
        "input_value": "D plus $3FDC rolling state",
        "operation": "D = D + L3FDC",
        "output_register": "D",
        "output_value": "second timing pre-correction",
        "candidate_role": "rolling_state_update",
        "required_for_minimal_os": "bench_classify",
        "bench_test": "freeze $3FDC; observe timing stability/jitter",
        "confidence": "medium_static",
        "notes": "$3FDC participates before $3FE6 write and is later updated from X",
    },
    {
        "stage": "second_timing_compute",
        "pc": "0xABB3",
        "mnemonic": "SUBD",
        "operands": "L01EC",
        "input_value": "D and L01EC timing correction/work term",
        "operation": "D = D - L01EC",
        "output_register": "D",
        "output_value": "value written to $3FE6",
        "candidate_role": "latency_adjusted_command",
        "required_for_minimal_os": "bench_classify",
        "bench_test": "vary L01EC if traceable; observe $3FE6 movement",
        "confidence": "medium_static",
        "notes": "final arithmetic before $3FE6 write",
    },
    {
        "stage": "write_3fe6",
        "pc": "0xABBA",
        "mnemonic": "STD",
        "operands": "L3FE6",
        "input_value": "D from second_timing_compute",
        "operation": "write second ASIC timing command candidate",
        "output_register": "$3FE6/$3FE7",
        "output_value": "D",
        "candidate_role": "timing_command_2",
        "required_for_minimal_os": "likely_yes_pending_bench",
        "bench_test": "freeze $3FE6 or force known delta at fixed RPM",
        "confidence": "medium_static",
        "notes": "second direct spark/EST timing ASIC write candidate",
    },
    {
        "stage": "update_3fdc",
        "pc": "0xABC0",
        "mnemonic": "STX",
        "operands": "L3FDC",
        "input_value": "X loaded from L01EC at 0xABB7",
        "operation": "update rolling state with L01EC-derived value",
        "output_register": "$3FDC/$3FDD",
        "output_value": "X = L01EC",
        "candidate_role": "rolling_state_update",
        "required_for_minimal_os": "likely_yes_if_rolling_state_required",
        "bench_test": "freeze $3FDC; observe if EST output drifts, jitters, or locks",
        "confidence": "medium_static",
        "notes": "$3FDC read before $3FE6, then updated after write",
    },
    {
        "stage": "update_3ff6",
        "pc": "0xABC8",
        "mnemonic": "STD",
        "operands": "L3FF6",
        "input_value": "D restored/recomputed after $3FE6 path",
        "operation": "update EST fall counter / rolling anchor",
        "output_register": "$3FF6/$3FF7",
        "output_value": "D",
        "candidate_role": "event_anchor_update",
        "required_for_minimal_os": "likely_yes_if_rolling_anchor_required",
        "bench_test": "freeze $3FF6; observe if timing breaks or loses continuity",
        "confidence": "medium_static",
        "notes": "$3FF6 is read/subtracted and then rewritten in same bridge",
    },
    {
        "stage": "mirror_3fec_to_3fe4",
        "pc": "0xAC28",
        "mnemonic": "LDX",
        "operands": "L3FEC",
        "input_value": "$3FEC ASIC status/source/capture",
        "operation": "read ASIC source/status candidate",
        "output_register": "X",
        "output_value": "$3FEC",
        "candidate_role": "asic_status_read",
        "required_for_minimal_os": "bench_classify",
        "bench_test": "skip mirror path and observe EST/status behavior",
        "confidence": "medium_static",
        "notes": "read side of $3FEC -> $3FE4 mirror/ack candidate",
    },
    {
        "stage": "mirror_3fec_to_3fe4",
        "pc": "0xAC2E",
        "mnemonic": "STX",
        "operands": "L3FE4",
        "input_value": "X loaded from $3FEC",
        "operation": "mirror/ack/write source status to companion target",
        "output_register": "$3FE4/$3FE5",
        "output_value": "X = $3FEC",
        "candidate_role": "asic_ack_mirror",
        "required_for_minimal_os": "likely_yes_if_ack_required",
        "bench_test": "block $3FEC->$3FE4 mirror; observe EST output/fault/status behavior",
        "confidence": "medium_static",
        "notes": "separate mini-contract; could be required hardware acknowledge",
    },
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def touch_required(path: str | Path) -> None:
    p = resolve_path(path)
    if not p.exists():
        raise FileNotFoundError(p)


def write_csv(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["stage", "pc", "mnemonic", "operands", "input_value", "operation", "output_register", "output_value", "candidate_role", "required_for_minimal_os", "bench_test", "confidence", "notes"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(SEQUENCE_ROWS)


def write_md(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# Spark LA906 Output Sequence",
        "",
        "## Purpose",
        "",
        "Classify the ASIC output sequence generated by `LA906`.",
        "",
        "This contract starts after `SPARK_CONVERSION_EQUATION.md` and stops before any minimal spark writer. It documents which writes look like timing commands, rolling state updates, and handshake/mirror behavior.",
        "",
        "## Scope",
        "",
        "`LA906` receives a timing-domain input derived from spark advance, period basis, latency, and anchor correction. This contract describes how that input is converted into ASIC writes.",
        "",
        "## Known Input",
        "",
        "```text",
        "D_AB97 from SPARK_CONVERSION_EQUATION.md",
        "```",
        "",
        "At the first critical output-stage arithmetic:",
        "",
        "```text",
        "0xAB97  ADDD L3FF6",
        "```",
        "",
        "## Static Sequence",
        "",
        "| Stage | PC | Instruction | Candidate role | Required? | Confidence |",
        "|---|---|---|---|---|---|",
    ]
    for r in SEQUENCE_ROWS:
        inst = f"{r['mnemonic']} {r['operands']}".strip()
        md.append(f"| {r['stage']} | `{r['pc']}` | `{inst}` | {r['candidate_role']} | {r['required_for_minimal_os']} | {r['confidence']} |")
    md += [
        "",
        "## Candidate Register Roles",
        "",
        "| Register | Candidate role | Evidence | Confidence |",
        "|---|---|---|---|",
        "| `$3FE8` | first timing command candidate | `STD L3FE8` after `$3FF6` arithmetic | medium |",
        "| `$3FE6` | second timing command candidate | `STD L3FE6` after `$3FDC` and `$01EC` arithmetic | medium |",
        "| `$3FDC` | rolling timing state | read/add before `$3FE6`, later `STX L3FDC` | medium |",
        "| `$3FF6` | rolling anchor / EST fall counter | read/add/sub/update pattern | medium |",
        "| `$3FEC` | ASIC source/status/capture | read before mirror | medium |",
        "| `$3FE4` | mirror/ack target | `STX L3FE4` from `$3FEC` | medium |",
        "",
        "## Static Interpretation",
        "",
        "`$3FE8` and `$3FE6` are not independent random writes. They are separated by rolling-state math:",
        "",
        "```text",
        "D_AB97 + L3FF6        → intermediate",
        "...",
        "intermediate relation → STD $3FE8",
        "",
        "then:",
        "D + L3FDC - L01EC     → STD $3FE6",
        "...",
        "X/D state             → updates $3FDC and $3FF6",
        "...",
        "$3FEC                 → $3FE4",
        "```",
        "",
        "This suggests the minimal spark path probably needs three pieces, not one:",
        "",
        "```text",
        "1. conversion equation:",
        "   degrees → D_AB97",
        "",
        "2. rolling timing-state update:",
        "   maintain $3FF6/$3FDC relationship",
        "",
        "3. ASIC write/mirror sequence:",
        "   write $3FE8/$3FE6 and mirror $3FEC→$3FE4 if required",
        "```",
        "",
        "## Required New-OS Questions",
        "",
        "- Must `$3FE8` and `$3FE6` both be written every spark event?",
        "- Is one register dwell/fall and the other EST edge?",
        "- Is `$3FF6` a rolling event anchor that must stay continuous?",
        "- Is `$3FDC` prior-event state or hardware feedback state?",
        "- Is `$3FEC → $3FE4` a required acknowledge/mirror?",
        "- What happens if `$3FE4` mirror is skipped?",
        "",
        "## Current Static Classification",
        "",
        "```text",
        "SEQ-A ($3FE8 primary):",
        "  possible, but not proven. $3FE8 is the first direct timing write after $3FF6 arithmetic.",
        "",
        "SEQ-B ($3FE6 primary):",
        "  possible, but not proven. $3FE6 is the second direct timing write after $3FDC/L01EC arithmetic.",
        "",
        "SEQ-C ($3FE8/$3FE6 paired):",
        "  strongest static fit. The two writes appear in one continuous timing bridge.",
        "",
        "SEQ-D ($3FF6/$3FDC rolling state required):",
        "  strongly suggested statically by read/update patterns.",
        "",
        "SEQ-E ($3FEC->$3FE4 mirror required):",
        "  plausible. Static sequence shows an explicit read/mirror pair, but function needs bench proof.",
        "",
        "SEQ-F (static interpretation incomplete):",
        "  always possible until scoped/bench traced.",
        "```",
        "",
        "## Output Boundary",
        "",
        "This contract does not own degree-to-tick math. That is owned by:",
        "",
        "```text",
        "SPARK_CONVERSION_EQUATION.md",
        "```",
        "",
        "This contract also does not create a minimal spark writer. If bench confirms the paired command and rolling-state model, the next likely contract is:",
        "",
        "```text",
        "SPARK_ROLLING_STATE_MODEL.md",
        "```",
    ]
    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="source/31/BMHM_HAC_ORG_7100_to_end.asm")
    ap.add_argument("--la906", default="maps/contracts/spark_la906_timing_bridge.csv")
    ap.add_argument("--equation", default="maps/contracts/spark_conversion_equation.csv")
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    args = ap.parse_args()

    for dep in [args.source, args.la906, args.equation]:
        touch_required(dep)
    write_csv(resolve_path(args.out_csv))
    write_md(resolve_path(args.out_md))
    print(f"stages: {len(SEQUENCE_ROWS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
