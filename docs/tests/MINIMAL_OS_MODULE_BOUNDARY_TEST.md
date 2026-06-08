# Minimal OS Module Boundary Test

## Goal

Validate the OS-level module boundary before creating additional source code. This test ensures each subsystem has a defined owner, interface, bench gate, and forbidden area.

## Required Artifacts

- `docs/contracts/MINIMAL_OS_MODULE_BOUNDARY.md`
- `maps/contracts/minimal_os_module_boundary.csv`
- `docs/contracts/EFI_OUTPUT_INIT_ROUTINE.md`
- `docs/contracts/MINIMAL_EFI_PW_WRITER.md`
- `docs/contracts/SPARK_MINIMAL_MODULE_BOUNDARY.md`
- `source/minimal_os/spark/README.md`
- future `IAC_IDLE_AIR_OUTPUT_CONTRACT.md`

## Static Boundary Checks

| Test | Check | Expected |
|---|---|---|
| fuel writer boundary | fuel output may expose `EFI_PW_WRITE` only | no extra runtime companion writes |
| spark no-code boundary | no `SPARK_WRITE`, no direct `$3FE8/$3FE6` writer | spark remains documentation/API only |
| IAC no-code boundary | no IAC writer before contract | IAC marked next unmapped subsystem |
| excluded subsystems | no TCC/shift/EGR/EVAP modules | excluded unless hardware-required |
| safe-state boundary | watchdog/dropout safe state exists as required-not-fully-contracted | no output-left-live assumption |
| map baseline | only committed full baseline is v0.2 | no false v0.3 references |

## Bench-Level Proof Gates

| Module | Gate | Required proof |
|---|---|---|
| RESET_INIT | ASIC init side effects | outputs stay safe and required modes are established |
| FUEL_OUTPUT | `$3FCE` control | injector PW tracks `$3FCE` count values |
| FUEL_OUTPUT | zero behavior | zero command means fuel off or known safe minimum behavior |
| SPARK_OUTPUT | `$3FE8/$3FE6` pair | EST timing follows paired command behavior |
| SPARK_OUTPUT | `$3FEC->$3FE4` | classify mirror as required ACK/status or optional |
| SPARK_OUTPUT | first-event seed | bad/zero `$3FF6/$3FDC` cannot cause wild first spark |
| SPARK_OUTPUT | bypass authority | physical bypass/EST authority trigger identified |
| IDLE_AIR_OUTPUT | stepper output sequence | IAC phase/latch sequence mapped before writer |
| WATCHDOG_SAFE_STATE | watchdog service | service sequence and reset behavior known |

## Integration Boundary Tests

### Test 1: Fuel-only output path

```text
RESET_INIT
→ EFI_OUTPUT_INIT
→ EFI_PW_WRITE(D)
```

Expected:

```text
only fuel runtime hardware write is STD $3FCE unless bench proves companion requirement
```

### Test 2: Spark authority path remains API-only

```text
SPARK_RUN_QUALIFY
→ SPARK_BYPASS_EST_AUTHORITY
→ SPARK_CONVERT_DEGREES_TO_TIME
→ SPARK_ROLLING_STATE
→ SPARK_ASIC_HANDOFF
```

Expected:

```text
no ASM writer exists until bench classifies paired command and authority behavior
```

### Test 3: IAC remains unmapped

Expected:

```text
IAC writer does not exist
IAC output contract is next technical pass
```

### Test 4: No strategy swamp regression

Expected absent:

```text
TCC strategy
shift logic
EGR strategy
EVAP strategy
unproven GM mode-word baggage
```

## Pass Criteria

```text
PASS:
  every runtime output has one owning module
  every bench-gated behavior is listed before code can be written
  unmapped IAC remains blocked from implementation
  spark remains blocked from writer code
  fuel writer remains limited to the proven/static $3FCE boundary
```

## Fail Criteria

```text
FAIL:
  any new direct hardware writer appears without source contract
  any spark writer appears before bench gates are closed
  any IAC output code appears before phase/latch contract
  any excluded subsystem is reintroduced without hardware-required evidence
  README or WORKING_STATE points to stale or nonexistent map/output state
```

## Next Step

After this boundary test passes, start:

```text
docs/contracts/IAC_IDLE_AIR_OUTPUT_CONTRACT.md
maps/contracts/iac_idle_air_output_contract.csv
docs/tests/IAC_IDLE_AIR_OUTPUT_TEST.md
tools/build_iac_output_contract.py
```
