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

## Architecture

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

Control algorithms may not directly touch HC11 peripheral addresses, ASIC addresses, stock hardware mailboxes, connector pins, or electrical polarity logic.

## Extraction closeout — frozen

```text
algorithm extraction           100%
scheduler/lifecycle            100%
diagnostics/failsafe           100%
calibration/tuning             100%
```

Calibration is now closed against the actual 64 KiB BMHM image. See:

- `docs/closeout/7427_CALIBRATION_BIN_AUDIT_CLOSEOUT.md`
- `maps/closeout/calibration_bin_production_correction_overlay.csv`

Key numeric/source corrections:

```text
$4146/$4148/$414A → BMHM FF F5, not HAC FF FE
second DFCO table repeated L4C80/L4C81 labels → actual $4C90/$4C91
second L4EDB FCB 60 → phantom record; executable table base is $4EDC
$50ED → BMHM D0, not HAC 00
```

Do not reopen frozen extraction categories unless new executable/ROM evidence materially contradicts them or feature scope is deliberately expanded.

## Current completion

```text
software-facing HW contract     96%
physical endpoint confirmation   0%
replacement-OS implementation   12%
complete runnable replacement    0%
```

## Endpoint phase

Committed:

- `docs/endpoints/7427_ENDPOINT_SETUP_TEST_CONFIRM.md`
- `maps/endpoints/7427_endpoint_setup.csv`
- `maps/endpoints/7427_endpoint_test_confirm.csv`

Every retained endpoint now has a Stage-1 setup record with software location, hardware class, expected electrical behavior, scaling/cadence, evidence level, permission default, and explicit bench procedure.

All Stage-2 physical rows remain `NOT_RUN`. Software proof does not count as physical proof.

## Replacement safe runtime

Committed:

- `source/replacement_os/include/runtime_abi.inc`
- `source/replacement_os/core/safe_runtime.asm`
- `source/replacement_os/hal/HAL_API.md`
- `source/replacement_os/hal/adc_read.asm`
- `source/replacement_os/hal/ref_read.asm`
- `tools/verify_safe_runtime_boundary.py`

Implemented semantic core:

```text
actuator-disabled reset state
6.25 ms semantic scheduler tick
16-segment counter
REF event ingestion
REF dropout age / forced safe state
key-off / shutdown-ready states
calibration-validity gate
semantic fuel/spark/IAC/pump/MIL requests
single command-arbitration path
debug heartbeat state
```

Implemented read-only HAL:

```text
HC11 ADC control/result access only
TPS raw
MAP raw
O2 raw
coolant raw
MAT raw/inversion
battery raw
REF period read from $3FC0
```

The safe core itself contains no hardware addresses. Direct `$30xx/$3Fxx` accesses exist only in the HAL files.

## Permission state

```text
fuel_permission  = FALSE
spark_permission = FALSE
iac_permission   = FALSE
pump_permission  = FALSE
aux_permission   = FALSE
```

No routine in the safe core sets an actuator permission token.

Existing subsystem gates remain valid:

```text
fuel: FUEL-001..FUEL-004 still require measured bench proof
spark: preserved stock handoff route only; custom direct writer forbidden until bench proof
IAC: no custom direct A/B/Enable/park writer until physical proof or completed preserved-driver proof
```

## Next valid work

```text
1. bring up ALDL/development observability with all actuator permissions false
2. bench BATTERY_IGN
3. bench TPS/MAP/COOLANT/MAT/O2 input paths
4. implement/verify validation + substitution layer above the read-only HAL
5. bench REF/DRP timing input and period/RPM scaling
6. then permission-gated IAC endpoint work
7. then spark/EST
8. then injector output using existing FUEL-001..FUEL-004 proof sequence
```

Do not return to broad disassembly as a substitute for endpoint testing or implementation.
