# Spark Timing Unit Conversion Test

## Goal

Bench-check the provisional degree-to-tick conversion between degree-domain spark state and the timing-domain `D` value consumed by `LA906` at `0xAB97`.

## Signals / Values To Capture

- REF input simulator signal
- EST output / ignition control signal
- bypass line if accessible
- RPM/ref period
- `L01FD` final spark candidate
- `L01EE` current retard / signed offset candidate
- `L0201` latency correction candidate
- `L005F` last DRP/ref period work value
- `L3FC0` ASIC timing/period source
- `D_AB97` value before `ADDD L3FF6`, if traceable
- `$3FE6` and `$3FE8` ASIC timing writes
- `$3FF6` and `$3FDC` rolling state

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| fixed RPM, +5° command | stable REF period, increase final spark by 5° | `D_AB97` shifts by a constant tick amount; EST advances |
| fixed RPM, -5° command | stable REF period, decrease final spark by 5° | `D_AB97` shifts opposite direction; EST retards |
| double RPM, same spark step | same +5° command at twice RPM | tick delta per degree shrinks roughly by half |
| same RPM, force latency +N | alter `L0201`/latency table result | `D_AB97` or final handoff shifts by N-equivalent timing correction |
| force knock retard +5° | stable RPM/spark, increase `L020C` | `D_AB97` shifts same direction as retarding spark |
| startup/crank path | crank/startup state | `L01F2` path changes or replaces normal final-spark conversion |
| rolling-state isolation | freeze or log `$3FF6/$3FDC` | determine whether conversion can be isolated from LA906 rolling state |

## Bench Sanity Values

At a given RPM:

```text
seconds_per_degree = 60 / (RPM × 360)
```

At 1000 RPM:

```text
1 crank degree = 166.667 us
5 degrees = 833.333 us
```

If spark uses a 1/65536-second count domain:

```text
1 count = 15.258789 us
5 degrees at 1000 RPM ≈ 54.6 counts
5 degrees at 2000 RPM ≈ 27.3 counts
```

This is a clue only. Do not assume spark uses the same count domain as EFI PW until measured.

## Classification

```text
UNIT-A:
  clean linear degree-to-period conversion found.

UNIT-B:
  conversion is linear but includes latency/table correction.

UNIT-C:
  conversion depends on rolling state and cannot be isolated without LA906 state.

UNIT-D:
  static unit interpretation wrong; need trace/emulation.
```

## Procedure

1. Hold a fixed RPM/ref signal and log baseline `L01FD`, `L01EE`, `L0201`, `L005F`, `L3FC0`, `D_AB97`, `$3FE6`, `$3FE8`, and EST offset.
2. Force final spark +5° and -5° at the same RPM.
3. Repeat the +5° step at 2× RPM.
4. Force/alter `L0201` if possible and observe whether output shifts independent of spark degrees.
5. Force knock retard and observe whether it enters before conversion through `L020C → L01EE`.
6. Run crank/startup mode and determine whether `L01F2` replaces the normal magnitude path.
7. Compare measured EST timing movement against the provisional conversion and sanity-count estimates.

## Data To Record

```csv
test_name,rpm,ref_period_us,final_spark_l01fd,current_retard_l01ee,latency_l0201,l005f,l3fc0,d_ab97,l3ff6,l3fdc,l3fe8,l3fe6,est_offset_deg,delta_d_ab97,delta_est_deg,classification,notes
```

## Pass Criteria

The conversion contract is confirmed enough for the next static step if:

```text
+/- spark degree changes produce signed, repeatable D_AB97 changes,
RPM changes scale D_AB97 delta per degree with period,
latency changes move timing independently of degree command,
and the resulting $3FE6/$3FE8 changes correlate with EST output.
```

## Fail / Stop Conditions

Stop and preserve the trace if:

- `D_AB97` does not change with forced spark degrees.
- `D_AB97` changes with spark but `$3FE6/$3FE8` do not affect EST output.
- RPM/ref period changes do not scale the timing-domain delta.
- `LF550` behavior cannot be inferred from captured values.
- startup/crank uses a separate hardware path not represented by this conversion.

## Next Step After Classification

If UNIT-A or UNIT-B is confirmed, create:

```text
docs/contracts/MATH_HELPER_LF550.md
maps/contracts/math_helper_lf550.csv
```

If UNIT-C is confirmed, define the rolling-state dependency before any spark writer.

No `SPARK_WRITE` routine should be created until the physical unit and rolling-state requirements are locked.
