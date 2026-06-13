# Spark Stock Handoff Preservation Contract Test

## Goal

Verify that the spark stock handoff preservation contract reclassifies the stock ASIC handoff as a preserved hardware-driver seam without creating spark implementation code or claiming physical ASIC register semantics.

## Required Files

```text
tools/build_spark_stock_handoff_preservation_contract.py
docs/contracts/SPARK_STOCK_HANDOFF_PRESERVATION_CONTRACT.md
maps/contracts/spark_stock_handoff_preservation_contract.csv
```

## Required Static Checks

| Test | Expected |
|---|---|
| no implementation | no spark ASM, writer, or direct ASIC write implementation is created |
| category shift stated | spark moves from ASIC bench-discovery block to static-proof-gated stock preservation |
| stock handoff driver | preserved stock routine owns all ASIC-facing spark writes |
| clean OS seam | clean OS may calculate desired spark and feed stock-compatible state |
| direct writer blocked | direct custom `$3FE8/$3FE6/$3FF6/$3FDC` writes remain forbidden |
| routine range gate | `SPARK-STOCK-001` identifies complete preserved handoff routine range as required |
| input-state gate | `SPARK-STOCK-002` lists required stock-compatible input state |
| output-write gate | `SPARK-STOCK-003` lists ASIC-facing writes owned by preserved routine |
| preservation invariants | `SPARK-STOCK-004` requires write order, delay calls, interrupt assumptions, and side effects |
| seed-state gate | `SPARK-STOCK-005` requires first-event/reset/dropout state to be initialized |
| writer exclusion | `SPARK-STOCK-006` blocks alternate direct custom spark ASIC writers |
| semantics deferred | `SPARK-STOCK-007` marks physical ASIC register semantics as deferred, not blocking |
| repo labels | contract defines `custom_spark_writer`, `stock_spark_handoff_preservation`, and `spark_physical_semantics` classifications |

## Required Policy

```text
Spark hardware authority model:

1. Clean OS may calculate desired spark.
2. Clean OS may feed stock-compatible spark state.
3. Preserved stock handoff routine owns all ASIC-facing spark writes.
4. Direct custom ASIC spark writes remain forbidden.
```

## Required Critical Interpretation

```text
We are not claiming to understand each ASIC spark register physically.
We are claiming the stock handoff routine is already the proven hardware driver.
Therefore the proof burden shifts from bench-discovering ASIC semantics
to statically preserving the complete stock handoff path.
```

## Required Inputs

The contract must preserve or require upstream equivalents for:

```text
L01FD final spark accumulator
L01EE signed/current retard-advance working value
L004F bit0 sign convention
L0201 latency correction
L005F / L3FC0 period basis
L3FDC rolling state
L3FF6 EST fall / rolling anchor
L01EC or companion rolling value if used by the handoff
EST/bypass/monitor flags expected by the routine
```

## Required Preserved Ownership

The preserved stock routine owns:

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

## Bypassed Bench Discovery

For stock preservation only, the following physical semantics are deferred:

```text
exact physical meaning of L3FE8
exact physical meaning of L3FE6
whether L3FDC is dwell/rolling offset/next event
whether L3FEC -> L3FE4 is ack or diagnostic
```

## Not Bypassed

The contract must still require:

```text
static proof that the preserved routine is complete
static proof that all required inputs are seeded
static proof that all side effects are preserved
static proof that write order and delays are preserved
static proof that first-event/dropout state is initialized safely
static proof that no alternate direct custom spark ASIC writer exists
eventual real-hardware validation before trusting it on an engine
```

## Pass Criteria

```text
PASS:
  no spark implementation files are added.
  no SPARK_WRITE implementation is introduced.
  no direct custom ASIC spark writer is introduced.
  stock handoff preservation is allowed only after static contract proof.
  custom spark writer remains bench-required.
  physical ASIC register semantics are deferred, not claimed.
  required stock-compatible inputs are listed.
  preserved stock routine ownership is listed.
  seed state and side effects remain required.
```

## Fail / Rework Criteria

```text
REWORK:
  contract implies raw-angle ASIC writes are allowed.
  contract claims exact physical meaning of $3FE8/$3FE6/$3FDC/$3FF6 without bench proof.
  direct custom ASIC writes are allowed outside preserved stock handoff.
  rolling state, mirror/ack/status behavior, or EST monitor side effects are deleted.
  first-event/reset/dropout seed state is not required.
  spark implementation is added by this pass.
```
