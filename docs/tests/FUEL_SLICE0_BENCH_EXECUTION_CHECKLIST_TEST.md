# FUEL SLICE-0 Bench Execution Checklist Test

## Purpose

Verify that the bench execution checklist remains a bench-proof planning artifact only.

## Required Files

```text
tools/build_fuel_slice0_bench_execution_checklist.py
docs/bench/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST.md
maps/bench/fuel_slice0_bench_execution_checklist.csv
docs/tests/FUEL_SLICE0_BENCH_EXECUTION_CHECKLIST_TEST.md
```

## Static Checks

The checklist must state:

```text
active route = compact $3FCE SLICE-0 bench path
FUEL-001 through FUEL-004 remain required before SLICE-1
FUEL-004 requires real dropout/unsafe zero path
$0000 vector proof is not dropout proof
no implementation is created
no proof is marked pass by default
```

The CSV must include rows for:

```text
PRE-001
FUEL-003-ZERO
FUEL-001-1MS
FUEL-001-2MS
FUEL-002-3MS
FUEL-001-4MS
FUEL-004-DROPOUT
POST-001
```

## Non-Relaxation

This checklist must not:

```text
create SLICE-1
mark FUEL-001/FUEL-002/FUEL-003/FUEL-004 as passed
replace maps/bench/fuel_slice0_bench_results.csv
claim dropout proof from FUEL_SLICE0_WRITE_ZERO
create runtime ASM or hardware writer code
relax compact $3FCE bench proof requirements
```

## Pass Criteria

The artifact passes if it gives a complete bench execution sequence and preserves all existing fuel gates.

## Fail Criteria

Fail if it permits SLICE-1 before FUEL-001 through FUEL-004 pass, treats the zero vector as dropout proof, or introduces implementation behavior.
