# IAC Stock Driver Preservation Contract

Purpose: decide whether IAC can bypass physical A/B/Enable/park bench proof by preserving the complete stock IAC hardware-driver routine.

This is a static decision seam only. It does not implement IAC code, does not create a direct IAC writer, and does not relax the bench requirement for any custom A/B/Enable/park writer.

## Current decision

```text
iac_stock_driver_preservation:
  contract_defined_preservation_not_proven

custom_iac_writer:
  bench_required

active_iac_route_if_work_resumes:
  no custom direct IAC writer without bench proof
  or complete stock IAC driver preservation proof first
```

## Authority model

If stock IAC driver preservation is eventually accepted:

```text
clean idle-air decision
→ stock-compatible IAC state
→ preserved stock IAC output driver
→ stock routine owns A/B/Enable/phase/park behavior
```

If preservation is incomplete or rejected:

```text
custom direct A/B/Enable/park writer
→ physical bench proof required before use
```

## Required gates

- `IAC-STOCK-001`: identify the complete preserved stock IAC hardware-driver routine range before accepting stock-driver preservation.
- `IAC-STOCK-002`: identify all required stock-compatible IAC input RAM/state variables that the clean OS must seed before calling the preserved driver.
- `IAC-STOCK-003`: list every hardware-facing IAC-related write performed by the preserved stock driver and prove the clean OS does not write those directly outside the preserved path.
- `IAC-STOCK-004`: preserve stock write order, delay calls, interrupt assumptions, port-shadow side effects, and major-loop/segment timing assumptions.
- `IAC-STOCK-005`: prove first-event, reset-in-work, bad-shutdown, park, ignition-off, and dropout/unsafe IAC states are initialized safely before the preserved driver is trusted.
- `IAC-STOCK-006`: prove no alternate custom direct IAC writer exists and no clean-OS path writes `L3062`, `L3060`, or `L3FFC` for IAC outside the preserved stock driver.
- `IAC-STOCK-007`: mark physical IAC port-bit semantics as deferred, not blocking, only if the complete stock IAC driver is preserved behavior-for-behavior.

## Source-trace anchors currently known

```text
L925E setup candidate:
  seeds IAC setup/park-related state, including L4EB0 -> L0007

L93E1-L940A reset/park candidate:
  reset-in-work, zero-position, run/start request, ignition-off, park, engine-running branches

L9B10 / L9BD6 position update candidates:
  decrement/increment L0007 present motor position

LF405 / LFB14-LFB69 port-output candidates:
  L3062 / L3060 / L3FFC interactions, port-shadow and strobe behavior
```

These anchors do not prove complete stock-driver preservation. They only define starting points for a later static proof index.

## Current route stack

```text
IAC stock-driver preservation:
  candidate route
  contract defined
  preservation proof not complete
  not accepted as active route

Custom IAC driver:
  direct A/B/Enable/park output remains bench-required

Physical IAC port-bit semantics:
  unresolved for custom direct writes
  deferrable only if complete stock driver is preserved
```

## Explicit non-claims

```text
This contract does not claim physical meaning of each L3062/L3060/L3FFC bit.
This contract does not prove the complete stock IAC driver range.
This contract does not authorize a custom direct IAC writer.
This contract does not bypass IAC bench proof for custom A/B/Enable/park output.
This contract does not create runtime ASM.
```

## Decision outcomes

```text
iac_stock_driver_preservation:
  accepted_static_route

iac_stock_driver_preservation:
  incomplete_custom_bench_route_required

iac_stock_driver_preservation:
  rejected_custom_bench_route_required
```

Current outcome is `contract_defined_preservation_not_proven`; therefore custom direct IAC hardware output remains bench-gated.
