# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloaded ZIPs as the primary project state. Generated downloads are exports only.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly. The target is a clean minimal OS/control program that preserves required hardware behavior for fuel, spark, idle air, sensors, watchdog/reset, ALDL/debug, and engine protection.

Current technical focus after the spark minimal-module-boundary pass:

```text
spark module documentation/API layout:
  create source/minimal_os/spark/README.md
  define module layout and API contracts only
```

Still no spark writer. The next artifact may define documentation/API layout only; it must not implement `SPARK_WRITE` or a spark handoff stub.

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
- `docs/contracts/SPARK_EST_FAULT_MONITOR_CONTRACT.md`
- `docs/contracts/SPARK_MINIMAL_MODULE_BOUNDARY.md`

Current spark split:

```text
SPARK_RUN_QUALIFY:
  first DRP valid, recent DRP valid, RPM threshold, qualifying event count, engine-running flag

SPARK_BYPASS_EST_AUTHORITY:
  bypass-safe crank behavior and safe authority transfer

SPARK_CONVERT_DEGREES_TO_TIME:
  desired spark degrees -> D_AB97 timing-domain input

SPARK_ROLLING_STATE:
  persistence/continuity model for $3FF6/$3FDC/L01EC

SPARK_ASIC_HANDOFF:
  paired $3FE8/$3FE6 timing writes

SPARK_ASIC_MIRROR_ACK:
  $3FEC->$3FE4 mirror/ack/status sync, bench-gated

SPARK_EST_MONITOR:
  optional/diagnostic unless MON-B/MON-C/MON-D is bench-proven

SPARK_DROPOUT_SAFE_STATE:
  invalid/missing REF/period safe behavior
```

## Current known spark module boundary

```text
required:
  SPARK_RUN_QUALIFY
  SPARK_BYPASS_EST_AUTHORITY
  SPARK_CONVERT_DEGREES_TO_TIME
  SPARK_ROLLING_STATE
  SPARK_ASIC_HANDOFF
  SPARK_DROPOUT_SAFE_STATE

bench-gated:
  $3FEC->$3FE4 mirror / ACK / status-sync requirement
  $3FF6/$3FDC first-event seed behavior
  physical bypass/EST authority trigger
  L0201/L3FC0 final postprocess units and sign/packing
  exact paired role of $3FE8/$3FE6
  dropout/missing-REF safe behavior

optional if MON-A:
  SPARK_EST_MONITOR
  Error 42 accumulation path
  diagnostic-only EST monitor behavior
```

## Current next target

Create documentation/API layout only:

```text
source/minimal_os/spark/README.md
```

Purpose:

```text
Define planned spark module layout, call order, inputs, outputs, and bench gates.
No ASM implementation yet.
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
