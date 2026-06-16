# SUBSYSTEM_ISOLATION_INDEX

## Purpose

Link the write-target network and dispatcher reverse map into subsystem-level decisions for the minimal 7427 OS.

This artifact decides what must be kept, what can be ignored only after proof, and what remains blocked.

It is static-only. It does not create runtime ASM, does not relax fuel/IAC bench gates, and does not authorize `SLICE-1`.

## Isolation rule

Do not delete a variable because it looks unimportant.

Delete only after its read/write network proves it does not feed:

```text
hardware
safety
dispatch
scheduler state
rolling state
preserved stock driver input
preserved stock driver side effect
```

## Current subsystem route decisions

| subsystem | current decision | next required proof |
|---|---|---|
| `fuel_compact_3FCE` | `active_bench_route` | run `FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST` and fill `fuel_slice0_bench_results.csv` |
| `fuel_stock_output_driver` | `incomplete_continue_3FCE_bench_route` | complete stock fuel output-driver static proof or continue compact `$3FCE` bench route |
| `spark_stock_handoff` | `accepted_static_route_after_contract_proof` | static preservation of complete handoff and input seeding before implementation |
| `spark_custom_writer` | `blocked_bench_required` | bench discovery if direct writer is ever reconsidered |
| `iac_stock_driver` | `contract_defined_preservation_not_proven` | IAC stock-driver static proof index or custom IAC bench proof |
| `iac_custom_writer` | `blocked_bench_required` | bench proof of A/B/Enable/phase/park or complete stock-driver preservation |
| `whole_rom_write_sweep` | `supporting_index` | review targets with hardware/safety/dispatch roles before deleting anything |
| `dispatcher_reverse_map` | `supporting_index` | resolve indirect dispatchers that land on hardware-output or safety routines |

## Must implement

```text
hardware sinks
safety gates
scheduler state
rolling state
required shadows
preserved stock driver inputs
preserved stock driver side effects
dispatcher selectors that reach required routines
final command variables
```

## May ignore only after proof

```text
emissions strategy
diagnostics-only mirrors
unused transmission branches
stock-only fault reporting
calibration update bookkeeping
redundant monitor logic
```

These are removable only after network proof shows they do not feed hardware, safety, dispatch, scheduler state, rolling state, or preserved-driver state.

## Active bottleneck

Fuel remains on the compact `$3FCE` SLICE-0 bench path.

`FUEL-001` through `FUEL-004` still block `SLICE-1` under that route.
