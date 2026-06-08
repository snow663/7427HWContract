# Spark Magnitude / Degree Scale Test

## Goal

Determine the physical degree scale of the unsigned magnitude `A` passed to `LF550` and confirm the sign convention used by `L004F bit0`.

## Required Signals / Values

- commanded final spark degrees
- `L01FD` final spark candidate
- `L01EE` signed offset / current retard candidate
- `L004F bit0` sign flag
- `A` immediately before `0xAB79 JSR LF550`
- `L005F` period basis
- `LF550` output
- `D_AB97`
- EST output timing relative to REF
- `L020B` low-octane retard if forcing retard
- `L020C` knock retard if forcing knock
- `L01F2` startup spark if testing crank/startup path

## Test Matrix

| Test | Condition | Expected if MAG-A 90°/256 is correct |
|---|---|---|
| fixed RPM, commanded 0° | zero/near-zero offset from reference | `A` near zero or sign transition near zero offset |
| fixed RPM, commanded 5° | stable period | `A ≈ 14` |
| fixed RPM, commanded 10° | stable period | `A ≈ 28`, about double 5° |
| fixed RPM, commanded 20° | stable period | `A ≈ 57`, about double 10° |
| fixed RPM, commanded 30° | stable period | `A ≈ 85` |
| retarded below reference | command crosses signed offset | `L004F bit0` changes state; `A` remains magnitude |
| force knock retard +5° | stable RPM/spark | `L020C`/`L01EE` shift by equivalent scale and EST retards |
| force low-octane retard +5° | stable RPM/spark | `L020B` subtracts before final spark store |
| startup mode | crank/startup state | `L01F2` path modifies or replaces normal magnitude |

## Candidate Scale Checks

### MAG-A: 90°/256 scale

```text
A_expected = round(deg * 256 / 90)
deg = A * 90 / 256
degree_per_count = 0.3515625°
```

Reference points:

```text
5°   → A ≈ 14
10°  → A ≈ 28
20°  → A ≈ 57
30°  → A ≈ 85
40°  → A ≈ 114
```

### MAG-B: 180°/256 scale

```text
A_expected = round(deg * 256 / 180)
deg = A * 180 / 256
degree_per_count = 0.703125°
```

Reference points:

```text
5°   → A ≈ 7
10°  → A ≈ 14
20°  → A ≈ 28
30°  → A ≈ 43
40°  → A ≈ 57
```

## Classification

```text
MAG-A:
  A uses 90°/256 scale = 0.3515625°/count.

MAG-B:
  A uses 180°/256 scale = 0.703125°/count.

MAG-C:
  A uses table-native spark units unrelated to simple crank degrees until later.

MAG-D:
  static interpretation of A is wrong.
```

## Procedure

1. Hold RPM/ref period fixed so `L005F` remains stable.
2. Force or command spark values at 0°, 5°, 10°, 20°, and 30° relative to the same reference/bias condition.
3. Capture `L01FD`, `L01EE`, `L004F bit0`, and `A` before `LF550`.
4. Compare measured `A` against MAG-A and MAG-B expected values.
5. Cross the sign boundary by commanding a value below the reference/initial spark offset.
6. Confirm `L004F bit0` changes while `A` remains an unsigned magnitude.
7. Force knock/low-octane retard and observe whether the same scale is used before `L01EE`.
8. Repeat in startup/crank mode and determine whether `L01F2` overrides, multiplies, or clamps the normal magnitude.

## Data To Record

```csv
test_name,rpm_ref_hz,commanded_spark_deg,l01fd,l01ee,l004f_bit0,a_before_lf550,l005f,lf550_output,d_ab97,est_offset_deg,path_result,notes
```

## Pass Criteria

```text
MAG-A confirmed if:
  A follows round(deg * 256 / 90) across 5/10/20/30° tests,
  L004F bit0 changes with signed advance/retard direction,
  A remains unsigned magnitude,
  LF550 output changes proportionally with A at fixed L005F.
```

## Fail / Stop Conditions

Stop and preserve trace if:

- `A` does not correlate with commanded spark degrees.
- `A` follows a different scale such as 180°/256.
- `L004F bit0` does not match the documented `1=retard, 0=advance` sign convention.
- startup mode bypasses the normal `L01FD/L01EE` path entirely.
- knock/low-octane retard enters after `LF550` rather than before magnitude conversion.

## Next Step After Classification

If MAG-A is confirmed or remains the strongest static candidate, create the combined provisional equation contract:

```text
docs/contracts/SPARK_CONVERSION_EQUATION.md
maps/contracts/spark_conversion_equation.csv
tests/static/spark_conversion_vectors.csv
```

That contract should combine:

```text
spark_mag_u8 = round(degrees * 256 / 90)
LF550 = round((spark_mag_u8 * L005F) / 256)
latency L0201
period anchor L3FC0
LA906 input D
```

Still do not create `SPARK_WRITE` until ASIC handoff behavior is bench-classified.
