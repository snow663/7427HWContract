#!/usr/bin/env python3
"""Build the ROM-verified integer conversion contract and legacy angle vectors.

Actual instruction execution is independently checked by test_factory_spark.py.
The angle vectors retain an engineering-scale hypothesis, separate from the
raw machine-word contract and its exact handoff vectors.
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
            rows.append({
                "name": name,
                "spark_deg": f"{deg:g}",
                "sign": sign,
                "period_basis_hex": f"0x{period:04X}",
                "period_basis_dec": str(period),
                "a_expected": str(a),
                "lf550_expected_hex": f"0x{out:04X}",
                "lf550_expected_dec": str(out),
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
    stages=[
        ("raw_command", "D_at_AB3E", "negative = command bit15; magnitude = u8(-low(command)) if negative else low(command)", "magnitude; 004F bit0", "AB3E-AB50"),
        ("startup_gain", "magnitude; 01F2; 0051 bit6", "if bit6 clear: m=u8(high(01F2)+bit7(low(01F2))); magnitude=u8(floor(magnitude*m/256)+1)", "effective magnitude", "AB51-AB61"),
        ("latency", "0062; ROM454A-4558", "F499 clamped unsigned linear interpolation with rounded absolute difference", "byte0201", "AB6A-AB72;F499-F4DD"),
        ("saved_timing", "effective magnitude; 005F; negative; 0201", "t=floor((magnitude*word005F+128)/256); saved=u16((t if negative else -t)-byte0201)", "stack word at SP_at_AB89-1", "AB75-AB8A;F550-F563"),
        ("period_anchor", "read16(3FC0) at AB8E", "anchor=(u16(-period)>>4)|F000; D was cleared independently of saved timing", "D_before_AB97", "AB8B-AB95"),
        ("stack_selection", "anchor; read16(3FF6) at AB97; saved", "candidate=u16(anchor+rolling1); chosen=saved if u16(candidate-saved) bit15 set else candidate", "chosen stack word", "AB97-ABA2"),
        ("first_write", "chosen; read16(3FF6) at ABA4", "first=u16(chosen-rolling2)", "3FE8", "ABA4-ABAA"),
        ("second_write", "first; read16(3FDC) at ABB0; word01EC at ABB3", "second=u16(first+work_read-correction1)", "3FE6", "ABB0-ABBA"),
        ("state_handoff", "word01EC at ABB7; chosen", "write correction2 to 3FDC; restore chosen stack word and write to 3FF6", "3FDC;3FF6", "ABB7-ABC8"),
    ]
    rows=[{"stage":stage,"input":inputs,"operation":operation,"output":output,
           "unit":"raw machine counts; physical timebase unassigned",
           "confidence":"ROM_bytes_and_independent_CPU_replay",
           "source_contract":"FACTORY_SPARK_INTEGER_HANDOFF.md",
           "notes":"PCs="+pcs+"; normal factory path requires 0086 bit6 clear; separate read PCs remain independent inputs"}
          for stage,inputs,operation,output,pcs in stages]
    with out.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def write_md(out: Path, vector_rows: list[dict[str,str]], vector_errors: list[str]) -> None:
    out.parent.mkdir(parents=True,exist_ok=True)
    md="""# Spark conversion equation

Status: **ROM-verified integer behavior with independent CPU replay** for `$AB3E-$ABCA`, with `$0086 bit6` clear. That bit selects the external `$180F` extension, whose implementation remains open. The command entering `$AB3E` is an explicit input; this does not establish the entire upstream spark calculation.

Authority: the 65,536-byte BMHM image, SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`. Full derivation, state producers, admission, initialization, and test scope are in [FACTORY_SPARK_INTEGER_HANDOFF.md](../analysis/FACTORY_SPARK_INTEGER_HANDOFF.md). Executable integer model: `tools/factory_spark.py`; independent ROM replay: `tools/factory_spark_replay.py`.

## Raw conversion

All words wrap modulo 65536; bytes wrap modulo 256. `negative` is command bit15. The magnitude uses only the low byte, negated as an 8-bit byte when `negative` is set. It is not a general absolute-value operation on the whole command word.

If `$0051 bit6` is clear, startup scaling first computes `m = u8(high($01F2) + bit7(low($01F2)))`, then `magnitude = u8(floor(magnitude*m/256) + 1)`. That product is truncated; the following increment is unconditional and can wrap.

`$F499` looks up a byte from the header/table at `$454A-$4558`, using `$0062`. It clamps the input to header `$C0`, interpolates between 16-count cells, rounds the absolute knot difference, and adds or subtracts that adjustment according to slope. `$0201` receives the resulting **byte**.

```text
t = floor((effective_magnitude * word005F + 128) / 256)
saved = u16((t if negative else -t) - byte0201)
```

At `$AB89-$AB8A`, `saved` is pushed as a word. X then addresses that word at `SP_at_AB89-1`.

## Separate anchor and stack selection

D is cleared at `$AB8C-$AB8D`. The following shifts operate on the negated period, independently of `saved`:

```text
anchor = (u16(-read16(3FC0, AB8E)) >> 4) | 0xF000
candidate = u16(anchor + read16(3FF6, AB97))
difference = u16(candidate - saved)
chosen = saved if (difference & 0x8000) else candidate
```

`$AB9C` is BMI: selection tests N alone after the wrapped subtraction. It is not a signed minimum. At period zero, `anchor=$F000`; at period one, `anchor=$FFFF`, so a zero period needs its own case.

The previous provisional equation subtracted `$3FC0` from the timing product and shifted the combined result. **That equation is superseded:** the timing result is saved on the stack while the separate anchor is calculated. `D_AB97` means the anchor before the instruction at `$AB97`, rather than a packed version of the timing product.

## Ordered handoff

```text
first  = u16(chosen - read16(3FF6, ABA4))
write16(3FE8, first)                              # ABAA
second = u16(first + read16(3FDC, ABB0) - word01EC_at_ABB3)
write16(3FE6, second)                             # ABBA
write16(3FDC, word01EC_at_ABB7)                    # ABC0
write16(3FF6, chosen)                             # ABC8
```

Different read PCs are separate model inputs. Equality of repeated hardware readbacks, atomic word sampling, hardware counter motion, and physical output timing are not inferred from a flat memory fixture. The monitor code beginning `$ABCB`, including the later `$3FEC/$3FE4` interaction, is outside this bounded contract.

## Engineering scale and older vectors

The historical degree vectors below check the `256/90` angle-scale hypothesis and the multiply primitive only. They do not validate an arbitrary degrees API, startup gain, latency, the anchor, or the four writes. The complete raw-input handoff vectors are `maps/structure/factory_spark_handoff_vectors.csv`, independently checked by `tests/test_factory_spark.py`.

| Name | Assumed degrees | Period basis | A count | Multiply result |
|---|---:|---:|---:|---:|
"""
    for row in vector_rows:
        md+=f"| {row['name']} | {row['spark_deg']} | {row['period_basis_dec']} | {row['a_expected']} | {row['lf550_expected_dec']} |\n"
    md+="\nHistorical vector arithmetic: "+("FAIL: "+"; ".join(vector_errors) if vector_errors else "PASS")+".\n"
    md+="\nExact software arithmetic is established for the stated inputs and path. Physical units, the external extension, upstream intent calculation, and ASIC output effects remain separate dependencies.\n"
    out.write_text(md,encoding="utf-8")


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
