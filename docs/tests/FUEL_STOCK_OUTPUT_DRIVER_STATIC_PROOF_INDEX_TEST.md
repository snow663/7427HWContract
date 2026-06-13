# FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX_TEST

## Scope

This test verifies that the fuel stock-output-driver static proof index is a decision/proof artifact only.

It must not create runtime ASM, a fuel writer, a stock-driver implementation, an ALDL/debug packet, or an engine-runnable SLICE-1 path.

## Required files

```text
tools/build_fuel_stock_output_driver_static_proof_index.py
docs/contracts/FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX.md
maps/contracts/fuel_stock_output_driver_static_proof_index.csv
docs/tests/FUEL_STOCK_OUTPUT_DRIVER_STATIC_PROOF_INDEX_TEST.md
```

## Required decision state

The current decision must remain:

```text
fuel_stock_driver_preservation:
  incomplete_continue_3FCE_bench_route
```

The test fails if this artifact claims `accepted_static_route` without proving all required stock-driver range, inputs, outputs, scheduler/timer dependencies, side effects, reset state, first-event state, dropout/no-fuel paths, and direct-writer exclusion.

## Static requirements

The proof index must include rows for:

```text
complete preserved stock fuel output-driver range
required input RAM/state variables
hardware-facing fuel writes
scheduler/timer/interrupt dependencies
enable/disable/DFCO/clear/dropout paths
clean-OS stock-compatible state feasibility
route decision
```

## Guardrails

The proof index must preserve this distinction:

```text
Fuel preservation contract exists
≠ fuel preservation proof is complete
≠ compact $3FCE bench gate is bypassed
```

## Pass criteria

The artifact passes if it identifies the candidate stock driver route and records the current decision as `incomplete_continue_3FCE_bench_route`.

## Fail criteria

The artifact fails if it emits fuel implementation code, promotes a partial stock driver as complete, bypasses FUEL-001 through FUEL-004 under the compact route, or creates a custom direct $3FCE writer.
