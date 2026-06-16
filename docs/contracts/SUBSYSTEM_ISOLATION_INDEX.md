# SUBSYSTEM_ISOLATION_INDEX

## Purpose

Link the write-target network and dispatcher reverse map into subsystem-level decisions for the minimal 7427 OS.

This artifact is static-only. It does not create runtime ASM, does not relax fuel/IAC bench gates, and does not allow SLICE-1.

## Isolation rule

Do not delete a variable because it looks unimportant. Delete only after its read/write network proves it does not feed hardware, safety, dispatch, or a preserved stock driver.

## Current subsystem route decisions

| subsystem | current decision | next required proof |
|---|---|---|
| `fuel_compact_3FCE` | `active_bench_route` | run FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST and fill fuel_slice0_bench_results.csv |
| `fuel_stock_output_driver` | `incomplete_continue_3FCE_bench_route` | complete stock fuel output-driver static proof or continue compact $3FCE bench route |
| `spark_stock_handoff` | `accepted_static_route_after_contract_proof` | static preservation of complete handoff and input seeding before implementation |
| `spark_custom_writer` | `blocked_bench_required` | bench discovery if direct writer is ever reconsidered |
| `iac_stock_driver` | `contract_defined_preservation_not_proven` | IAC stock-driver static proof index or custom IAC bench proof |
| `iac_custom_writer` | `blocked_bench_required` | bench proof of A/B/Enable/phase/park or complete stock-driver preservation |
| `whole_rom_write_sweep` | `supporting_index` | review targets with hardware/safety/dispatch roles before deleting anything |
| `dispatcher_reverse_map` | `supporting_index` | resolve indirect dispatchers that land on hardware-output or safety routines |

## Must preserve if using stock driver

A preserved stock driver route must preserve the complete routine range, every input/state variable consumed, every side effect produced, write ordering, timing/delay assumptions, reset/dropout seed state, and any dispatcher path required to reach the routine.

## May ignore only after proof

Emissions strategy, diagnostics-only mirrors, unused transmission branches, calibration bookkeeping, and redundant monitors are not removable by name. They become removable only after the network proves they do not feed hardware, safety, dispatch, or preserved-driver state.

## Active bottleneck

Fuel remains on the compact `$3FCE` SLICE-0 bench path. `FUEL-001` through `FUEL-004` still block SLICE-1 under that route.
