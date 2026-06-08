#!/usr/bin/env python3
"""Build the provisional spark conversion equation contract.

This tool assembles the static equation boundary from prior contract outputs and
checks the static vector math for the known portions:
  A_count = round(abs(deg) * 256 / 90)
  LF550   = round((A_count * period_basis) / 256)

It intentionally does not emulate stock spark code or produce a spark writer.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

DEG_SCALE_DENOMINATOR = 90.0
DEG_SCALE_NUMERATOR = 256.0

DEFAULT_VECTORS = [
    ("zero_deg", 0.0, "advance", 0x03D7, 0x0000, 0x0000, "90deg basis at 1000 rpm if 1/65536 sec"),
    ("five_deg", 5.0, "advance", 0x03D7, 0x0000, 0x0000, "5deg sanity"),
    ("ten_deg", 10.0, "advance", 0x03D7, 0x0000, 0x0000, "10deg sanity"),
    ("twenty_deg", 20.0, "advance", 0x03D7, 0x0000, 0x0000, "20deg sanity"),
    ("thirty_deg", 30.0, "advance", 0x03D7, 0x0000, 0x0000, "30deg sanity"),
    ("forty_deg", 40.0, "advance", 0x03D7, 0x0000, 0x0000, "40deg sanity; corrected LF550 math gives 0x01B6"),
    ("five_deg_2000rpm", 5.0, "advance", 0x01EB, 0x0000, 0x0000, "period roughly half, output roughly half"),
    ("twenty_deg_2000rpm", 20.0, "advance", 0x01EB, 0x0000, 0x0000, "period roughly half, output roughly half"),
]


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def spark_deg_to_a_count(deg: float) -> int:
    return int(round(abs(deg) * DEG_SCALE_NUMERATOR / DEG_SCALE_DENOMINATOR))


def lf550(a_count: int, period_basis: int) -> int:
    return ((a_count * period_basis) + 0x80) >> 8


def parse_hex_or_dec(value: str) -> int:
    value = str(value).strip().lower()
    if value.startswith("0x"):
        return int(value, 16)
    if value.startswith("$"):
        return int(value[1:], 16)
    return int(value, 10)


def ensure_vectors(path: Path) -> list[dict[str, str]]:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        rows = []
        for name, deg, sign, period, latency, anchor, notes in DEFAULT_VECTORS:
            a = spark_deg_to_a_count(deg)
            out = lf550(a, period)
            raw = out - latency - anchor
            rows.append({
                "name": name,
                "spark_deg": f"{deg:g}",
                "sign": sign,
                "period_basis_hex": f"0x{period:04X}",
                "period_basis_dec": str(period),
                "latency_hex": f"0x{latency:04X}",
                "anchor_hex": f"0x{anchor:04X}",
                "a_expected": str(a),
                "lf550_expected_hex": f"0x{out:04X}",
                "lf550_expected_dec": str(out),
                "raw_time_expected": str(raw),
                "notes": notes,
            })
        with path.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(rows)
    with path.open(newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def verify_vectors(rows: list[dict[str, str]]) -> list[str]:
    errors: list[str] = []
    for i, row in enumerate(rows, 2):
        deg = float(row["spark_deg"])
        period = parse_hex_or_dec(row["period_basis_hex"])
        if period != int(row["period_basis_dec"]):
            errors.append(f"row {i}: period hex/dec mismatch")
        expected_a = spark_deg_to_a_count(deg)
        actual_a = int(row["a_expected"])
        if expected_a != actual_a:
            errors.append(f"row {i}: A expected {expected_a}, got {actual_a}")
        expected_lf = lf550(actual_a, period)
        actual_lf = parse_hex_or_dec(row["lf550_expected_hex"])
        if expected_lf != actual_lf or expected_lf != int(row["lf550_expected_dec"]):
            errors.append(f"row {i}: LF550 expected {expected_lf}/0x{expected_lf:04X}, got {row['lf550_expected_hex']}/{row['lf550_expected_dec']}")
    return errors


def write_equation_csv(out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = [
        {
            "stage": "spark_offset_to_magnitude",
            "input": "spark_offset_deg",
            "operation": "A_count = round(abs(spark_offset_deg) * 256 / 90)",
            "output": "spark_mag_u8 / A_count",
            "unit": "90deg/256 scale = 0.3515625 deg/count",
            "confidence": "high_static_pending_bench",
            "source_contract": "SPARK_MAGNITUDE_SCALE_CONTRACT.md",
            "notes": "L01FD/L01EE/A path; L004F bit0 carries sign",
        },
        {
            "stage": "magnitude_times_period",
            "input": "A_count, L005F/L0060",
            "operation": "spark_time_delta = round((A_count * L005F) / 256)",
            "output": "spark_time_delta",
            "unit": "timing-domain candidate; depends on L005F period unit",
            "confidence": "high_static_for_math_medium_for_physics",
            "source_contract": "MATH_HELPER_LF550.md; SPARK_TIMEBASE_PERIOD_CONTRACT.md",
            "notes": "LF550 locked as rounded 8x16 fixed-point multiply",
        },
        {
            "stage": "latency_correction",
            "input": "spark_time_delta, L0201",
            "operation": "subtract latency correction",
            "output": "latency_adjusted_delta",
            "unit": "same/pre-shift timing-domain candidate",
            "confidence": "medium_static_pending_bench",
            "source_contract": "SPARK_TIMING_UNIT_CONVERSION.md",
            "notes": "0xAB72 STAA L0201; 0xAB84 SUBB L0201",
        },
        {
            "stage": "period_anchor_subtract",
            "input": "latency_adjusted_delta, L3FC0",
            "operation": "subtract/combine hardware period anchor",
            "output": "raw_time_pre_pack",
            "unit": "timing-domain candidate",
            "confidence": "medium_static_pending_bench",
            "source_contract": "SPARK_TIMEBASE_PERIOD_CONTRACT.md",
            "notes": "0xAB8E SUBD L3FC0 before four right shifts",
        },
        {
            "stage": "pack_or_shift_for_la906",
            "input": "raw_time_pre_pack, L004F bit0",
            "operation": "stock_postprocess(raw_time, sign); includes four shifts and high-nibble/sign tagging candidate",
            "output": "D_AB97",
            "unit": "LA906 timing-domain input",
            "confidence": "low_medium_static_pending_bench",
            "source_contract": "SPARK_TIMING_UNIT_CONVERSION.md; SPARK_LA906_TIMING_BRIDGE.md",
            "notes": "postprocess not fully locked; keep as stock_postprocess until bench/emulation",
        },
        {
            "stage": "la906_handoff_boundary",
            "input": "D_AB97, L3FF6/L3FDC/L01EC/L3FEC",
            "operation": "LA906 rolling-state bridge",
            "output": "$3FE8/$3FE6/$3FDC/$3FF6/$3FEC->$3FE4",
            "unit": "ASIC timing handoff",
            "confidence": "medium_static_pending_bench",
            "source_contract": "SPARK_LA906_TIMING_BRIDGE.md; SPARK_ASIC_HANDOFF_CONTRACT.md",
            "notes": "owned by output-sequence contract, not by this equation contract",
        },
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_md(out: Path, vector_rows: list[dict[str, str]], vector_errors: list[str]) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# Spark Conversion Equation",
        "",
        "## Purpose",
        "",
        "Combine the static spark contracts into a provisional equation from desired spark degrees to the timing-domain value consumed by `LA906`.",
        "",
        "This is the math boundary only. It does **not** define the ASIC output sequence and does **not** create a spark writer.",
        "",
        "## Inputs",
        "",
        "| Input | Meaning | Unit | Confidence |",
        "|---|---|---|---|",
        "| `spark_offset_deg` | desired advance/retard offset relative to the stock reference/bias path | crank degrees | medium, API candidate |",
        "| `L005F/L0060` | period basis used by `LF550` | time for DRP/ref period, likely 90° basis | pending bench |",
        "| `L0201` | RPM-indexed latency correction | timing-domain/pre-shift counts candidate | pending bench |",
        "| `L3FC0` | ASIC period/event anchor | timing-domain counts candidate | pending bench |",
        "| `L004F bit0` | sign flag | `1=retard`, `0=advance` | medium-high static |",
        "| `D_AB97` | LA906 entry value before `ADDD L3FF6` | timing-domain packed/postprocessed value | pending bench |",
        "",
        "## Source Contracts Merged",
        "",
        "```text",
        "SPARK_MAGNITUDE_SCALE_CONTRACT.md",
        "MATH_HELPER_LF550.md",
        "SPARK_TIMEBASE_PERIOD_CONTRACT.md",
        "SPARK_TIMING_UNIT_CONVERSION.md",
        "SPARK_LA906_TIMING_BRIDGE.md",
        "```",
        "",
        "## Known Static Math",
        "",
        "```text",
        "A_count = round(abs(spark_offset_deg) * 256 / 90)",
        "",
        "LF550(A, M16) = round((A * M16) / 256)",
        "",
        "spark_time_delta = round((A_count * L005F) / 256)",
        "```",
        "",
        "The 90°/256 angle scale is the leading static candidate from repeated `SPK ADV 256/90` comments. `LF550` is already classified as the rounded 8×16 fixed-point multiply helper.",
        "",
        "## Provisional LA906 Input",
        "",
        "Conservative form:",
        "",
        "```text",
        "spark_mag_u8 = round(abs(spark_offset_deg) * 256 / 90)",
        "",
        "spark_time_delta = LF550(spark_mag_u8, L005F)",
        "",
        "D_AB97 = stock_postprocess(",
        "    spark_time_delta,",
        "    L0201 latency,",
        "    L3FC0 anchor,",
        "    L004F bit0 sign",
        ")",
        "```",
        "",
        "Current static candidate:",
        "",
        "```text",
        "raw_time = spark_time_delta - L0201 - L3FC0",
        "D_AB97 ≈ pack_or_shift(raw_time, sign=L004F bit0)",
        "```",
        "",
        "The exact `pack_or_shift` step is not fully locked. Static rows show four right shifts and high-nibble/sign tagging before `0xAB97`, but that needs bench or emulator confirmation before code generation.",
        "",
        "## Static Vector Scope",
        "",
        "The first vector set intentionally verifies only the known math:",
        "",
        "```text",
        "A_count = round(deg * 256 / 90)",
        "LF550 = round((A_count * period_basis) / 256)",
        "```",
        "",
        "It does not lock `L0201`, `L3FC0`, or final `D_AB97` packing yet.",
        "",
        "| Name | Spark deg | Period basis | A expected | LF550 expected | Notes |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for row in vector_rows:
        md.append(f"| `{row['name']}` | {row['spark_deg']} | `{row['period_basis_hex']}` / {row['period_basis_dec']} | {row['a_expected']} | `{row['lf550_expected_hex']}` / {row['lf550_expected_dec']} | {row['notes']} |")
    md += [
        "",
        "## Vector Verification Status",
        "",
    ]
    if vector_errors:
        md += ["```text", "status: FAIL", *vector_errors, "```", ""]
    else:
        md += ["```text", "status: PASS", "static vector math matches the provisional equation", "```", ""]
    md += [
        "## Output Boundary",
        "",
        "This contract stops at the value consumed by `LA906`. It does not define which ASIC writes are required at runtime. That remains owned by:",
        "",
        "```text",
        "SPARK_LA906_TIMING_BRIDGE.md",
        "SPARK_ASIC_HANDOFF_CONTRACT.md",
        "```",
        "",
        "## Bench Required",
        "",
        "This equation is static-provisional until bench traces prove:",
        "",
        "1. `L005F` physical period unit",
        "2. `L0201` latency unit",
        "3. `L3FC0` anchor meaning",
        "4. sign/high-nibble packing",
        "5. LA906 ASIC write effects",
        "",
        "## Current Classification",
        "",
        "```text",
        "EQ-A:",
        "  not proven. Static equation predicts the known A_count and LF550 terms.",
        "",
        "EQ-B:",
        "  current best status. Equation predicts LF550 output, but postprocess through L0201/L3FC0/sign packing remains unresolved.",
        "",
        "EQ-C:",
        "  possible if L005F period unit differs from the 90°/256 assumption.",
        "",
        "EQ-D:",
        "  not supported statically, but bench/emulator proof remains required.",
        "```",
        "",
        "## Stop Condition",
        "",
        "Do not create `SPARK_WRITE` until both this conversion equation and the LA906 output sequence are bench-classified.",
    ]
    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--magnitude", default="maps/contracts/spark_magnitude_scale_contract.csv")
    ap.add_argument("--lf550", default="maps/contracts/math_helper_lf550.csv")
    ap.add_argument("--timebase", default="maps/contracts/spark_timebase_period_contract.csv")
    ap.add_argument("--timing-units", default="maps/contracts/spark_timing_unit_conversion.csv")
    ap.add_argument("--la906", default="maps/contracts/spark_la906_timing_bridge.csv")
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    ap.add_argument("--vectors", required=True)
    args = ap.parse_args()

    # Touch dependencies for path validation in normal repo use.
    for dep in [args.magnitude, args.lf550, args.timebase, args.timing_units, args.la906]:
        p = resolve_path(dep)
        if not p.exists():
            raise FileNotFoundError(p)

    vector_rows = ensure_vectors(resolve_path(args.vectors))
    vector_errors = verify_vectors(vector_rows)
    write_equation_csv(resolve_path(args.out_csv))
    write_md(resolve_path(args.out_md), vector_rows, vector_errors)
    print(f"vectors: {len(vector_rows)}")
    print(f"vector_errors: {len(vector_errors)}")
    return 1 if vector_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
