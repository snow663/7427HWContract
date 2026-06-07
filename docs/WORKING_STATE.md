# Working State

This repository is the working directory for the 7427 hardware-contract reverse-engineering project. Do not treat downloaded ZIPs as the primary project state. Generated downloads are exports only.

## Current focus

Extract the CPU-to-hardware contract for the GM 16197427 PCM using the `$31` BMHM/HAC disassembly. The target is a clean minimal OS/control program that preserves required hardware behavior for fuel, spark, idle air, sensors, watchdog/reset, ALDL/debug, and engine protection.

## Current completed repo artifacts

Core working docs:

- `README.md`
- `docs/WORKING_STATE.md`
- `docs/ASIC_HARDWARE_REGISTER_CONTRACT.md`
- `docs/VARIABLE_DEPENDENCY_GRAPH.md`
- `docs/DYNAMIC_TRACE_PLAN.md`
- `docs/7427_Static_Analysis_Summary_v0.2.md`
- `docs/7427_Minimal_OS_Skeleton_v0.1.md`
- `docs/7427_Calibration_Layout_v0.1.md`

Repo structure docs/tools:

- `maps/README.md`
- `maps/by_subsystem/SPLIT_INDEX.md`
- `maps/current/HARDWARE_TEST_MATRIX.md`
- `source/README.md`
- `tools/hw_access_map_analyzer.py`

## Local/generated artifacts from static pass v0.2

These were generated in the current analysis session. Large CSV/source artifacts are prepared locally and should be committed as split files when connector-safe or through normal Git:

- `7427_Hardware_Access_Map_v0.2.csv`
- `7427_Hardware_Access_Map_HW_Only_v0.2.csv`
- `7427_Hardware_Test_Matrix_v0.2.csv`
- `7427_ASIC_Register_Contract_v0.2.md`
- `7427_Variable_Dependency_Graph_v0.2.md`
- `31_HAC_from_ORG_7100_to_end_NOWRAP.asm`
- `build_v02_outputs.py`

## Prepared local split files

The large hardware map has been split locally by subsystem. These are the intended repo paths:

```text
maps/by_subsystem/aldl_sci.csv
maps/by_subsystem/asic_command_output.csv
maps/by_subsystem/asic_status_ref.csv
maps/by_subsystem/asic_unknown.csv
maps/by_subsystem/boot_watchdog_cpu.csv
maps/by_subsystem/fuel_math_handoff.csv
maps/by_subsystem/fuel_sched_timer.csv
maps/by_subsystem/hc11_core.csv
maps/by_subsystem/idle_iac.csv
maps/by_subsystem/io_latch_output.csv
maps/by_subsystem/sensor_adc.csv
maps/by_subsystem/spark_est.csv
maps/by_subsystem/unknown_306x_board_io.csv
```

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

Commit the split CSVs in this order:

1. `fuel_sched_timer.csv`
2. `spark_est.csv`
3. `asic_status_ref.csv`
4. `io_latch_output.csv`
5. `unknown_306x_board_io.csv`
6. `hardware_test_matrix.csv`
7. remaining subsystem CSVs

## Rule going forward

Stable current files live in the repo. Versioning is Git history. Only create downloadable artifacts when explicitly useful for transfer, review, or local bench work.
