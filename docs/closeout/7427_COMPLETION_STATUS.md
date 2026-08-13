# 7427 Completion Status

## Current primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN from supplied 31.zip
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

Percentages have explicit scope and must not be reduced because a later hardware/bench category remains incomplete.

## Fixed completion table

| Category | Current | Scope / completion definition | Status |
|---|---:|---|---|
| **algorithm extraction** | **100%** | Semantic production-control relationships for retained fuel, spark/knock, crank/warmup/afterstart, AE/PE/DFCO/closed-loop fuel, and idle/IAC. Physical hardware behavior excluded. | **FROZEN** |
| **scheduler/lifecycle** | **100%** | Reset/init, heartbeat/dispatch, REF/DRP lifecycle, crank/run/stall/dropout, key-off delayed shutdown, overrun/watchdog responsibilities. | **FROZEN** |
| **diagnostics/failsafe** | **100%** | Material validation, substitution, inhibit and safe-state behavior that changes production control. OEM DTC packing/reporting excluded unless behavior-changing. | **FROZEN** |
| **calibration/tuning** | **100%** | Source extraction/ownership plus direct 11,916-record audit against the actual 64 KiB BMHM BIN, reviewed production corrections, width/address/alignment review, BIN-numeric-authority rule. | **FROZEN** |
| **software-facing HW contract** | **96%** | Normalized Stage-1 endpoint inventory now exists for retained ADC/timing inputs and fuel/pump/IAC/spark/debug/shutdown outputs; HAL API and safe defaults are defined. Remaining 4% is endpoint-specific HAL implementation plus final shared-register/auxiliary semantic pinning without making physical claims. | ACTIVE |
| **physical endpoint confirmation** | **0%** | Stage-2 result matrix exists, but every physical endpoint remains `NOT_RUN` until measured stimulus/command-to-pin evidence is entered. | BENCH FRONTIER |
| **replacement-OS implementation** | **12%** | Semantic runtime ABI, actuator-disabled safe init, 6.25 ms scheduler core, REF/dropout/key-off lifecycle entry points, safe arbitration, debug heartbeat, HAL boundary and static safety verifier now exist. No target-linked processor/timer/ADC/SCI HAL or bootable ROM yet. | ACTIVE |
| **complete runnable replacement** | **0%** | Requires target boot, endpoint gates, controlled actuator enable, first start, closed-loop/learning and shutdown/dropout validation. | NOT STARTED |

## Extraction phase gate — PASSED

```text
algorithm             100  FROZEN
scheduler/lifecycle   100  FROZEN
diagnostics/failsafe  100  FROZEN
calibration/tuning    100  FROZEN
```

Calibration authority artifacts:

- `docs/closeout/7427_CALIBRATION_BIN_AUDIT_CLOSEOUT.md`
- `maps/closeout/calibration_bin_production_correction_overlay.csv`

Reviewed production corrections:

```text
$4146/$4148/$414A: use BMHM FF F5, not HAC FF FE
second DFCO table labels L4C80/L4C81: correct addresses are $4C90/$4C91
second L4EDB FCB 60: phantom source record; executable table base is $4EDC
$50ED: use BMHM D0, not HAC 00
```

No frozen extraction category should be reopened unless new executable/ROM evidence materially contradicts it or retained feature scope is deliberately expanded.

## Endpoint contract phase

Committed:

- `docs/endpoints/7427_ENDPOINT_SETUP_TEST_CONFIRM.md`
- `maps/endpoints/7427_endpoint_setup.csv`
- `maps/endpoints/7427_endpoint_test_confirm.csv`

The Stage-1 setup inventory explicitly separates software proof from electrical/pin proof. Stage-2 begins at zero and can advance only from measured evidence.

Initial actuator policy remains:

```text
fuel_permission  = FALSE
spark_permission = FALSE
iac_permission   = FALSE
pump_permission  = FALSE
aux_permission   = FALSE
```

## Replacement OS phase

Committed:

- `source/replacement_os/include/runtime_abi.inc`
- `source/replacement_os/core/safe_runtime.asm`
- `source/replacement_os/hal/HAL_API.md`
- `tools/verify_safe_runtime_boundary.py`

Current core behavior:

```text
safe initialization
6.25 ms semantic tick / 16-segment counter
REF-event ingestion without hardware ownership
REF dropout-age tracking
forced dropout state
key-off and shutdown-ready states
calibration-validity gate
semantic fuel/spark/IAC/pump/MIL requests
single safe arbitration path
all output command-valid flags inactive unless permission token is present
debug heartbeat/snapshot sequencing
```

The safe core contains no direct hardware addresses and does not expose a routine that sets an actuator permission token.

## Next implementation order

```text
1. implement read-only ADC HAL + engine-off debug transport
2. bench-confirm BATTERY_IGN and ALDL_DEBUG
3. bench-confirm TPS/MAP/COOLANT/MAT/O2 inputs
4. implement frozen validation/substitution layer above HAL
5. implement REF/DRP read-only/event HAL and bench-confirm period scaling
6. only then begin permission-gated IAC output work
7. spark/EST after IAC endpoint proof
8. injector output after existing FUEL-001..FUEL-004 proof
```

A complete algorithm never authorizes an actuator by itself.
