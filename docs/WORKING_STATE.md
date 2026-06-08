# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloaded ZIPs as the primary project state. Generated downloads are exports only.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly. The target is a clean minimal OS/control program that preserves required hardware behavior for fuel, spark, idle air, sensors, watchdog/reset, ALDL/debug, and engine protection.

Current technical focus after the calibration source index pass:

```text
hardware contracts: staged
source-side module API boundaries: fuel partial, spark/IAC API-only
calibration source index: complete as planning map
next work: use calibration index only for module input-boundary planning, not tuning or writer code
```

## Completed contract phase

### OS-level boundary

Completed:

- `docs/contracts/MINIMAL_OS_MODULE_BOUNDARY.md`
- `maps/contracts/minimal_os_module_boundary.csv`
- `docs/tests/MINIMAL_OS_MODULE_BOUNDARY_TEST.md`

Current OS module map:

```text
RESET_INIT
SENSOR_ACQUIRE
REF_RPM_PERIOD
FUEL_OUTPUT
SPARK_OUTPUT
IDLE_AIR_OUTPUT
ALDL_DEBUG
WATCHDOG_SAFE_STATE
TRANSMISSION_EMISSIONS_EXCLUDED
```

### IAC / idle-air output side

Completed static/source-proof passes:

- `docs/contracts/IAC_IDLE_AIR_OUTPUT_CONTRACT.md`
- `maps/contracts/iac_idle_air_output_contract.csv`
- `docs/tests/IAC_IDLE_AIR_OUTPUT_TEST.md`
- `docs/contracts/IAC_PHASE_SEQUENCE_CONTRACT.md`
- `maps/contracts/iac_phase_sequence_contract.csv`
- `docs/tests/IAC_PHASE_SEQUENCE_TEST.md`
- `docs/contracts/IAC_ENABLE_FAULT_GATE_CONTRACT.md`
- `maps/contracts/iac_enable_fault_gate_contract.csv`
- `docs/tests/IAC_ENABLE_FAULT_GATE_TEST.md`
- `docs/contracts/IAC_INIT_PARK_CONTRACT.md`
- `maps/contracts/iac_init_park_contract.csv`
- `docs/tests/IAC_INIT_PARK_TEST.md`
- `source/minimal_os/iac/README.md`

Current IAC source-proven model:

```text
actual/present position = L0007
desired/target position = L0008
mode/output state byte  = L000A
direction bit           = L000A bit0
A/B ring bits           = L000A bits2/3
Enable candidate        = L000A bit4
output shadow           = L004C bits2/3/4
hardware latch write    = L004C -> L3062
```

IAC is source/API staged only. No IAC writer exists yet.

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
- `source/minimal_os/spark/README.md`

Spark is source/API staged only. No spark writer exists yet.

### Calibration source index

Completed:

- `tools/build_calibration_source_index.py`
- `docs/contracts/CALIBRATION_SOURCE_INDEX.md`
- `maps/contracts/calibration_source_index.csv`
- `docs/tests/CALIBRATION_SOURCE_INDEX_TEST.md`

Source input:

```text
31_HAC_calibration_extract_nowrap.html
```

Validated source summary:

```text
section_count: 226
record_count: 11916
fcb_count: 11431
fdb_count: 485
min_data_address: $4000
max_data_address: $70FF
parse_error_count: 0
```

Current index counts:

```text
module candidates:
  crank_start: 18
  egr_excluded: 17
  evap_excluded: 4
  fuel: 24
  iac_idle: 36
  sensor_scaling: 33
  spark: 19
  spark_latency: 1
  trans_excluded: 49
  unknown: 24
  warmup_afterstart: 1

minimal-OS relevance:
  bench_gated: 56
  excluded: 70
  likely_required: 76
  unknown: 24
```

Calibration index discipline:

```text
No section is marked required by this index alone.
Excluded transmission/EGR/EVAP/emissions sections remain excluded unless a future hardware contract proves otherwise.
Unknown sections remain visible instead of being silently guessed.
The index is a planning map, not a tuning artifact.
```

## Current known hard boundaries

```text
Fuel may have a provisional runtime writer:
  EFI_PW_WRITE:
    D -> STD $3FCE

Spark may not yet have a writer:
  no SPARK_WRITE
  no direct $3FE8/$3FE6 writer
  no physical EST authority code

IAC may not yet have a writer:
  no IAC_WRITE
  no direct L3062 writer
  no source/minimal_os/iac/*.asm yet
  source/minimal_os/iac/README.md exists as documentation/API layout only

Calibration may not drive code by itself:
  no tuning changes
  no table selection as required unless tied to a hardware/source contract
  no trans/EGR/EVAP/emissions migration unless proven hardware-required
```

## Current next target

Use the completed hardware/API/calibration stack for module input-boundary planning only.

Likely next planning artifacts, not code:

```text
docs/contracts/FUEL_MINIMAL_MODULE_INPUTS.md
docs/contracts/SPARK_MINIMAL_MODULE_INPUTS.md
docs/contracts/IAC_MINIMAL_MODULE_INPUTS.md
```

Each input-boundary pass should reference:

```text
hardware/source contract need
calibration source section(s)
bench gate if physical behavior is not proven
excluded/unknown status if not needed yet
```

## Static-map note

The current repo still contains the original static full-map baseline:

```text
maps/full/hardware_access_map_v0.2.csv
```

Do not reference `maps/full/hardware_access_map_v0.3.csv` as committed until it is actually regenerated or uploaded.

## Rule going forward

Stable current files live in the repo. Versioning is Git history. Only create downloadable artifacts when explicitly useful for transfer, review, or local bench work.

Before starting a new technical pass, check this file first so a future thread does not rewind the project to an earlier subsystem.
