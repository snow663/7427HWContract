# Working State

This repository is the working directory for the 7427 hardware-contract and replacement-OS project. Git history is the version record.

## Current primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN from supplied 31.zip
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
working executable source: source/31/BMHM_HAC_ORG_7100_to_end.asm
```

## Architecture rule

```text
CALIBRATION
    ↓
ALGORITHM / CONTROL LOGIC
    ↓
COMMANDS / ARBITRATION
    ↓
HAL
    ↓
7427 HARDWARE CONTRACT
```

Classification:

```text
mathematical/control relationship = algorithm
values plugged into it             = calibration
register/mailbox/port access       = hardware/HAL
physical voltage/current/polarity  = bench endpoint
```

No replacement control algorithm may directly touch HC11 peripheral addresses, ASIC addresses, connector pins, or stock RAM mailboxes. Hardware-specific access belongs behind the 7427 HAL.

## Extraction closeout — FROZEN

```text
algorithm extraction           100%
scheduler/lifecycle            100%
diagnostics/failsafe           100%
calibration/tuning             100%
```

Authority artifacts:

- `docs/closeout/7427_EXTRACTION_CLOSEOUT.md`
- `docs/closeout/7427_DIAGNOSTIC_FAILSAFE_CLOSEOUT.md`
- `docs/closeout/7427_PRODUCTION_CALIBRATION_MANIFEST.md`
- `docs/closeout/7427_CALIBRATION_BIN_AUDIT_CLOSEOUT.md`
- `docs/closeout/7427_COMPLETION_STATUS.md`
- `maps/closeout/calibration_bin_production_correction_overlay.csv`

Do not reopen these categories because additional stock code can be traced. Reopen only for contradictory executable/ROM evidence or deliberate scope expansion.

## BMHM calibration audit result

The actual target BIN supplied in `31.zip` has been used as numeric authority.

```text
records audited:            11,916
exact matches:              11,700
value mismatches:              120
source-width errors:             96
outside-BIN records:              0
odd-address FDB reviews:        212
label-width review rows:        138
```

Production corrections are reviewed and machine-readable. Important fixes include:

```text
$4146/$4148/$414A  → use BMHM FF F5, not HAC FF FE
second DFCO table source labels L4C80/L4C81 → actual addresses $4C90/$4C91
second L4EDB FCB 60 → phantom source record; executable table base is $4EDC
$50ED → use BMHM D0, not HAC 00
```

Remote-broadcast/service and excluded transmission source-layout defects remain recorded but do not block the standalone production engine-control OS.

## Current completion

```text
software-facing HW contract     92%
physical endpoint confirmation   0%
replacement-OS implementation    5%
complete runnable replacement    0%
```

The current work phase is no longer open-ended reverse engineering.

## Active phase — endpoint contract + engine-off safe runtime

Required dataflow:

```text
physical inputs/timers
        ↓
HAL
        ↓
semantic sensor/event snapshot
        ↓
validation/substitution/lifecycle
        ↓
engine/control state
        ↓
production algorithms
        ↓
semantic command requests
        ↓
arbitration/safety
        ↓
HAL
        ↓
physical hardware
```

### Stage 1 endpoint SETUP

For every retained input/output record:

```text
semantic signal
software acquisition/command location
hardware class
candidate connector/pin if known
expected electrical behavior
expected range/polarity/frequency
scaling/conversion
sample/update cadence
evidence level
explicit bench stimulus/test procedure
```

Evidence levels:

```text
SOFTWARE_PROVEN
ELECTRICAL_INFERRED
PHYSICAL_PIN_INFERRED
BENCH_CONFIRMED
```

### Stage 2 TEST-CONFIRM

Inputs:

```text
physical stimulus → raw software value → converted semantic value
```

Outputs:

```text
semantic/software command → HAL/register/mailbox → physical output
```

Record applied command/stimulus, observed raw value, converted value, output response, polarity/monotonicity, scaling/timebase, connector/pin and PASS/FAIL. Only measured evidence may set `BENCH_CONFIRMED`.

## Current hardware gates remain valid

### Fuel

```text
compact $3FCE SLICE-0 route remains bench-only
FUEL-001..FUEL-004 remain not_run until measured evidence exists
FUEL-004 requires actual dropout/unsafe zero-path evidence
no engine-runnable injector permission yet
```

### Spark

```text
stock handoff preservation is the accepted static route
semantic spark calculation is allowed
custom direct ASIC spark writer remains bench-required
physical EST/BYPASS permission remains disabled
```

### IAC

```text
semantic IAC algorithm is complete
stock-driver preservation proof is not yet complete
custom direct A/B/Enable/park writer remains bench-required
physical IAC permission remains disabled
```

Algorithm completion never authorizes an actuator.

## Engine-off safe runtime implementation target

Build next:

```text
RESET/BOOT
  → relocate/init processor state
  → initialize HAL-owned hardware only
  → force all production actuator permissions FALSE

BASE SCHEDULER
  → 6.25 ms heartbeat-compatible timing
  → semantic task/event flags
  → overrun detection

SENSOR ACQUISITION
  → raw HAL snapshot
  → no algorithm reads hardware directly

VALIDATION/SUBSTITUTION
  → MAP/TPS/CTS/MAT/O2/REF/battery validity
  → deterministic substitutions from frozen diagnostic closeout

LIFECYCLE
  → key-on / crank / run / dropout / key-off / shutdown states

ALDL/DEVELOPMENT OBSERVABILITY
  → expose raw snapshot, converted values, validity, lifecycle, command requests and permission gates

SAFE COMMAND ARBITRATION
  → fuel_permission = FALSE
  → spark_permission = FALSE
  → iac_permission = FALSE
  → retained auxiliary permissions = FALSE
```

No physical actuator may become active merely because its semantic request is nonzero.

## Bring-up sequence

```text
safe runtime
→ sensor endpoints
→ IAC
→ spark / EST / dwell
→ injectors
→ first controlled engine start
→ closed loop / learning
→ retained auxiliary outputs
```

The next repo work is normalized endpoint setup records plus engine-off safe-runtime source/API scaffolding, not more broad stock disassembly.
