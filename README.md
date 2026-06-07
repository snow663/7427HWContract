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

## Current repo files

- `docs/WORKING_STATE.md` — active state and next targets
- `docs/ASIC_HARDWARE_REGISTER_CONTRACT.md` — concise hardware register contract
- `docs/VARIABLE_DEPENDENCY_GRAPH.md` — current dependency graph
- `docs/DYNAMIC_TRACE_PLAN.md` — bench/dynamic trace plan
- `docs/STATIC_ANALYSIS_SUMMARY.md` — static pass summary
- `docs/MINIMAL_OS_SKELETON.md` — minimal OS structure
- `docs/CALIBRATION_LAYOUT.md` — clean calibration layout
- `maps/current/hardware_access_map_hw_only.csv` — hardware-facing rows
- `maps/current/hardware_test_matrix.csv` — bench test matrix
- `maps/by_subsystem/*.csv` — subsystem split maps
- `maps/full/hardware_access_map_v0.2.csv` — full static access map
- `source/31/BMHM_HAC_ORG_7100_to_end.asm` — source listing used for v0.2
- `tools/*.py` — analysis/build tooling

## Current static-pass findings

- Total access rows: `7507`
- Hardware-facing rows: `693`
- Minimal-OS required rows: `904`
- Explicit test-item rows: `23`

Primary hardware targets:

```text
$301C/$301E   TOC4/TOC5 injector compare path
$3020         TCTL1 output compare action bits
$3022         TMSK1 timer interrupt enable/disable
$3023         TFLG1 write-one-clear event flags
$3FCA         ASIC/ref/status timing source candidate
$3FFA         packed ASIC status candidate
$3FFC         I/O D port/output latch candidate
$3FE6/$3FE8   spark/EST handoff candidates
$3FF6         spark/output scheduler candidate
$306x         board/ASIC-adjacent unknowns
```

## Working rule

Use stable filenames for current work. Let Git history preserve versions. Avoid creating parallel `almost same` copies unless there is a real branch/release reason.
