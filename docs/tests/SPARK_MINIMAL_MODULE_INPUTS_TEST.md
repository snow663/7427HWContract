# Spark Minimal Module Inputs Test

## Goal

Verify that the spark input-boundary planning pass defines inputs only and does not imply the spark output path is implementation-ready.

This test validates the planning boundary. It does not implement spark math, write ASIC timing registers, or create a spark writer.

## Required Files

```text
docs/contracts/SPARK_MINIMAL_MODULE_INPUTS.md
maps/contracts/spark_minimal_module_inputs.csv
tools/build_spark_minimal_module_inputs.py
```

## Required Static Checks

| Test | Expected |
|---|---|
| no spark writer | no `SPARK_WRITE` file/symbol is created by this pass |
| no ASM | no `source/minimal_os/spark/*.asm` file is created |
| no direct timing writer | no direct `$3FE8/$3FE6` writer is introduced |
| no rolling-state writer | no direct `$3FF6/$3FDC` writer is introduced |
| no EST authority code | no physical EST/bypass control code is introduced |
| LA906 output sequence | remains bench-gated |
| base spark input | represented |
| startup spark input | represented |
| latency/timebase inputs | represented |
| bypass/EST authority state | represented as input/gate only |
| rolling-state seed | represented and bench-gated |
| EST monitor state | represented as optional/bench-gated |
| trans/EGR/EVAP | not marked required |
| unknowns | listed, not guessed |
| calibration-only promotion | no calibration section promotes itself to required |

## Command

```bash
python tools/build_spark_minimal_module_inputs.py \
  --cal-index maps/contracts/calibration_source_index.csv \
  --out-md docs/contracts/SPARK_MINIMAL_MODULE_INPUTS.md \
  --out-csv maps/contracts/spark_minimal_module_inputs.csv
```

## Must Remain Forbidden

```text
SPARK_WRITE
spark_handoff.asm
spark_convert.asm
direct $3FE8/$3FE6 writer
direct $3FF6/$3FDC rolling-state writer
physical EST/bypass authority code
```

## Required Input Presence

The CSV must include rows for:

```text
RPM / engine speed
MAP / load
crank/run state
bypass/EST authority state
reference/DRP period basis
desired base spark table
startup spark
coolant spark modifier
spark latency correction
spark magnitude scale
degree-to-time conversion dependency
rolling timing state seed
spark enable / dropout safe state
```

## Bench-Gated Output Dependencies

The contract must keep these bench-gated:

```text
physical EST/bypass authority trigger
$3FE8/$3FE6 exact physical role
$3FF6/$3FDC first-event seed
$3FEC->$3FE4 mirror/ack requirement
final LA906 packing/sign behavior
EST fault monitor side effects
knock-retard hardware behavior
```

## Exclusion Discipline

These must not be required for first minimal OS:

```text
transmission torque-management spark
transmission-related retard
EGR spark correction
EVAP/emissions spark modifiers
diagnostic-only spark behavior unless it affects hardware authority or safe state
```

## Pass Criteria

```text
PASS:
  all required input categories are represented.
  output handoff remains bench-gated.
  no writer or ASM file is created.
  no direct ASIC timing register writer is introduced.
  trans/EGR/EVAP spark-adjacent sections are excluded.
  unknown inputs remain visible.
  no calibration-only row marks itself required without a hardware/source dependency.
```

## Fail / Rework Criteria

```text
REWORK:
  any file or row implies direct spark output implementation is ready.
  any direct $3FE8/$3FE6/$3FF6/$3FDC writer appears.
  physical EST/bypass authority is treated as solved.
  EGR/trans/EVAP spark modifiers are promoted to required.
  unknown spark-adjacent calibration sections are silently guessed.
```

## Next Planning Artifact

After this pass, continue with:

```text
IAC_MINIMAL_MODULE_INPUTS
```
