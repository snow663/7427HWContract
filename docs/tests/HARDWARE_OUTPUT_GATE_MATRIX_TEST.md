# Hardware Output Gate Matrix Test

Goal: verify that `HARDWARE_OUTPUT_GATE_MATRIX` remains a single-source-of-truth planning artifact and does not relax subsystem gates or create implementation.

## Required files

```text
tools/build_hardware_output_gate_matrix.py
docs/contracts/HARDWARE_OUTPUT_GATE_MATRIX.md
maps/contracts/hardware_output_gate_matrix.csv
docs/tests/HARDWARE_OUTPUT_GATE_MATRIX_TEST.md
```

## Required CSV rows

```text
fuel_compact_3FCE
fuel_stock_output_driver
spark_stock_handoff
spark_custom_writer
iac_stock_driver
iac_custom_writer
```

## Required decisions

```text
fuel_compact_3FCE: active_bench_route
fuel_stock_output_driver: candidate_incomplete
spark_stock_handoff: accepted_static_route
spark_custom_writer: blocked_bench_required
iac_stock_driver: contract_defined_not_proven
iac_custom_writer: blocked_bench_required
```

## Required route statements

```text
fuel_compact_3FCE:
  compact $3FCE SLICE-0 bench route remains active
  FUEL-001 through FUEL-004 still block SLICE-1

fuel_stock_output_driver:
  stock preservation is considered but incomplete
  incomplete proof does not bypass $3FCE bench route

spark_stock_handoff:
  preserved stock handoff accepted as static-proof route
  physical ASIC spark semantics deferred

spark_custom_writer:
  custom direct ASIC writer remains bench-required

iac_stock_driver:
  preservation contract defined but proof incomplete

iac_custom_writer:
  custom direct A/B/Enable/park writer remains bench-required
```

## Static checks

PASS requires:

```text
no runtime ASM emitted
no subsystem implementation emitted
no custom writer emitted
no bench result claimed
no SLICE-1 gate relaxed
fuel compact $3FCE remains active bench route
fuel stock output-driver preservation remains incomplete
spark stock handoff remains static-proof route only
custom spark writer remains bench-required
IAC stock-driver preservation remains not proven
custom IAC writer remains bench-required
```

FAIL if any wording implies:

```text
FUEL-001 through FUEL-004 passed without bench evidence
compact $3FCE bench path bypassed by an incomplete stock fuel proof
IAC stock-driver preservation accepted without proof index
custom direct ASIC spark writes allowed
custom direct IAC A/B/Enable/park writes allowed
runtime ASM created by this matrix
```
