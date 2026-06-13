# Stock Driver Preservation Policy Test

## Goal

Verify that the repo-level stock-driver preservation policy clearly separates preserved stock hardware drivers from custom direct ASIC writers.

This is a static policy contract only. It must not create runtime ASM, subsystem implementation, custom writers, or bench result claims.

## Required Files

```text
tools/build_stock_driver_preservation_policy.py
docs/contracts/STOCK_DRIVER_PRESERVATION_POLICY.md
maps/contracts/stock_driver_preservation_policy.csv
```

## Required Checks

| Test | Expected |
|---|---|
| preserved stock driver rule | static completeness/input/side-effect proof required |
| custom direct writer rule | bench proof required |
| physical semantics rule | deferred for complete preservation, required for custom writer |
| fuel classification | bench-required unless stock fuel driver is preserved |
| spark classification | stock handoff preservation allowed after static contract |
| IAC classification | bench-required unless stock IAC driver is preserved |
| implementation boundary | no runtime ASM or writer created |
| final validation boundary | real-hardware validation still required before trusting engine operation |

## Required CSV Rows

```text
STOCK-DRV-001 preserved_stock_driver_definition
STOCK-DRV-002 input_state_seeding
STOCK-DRV-003 side_effects_order_delay
STOCK-DRV-004 custom_direct_writer
STOCK-DRV-005 physical_register_semantics
STOCK-DRV-006 fuel_policy
STOCK-DRV-007 spark_policy
STOCK-DRV-008 iac_policy
STOCK-DRV-009 runtime_validation
```

## Pass Criteria

```text
PASS:
  policy separates preserved stock driver from custom direct writer.
  preserved stock driver requires static completeness proof.
  custom direct writer requires bench proof.
  spark can use preserved stock handoff after static contract.
  fuel remains bench-proof gated unless stock fuel driver is preserved.
  IAC remains bench-proof gated unless stock IAC driver is preserved.
  physical ASIC semantics are deferred only for complete preserved stock drivers.
  no implementation files are created by this policy.
```

## Fail / Rework Criteria

```text
REWORK:
  policy permits custom direct writer without bench proof.
  policy treats partial stock routine copy as complete preservation.
  policy lets physical semantics deferral justify custom writes.
  policy claims final engine safety from static preservation alone.
  policy creates runtime ASM, hardware writer, or implementation code.
```
