# FUEL_STOCK_OUTPUT_DRIVER_PRESERVATION_CONTRACT

## Purpose

Define the decision seam for using the stock `$31` fuel scheduler/output driver as a preserved black-box hardware driver.

This contract does not implement fuel code, does not replace the existing SLICE-0 `$3FCE` bench path, and does not claim the fuel stock-driver preservation proof is complete.

It defines when fuel may follow the stock-driver preservation model instead of requiring per-register bench discovery or a compact direct `$3FCE` writer proof.

## Fuel hardware authority model

```text
1. Clean OS may calculate desired fuel mass / BPW / enrichment state.
2. Clean OS may feed stock-compatible fuel state into a preserved stock fuel scheduler/output driver.
3. Preserved stock fuel scheduler/output driver owns all hardware-facing fuel writes.
4. Direct custom fuel ASIC / $3FCE writers remain bench-proof gated.
```

## Critical distinction

```text
preserved stock fuel output driver:
  static completeness proof required before use
  no per-register physical bench proof required before use if complete

compact direct $3FCE writer:
  bench proof required before engine-runnable use
```

Preserving the stock fuel output driver is not the same thing as writing `$3FCE` from clean code.

## What this can bypass

If a complete stock fuel scheduler/output driver is preserved behavior-for-behavior, the project does not need to first prove the physical meaning of every fuel scheduler / ASIC support register before using that preserved path.

The stock routine is treated as the already-proven hardware driver. The proof burden shifts to preserving the complete stock routine and feeding compatible state.

## What this cannot bypass

```text
static proof that the preserved routine range is complete
static proof that all required inputs/state are seeded
static proof that side effects, write order, delay calls, and interrupt assumptions are preserved
static proof that reset, first-event, crank/run, dropout, unsafe, and no-fuel states are safe
static proof that no alternate direct custom fuel writer exists outside the gated path
eventual real-hardware validation before engine trust
```

## Contract gates

### FUEL-STOCK-001 — complete_stock_driver_range

Requirement: Identify the complete preserved stock fuel scheduler/output-driver routine range before use.

Status: `required_not_proven`

Bench requirement: `no_if_complete_stock_preserved`

Fallback if incomplete: `compact_$3FCE_SLICE0_bench_path`

### FUEL-STOCK-002 — required_inputs_and_state

Requirement: Identify every required BPW, fuel-mode, enable, timer, crank/run, dropout, async/sync, and no-fuel input/state value consumed by the preserved routine.

Status: `required_not_proven`

Bench requirement: `no_if_complete_stock_preserved`

Fallback if incomplete: `compact_$3FCE_SLICE0_bench_path`

### FUEL-STOCK-003 — output_writes_and_side_effects

Requirement: Identify all ASIC/hardware-facing writes and RAM side effects performed by the preserved routine, including `$3FCE` and any scheduler/timer/no-fuel state it owns.

Status: `required_not_proven`

Bench requirement: `no_if_complete_stock_preserved`

Fallback if incomplete: `compact_$3FCE_SLICE0_bench_path`

### FUEL-STOCK-004 — order_delay_interrupt_assumptions

Requirement: Preserve write order, delay calls, interrupt/update-window assumptions, and atomicity expected by the stock fuel output driver.

Status: `required_not_proven`

Bench requirement: `no_if_complete_stock_preserved`

Fallback if incomplete: `compact_$3FCE_SLICE0_bench_path`

### FUEL-STOCK-005 — reset_crank_dropout_seed_state

Requirement: Prove reset, first-event, crank/run, dropout, unsafe, and no-fuel seed states are initialized before the preserved driver can command output.

Status: `required_not_proven`

Bench requirement: `no_if_complete_stock_preserved`

Fallback if incomplete: `compact_$3FCE_SLICE0_bench_path`

### FUEL-STOCK-006 — no_alternate_custom_writer

Requirement: Prove no alternate direct custom `$3FCE` / ASIC fuel writer exists outside the preserved stock driver path unless it remains bench-proof gated.

Status: `required_not_proven`

Bench requirement: `no_if_complete_stock_preserved`

Fallback if incomplete: `compact_$3FCE_SLICE0_bench_path`

### FUEL-STOCK-007 — physical_semantics_deferred

Requirement: Mark physical meaning of individual fuel ASIC/scheduler registers as deferred and not blocking only for a complete preserved stock driver.

Status: `required_not_proven`

Bench requirement: `no_if_complete_stock_preserved`

Fallback if incomplete: `compact_$3FCE_SLICE0_bench_path`

### FUEL-STOCK-FALLBACK — compact_direct_writer_fallback

Requirement: If complete stock-driver preservation is not proven, retain the existing compact `$3FCE` writer path and require `FUEL-001` through `FUEL-004` bench proof before `SLICE-1`.

Status: `active_fallback`

Bench requirement: `yes`

Fallback if incomplete: `current_required_path`

## Current decision state

```text
Fuel stock-driver preservation:
  contract defined
  preservation proof not complete
  no implementation emitted

Current active fuel route:
  compact $3FCE SLICE-0 bench path remains active
  FUEL-001 through FUEL-004 still required before SLICE-1 unless stock-driver preservation is completed and accepted
```

## Explicitly forbidden by this contract

```text
new runtime fuel ASM
custom direct fuel ASIC writer
custom direct $3FCE writer promoted to engine-runnable without bench proof
partial stock output driver treated as complete
unseeded BPW/fuel-mode/timer/dropout state entering preserved driver
deleting stock side effects because their physical meaning is unknown
claiming final engine safety from this contract alone
```
