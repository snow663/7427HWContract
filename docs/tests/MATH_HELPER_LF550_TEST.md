# LF550 Math Helper Test

## Goal

Determine and preserve the exact operation performed by `LF550` so the spark degree-to-tick conversion can be implemented without carrying unnecessary stock-code baggage.

## Static Classification Under Test

```text
input:
  A = unsigned 8-bit multiplier/scalar
  X = pointer to unsigned 16-bit multiplicand

output:
  D = rounded upper 16 bits of A * [X:X+1]

equation:
  D = round((A * M16) / 256)
  D ≈ (A * M16 + 0x80) >> 8
```

## Static Tests

1. Slice full helper body from `0xF550` through `0xF563`.
2. Confirm `A` is saved at entry as the multiplier.
3. Confirm `1,X` and `0,X` are read as low/high bytes of the 16-bit multiplicand.
4. Confirm two HC11 `MUL` instructions are used.
5. Confirm `ADCA #$00` is used for rounding/carry propagation.
6. Confirm return value is in `D` / `A:B`.
7. Confirm no saturation exists inside `LF550`.
8. Inventory all callers and compare call-site comments/post-call usage.

## Static Vector File

Use:

```text
tests/static/lf550_vectors.csv
```

The vectors are based on the locked helper equation but should still be verified in an emulator or trace harness before using in a final spark writer.

## Emulator Tests

Run `LF550` in isolation if possible.

| Test | A multiplier | X points to | Expected |
|---|---:|---:|---:|
| zero magnitude | `$00` | `$1000` | `$0000` |
| unit magnitude | `$01` | `$1000` | `$0010` |
| five-count magnitude | `$05` | `$1000` | `$0050` |
| half operand | `$10` | `$0800` | `$0080` |
| round down edge | `$01` | `$007F` | `$0000` |
| round up edge | `$01` | `$0080` | `$0001` |
| max product | `$FF` | `$FFFF` | `$FEFF` |

## Bench Correlation

At fixed RPM, force a spark magnitude step and compare observed `LA906` entry delta against predicted `LF550` output:

```text
predicted_mult = round((spark_mag_u8 * L005F_period_basis_u16) / 256)
```

Then vary RPM/ref period with the same spark magnitude. If `L005F` is the period basis, predicted output should scale with the period value.

## Pass Criteria

```text
LF550-PASS:
  isolated/emulated helper output matches all static vectors
  no saturation is observed
  rounding boundary behaves as expected at 0x007F/0x0080 for A=1
  spark-path LA906 input movement matches the helper output trend
```

## Fail Criteria

```text
LF550-FAIL:
  return value is not D
  helper uses signed input unexpectedly
  helper saturates or clamps
  rounding differs from the vector model
  caller input register is not A in the spark path
```

## Impact On Spark Conversion

If this test passes, update `SPARK_TIMING_UNIT_CONVERSION.md` so:

```text
mult = LF550(spark_mag, period_basis)
```

becomes:

```text
mult = round((spark_mag_u8 * period_basis_u16) / 256)
```

This still does not permit a final spark writer. Remaining blockers:

```text
unit of spark_mag_u8
unit/timebase of L005F
meaning of L3FC0 subtraction
meaning of L0201 latency table units
LA906 rolling-state and ASIC handoff behavior
```
