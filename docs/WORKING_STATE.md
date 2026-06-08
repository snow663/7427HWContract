# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloaded ZIPs as the primary project state. Generated downloads are exports only.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly. The target is a clean minimal OS/control program that preserves required hardware behavior for fuel, spark, idle air, sensors, watchdog/reset, ALDL/debug, and engine protection.

Current technical focus after the IAC source-side boundary pass:

```text
next calibration-side pass:
  CALIBRATION_SOURCE_INDEX
```

The source now proves the IAC desired/actual compare, A/B phase ring, Enable voltage/fault gate candidate, init/park/reset behavior, and source-side IAC module API boundary. No IAC writer exists yet.

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

Phase sequence if bit2=A and bit3=B:

```text
direction bit0 = 0:
  none -> A -> A+B -> B -> none
  0x00 -> 0x04 -> 0x0C -> 0x08 -> 0x00

direction bit0 = 1:
  none -> B -> A+B -> A -> none
  0x00 -> 0x08 -> 0x0C -> 0x04 -> 0x00
```

Enable/fault gate source model:

```text
L00A7 = battery volts, VDC/10
CMPA #169 = 16.9 V high-voltage threshold candidate
L4EB6 = low-voltage threshold candidate
ANDB #$EF = clear L000A bit4 candidate
ORAB #$10 = set L000A bit4 candidate
L003E bit2 = low-battery/protection flag
L93C5 bad-shutdown/setup path preserves A/B and clears Enable/direction with ANDA #$0C
```

Init/park source model:

```text
L4EB0 = 145 steps IAC park down
NVM fail path: L4EB0 -> L0007 actual/present position
reset-in-work path: L0008 := 0 until L0007 reaches 0
reset complete: clear L0009 bit0, set L0009 bit2, call L92A4
ignition-off/R-S requested: L4EB0 -> L9899 -> L0008 desired/target position
common desired sink: L9899 STAA L0008
```

IAC source-side module boundary:

```text
IAC_INIT_PARK
IAC_ENABLE_GATE
IAC_POSITION_COMPARE
IAC_PHASE_STEP
IAC_STEP_CADENCE
IAC_TARGET_COMPUTE
IAC_OUTPUT_LATCH
IAC_DIAGNOSTIC_MONITOR
```

Bench gates:

```text
physical pins for L3062 bits2/3/4
whether bit2=A and bit3=B or swapped
whether count +1 means open or closed
whether L3062 bit4 is physical IAC Enable
whether Enable is continuous driver gate
whether L0008=0 is open or closed physically
whether L4EB0=145 is open, closed, or stock park-down overtravel
whether reset-in-work physically overdrives to a stop
exact cadence/timer for next step
```

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

Transmission/emissions remain excluded:
  no TCC
  no shift logic
  no EGR
  no EVAP
  no inherited mode-word baggage unless proven hardware-required
```

## Current next target

Use the local calibration HTML source to build the calibration index:

```text
tools/build_calibration_source_index.py
docs/contracts/CALIBRATION_SOURCE_INDEX.md
maps/contracts/calibration_source_index.csv
```

The calibration index should classify the local extract by module relevance:

```text
fuel
spark
IAC/idle
crank/start
battery/deadtime/latency
ALDL/debug
trans/excluded
emissions/excluded
unknown
```

Calibration must remain secondary to the hardware contracts. The index should classify what exists and what is likely relevant; it should not create module code or override the source-proven hardware boundaries.

## Static-map note

The current repo still contains the original static full-map baseline:

```text
maps/full/hardware_access_map_v0.2.csv
```

Do not reference `maps/full/hardware_access_map_v0.3.csv` as committed until it is actually regenerated or uploaded.

## Local project-source note

The project-source attachments include:

```text
31_HAC_calibration_extract_nowrap.html
```

That file is a local source artifact, not currently a committed GitHub repo file. Use it for `CALIBRATION_SOURCE_INDEX`.

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
