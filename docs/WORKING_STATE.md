# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloaded ZIPs as the primary project state. Generated downloads are exports only.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly. The target is a clean minimal OS/control program that preserves required hardware behavior for fuel, spark, idle air, sensors, watchdog/reset, ALDL/debug, and engine protection.

Current technical focus after the fuel SLICE-0 bench result capture pass:

```text
hardware contracts: staged
source-side module API boundaries: fuel partial, spark/IAC API-only
calibration source index: complete as planning map
fuel input boundary: complete as planning map
spark input boundary: complete as planning map
iac input boundary: complete as planning map
execution scheduler boundary: complete as planning map
boot/safe-state boundary: complete as planning map
state-variable boundary: complete as planning map
ALDL/debug visibility boundary: complete as planning map
bench proof package: complete as proof/test-definition map
first minimal fuel-only slice boundary: complete as contract map
fuel SLICE-0 bench harness: complete, bench-only / not engine-runnable
fuel SLICE-0 bench result capture: complete, default status not_run
next work: enter real bench data for FUEL-001/FUEL-002/FUEL-003 partial, and separately run dropout proof for FUEL-004
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

### Fuel SLICE-0 bench result capture

Completed:

- `tools/verify_fuel_slice0_bench_results.py`
- `maps/bench/fuel_slice0_bench_results.csv`
- `docs/bench/FUEL_SLICE0_BENCH_RESULTS.md`
- `docs/tests/FUEL_SLICE0_BENCH_RESULTS_TEST.md`

Current result-capture discipline:

```text
Default proof status is not_run.
The result CSV is the structured place for real scope/logic-analyzer/ALDL data.
FUEL-001 vectors are present.
FUEL-002 $00C5 / 197 / 3.005981 ms row is present.
FUEL-003 zero-vector row is present and may become partial if only zero-vector evidence exists.
FUEL-004 dropout row is present but cannot pass from SLICE-0 vector testing alone.
pass_fail is controlled: not_run, pass, fail, partial.
Any pass row must include measured_pw_ms or measured_register_or_debug_counts.
FUEL-004 pass requires dropout/unsafe evidence.
SLICE-1 cannot be marked allowed unless FUEL-001 through FUEL-004 are pass.
```

Current tolerance rule:

```text
pass if measured PW is within ±0.05 ms or ±3% of expected, whichever is larger

$00C5 = 197 counts
197 / 65.536 = 3.005981 ms
initial acceptable range: 2.956 ms to 3.056 ms
```

### Fuel SLICE-0 bench harness

Completed:

- `source/minimal_os/fuel/slice0_bench_harness.asm`
- `tools/verify_fuel_slice0_bench_harness.py`
- `tests/static/fuel_slice0_bench_vectors.csv`
- `docs/bench/FUEL_SLICE0_BENCH_HARNESS.md`
- `docs/tests/FUEL_SLICE0_BENCH_HARNESS_TEST.md`

Current harness discipline:

```text
bench-only
not engine-runnable
not scheduler-owned
not reset-vector-owned
not crank/run fuel control
no direct $3FCE / L3FCE write in harness
no spark writer
no IAC writer
no ALDL packet code
no fuel math
no sensor reads
no VE table use
```

### First minimal fuel-only runnable slice boundary

Completed:

- `tools/build_first_minimal_fuel_only_slice.py`
- `docs/contracts/FIRST_MINIMAL_FUEL_ONLY_SLICE.md`
- `maps/contracts/first_minimal_fuel_only_slice.csv`
- `docs/tests/FIRST_MINIMAL_FUEL_ONLY_SLICE_TEST.md`

Current slice discipline:

```text
No runtime ASM created.
No fuel-only runtime implementation created.
No spark ASM/writer created.
No IAC ASM/writer created.
Only EFI_PW_WRITE -> $3FCE is allowed in the fuel-only slice boundary.
SLICE-0 is explicitly not engine-runnable.
SLICE-1 is blocked until FUEL-001 through FUEL-004 pass.
SLICE-2 is future-only after sensor/acquisition/fuel-model proof.
Dropout forces $3FCE = 0.
ALDL/debug raw counts and milliseconds visibility are required.
Calibration cannot make the slice runnable by itself.
Trans/EGR/EVAP remain excluded.
```

Current valid next branches:

```text
bench FUEL-001 through FUEL-004
implement SLICE-0 bench harness first, if explicitly bench-harness-only and not engine runnable
```

Do not implement `SLICE-1` until the fuel proof rows are actually satisfied.

### Bench proof package

Completed:

- `tools/build_bench_proof_package.py`
- `docs/bench/BENCH_PROOF_PACKAGE.md`
- `maps/bench/bench_proof_matrix.csv`
- `docs/tests/BENCH_PROOF_PACKAGE_TEST.md`

Current bench proof discipline:

```text
No runtime ASM created.
No bench-hook implementation created.
No ALDL packet code created.
No fuel-only runnable code created.
Fuel $3FCE proof rows are defined.
Spark handoff/rolling/bypass proof rows are defined and remain bench-gated.
IAC A/B/Enable/park/cadence proof rows are defined and remain bench-gated.
Boot/dropout/watchdog proof rows are defined.
ALDL/debug visibility is tied to proof rows.
No proof row grants write authority by itself.
Unknown physical mappings remain unresolved until bench data exists.
```

Implementation gates:

```text
Fuel-only runnable slice:
  allowed after fuel PW output and boot-safe fuel gates are bench-proven
  FUEL-001 through FUEL-004 must pass before the first fuel-only runtime slice proceeds

Spark implementation:
  blocked until SPARK-001 through SPARK-006 are resolved or replaced by a safer documented hardware strategy

IAC implementation:
  blocked until IAC-001 through IAC-009 are resolved
```

### ALDL / debug visibility boundary

Completed:

- `tools/build_minimal_os_aldl_debug_map.py`
- `docs/contracts/MINIMAL_OS_ALDL_DEBUG_MAP.md`
- `maps/contracts/minimal_os_aldl_debug_map.csv`
- `docs/tests/MINIMAL_OS_ALDL_DEBUG_MAP_TEST.md`

Current ALDL/debug discipline:

```text
No ALDL packet implementation created.
No mode handler ASM created.
No serial ISR changes created.
No runtime code created.
No write authority is granted by debug visibility.
Fuel $3FCE raw counts and millisecond conversion are represented.
Spark handoff/rolling candidates are debug-visible but bench-gated.
IAC actual/desired/phase/enable/shadow/latch values are debug-visible but bench-gated.
Scheduler/boot/dropout/watchdog values are represented.
Trans/EGR/EVAP/emissions/stock mode-word ALDL baggage are excluded.
Unknown debug values remain listed instead of guessed.
```

Current key debug guardrails:

```text
Debug exposure of $3FE8/$3FE6/$3FF6/$3FDC does not permit spark writes.
Debug exposure of L3062/L004C does not permit IAC writes.
Debug exposure of $3FCE does not permit nonzero fuel unless fuel gates permit it.
ALDL visibility is observational only.
```

### State-variable boundary

Completed:

- `tools/build_minimal_os_state_variables.py`
- `docs/contracts/MINIMAL_OS_STATE_VARIABLES.md`
- `maps/contracts/minimal_os_state_variables.csv`
- `docs/tests/MINIMAL_OS_STATE_VARIABLES_TEST.md`

Current state-variable discipline:

```text
No runtime ASM created.
No RAM allocator created.
No linker map created.
Every carried-forward state variable has an owner.
Hardware shadows are separated from logical state.
Fuel $3FCE state is represented.
Spark rolling/timebase/output candidates remain bench-gated where needed.
IAC actual/desired/state/output shadow variables are represented.
Boot/scheduler/dropout/watchdog/ALDL-debug state is represented.
Trans/EGR/EVAP/emissions/unused GM mode baggage are excluded.
Unknown state remains listed instead of guessed.
```

### Boot / safe-state boundary

Completed:

- `tools/build_minimal_os_boot_safe_state.py`
- `docs/contracts/MINIMAL_OS_BOOT_SAFE_STATE.md`
- `maps/contracts/minimal_os_boot_safe_state.csv`
- `docs/tests/MINIMAL_OS_BOOT_SAFE_STATE_TEST.md`

Current boot-safe discipline:

```text
No reset vector ASM created.
No scheduler ASM created.
No startup implementation created.
Fuel $3FCE zero/no-pulse state is represented.
Nonzero fuel remains gated by fuel calculation and no-fuel enable.
Spark direct hardware writes remain forbidden.
IAC direct L3062 writes remain forbidden.
REF wait, crank qualify, first valid period, run qualify, dropout, and watchdog-safe states are represented.
Unknown boot ownership remains listed instead of guessed.
```

### Execution scheduler boundary

Completed:

- `tools/build_minimal_os_execution_scheduler.py`
- `docs/contracts/MINIMAL_OS_EXECUTION_SCHEDULER.md`
- `maps/contracts/minimal_os_execution_scheduler.csv`
- `docs/tests/MINIMAL_OS_EXECUTION_SCHEDULER_TEST.md`

Current scheduler discipline:

```text
No runtime scheduler ASM created.
No new hardware writer created.
Only $3FCE is provisionally allowed, and only through EFI_PW_WRITE / MINIMAL_EFI_PW_WRITER.
Spark hardware writes remain forbidden.
IAC L3062 writes remain forbidden.
ALDL/debug owns visibility only, not control outputs.
Unknown event ownership remains listed instead of guessed.
```

Current event classes represented:

```text
RESET_INIT
CRANK_INIT
REF_DRP_EVENT
FUEL_CALC_EVENT
FUEL_OUTPUT_EVENT
SPARK_PERIOD_EVENT
SPARK_OUTPUT_EVENT
IAC_CADENCE_EVENT
IAC_OUTPUT_EVENT
SENSOR_SAMPLE_EVENT
ALDL_SERVICE_EVENT
WATCHDOG_SERVICE_EVENT
DROPOUT_SAFE_STATE
FOREGROUND_BACKGROUND_LOOP
BENCH_ONLY_HOOK
EXCLUDED
UNKNOWN
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

### IAC minimal module inputs

Completed:

- `tools/build_iac_minimal_module_inputs.py`
- `docs/contracts/IAC_MINIMAL_MODULE_INPUTS.md`
- `maps/contracts/iac_minimal_module_inputs.csv`
- `docs/tests/IAC_MINIMAL_MODULE_INPUTS_TEST.md`

IAC input discipline:

```text
No IAC motion implemented.
No IAC ASM writer created.
No direct L3062 writer created.
Phase, Enable, park/reset, and cadence behavior remain bench-gated.
Trans/EGR/EVAP idle-adjacent sections remain excluded.
Unknown IAC inputs remain listed instead of guessed.
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

### Fuel minimal module inputs

Completed:

- `tools/build_fuel_minimal_module_inputs.py`
- `docs/contracts/FUEL_MINIMAL_MODULE_INPUTS.md`
- `maps/contracts/fuel_minimal_module_inputs.csv`
- `docs/tests/FUEL_MINIMAL_MODULE_INPUTS_TEST.md`

Current fuel input discipline:

```text
No fuel equation implemented.
No tuning values changed.
No fuel ASM writer changed or added.
Calibration sections do not become required by index presence alone.
DFCO/no-fuel, injector deadtime, low-PW correction, and EFI PW unit conversion remain explicit hardware/source dependencies.
Transmission/EGR/EVAP/emissions sections remain excluded.
```

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

### Spark minimal module inputs

Completed:

- `tools/build_spark_minimal_module_inputs.py`
- `docs/contracts/SPARK_MINIMAL_MODULE_INPUTS.md`
- `maps/contracts/spark_minimal_module_inputs.csv`
- `docs/tests/SPARK_MINIMAL_MODULE_INPUTS_TEST.md`

Spark input discipline:

```text
No spark math implemented.
No spark ASM writer created.
No direct $3FE8/$3FE6 writer created.
No physical EST/bypass authority code created.
Trans/EGR/EVAP spark-adjacent sections remain excluded.
Unknown spark inputs remain listed instead of guessed.
```

### Calibration source index

Completed:

- `tools/build_calibration_source_index.py`
- `docs/contracts/CALIBRATION_SOURCE_INDEX.md`
- `maps/contracts/calibration_source_index.csv`
- `docs/tests/CALIBRATION_SOURCE_INDEX_TEST.md`

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
  no spark_handoff.asm
  no spark_convert.asm
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

Scheduler may not create runtime code yet:
  no runtime scheduler ASM
  no module dispatch code
  no new hardware writes
  no calibration-driven events without hardware/source contract ownership

Boot/safe-state may not create startup code yet:
  no reset vector ASM
  no startup implementation
  no direct spark ASIC writes
  no direct IAC L3062 writes
  no nonzero fuel boot default

State-variable map may not allocate RAM yet:
  no allocator
  no linker map
  no runtime ASM
  no full stock RAM clone
  no carry-forward solely because a variable exists in stock code

ALDL/debug map may not create runtime code yet:
  no ALDL packet implementation
  no mode handler ASM
  no serial ISR changes
  no write authority
  no stock ALDL baggage solely because stock exposed it

Bench proof package may not create implementation yet:
  no runtime ASM
  no bench-hook implementation
  no ALDL packet code
  no fuel-only runnable code
  no proof row grants write authority by itself

Fuel-only slice boundary may not create implementation yet:
  no runtime ASM
  no engine-runnable SLICE-1 before FUEL-001 through FUEL-004 pass
  no spark writer
  no IAC writer
  no direct $3FE8/$3FE6/$3FF6/$3FDC/L3062 writes

Fuel SLICE-0 bench harness boundaries:
  bench-only
  not engine-runnable
  fixed vectors only
  JSR EFI_PW_WRITE only
  no direct $3FCE / L3FCE write in harness
  no sensors
  no fuel math
  no VE tables
  no ALDL packet code

Fuel SLICE-0 bench result capture boundaries:
  default status not_run
  no proof pass without measured data
  FUEL-004 cannot pass from vector testing alone
  no SLICE-1 allowed claim unless FUEL-001 through FUEL-004 pass

Calibration may not drive code by itself:
  no tuning changes
  no table selection as required unless tied to a hardware/source contract
  no trans/EGR/EVAP/emissions migration unless proven hardware-required
```

## Current next target

Next action is bench-data capture, not code expansion:

```text
run SLICE-0 vectors on bench
record measured values in maps/bench/fuel_slice0_bench_results.csv
run tools/verify_fuel_slice0_bench_results.py
```

Do not move to:

```text
SLICE-1 engine-runnable fuel-only skeleton
```

until:

```text
FUEL-001 = pass
FUEL-002 = pass
FUEL-003 = pass
FUEL-004 = pass
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
