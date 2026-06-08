# Spark Conversion Equation Test

## Goal

Test the provisional static equation from desired spark degrees to the timing-domain value entering `LA906`, without creating a spark writer.

## Equation Under Test

Known static math:

```text
A_count = round(abs(spark_offset_deg) * 256 / 90)

spark_time_delta = round((A_count * L005F) / 256)
```

Conservative postprocess boundary:

```text
D_AB97 = stock_postprocess(
    spark_time_delta,
    L0201 latency,
    L3FC0 anchor,
    L004F bit0 sign
)
```

The postprocess portion is not yet locked.

## Required Signals / Values

- commanded spark offset degrees
- `A` before `LF550`
- `L005F/L0060` period basis
- `LF550` output
- `L0201` latency correction
- `L3FC0` anchor/source term
- `L004F bit0` sign flag
- `D_AB97` before `ADDD L3FF6`
- LA906 writes to `$3FE8/$3FE6/$3FDC/$3FF6`
- EST output timing relative to REF

## Static Vector File

Use:

```text
tests/static/spark_conversion_vectors.csv
```

These vectors verify only:

```text
A_count = round(deg * 256 / 90)
LF550 = round((A_count * period_basis) / 256)
```

They intentionally do not claim final `D_AB97` until latency, anchor, and sign packing are proven.

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| fixed RPM, command 0° | stable period | `A=0`, LF550 output zero |
| fixed RPM, command 5° | stable period | `A≈14`, LF550 output matches vector |
| fixed RPM, command 10° | stable period | `A≈28`, LF550 output about double 5° |
| fixed RPM, command 20° | stable period | `A≈57`, LF550 output about double 10° |
| fixed RPM, command 30° | stable period | `A≈85`, LF550 output matches vector |
| double RPM | same command, period halves | `L005F` roughly halves; LF550 output roughly halves |
| force latency +N | same spark/period | `L0201` changes; `D_AB97` shifts through postprocess |
| sign crossing | command below reference/bias | `L004F bit0` flips and output moves opposite direction |
| trace D_AB97 | compare static prediction to register D | determines whether postprocess model is right |

## Classification

```text
EQ-A:
  static equation predicts D_AB97 within rounding.

EQ-B:
  equation predicts LF550 output but not postprocess; L0201/L3FC0/sign packing unresolved.

EQ-C:
  A scale and LF550 are correct, but L005F period unit differs from assumption.

EQ-D:
  static model incomplete.
```

## Procedure

1. Hold RPM/ref period fixed and command 0/5/10/20/30° spark offsets.
2. Capture `A` before `LF550` and verify it follows the 256/90 scale.
3. Capture `L005F` and verify `LF550` output with the static formula.
4. Double RPM/ref rate and verify `L005F` and `LF550` output roughly halve.
5. Force or modify latency if practical and capture how `L0201` changes `D_AB97`.
6. Cross the sign boundary and verify `L004F bit0` changes direction while magnitude remains unsigned.
7. Compare predicted `D_AB97` to traced `D_AB97` after including latency/anchor/packing if possible.

## Data To Record

```csv
test_name,rpm_ref_hz,spark_offset_deg,a_before_lf550,l005f,lf550_expected,lf550_measured,l0201,l3fc0,l004f_bit0,d_ab97_predicted,d_ab97_measured,l3fe8,l3fe6,l3fdc,l3ff6,est_offset_deg,path_result,notes
```

## Pass Criteria

```text
EQ-A pass:
  A_count matches 256/90 scale,
  LF550 output matches rounded 8x16 formula,
  D_AB97 prediction matches trace after latency/anchor/sign postprocess.
```

## Partial Pass Criteria

```text
EQ-B pass:
  A_count and LF550 output match,
  but D_AB97 postprocess remains unresolved.
```

## Fail / Stop Conditions

Stop and preserve trace if:

- `A` does not follow 256/90 scale.
- LF550 trace does not match rounded `(A * L005F) / 256`.
- `L005F` does not track RPM/ref period at all.
- `D_AB97` changes with an untracked variable outside this equation.
- LA906 output writes do not correlate with predicted timing-domain movement.

## Next Step

After this equation is bench/emulator classified, the next repo target is:

```text
docs/contracts/SPARK_LA906_OUTPUT_SEQUENCE.md
maps/contracts/spark_la906_output_sequence.csv
docs/tests/SPARK_LA906_OUTPUT_SEQUENCE_TEST.md
```

No `SPARK_WRITE` until both the conversion equation and LA906 output sequence are classified.
