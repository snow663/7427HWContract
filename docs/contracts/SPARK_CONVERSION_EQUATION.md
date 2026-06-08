# Spark Conversion Equation

## Purpose

Combine the static spark contracts into a provisional equation from desired spark degrees to the timing-domain value consumed by `LA906`.

This is the math boundary only. It does **not** define the ASIC output sequence and does **not** create a spark writer.

## Inputs

| Input | Meaning | Unit | Confidence |
|---|---|---|---|
| `spark_offset_deg` | desired advance/retard offset relative to the stock reference/bias path | crank degrees | medium, API candidate |
| `L005F/L0060` | period basis used by `LF550` | time for DRP/ref period, likely 90° basis | pending bench |
| `L0201` | RPM-indexed latency correction | timing-domain/pre-shift counts candidate | pending bench |
| `L3FC0` | ASIC period/event anchor | timing-domain counts candidate | pending bench |
| `L004F bit0` | sign flag | `1=retard`, `0=advance` | medium-high static |
| `D_AB97` | LA906 entry value before `ADDD L3FF6` | timing-domain packed/postprocessed value | pending bench |

## Source Contracts Merged

```text
SPARK_MAGNITUDE_SCALE_CONTRACT.md
MATH_HELPER_LF550.md
SPARK_TIMEBASE_PERIOD_CONTRACT.md
SPARK_TIMING_UNIT_CONVERSION.md
SPARK_LA906_TIMING_BRIDGE.md
```

## Known Static Math

```text
A_count = round(abs(spark_offset_deg) * 256 / 90)

LF550(A, M16) = round((A * M16) / 256)

spark_time_delta = round((A_count * L005F) / 256)
```

The 90°/256 angle scale is the leading static candidate from repeated `SPK ADV 256/90` comments. `LF550` is already classified as the rounded 8×16 fixed-point multiply helper.

## Provisional LA906 Input

Conservative form:

```text
spark_mag_u8 = round(abs(spark_offset_deg) * 256 / 90)

spark_time_delta = LF550(spark_mag_u8, L005F)

D_AB97 = stock_postprocess(
    spark_time_delta,
    L0201 latency,
    L3FC0 anchor,
    L004F bit0 sign
)
```

Current static candidate:

```text
raw_time = spark_time_delta - L0201 - L3FC0
D_AB97 ≈ pack_or_shift(raw_time, sign=L004F bit0)
```

The exact `pack_or_shift` step is not fully locked. Static rows show four right shifts and high-nibble/sign tagging before `0xAB97`, but that needs bench or emulator confirmation before code generation.

## Static Vector Scope

The first vector set intentionally verifies only the known math:

```text
A_count = round(deg * 256 / 90)
LF550 = round((A_count * period_basis) / 256)
```

It does not lock `L0201`, `L3FC0`, or final `D_AB97` packing yet.

| Name | Spark deg | Period basis | A expected | LF550 expected | Notes |
|---|---:|---:|---:|---:|---|
| `zero_deg` | 0 | `0x03D7` / 983 | 0 | `0x0000` / 0 | 90deg basis at 1000 rpm if 1/65536 sec |
| `five_deg` | 5 | `0x03D7` / 983 | 14 | `0x0036` / 54 | 5deg sanity |
| `ten_deg` | 10 | `0x03D7` / 983 | 28 | `0x006C` / 108 | 10deg sanity |
| `twenty_deg` | 20 | `0x03D7` / 983 | 57 | `0x00DB` / 219 | 20deg sanity |
| `thirty_deg` | 30 | `0x03D7` / 983 | 85 | `0x0146` / 326 | 30deg sanity |
| `forty_deg` | 40 | `0x03D7` / 983 | 114 | `0x01B6` / 438 | 40deg sanity; corrected LF550 math gives 0x01B6 |
| `five_deg_2000rpm` | 5 | `0x01EB` / 491 | 14 | `0x001B` / 27 | period roughly half output roughly half |
| `twenty_deg_2000rpm` | 20 | `0x01EB` / 491 | 57 | `0x006D` / 109 | period roughly half output roughly half |

## Vector Verification Status

```text
status: PASS
static vector math matches the provisional equation
```

## Output Boundary

This contract stops at the value consumed by `LA906`. It does not define which ASIC writes are required at runtime. That remains owned by:

```text
SPARK_LA906_TIMING_BRIDGE.md
SPARK_ASIC_HANDOFF_CONTRACT.md
```

## Bench Required

This equation is static-provisional until bench traces prove:

1. `L005F` physical period unit
2. `L0201` latency unit
3. `L3FC0` anchor meaning
4. sign/high-nibble packing
5. LA906 ASIC write effects

## Current Classification

```text
EQ-A:
  not proven. Static equation predicts the known A_count and LF550 terms.

EQ-B:
  current best status. Equation predicts LF550 output, but postprocess through L0201/L3FC0/sign packing remains unresolved.

EQ-C:
  possible if L005F period unit differs from the 90°/256 assumption.

EQ-D:
  not supported statically, but bench/emulator proof remains required.
```

## Stop Condition

Do not create `SPARK_WRITE` until both this conversion equation and the LA906 output sequence are bench-classified.
