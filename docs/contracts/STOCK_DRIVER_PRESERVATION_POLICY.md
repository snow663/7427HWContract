# Stock Driver Preservation Policy

## Purpose

Define when a subsystem can bypass per-register ASIC bench discovery by preserving the stock hardware-driver routine.

This policy prevents contradictions between fuel, spark, and IAC as the project shifts from trying to understand every ASIC register physically to preserving proven stock hardware drivers where practical.

This policy does not create runtime code, hardware writer ASM, or subsystem implementation.

## Core Rule

```text
Preserved stock driver:
  static completeness proof required
  input/state seeding proof required
  side effects/order/delay proof required
  no physical per-register proof required before use

Custom direct writer:
  bench proof required
```

## Required Static Proof for a Preserved Stock Driver

A preserved stock driver may be used as the hardware authority only if all of the following are true:

```text
1. Complete stock hardware-driver routine range is identified.
2. All required input RAM/calculated state is identified.
3. All required flags, mode bits, period bases, rolling anchors, and companion state are identified.
4. All ASIC-facing writes performed by the preserved routine are identified.
5. Write order is preserved.
6. Delay calls and timing/interrupt assumptions are preserved.
7. Mirror/ack/status behavior is preserved.
8. Monitor and fault side effects are preserved.
9. First-event, reset, dropout, and restart seed states are initialized safely.
10. No alternate custom direct writer exists for the same hardware function.
```

## What Preservation Bypasses

For a complete preserved stock hardware driver, the project does not need to bench-discover the physical meaning of each ASIC register before using the preserved path.

Allowed deferral:

```text
exact physical meaning of individual ASIC registers
internal ASIC latch/compare semantics
whether a value is ack, mirror, diagnostic, rolling state, or direct output
```

The reason is narrow: the stock routine is treated as the already-proven hardware driver. The proof burden shifts to preserving that routine completely and feeding it compatible state.

## What Preservation Does Not Bypass

Preservation does not bypass:

```text
static proof of complete routine range
static proof of input/state seeding
static proof of side effects/order/delay preservation
static proof of safe reset/first-event/dropout state
eventual real-hardware validation before trusting engine operation
```

## Custom Direct Writer Rule

A custom direct writer cannot inherit the stock driver proof.

Any new direct ASIC writer requires bench proof of:

```text
register semantics
unit conversion
write timing/window
write order
latch/commit behavior
safety/default state
physical output behavior
dropout/restart behavior
```

## Current Subsystem Classification

```text
fuel:
  bench_required_unless_stock_driver_preserved
  current compact $3FCE path remains bench-proof gated

spark:
  stock_preservation_allowed_after_static_contract
  clean spark state -> preserved stock handoff routine
  custom direct spark writer remains blocked/bench-required
  physical spark ASIC semantics deferred, not blocking

iac:
  bench_required_unless_stock_driver_preserved
  custom A/B/Enable/park writer remains bench-required
  stock-driver preservation may reclassify IAC if complete stock IAC driver is preserved
```

## Label Policy

```text
custom_direct_writer:
  blocked_bench_required

stock_driver_preservation:
  allowed_after_static_contract

physical_register_semantics:
  deferred_bench_optional_for_preservation
  required_for_custom_writer
```

## Guardrails

Allowed:

```text
clean OS calculates desired state
clean OS feeds stock-compatible state variables
preserved stock driver owns hardware-facing writes
physical per-register semantics are documented as deferred
```

Blocked:

```text
partial stock driver copy treated as complete
unseeded state entering preserved stock driver
custom direct ASIC writer without bench proof
simplified raw-register writer without bench proof
deleting rolling state, mirror/ack behavior, monitor flags, or delay assumptions
claiming physical register meaning without trace or bench evidence
claiming final engine safety solely from static preservation
```
