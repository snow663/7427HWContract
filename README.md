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

Current spark boundary:

```text
SPARK_CONVERSION_EQUATION
  desired spark degrees -> D_AB97 timing-domain input

SPARK_LA906_OUTPUT_SEQUENCE
  D_AB97 -> $3FE8/$3FE6 writes + $3FDC/$3FF6 updates + $3FEC->$3FE4 mirror

SPARK_ROLLING_STATE_MODEL
  persistence/continuity model for $3FF6/$3FDC/L01EC

SPARK_INIT_STATE
  first-event seeding and crank/run entry hazard

SPARK_BYPASS_EST_TRANSITION
  module bypass/base timing -> EST/ASIC-controlled timing authority transfer

SPARK_EST_FAULT_MONITOR_CONTRACT
  Error 42 / EST monitor path and side-effect classification
```

No spark writer exists yet. That boundary is intentional.

## Current next target

Next non-code artifact:

```text
docs/contracts/SPARK_MINIMAL_MODULE_BOUNDARY.md
```

Purpose:

```text
Define required, optional, and bench-gated spark-side modules before any spark code stub.
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
