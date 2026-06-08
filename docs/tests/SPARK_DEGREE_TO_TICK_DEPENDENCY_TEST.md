# Spark Degree-to-Tick Dependency Bench Test

## Goal

Determine how degree-domain spark/retard variables become the timing-domain value consumed by `LA906`, and define the future minimal-OS spark API boundary.

## Required Signals

- REF input simulator signal
- EST output / ignition control signal
- bypass line if accessible
- final spark RAM candidate (`L01FD`)
- current retard / LA906 source candidate (`L01EE`)
- LA906 entry value in `D` at or before `0xAB97`, if traceable
- latency correction candidate (`L0201`)
- timing correction candidate (`L01EC`)
- REF/DRP period source (`L3FC0`)
- rolling state (`L3FF6`, `$3FDC`)
- ASIC timing writes (`$3FE6`, `$3FE8`)
- knock retard variable (`L020C`)
- low-octane retard variable (`L020B`)
- startup spark variable (`L01F2`)

## Test Matrix

| Test | Condition | Expected if D2T-A/D2T-B static read is correct |
|---|---|---|
| fixed RPM, spark +5° | stable REF period, force final spark higher | `L01FD/L01EE` move in degree-domain; LA906 entry D and `$3FE6/$3FE8` move in time-domain |
| fixed RPM, spark -5° | stable REF period, force final spark lower | opposite timing-domain movement from +5° step |
| fixed spark, RPM sweep | hold final spark constant, change REF period | degree-domain vars stay mostly constant; LA906 entry D and ASIC writes scale with period |
| knock retard forced | stable RPM/spark, force knock retard | `L020C` changes; `L01EE`/LA906 input retard accordingly; EST output retards |
| low-octane retard forced | stable RPM/spark, force `L020B` | `L01FD` changes before conversion; EST output retards |
| startup/crank mode | crank/startup state | `L01F2` path affects or replaces normal final spark path |
| latency value forced | stable RPM/spark, alter latency table/result | `L0201` changes output timing independent of degree-domain spark |
| rolling state freeze | freeze `$3FF6` or `$3FDC` if possible | timing jitters, locks, or breaks if rolling state is required |

## Classification

```text
D2T-A:
  final spark degrees feed a clear degree-to-tick conversion before LA906.

D2T-B:
  LA906 consumes an already converted tick-domain value.

D2T-C:
  final spark and rolling state are interleaved; minimal OS must maintain stock-style intermediate variables.

D2T-D:
  bench timing does not correlate with traced variables; static interpretation incomplete.
```

## Procedure

1. Run a fixed-RPM reference signal and capture baseline `L01FD`, `L01EE`, `L0201`, `L3FC0`, `$3FF6`, `$3FDC`, `$3FE6`, and `$3FE8`.
2. Step final spark by +5° and -5° while holding RPM fixed.
3. Hold final spark fixed and sweep RPM/reference period.
4. Force or simulate knock retard and record where the retard enters the dependency chain.
5. Force startup/crank mode and record whether `L01F2` bypasses normal `L01FD` behavior.
6. Force or alter the latency table/result if practical and observe whether output shifts independent of spark degrees.
7. Record EST output timing relative to REF for every test.

## Data To Record

```csv
test_name,rpm_ref_hz,final_spark_candidate_l01fd,current_retard_l01ee,latency_l0201,knock_l020c,low_octane_l020b,startup_l01f2,l3fc0,la906_entry_d,l3ff6,l3fdc,l3fe8,l3fe6,est_offset_deg,path_result,notes
```

## Pass Criteria

The dependency contract is confirmed if:

```text
degree-domain changes move L01FD/L01EE first,
RPM/ref-period changes scale the timing-domain value entering LA906,
latency correction moves output timing after the multiply/period conversion,
and $3FE6/$3FE8 changes correlate with measured EST output timing.
```

## Fail / Stop Conditions

Stop and preserve the trace if:

- EST output timing does not correlate with `L01FD`, `L01EE`, or LA906 entry `D`.
- `$3FE6/$3FE8` do not correlate with EST timing but another register does.
- `$3FF6` or `$3FDC` freeze has no effect despite static rolling-state evidence.
- startup/crank behavior bypasses this path entirely.

## Next Step After Classification

If D2T-A/B/C are confirmed, the next repo target is a narrow conversion contract:

```text
docs/contracts/SPARK_TIMING_UNIT_CONVERSION.md
maps/contracts/spark_timing_unit_conversion.csv
```

No spark writer should be created until the conversion units and rolling-state requirements are known.
