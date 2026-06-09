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
- `source/minimal_os/iac/README.md` — IAC source API/layout boundary, no ASM implementation
- `tools/*.py` — repo-relative analysis/build tools

Legacy/static-base artifacts still present:

- `maps/full/hardware_access_map_v0.2.csv` — original full static access map baseline

Note: do not claim a regenerated `maps/full/hardware_access_map_v0.3.csv` exists until it is committed.

## Completed contract phase

### Minimal OS boundary

- `docs/contracts/MINIMAL_OS_MODULE_BOUNDARY.md`
- `maps/contracts/minimal_os_module_boundary.csv`
- `docs/tests/MINIMAL_OS_MODULE_BOUNDARY_TEST.md`

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
- `docs/contracts/IAC_INIT_PARK_CONTRACT.md`
- `maps/contracts/iac_init_park_contract.csv`
- `docs/tests/IAC_INIT_PARK_TEST.md`
- `source/minimal_os/iac/README.md`

No IAC writer exists yet.

### IAC minimal module inputs

- `tools/build_iac_minimal_module_inputs.py`
- `docs/contracts/IAC_MINIMAL_MODULE_INPUTS.md`
- `maps/contracts/iac_minimal_module_inputs.csv`
- `docs/tests/IAC_MINIMAL_MODULE_INPUTS_TEST.md`

This is a planning boundary only. It defines inputs needed before the already-mapped IAC path can be commanded safely:

```text
L0007 actual/present
L0008 desired/target
L000A state byte
L004C output shadow
L3062 hardware latch
```

No IAC motion, direct `L3062` writer, or idle strategy ASM is implemented by this pass.

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

### Fuel minimal module inputs

- `tools/build_fuel_minimal_module_inputs.py`
- `docs/contracts/FUEL_MINIMAL_MODULE_INPUTS.md`
- `maps/contracts/fuel_minimal_module_inputs.csv`
- `docs/tests/FUEL_MINIMAL_MODULE_INPUTS_TEST.md`

This is a planning boundary only. It defines the inputs that feed the future fuel calculation ending in:

```text
D = EFI pulsewidth counts in 1/65536 second units
STD $3FCE
```

No fuel equation or tuning change is implemented by this pass.

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

No spark writer exists yet. That boundary is intentional.

### Spark minimal module inputs

- `tools/build_spark_minimal_module_inputs.py`
- `docs/contracts/SPARK_MINIMAL_MODULE_INPUTS.md`
- `maps/contracts/spark_minimal_module_inputs.csv`
- `docs/tests/SPARK_MINIMAL_MODULE_INPUTS_TEST.md`

This is a planning boundary only. Spark output remains source-mapped but bench-gated. No spark writer, direct `$3FE8/$3FE6` writer, rolling-state writer, or physical EST/bypass code is implemented by this pass.

### Calibration source index

- `tools/build_calibration_source_index.py`
- `docs/contracts/CALIBRATION_SOURCE_INDEX.md`
- `maps/contracts/calibration_source_index.csv`
- `docs/tests/CALIBRATION_SOURCE_INDEX_TEST.md`

The calibration index parses the local `31_HAC_calibration_extract_nowrap.html` machine-readable JSON payload and classifies 226 calibration sections by module relevance.

Index discipline:

```text
No section is marked required by the index alone.
Transmission/EGR/EVAP/emissions remain excluded unless hardware-required.
Unknown sections remain visible instead of being silently guessed.
The index is a planning map, not a tuning artifact.
```

## Current next target

Next planning artifact, not code:

```text
docs/contracts/MINIMAL_OS_EXECUTION_SCHEDULER.md
maps/contracts/minimal_os_execution_scheduler.csv
tools/build_minimal_os_execution_scheduler.py
docs/tests/MINIMAL_OS_EXECUTION_SCHEDULER_TEST.md
```

## Current hard boundaries

```text
Fuel may have a provisional runtime writer:
  D -> STD $3FCE

Spark may not yet have a writer:
  no SPARK_WRITE
  no direct $3FE8/$3FE6 writer
  no direct $3FF6/$3FDC rolling-state writer
  no physical EST authority code

IAC may not yet have a writer:
  no IAC_WRITE
  no iac_output.asm
  no iac_phase_step.asm
  no iac_init_park.asm
  no iac_enable_gate.asm
  no direct L3062 writer
  no idle strategy ASM

Calibration may not drive code by itself:
  no tuning changes
  no table selection as required unless tied to a hardware/source contract
  no trans/EGR/EVAP/emissions migration unless proven hardware-required
```

## Working rule

Use stable filenames for current work. Let Git history preserve versions. Avoid creating parallel `almost same` copies unless there is a real branch/release reason.
