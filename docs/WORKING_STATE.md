# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloaded ZIPs as the primary project state. Generated downloads are exports only.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly. The target is a clean minimal OS/control program that preserves required hardware behavior for fuel, spark, idle air, sensors, watchdog/reset, ALDL/debug, and engine protection.

## Current completed repo artifacts

- `docs/7427_Static_Analysis_Summary_v0.2.md`
- `docs/7427_Minimal_OS_Skeleton_v0.1.md`
- `docs/7427_Calibration_Layout_v0.1.md`

## Local/generated artifacts from static pass v0.2

These were generated in the current analysis session. Large CSV/source artifacts should be committed through normal Git or split into smaller repo-safe chunks:

- `7427_Hardware_Access_Map_v0.2.csv`
- `7427_Hardware_Access_Map_HW_Only_v0.2.csv`
- `7427_Hardware_Test_Matrix_v0.2.csv`
- `7427_ASIC_Register_Contract_v0.2.md`
- `7427_Variable_Dependency_Graph_v0.2.md`
- `build_v02_outputs.py`

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

## Rule going forward

Stable current files live in the repo. Versioning is Git history. Only create downloadable artifacts when explicitly useful for transfer, review, or local bench work.
