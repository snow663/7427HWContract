# IAC Stock Driver Preservation Contract Test

This test defines acceptance criteria for the static IAC preservation contract. It is not a runtime or bench test.

## Required files

```text
tools/build_iac_stock_driver_preservation_contract.py
docs/contracts/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT.md
maps/contracts/iac_stock_driver_preservation_contract.csv
docs/tests/IAC_STOCK_DRIVER_PRESERVATION_CONTRACT_TEST.md
```

## Static assertions

The contract must state:

```text
IAC stock-driver preservation is only a candidate route.
Current decision is contract_defined_preservation_not_proven.
Custom direct A/B/Enable/park writer remains bench-required.
No IAC implementation is emitted.
No direct L3062/L3060/L3FFC writer is authorized outside a proven preserved stock driver.
Physical port-bit semantics may be deferred only for complete stock-driver preservation.
```

## Required gate rows

The CSV must include:

```text
IAC-STOCK-001 complete preserved driver range
IAC-STOCK-002 required input/state seeding
IAC-STOCK-003 hardware-facing writes
IAC-STOCK-004 order/delay/interrupt/side effects
IAC-STOCK-005 reset/park/dropout state
IAC-STOCK-006 no alternate custom writer
IAC-STOCK-007 physical semantics deferred only if preserved complete
IAC-STOCK-DECISION current decision
```

## Source-trace minimum

The contract should identify these known source anchors as starting points, not as a completed proof:

```text
L925E setup candidate
L93E1-L940A reset/park candidate
L9B10 / L9BD6 position update candidates
LF405 / LFB14-LFB69 port-output candidates
```

## Fail conditions

The contract fails if it:

```text
marks IAC stock-driver preservation accepted without a later static proof index
authorizes custom direct L3062/L3060/L3FFC writes
claims physical A/B/Enable/park bit meanings without bench or trace evidence
emits runtime ASM
relaxes bench proof for custom direct IAC hardware output
treats partial stock source anchors as a complete preserved driver
```
