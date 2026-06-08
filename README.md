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

Next non-code artifact:

```text
docs/contracts/MINIMAL_OS_MODULE_BOUNDARY.md
```

Purpose:

```text
Combine fuel and spark boundaries with the next unknown hardware subsystem boundary.
Likely next unknown subsystem: IAC/idle air output contract.
```

## Current known hazard

```text
global clear may zero $3FF6/$3FDC
but LA906 reads $3FF6/$3FDC before updating them
so first valid EST handoff depends on bypass/run gating or safe seed behavior
```

Current static spark authority/monitor model:

```text
run qualification = RPM threshold + DRP/ref event count
Error 42 monitor = L3FCA -> L0205 comparison and L022C counter
L004F bit6 = EST monitor enable, not proven physical bypass output control
no direct static proof that Error 42 forces bypass, disables LA906, or changes fuel
$3FEC->$3FE4 = possible shared status/mirror/ack, bench-gated
```

## Working rule

Use stable filenames for current work. Let Git history preserve versions. Avoid creating parallel `almost same` copies unless there is a real branch/release reason.
