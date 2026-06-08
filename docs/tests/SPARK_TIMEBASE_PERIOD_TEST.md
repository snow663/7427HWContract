# Spark Timebase / Period Test

## Goal

Determine the physical unit of `L005F/L0060`, `$3FC0/$3FC1`, and `L0201`, and decide whether the spark timing conversion can be written algebraically.

## Required Signals / Variables

- REF input frequency
- RPM
- `L005F/L0060`
- `$3FC0/$3FC1`
- `L0201`
- `L01EC`
- `L01EE`
- D at `0xAB97` if traceable
- EST output
- final spark candidate `L01FD`
- LA906 writes to `$3FE6` and `$3FE8`
- rolling state `$3FF6` and `$3FDC`

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| fixed spark, 500 rpm | low ref rate | `L005F` large if period-based |
| fixed spark, 1000 rpm | double ref rate | `L005F` roughly half if period-based |
| fixed spark, 2000 rpm | double again | `L005F` roughly half again |
| fixed rpm, +5° spark | same period | `L005F` unchanged, D_AB97 changes |
| fixed rpm, -5° spark | same period | `L005F` unchanged, D_AB97 changes opposite direction |
| fixed rpm, latency table change | same spark/period | `L0201` changes, D_AB97 shifts |
| crank/startup mode | low rpm/startup | startup override path changes spark magnitude source |
| freeze `$3FC0` if possible | stable period | determine whether it is true anchor or derived/status |

## Classification

```text
TB-A:
  L005F is raw or scaled REF/DRP period.

TB-B:
  L005F is filtered/derived RPM period.

TB-C:
  L005F is not period; static interpretation is wrong.

LAT-A:
  L0201 is latency in same unit as LF550 output.

LAT-B:
  L0201 is latency in pre-shift or packed units.

ANCHOR-A:
  L3FC0 is a hardware period/event anchor used before LA906.

ANCHOR-B:
  L3FC0 is not directly part of spark timing conversion.
```

## Numeric Sanity Targets

Assuming a 1/65536-second timebase only as a test hypothesis:

```text
1000 rpm:
  one crank revolution = 60 ms
  90°  = 15 ms  = 983 counts
  180° = 30 ms  = 1966 counts
  360° = 60 ms  = 3932 counts
  720° = 120 ms = 7864 counts

2000 rpm:
  90°  = 7.5 ms = 491.5 counts
  180° = 15 ms  = 983 counts
  360° = 30 ms  = 1966 counts
  720° = 60 ms  = 3932 counts
```

If observed `L005F` at 1000 rpm is near one of these values, or a fixed 16× / 1/16× version, the physical period basis can be inferred.

## Procedure

1. Run a fixed reference signal and capture `L005F`, `$3FC0`, `L0201`, `L01EC`, `L01EE`, and D at `0xAB97`.
2. Hold spark fixed and step RPM from 500 → 1000 → 2000.
3. Verify whether `L005F` and `$3FC0` scale with period.
4. Hold RPM fixed and step spark +5° / -5°.
5. Verify whether `L005F` stays constant while D_AB97 and `$3FE6/$3FE8` move.
6. Force or alter latency table/result if practical.
7. Verify whether `L0201` shifts D_AB97 and measured EST output without changing degree-domain spark.
8. Record whether `$3FC0` behaves as an anchor by observing the effect of freezing or substituting it if the harness allows.

## Data To Record

```csv
test_name,rpm,ref_hz,final_spark_l01fd,current_retard_l01ee,l005f,l3fc0,l0201,l01ec,d_ab97,l3fe8,l3fe6,l3ff6,l3fdc,est_offset_deg,path_result,notes
```

## Pass Criteria

```text
TB-A/LAT-A/ANCHOR-A likely if:
  L005F scales inversely with RPM/ref frequency,
  L0201 shifts D_AB97 in the same numeric family as LF550 output,
  L3FC0 movement changes D_AB97 or LA906 timing output,
  and measured EST offset follows predicted timing-domain changes.
```

## Fail / Stop Conditions

Stop and preserve the trace if:

- `L005F` does not change with RPM/ref period.
- D_AB97 does not change with spark steps at fixed RPM.
- `$3FE6/$3FE8` do not correlate with D_AB97 or measured EST output.
- `$3FC0` appears unrelated to the LA906 conversion despite the static subtraction.
- `L0201` changes but does not affect D_AB97 or measured EST output.

## Next Step After Classification

If `L005F` period basis and `L0201` units are classified, the next repo target is:

```text
docs/contracts/SPARK_CONVERT_DEG_TO_LA906_INPUT.md
source/minimal_os/spark/spark_convert_deg_to_la906_input.asm or .py reference model
tests/static/spark_convert_vectors.csv
```

No final spark writer should be created until LA906 output register effects are bench-classified.
