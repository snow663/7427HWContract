# Spark Stock Handoff Preservation Contract

## Purpose

Lock the stock 7427 / `$31` spark ASIC handoff routine as the required spark hardware driver seam.

This document does not implement spark code, does not create a spark writer, and does not claim physical semantics for each ASIC spark register.

It changes the proof category from:

```text
bench-blocked because ASIC meaning is unknown
```

to:

```text
static-proof-gated because stock ASIC handoff is preserved
```

## Spark Hardware Authority Model

```text
1. Clean OS may calculate desired spark.
2. Clean OS may feed stock-compatible spark state.
3. Preserved stock handoff routine owns all ASIC-facing spark writes.
4. Direct custom ASIC spark writes remain forbidden.
```

## Critical Interpretation

```text
We are not claiming to understand each ASIC spark register physically.
We are claiming the stock handoff routine is already the proven hardware driver.
Therefore the proof burden shifts from bench-discovering ASIC semantics
to statically preserving the complete stock handoff path.
```

## Allowed Path

```text
clean spark calculation
→ stock-compatible final spark state
→ preserved stock spark handoff routine
→ ASIC writes handled by preserved routine
```

## Forbidden Path

```text
clean spark calculation
→ direct $3FE8 / $3FE6 / $3FDC / $3FF6 writes
```

## Required Inputs to Preserve

```text
L01FD final spark accumulator
L01EE signed/current retard-advance working value, or its upstream equivalent
L004F bit0 sign convention
L0201 latency correction
L005F / L3FC0 period basis
L3FDC rolling state
L3FF6 EST fall / rolling anchor
L01EC or companion rolling value if used by the handoff
EST/bypass/monitor flags expected by the routine
```

## Preserved Stock Routine Owns

```text
conversion into timing-domain values
add/subtract against rolling anchor
L3FE8 write
L3FE6 write
L3FDC update
L3FF6 update
L3FEC -> L3FE4 mirror/ack/status behavior
EST monitor side effects
```

## What This Bypasses

For stock handoff preservation only, this bypasses bench proof of:

```text
exact physical meaning of L3FE8
exact physical meaning of L3FE6
whether L3FDC is dwell/rolling offset/next event
whether L3FEC -> L3FE4 is ack or diagnostic
```

## What This Does Not Bypass

```text
static proof that the preserved routine is complete
static proof that all required inputs are seeded
static proof that all side effects are preserved
static proof that write order and delays are preserved
static proof that first-event/dropout state is initialized safely
static proof that no alternate direct custom spark ASIC writer exists
eventual real-hardware validation before trusting it on an engine
```

## Gate Rows

| Gate | Category | Object | Allowed | Blocked | Semantics | Gate |
|---|---|---|---|---|---|---|
| `SPARK-STOCK-001` | routine_range | complete preserved handoff routine | allowed_after_static_contract | new_spark_writer; simplified_raw_angle_writer | deferred_not_blocking | must identify complete routine range before extraction/link |
| `SPARK-STOCK-002` | required_inputs | stock-compatible spark state inputs | allowed_after_static_contract | unseeded_inputs; deleted_state | deferred_not_blocking | all required inputs must be present before preserved routine can be used |
| `SPARK-STOCK-003` | output_writes | ASIC-facing writes performed by preserved routine | allowed_only_inside_preserved_stock_handoff | direct_custom_asic_writes | deferred_not_blocking | no alternate direct writer may exist |
| `SPARK-STOCK-004` | preservation_invariants | write order, delay calls, interrupt assumptions, side effects | allowed_if_behavior_preserved | changed_order; removed_delay; reordered_status_mirror | deferred_not_blocking | behavior-for-behavior preservation required |
| `SPARK-STOCK-005` | seed_state | first-event / reset / dropout seed state | allowed_after_seed_contract | uninitialized_first_event; unsafe_dropout_restart | deferred_not_blocking | must be safe before engine use |
| `SPARK-STOCK-006` | writer_exclusion | no alternate direct custom spark ASIC writer | custom_spark_writer_blocked_bench_required | direct $3FE8/$3FE6/$3FF6/$3FDC writer; SPARK_WRITE | deferred_not_blocking | fails if direct writer exists |
| `SPARK-STOCK-007` | physical_semantics | ASIC spark register physical meaning | deferred_bench_optional | physical_semantics_required_before_preservation | deferred_not_blocking | not blocking for preserved stock handoff; still required for custom writer |
| `SPARK-STOCK-008` | classification | repo labels | stock_spark_handoff_preservation_allowed_after_static_contract | custom_spark_writer_blocked_bench_required | spark_physical_semantics_deferred_bench_optional | used to prevent future regression to wrong gate |

## Repo Classification

```text
custom_spark_writer:
  blocked_bench_required

stock_spark_handoff_preservation:
  allowed_after_static_contract

spark_physical_semantics:
  deferred_bench_optional
```

## Discipline

No spark implementation is created by this contract. First lock the seam: clean spark decision in, preserved stock hardware driver out.
