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

- `docs/WORKING_STATE.md` — active project state and next target/decision point
- `docs/contracts/*.md` — current subsystem contracts
- `docs/bench/*.md` — bench proof packages
- `docs/tests/*.md` — bench/static test plans
- `maps/contracts/*.csv` — machine-readable contract summaries
- `maps/bench/*.csv` — bench proof matrices
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

## Completed planning stack

### First minimal fuel-only runnable slice boundary

- `tools/build_first_minimal_fuel_only_slice.py`
- `docs/contracts/FIRST_MINIMAL_FUEL_ONLY_SLICE.md`
- `maps/contracts/first_minimal_fuel_only_slice.csv`
- `docs/tests/FIRST_MINIMAL_FUEL_ONLY_SLICE_TEST.md`

This is a contract/planning boundary only. It defines SLICE-0/1/2 and blocks engine-runnable fuel-only implementation until the required fuel bench proofs pass.

Slice discipline:

```text
No runtime ASM created.
No fuel-only runtime implementation created.
No spark or IAC writer created.
SLICE-0 is explicitly not engine-runnable.
SLICE-1 requires FUEL-001 through FUEL-004.
SLICE-2 is future-only after sensor/acquisition/fuel-model proof.
Only EFI_PW_WRITE -> $3FCE is allowed by the fuel-only slice boundary.
```

### Bench proof package

- `tools/build_bench_proof_package.py`
- `docs/bench/BENCH_PROOF_PACKAGE.md`
- `maps/bench/bench_proof_matrix.csv`
- `docs/tests/BENCH_PROOF_PACKAGE_TEST.md`

This is a planning/test-definition package only. It defines proof tasks, pass/fail conditions, tooling needs, ALDL visibility needs, scope needs, bench hook needs, and implementation gates.

Bench proof discipline:

```text
No runtime ASM created.
No bench-hook implementation created.
No ALDL packet code created.
No fuel-only runnable code created.
No proof row grants write authority by itself.
```

### Minimal OS boundary

- `docs/contracts/MINIMAL_OS_MODULE_BOUNDARY.md`
- `maps/contracts/minimal_os_module_boundary.csv`
- `docs/tests/MINIMAL_OS_MODULE_BOUNDARY_TEST.md`

### ALDL / debug visibility boundary

- `tools/build_minimal_os_aldl_debug_map.py`
- `docs/contracts/MINIMAL_OS_ALDL_DEBUG_MAP.md`
- `maps/contracts/minimal_os_aldl_debug_map.csv`
- `docs/tests/MINIMAL_OS_ALDL_DEBUG_MAP_TEST.md`

This is a planning boundary only. It defines which state variables and hardware-shadow candidates should be exposed for bench proof, first-run validation, and live troubleshooting.

### State-variable boundary

- `tools/build_minimal_os_state_variables.py`
- `docs/contracts/MINIMAL_OS_STATE_VARIABLES.md`
- `maps/contracts/minimal_os_state_variables.csv`
- `docs/tests/MINIMAL_OS_STATE_VARIABLES_TEST.md`

This is a planning boundary only. It consolidates source-proven symbols, hardware shadows, logical minimal-OS state, scheduler/boot/watchdog state, ALDL/debug state, explicit exclusions, and unknowns.

### Boot / safe-state boundary

- `tools/build_minimal_os_boot_safe_state.py`
- `docs/contracts/MINIMAL_OS_BOOT_SAFE_STATE.md`
- `maps/contracts/minimal_os_boot_safe_state.csv`
- `docs/tests/MINIMAL_OS_BOOT_SAFE_STATE_TEST.md`

This is a planning boundary only. It defines reset, output-safe defaults, RAM seed, REF wait, crank qualify, first valid period, run qualify, dropout, and watchdog-safe states.

### Execution scheduler boundary

- `tools/build_minimal_os_execution_scheduler.py`
- `docs/contracts/MINIMAL_OS_EXECUTION_SCHEDULER.md`
- `maps/contracts/minimal_os_execution_scheduler.csv`
- `docs/tests/MINIMAL_OS_EXECUTION_SCHEDULER_TEST.md`

This is a planning boundary only. It defines when reset, crank, REF/DRP, fuel, spark, IAC, ALDL, watchdog, and dropout-safe events are allowed to run.

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

This is a planning boundary only. It defines inputs needed before the already-mapped IAC path can be commanded safely.

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

## Current next target

Valid next branches:

```text
bench FUEL-001 through FUEL-004
implement SLICE-0 bench harness first, if explicitly bench-harness-only and not engine runnable
```

Forbidden next branch:

```text
SLICE-1 engine-runnable fuel-only skeleton before FUEL-001 through FUEL-004 pass
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

Fuel-only slice boundary may not create implementation yet:
  no runtime ASM
  no engine-runnable SLICE-1 before FUEL-001 through FUEL-004 pass
  no spark writer
  no IAC writer
  no direct $3FE8/$3FE6/$3FF6/$3FDC/L3062 writes

Bench proof package may not create implementation yet:
  no runtime ASM
  no bench-hook implementation
  no ALDL packet code
  no fuel-only runnable code
  no proof row grants write authority by itself
```

## Working rule

Use stable filenames for current work. Let Git history preserve versions. Avoid creating parallel `almost same` copies unless there is a real branch/release reason.
