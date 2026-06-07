# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloaded ZIPs as the primary project state. Generated downloads are exports only.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly. The target is a clean minimal OS/control program that preserves required hardware behavior for fuel, spark, idle air, sensors, watchdog/reset, ALDL/debug, and engine protection.

## Current completed repo artifacts

Core working docs:

- `README.md`
- `docs/WORKING_STATE.md`
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
- `maps/full/hardware_access_map_v0.2.csv`
- `maps/by_subsystem/*.csv`
- `source/31/BMHM_HAC_ORG_7100_to_end.asm`
- `source/31/metadata.md`
- `tools/build_hw_map.py`
- `tools/build_v02_outputs.py`

## Static pass v0.2 summary

- Total access rows: `7507`
- Hardware-facing rows: `693`
- Minimal-OS required rows: `904`
- Explicit test-item rows: `23`

## Immediate hardware targets

- `$301C/$301E` — TOC4/TOC5 injector compare path
- `$3020` — TCTL1 output compare action bits
- `$3022` — TMSK1 timer interrupt enable/disable
- `$3023` — TFLG1 write-one-clear event flags
- `$3FCA` — ASIC/ref/status timing source candidate
- `$3FFA` — packed ASIC status candidate
- `$3FFC` — I/O D port/output latch candidate
- `$3FE6/$3FE8/$3FF6` — spark/EST handoff candidates
- `$306x` — board/ASIC-adjacent unknowns, test before removal

## Next step

Bench/dynamic trace prep:

1. Load `maps/current/hardware_test_matrix.csv`.
2. Start with `maps/by_subsystem/fuel_sched_timer.csv`.
3. Capture `$301C/$301E/$3020/$3022/$3023` under key-on, crank, idle, AE, DFCO.
4. Then capture spark/EST candidates: `$3FE6/$3FE8/$3FF6/$3FDC`.
5. Then capture ASIC/ref/status candidates: `$3FCA/$3FFA/$3FCx`.
6. Then classify `$3060-$306F` as required or removable.

## Rule going forward

Stable current files live in the repo. Versioning is Git history. Only create downloadable artifacts when explicitly useful for transfer, review, or local bench work.
