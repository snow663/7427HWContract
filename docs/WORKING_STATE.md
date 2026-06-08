# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloaded ZIPs as the primary project state. Generated downloads are exports only.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly. The target is a clean minimal OS/control program that preserves required hardware behavior for fuel, spark, idle air, sensors, watchdog/reset, ALDL/debug, and engine protection.

Current technical focus after the bypass/EST pass:

```text
spark module boundary:
  decide whether next pass is SPARK_EST_FAULT_MONITOR_CONTRACT
  or SPARK_MINIMAL_MODULE_BOUNDARY
```

Still no spark writer. Authority transfer, fault handling, and LA906 output effect must be bench-classified before any `SPARK_WRITE` or spark handoff stub.

## Completed contract phase

### Fuel output side

Completed static/provisional contracts:

- `docs/contracts/EFI_PW_3FCE_CONTRACT.md`
- `docs/contracts/EFI_PW_UNITS.md`
- `docs/contracts/EFI_OUTPUT_COMPANION_REGISTERS.md`
- `docs/contracts/EFI_OUTPUT_INIT_STATE.md`
- `docs/contracts/MINIMAL_EFI_PW_WRITER.md`
- `docs/contracts/EFI_OUTPUT_INIT_ROUTINE.md`

Current fuel-output split:

```text
EFI_OUTPUT_INIT:
  one-time ASIC/window/output state

EFI_PW_WRITE:
  runtime EFI pulsewidth command
  D -> STD $3FCE
```

Fuel output is statically clean enough to keep as a two-layer skeleton. Bench confirmation is still required before treating `$3FCE` as fully proven hardware control.

### Spark output side

Completed static/provisional contracts:

- `docs/contracts/SPARK_ASIC_HANDOFF_CONTRACT.md`
- `docs/contracts/SPARK_LA906_TIMING_BRIDGE.md`
- `docs/contracts/SPARK_DEGREE_TO_TICK_DEPENDENCY.md`
- `docs/contracts/MATH_HELPER_LF550.md`
- `docs/contracts/SPARK_TIMEBASE_PERIOD_CONTRACT.md`
- `docs/contracts/SPARK_MAGNITUDE_SCALE_CONTRACT.md`
- `docs/contracts/SPARK_CONVERSION_EQUATION.md`
- `docs/contracts/SPARK_LA906_OUTPUT_SEQUENCE.md`
- `docs/contracts/SPARK_ROLLING_STATE_MODEL.md`
- `docs/contracts/SPARK_INIT_STATE.md`
- `docs/contracts/SPARK_BYPASS_EST_TRANSITION.md`

Current spark split:

```text
SPARK_CONVERSION_EQUATION:
  desired spark degrees -> D_AB97 timing-domain input

SPARK_LA906_OUTPUT_SEQUENCE:
  D_AB97 -> $3FE8/$3FE6 writes
          -> $3FDC/$3FF6 rolling-state updates
          -> $3FEC->$3FE4 mirror/ack candidate

SPARK_ROLLING_STATE_MODEL:
  persistence/continuity model for $3FF6/$3FDC/L01EC

SPARK_INIT_STATE:
  first-event seed hazard before first valid run-mode LA906 update

SPARK_BYPASS_EST_TRANSITION:
  crank/run qualification and bypass-to-EST authority transfer model
```

## Current known spark authority model

```text
key-on/stall/reset:
  L004F bit7 ENGINE RUNNING cleared
  L004F bit4 RUN FUEL cleared
  L0044 bit3 FIRST DRP VALID cleared/rearmed

run qualification:
  first DRP/ref valid latch is required
  L4133 is the 450 RPM bypass-to-run threshold candidate
  L0210 is the qualifying DRP/ref event counter
  L004F bit7 is set when threshold + count gates pass

EST/fault monitor:
  L004F bit6 is major-loop EST monitor enable
  Error 42 captured rows point to L3FCA -> L0205 comparison and L022C counter
  L3FEC->$3FE4 mirror remains possible sync/ack behavior
```

## Current next target

Choose based on whether the Error 42/EST monitor needs its own standalone proof before defining the module boundary.

Option A, if fault logic remains complex:

```text
docs/contracts/SPARK_EST_FAULT_MONITOR_CONTRACT.md
maps/contracts/spark_est_fault_monitor_contract.csv
docs/tests/SPARK_EST_FAULT_MONITOR_TEST.md
```

Option B, if the bypass/EST contract is enough to define software boundaries:

```text
docs/contracts/SPARK_MINIMAL_MODULE_BOUNDARY.md
```

Do not create a spark writer yet.

## Static-map note

The current repo still contains the original static full-map baseline:

```text
maps/full/hardware_access_map_v0.2.csv
```

Do not reference `maps/full/hardware_access_map_v0.3.csv` as committed until it is actually regenerated or uploaded.

## Current generated/derived artifact groups

Core working docs:

- `README.md`
- `docs/WORKING_STATE.md`
- `docs/contracts/*.md`
- `docs/tests/*.md`
- `docs/ASIC_HARDWARE_REGISTER_CONTRACT.md`
- `docs/ASIC_Register_Contract.md`
- `docs/VARIABLE_DEPENDENCY_GRAPH.md`
- `docs/DYNAMIC_TRACE_PLAN.md`
- `docs/STATIC_ANALYSIS_SUMMARY.md`
- `docs/MINIMAL_OS_SKELETON.md`
- `docs/CALIBRATION_LAYOUT.md`

Maps/source/tools:

- `maps/current/hardware_access_map_hw_only.csv`
- `maps/current/hardware_test_matrix.csv`
- `maps/contracts/*.csv`
- `maps/by_subsystem/*.csv`
- `maps/full/hardware_access_map_v0.2.csv`
- `source/31/BMHM_HAC_ORG_7100_to_end.asm`
- `source/31/metadata.md`
- `tools/*.py`

## Rule going forward

Stable current files live in the repo. Versioning is Git history. Only create downloadable artifacts when explicitly useful for transfer, review, or local bench work.

Before starting a new technical pass, check this file first so a future thread does not rewind the project to an earlier subsystem.
