#!/usr/bin/env python3
"""Build a provisional spark timing unit-conversion contract.

This tool organizes the static conversion stages between degree-domain spark state
and the timing-domain D value consumed at 0xAB97 in LA906. It intentionally does
not emulate the full routine yet.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

STAGES = [
    {
        "stage":"degree_accumulator",
        "pc":"0xA81B",
        "mnemonic":"STD",
        "operands":"L01FD",
        "input_symbol":"L01FC/L020B/modifiers",
        "input_candidate_unit":"spark degrees / scaled degree-domain",
        "output_symbol":"L01FD",
        "output_candidate_unit":"final spark advance, degree-domain",
        "operation":"store final spark after low-octane/base/modifier path",
        "constant":"",
        "scale_candidate":"unknown; likely GM scaled spark degrees",
        "physical_interpretation":"final software spark accumulator before bridge",
        "confidence":"medium_high_static",
        "notes":"L01FD is labeled FINAL SPK ADV in multiple source comments",
    },
    {
        "stage":"degree_to_signed_offset",
        "pc":"0xAA1A-0xAA30",
        "mnemonic":"LDD/STD/SUBD/ADDD",
        "operands":"L01FD,L01EE",
        "input_symbol":"L01FD",
        "input_candidate_unit":"degree-domain final spark",
        "output_symbol":"L01EE",
        "output_candidate_unit":"signed current retard/offset, degree-domain until conversion",
        "operation":"transform final spark into current retard/2s-complement offset state",
        "constant":"",
        "scale_candidate":"same degree-domain scale as L01FD until conversion",
        "physical_interpretation":"software advance/retard error or offset to schedule",
        "confidence":"medium_static",
        "notes":"L01EE comments: CURRENT RETARD (2's CMP)",
    },
    {
        "stage":"knock_low_octane_fold_in",
        "pc":"0xA811,0xAABC-0xAAD8",
        "mnemonic":"SUBB/ADDA/STAA/LDD/STD",
        "operands":"L020B,L020C,L01EE",
        "input_symbol":"L020B/L020C",
        "input_candidate_unit":"degree-domain retard",
        "output_symbol":"L01FD/L01EE",
        "output_candidate_unit":"degree-domain after retard corrections",
        "operation":"subtract or add retard sources before timing conversion",
        "constant":"",
        "scale_candidate":"same as spark degree-domain variables",
        "physical_interpretation":"retarding spark before conversion to time",
        "confidence":"medium_high_static",
        "notes":"L020B low octane spark retard; L020C DEG,KNOCK RETARD",
    },
    {
        "stage":"sign_magnitude_transform",
        "pc":"0xAB47-0xAB50",
        "mnemonic":"LDD/BPL/BSET/NEGB/CLRA",
        "operands":"L01EE,L004F,#$01",
        "input_symbol":"L01EE",
        "input_candidate_unit":"signed degree-domain offset",
        "output_symbol":"B with L004F bit0 sign",
        "output_candidate_unit":"magnitude plus sign flag",
        "operation":"if negative set L004F bit0 and negate B; clear A",
        "constant":"0x01",
        "scale_candidate":"8-bit magnitude used for multiply",
        "physical_interpretation":"separate advance/retard direction from magnitude",
        "confidence":"medium_static",
        "notes":"comment indicates 1 = retard and 0 = advance in existing contract; verify with source/bench",
    },
    {
        "stage":"startup_override_magnitude",
        "pc":"0xAB55-0xAB5B",
        "mnemonic":"LDAB/MUL/STD",
        "operands":"L01F2, stack",
        "input_symbol":"L01F2",
        "input_candidate_unit":"startup spark degree-domain",
        "output_symbol":"D",
        "output_candidate_unit":"startup-derived magnitude before period multiply",
        "operation":"startup path can replace/scale the normal B magnitude",
        "constant":"",
        "scale_candidate":"startup-specific; bench required",
        "physical_interpretation":"crank/startup spark is not necessarily normal final spark",
        "confidence":"medium_static",
        "notes":"L01F2 labeled START UP SPARK; path controlled by flags before LAB69",
    },
    {
        "stage":"latency_lookup",
        "pc":"0xAB69-0xAB72",
        "mnemonic":"LDAA/LDX/JSR/STAA",
        "operands":"L0062,#$454A,LF499,L0201",
        "input_symbol":"L0062/table_$454A",
        "input_candidate_unit":"RPM/25 index",
        "output_symbol":"L0201",
        "output_candidate_unit":"latency correction / tick correction candidate",
        "operation":"2D lookup indexed by engine RPM/25 stores latency correction",
        "constant":"table $454A",
        "scale_candidate":"table units unknown; subtracted from B after multiply",
        "physical_interpretation":"EST/module latency or scheduling latency compensation",
        "confidence":"medium_static",
        "notes":"L0201 is subtracted at 0xAB84",
    },
    {
        "stage":"degree_period_multiply",
        "pc":"0xAB76-0xAB79",
        "mnemonic":"LDX/JSR",
        "operands":"#$005F,LF550",
        "input_symbol":"B magnitude, L005F",
        "input_candidate_unit":"degree magnitude and last DRP/ref period basis",
        "output_symbol":"D",
        "output_candidate_unit":"time/tick-domain intermediate",
        "operation":"multiply 8-bit spark magnitude against 16-bit period basis using LF550",
        "constant":"X=$005F",
        "scale_candidate":"likely 8x16 fixed-point multiply; exact LF550 contract still needed",
        "physical_interpretation":"convert degrees to a time offset using current engine period",
        "confidence":"medium_static",
        "notes":"key unresolved math helper; create MATH_HELPER_LF550 if unit remains ambiguous",
    },
    {
        "stage":"latency_subtract",
        "pc":"0xAB84",
        "mnemonic":"SUBB",
        "operands":"L0201",
        "input_symbol":"L0201",
        "input_candidate_unit":"latency correction",
        "output_symbol":"D/B",
        "output_candidate_unit":"time/tick-domain minus latency",
        "operation":"subtract latency lookup from low byte of multiply result",
        "constant":"",
        "scale_candidate":"same low-byte units as LF550 output",
        "physical_interpretation":"compensate output timing for latency",
        "confidence":"medium_static",
        "notes":"borrow/carry behavior through following operations needs exact emulation",
    },
    {
        "stage":"period_anchor_subtract",
        "pc":"0xAB8E-0xAB96",
        "mnemonic":"SUBD/LSRD/ORAA",
        "operands":"L3FC0, four LSRD, #$F0",
        "input_symbol":"L3FC0",
        "input_candidate_unit":"ASIC REF/DRP period or capture count",
        "output_symbol":"D_AB97",
        "output_candidate_unit":"timing-domain offset before rolling anchor add",
        "operation":"subtract period/timebase term, shift right 4, set high nibble marker/sign bits",
        "constant":"0xF0, shift /16",
        "scale_candidate":"(multiply_result - L3FC0) >> 4 with high-nibble tagging",
        "physical_interpretation":"forms LA906-ready timing offset relative to rolling anchor",
        "confidence":"medium_static",
        "notes":"exact signed interpretation of ORAA #$F0 must be bench/emulation-confirmed",
    },
    {
        "stage":"la906_sink",
        "pc":"0xAB97",
        "mnemonic":"ADDD",
        "operands":"L3FF6",
        "input_symbol":"D_AB97,L3FF6",
        "input_candidate_unit":"timing-domain offset plus rolling EST fall counter",
        "output_symbol":"D",
        "output_candidate_unit":"absolute/rolling ASIC timing command candidate",
        "operation":"add rolling anchor L3FF6",
        "constant":"",
        "scale_candidate":"same timebase as LA906 ASIC timing writes, exact count/us pending",
        "physical_interpretation":"bridge from conversion result into ASIC spark scheduling sequence",
        "confidence":"high_static_sink_low_physical_units",
        "notes":"D is not raw spark degrees at this point",
    },
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else repo_root() / p


def write_csv(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["stage","pc","mnemonic","operands","input_symbol","input_candidate_unit","output_symbol","output_candidate_unit","operation","constant","scale_candidate","physical_interpretation","confidence","notes"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(STAGES)


def write_md(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# Spark Timing Unit Conversion",
        "",
        "## Purpose",
        "",
        "Document how degree-domain spark/retard state is converted into the timing-domain value consumed by `LA906` at `0xAB97`.",
        "",
        "This is an equation/units contract, not a spark writer.",
        "",
        "## Known Sink",
        "",
        "```text",
        "0xAB97  ADDD L3FF6",
        "```",
        "",
        "At this point, `D` is no longer raw spark degrees. It is a timing-domain offset or absolute/rolling timing value input to the LA906 bridge.",
        "",
        "## Known Upstream Chain",
        "",
        "```text",
        "L01FD final spark advance",
        "→ L01EE current retard/signed offset state",
        "→ sign/magnitude transform using L004F bit0",
        "→ latency lookup result L0201",
        "→ multiply against DRP/ref period basis L005F",
        "→ subtract latency",
        "→ combine with L3FC0 / period term",
        "→ D at 0xAB97",
        "```",
        "",
        "## Candidate Units",
        "",
        "| Symbol | Candidate unit | Evidence | Confidence |",
        "|---|---|---|---|",
        "| `L01FD` | spark degrees, likely GM-scaled | labels `FINAL SPK ADV` | medium-high |",
        "| `L01EE` | signed spark/retard offset | feeds sign/magnitude conversion before `LA906` | medium |",
        "| `L005F` | last DRP/ref period basis | `LDX #$005F` before `LF550` multiply | medium |",
        "| `L0201` | latency correction | RPM-indexed lookup, then `SUBB L0201` | medium |",
        "| `L3FC0` | ASIC timing/period source | `SUBD L3FC0` before sink | medium |",
        "| `D at 0xAB97` | timing-domain offset/command input | feeds LA906 rolling timing math | high static / physical unit pending |",
        "",
        "## Equation Candidate",
        "",
        "Provisional form:",
        "",
        "```text",
        "D_AB97 = f(L01EE, L005F, L0201, L3FC0)",
        "```",
        "",
        "More concrete static shape:",
        "",
        "```text",
        "spark_mag = abs_or_startup_override(L01EE, L01F2, L004F bit0)",
        "latency = lookup_$454A(RPM/25) → L0201",
        "period_basis = L005F",
        "period_anchor = L3FC0",
        "mult = LF550(spark_mag, period_basis)",
        "D_AB97 ≈ ((mult - latency - period_anchor) >> 4) with high-nibble/sign tagging",
        "```",
        "",
        "Do not treat this as final executable math yet. `LF550` return scaling, borrow behavior around `SUBB L0201`, and the meaning of `ORAA #$F0` still need helper-level trace or bench proof.",
        "",
        "## Static Conversion Stages",
        "",
        "| Stage | PC | Operation | Input | Output | Scale candidate | Confidence |",
        "|---|---|---|---|---|---|---|",
    ]
    for s in STAGES:
        md.append(f"| {s['stage']} | `{s['pc']}` | {s['operation']} | `{s['input_symbol']}` | `{s['output_symbol']}` | {s['scale_candidate']} | {s['confidence']} |")
    md += [
        "",
        "## LF550 Helper Gate",
        "",
        "The high-value unresolved item is the call at:",
        "",
        "```text",
        "0xAB76  LDX #$005F",
        "0xAB79  JSR LF550",
        "```",
        "",
        "The next static sub-target is to define `LF550`:",
        "",
        "```text",
        "Does LF550 implement 8x16 multiply?",
        "Does it divide or normalize by 256?",
        "Which register carries the 8-bit spark magnitude?",
        "Where does the 16-bit product return?",
        "Does it preserve X as pointer to L005F or consume memory at X?",
        "```",
        "",
        "If this contract remains fuzzy after bench, add `docs/contracts/MATH_HELPER_LF550.md` before any spark writer work.",
        "",
        "## Bench Sanity Math",
        "",
        "At a given RPM:",
        "",
        "```text",
        "seconds_per_degree = 60 / (RPM × 360)",
        "```",
        "",
        "At 1000 RPM:",
        "",
        "```text",
        "1 crank degree = 166.667 us",
        "5 degrees = 833.333 us",
        "```",
        "",
        "If spark uses the same 1/65536-second timebase as EFI PW, then:",
        "",
        "```text",
        "1 count = 15.258789 us",
        "5 degrees at 1000 RPM ≈ 54.6 counts",
        "5 degrees at 2000 RPM ≈ 27.3 counts",
        "```",
        "",
        "Do **not** assume this timebase. Use it as a bench clue: if a +5° step at 1000 RPM moves the LA906 timing-domain value by about 55 counts and the delta halves at 2000 RPM, the units are likely close to 1/65536 second.",
        "",
        "## Required New-OS Boundary",
        "",
        "Current static evidence supports this future boundary:",
        "",
        "```text",
        "minimal spark strategy produces desired/final spark in degree-domain",
        "conversion layer computes LA906-ready timing-domain offset using period and latency",
        "LA906 bridge maintains rolling ASIC state and writes $3FE8/$3FE6/$3FF6/$3FDC/$3FE4",
        "```",
        "",
        "Future API options:",
        "",
        "```text",
        "Option A: caller provides final spark degrees; conversion layer produces D_AB97.",
        "Option B: caller provides LA906-ready timing-domain D directly.",
        "Option C: caller maintains stock-compatible L01FD/L01EE/L0201/L01EC/L3FF6/L3FDC state.",
        "```",
        "",
        "## Open Questions",
        "",
        "- Is `L01FD` scaled as whole degrees, half-degrees, or 256/90-degree style units?",
        "- Is `L01EE` advance-positive or retard-positive before the sign split?",
        "- Is `L004F` bit0 the sign of the timing offset in every path?",
        "- Does `L005F` represent 90°, 180°, 360°, or 720° of crank/reference period?",
        "- Is `L0201` EST/module latency in ticks, table-scaled counts, or a subtractive byte correction?",
        "- Does `L3FC0` represent current DRP period, prior event capture, or ASIC timing anchor?",
        "- Is `D_AB97` in the same timebase as EFI PW or a spark-only ASIC count domain?",
        "",
        "## Stop Condition",
        "",
        "Do not write `SPARK_WRITE` until this file can answer:",
        "",
        "```text",
        "For X degrees at Y RPM/ref period, what LA906 input value should be produced?",
        "```",
    ]
    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="source/31/BMHM_HAC_ORG_7100_to_end.asm")
    ap.add_argument("--dependency", default="maps/contracts/spark_degree_to_tick_dependency.csv")
    ap.add_argument("--la906", default="maps/contracts/spark_la906_timing_bridge.csv")
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    args = ap.parse_args()
    # Current first pass uses distilled stage metadata; arguments are retained for reproducible CLI shape.
    write_csv(resolve_path(args.out_csv))
    write_md(resolve_path(args.out_md))
    print(f"wrote {len(STAGES)} timing-unit stages")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
