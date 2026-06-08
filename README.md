# 7427HWContract

Working repository for the GM 16197427 `7427` PCM hardware-contract reverse-engineering project.

The repo is the project state. Downloadable ZIPs/CSVs are exports only and should not become the primary working record.

## Objective

Extract the HC11 CPU-to-hardware/ASIC contract from the stock `$31` BMHM/HAC ROM/disassembly, then use that contract to build a clean minimal engine-control OS:

- speed-density TBI fuel
- spark control
- IAC/idle air control
- AE / PE / DFCO
- crank / warmup / afterstart fuel
- injector low-pulsewidth transfer correction
- ALDL/debug visibility

Out of scope unless proven hardware-required:

- automatic transmission strategy
- TCC strategy
- EGR behavior
- EVAP/purge behavior
- inherited GM mode-word baggage

## Current repo index

Core state:

- `docs/WORKING_STATE.md` — active project state and next target
- `docs/contracts/*.md` — current subsystem contracts
- `docs/tests/*.md` — bench/static test plans
- `maps/contracts/*.csv` — machine-readable contract summaries
- `maps/current/hardware_access_map_hw_only.csv` — current hardware-facing static map view
- `maps/current/hardware_test_matrix.csv` — bench test matrix
- `maps/by_subsystem/*.csv` — subsystem split maps
- `source/31/BMHM_HAC_ORG_7100_to_end.asm` — source listing used by contract builders
- `source/minimal_os/spark/README.md` — spark source API/layout boundary, no ASM implementation
- `tools/*.py` — repo-relative analysis/build tools

Legacy/static-base artifacts still present:

- `maps/full/hardware_access_map_v0.2.csv` — original full static access map baseline

Note: do not claim a regenerated `maps/full/hardware_access_map_v0.3.csv` exists until it is committed.

## Completed contract phase

### Minimal OS boundary

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

### IAC / idle-air output contract

- `docs/contracts/IAC_IDLE_AIR_OUTPUT_CONTRACT.md`
- `maps/contracts/iac_idle_air_output_contract.csv`
- `docs/tests/IAC_IDLE_AIR_OUTPUT_TEST.md`
- `docs/contracts/IAC_PHASE_SEQUENCE_CONTRACT.md`
- `maps/contracts/iac_phase_sequence_contract.csv`
- `docs/tests/IAC_PHASE_SEQUENCE_TEST.md`
- `docs/contracts/IAC_ENABLE_FAULT_GATE_CONTRACT.md`
- `maps/contracts/iac_enable_fault_gate_contract.csv`
- `docs/tests/IAC_ENABLE_FAULT_GATE_TEST.md`

Current source-proven IAC model:

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

Source-proven phase ring if bit2=A and bit3=B:

```text
direction bit0 = 0:
  none -> A -> A+B -> B -> none
  0x00 -> 0x04 -> 0x0C -> 0x08 -> 0x00

direction bit0 = 1:
  none -> B -> A+B -> A -> none
  0x00 -> 0x08 -> 0x0C -> 0x04 -> 0x00
```

Enable/fault gate model:

```text
L00A7 = battery volts, VDC/10
CMPA #169 = 16.9 V high-voltage threshold candidate
L4EB6 = low-voltage threshold candidate
ANDB #$EF = clear L000A bit4 candidate
ORAB #$10 = set L000A bit4 candidate
L003E bit2 = low-battery/protection flag
L93C5 bad-shutdown/setup path preserves A/B and clears Enable/direction with ANDA #$0C
```

No IAC writer exists yet.

### Fuel output contract

- `docs/contracts/EFI_PW_3FCE_CONTRACT.md`
- `docs/contracts/EFI_PW_UNITS.md`
- `docs/contracts/EFI_OUTPUT_COMPANION_REGISTERS.md`
- `docs/contracts/EFI_OUTPUT_INIT_STATE.md`
- `docs/contracts/MINIMAL_EFI_PW_WRITER.md`
- `docs/contracts/EFI_OUTPUT_INIT_ROUTINE.md`

Current fuel boundary:

```text
EFI_OUTPUT_INIT   = one-time ASIC/window/output state
EFI_PW_WRITE      = runtime EFI pulsewidth command via STD $3FCE
```

### Spark static contract

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

Current spark boundary:

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

No spark writer exists yet. That boundary is intentional.

## Current next target

Isolate init/park/reset behavior and actual-position seeding:

```text
docs/contracts/IAC_INIT_PARK_CONTRACT.md
maps/contracts/iac_init_park_contract.csv
docs/tests/IAC_INIT_PARK_TEST.md
tools/build_iac_init_park_contract.py
```

Purpose:

```text
Determine how stock code makes L0007 actual/present position trustworthy before normal IAC control.
```

## Current hard boundaries

```text
Fuel may have a provisional runtime writer:
  D -> STD $3FCE

Spark may not yet have a writer:
  no SPARK_WRITE
  no direct $3FE8/$3FE6 writer
  no physical EST authority code

IAC may not yet have a writer:
  no IAC writer until phase sequence, enable/fault gate, and init/park contracts are split and bench-gated

Transmission/emissions remain excluded:
  no TCC
  no shift logic
  no EGR
  no EVAP
  no inherited mode-word baggage unless proven hardware-required
```

## Working rule

Use stable filenames for current work. Let Git history preserve versions. Avoid creating parallel `almost same` copies unless there is a real branch/release reason.
