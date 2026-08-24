# BMHM 0.3.2 — Bosch-style engine-state layer

Experimental successor to BMHM 0.3.1. This build moves `$31` toward an early Motronic/L-Jetronic-style state model: corrected throttle position determines closed-throttle versus part-load operation, and RPM determines DECEL versus TRUE IDLE while the throttle is closed. Vehicle speed remains observable but is not used to decide engine idle state.

## Binary identity

- File: `BMHM_0.3.2.bin`
- Base: `BMHM_0.3.1.bin`
- SHA-256: `1ab8e29525d963e49b749371dc7edaff8a3b3ef70286c0af04571c328f7c1b6e`
- `$31` checksum: `$2285` at `$4006-$4007`

The binary itself is distributed separately from this workbench documentation.

## State model

The state input is final corrected engine TPS `$01D9`, downstream of the stock TPS A/D and self-zero/filter processing.

### PART / DRIVE

`TPS > virtual closed-throttle threshold`

- normal/open-TPS VE path
- normal DAMP1 closed-loop lambda eligible
- normal BLM cells
- stock PE/WOT strategy remains intact

### DECEL

`TPS closed` and `RPM above TRUE-IDLE window`

- TRUE-IDLE flag `$0050.b7` is clear
- closed-throttle VE surface remains available below the stock 1800-RPM selector ceiling
- BLM cell 16 is not forced
- idle spark is disabled
- IAC closed-loop idle control is disabled
- with `$FE9F bit0=1`, lambda is open loop; stock DFCO remains independent

### TRUE IDLE

`TPS closed` and `RPM inside TRUE-IDLE window`

- `$0050.b7` is set centrally
- closed-throttle VE surface
- BLM cell 16
- idle spark enabled through stock downstream qualifications
- IAC closed-loop idle control permitted
- with `$FE9F bit0=1`, lambda is open loop

## Tunable state thresholds

| Address | Parameter | Raw | Equation | Default |
|---|---|---:|---|---:|
| `$FF88` | True Idle Enter RPM | 44 | `X * 25` | 1100 RPM |
| `$FF89` | True Idle Exit RPM | 48 | `X * 25` | 1200 RPM |
| `$FF8A` | Virtual Idle Switch Enter TPS | 2 | `X * 100 / 256` | 0.78125% |
| `$FF8B` | Virtual Idle Switch Exit TPS | 3 | `X * 100 / 256` | 1.171875% |

Entry requires TPS <= `$FF8A` and RPM <= `$FF88`. Once TRUE IDLE is active, it is held while TPS <= `$FF8B` and RPM <= `$FF89`. `$0050.b7` itself is the hysteresis memory.

These TPS values are **not absolute sensor voltage thresholds**. They operate on `$01D9`, after the stock learned TPS-zero compensation.

## Centralization changes

The old 0.3.1 implementation used the RPM gate mainly for IAC and idle spark while the broader GM idle/fuel classification could remain active during rolling decel. 0.3.2 moves the state decision upstream:

- `$899B -> $FEF8`: centralized corrected-TPS + RPM TRUE-IDLE classifier.
- BLM cell 16 now keys from centralized `$0050.b7`.
- IAC closed-loop qualification keys from centralized `$0050.b7`.
- idle spark keys from centralized `$0050.b7`.
- the closed-throttle VE selector uses the same virtual closed-throttle TPS boundary but remains independent of TRUE-IDLE RPM, preserving a dedicated decel/closed-throttle fuel surface.

This lets DECEL and TRUE IDLE share a closed-throttle fuel surface without pretending that a 1500–2000 RPM overrun event is an actual idle-control event.

## Lambda behavior

DAMP1 is unchanged.

`$FE9F bit0` is redefined for this build as **Closed Throttle Open Loop**:

- `0`: stock closed-loop eligibility
- `1`: closed throttle is forced open loop; part load remains eligible for DAMP1 closed loop

`$FE9F bit1` remains the global closed-loop fueling disable and the existing BLM-neutralization and INT/P-neutralization hooks remain unchanged.

With the default `$FE9F=$01`, DECEL and TRUE IDLE are open loop, while part load is closed-loop eligible. DFCO remains separately qualified and can still cut fuel on decel.

## DAMP1 status

No further reduction in closed-loop authority was made in 0.3.2. The 2026-08-23 validation of 0.3.1 showed, versus the pre-DAMP1 reference in the target load region:

- mean `abs(INT-128)` down about 22.6%
- median stable-load BPW range down about 20.6%
- 75th-percentile stable-load BPW range down from 8.51% to 6.26%

The downstream wideband did not yet show a reduced AFR swing, so DAMP1 is retained as a useful but not complete narrowband-controller damping change.

## TPS self-zero caveat

The stock TPS processing remains intact. Raw TPS is acquired at `$00A6`, the learned zero is maintained in `$02F6`, and corrected engine TPS is produced through `$01A6/$01D9`.

The runtime upward TPS-zero learning path around `$B12C-$B15D` still contains its original decel qualification based on filtered VSS-derived state. 0.3.2 intentionally does **not** alter that learner yet. That dependency should be traced and redesigned separately rather than replaced with a fake fixed speed.

## Future AUX high idle

AUX high idle is **not implemented in 0.3.2**. The new state layer provides a clean insertion point: a future AUX request can deliberately force idle-control authority above the normal `$FF88/$FF89` RPM window while selecting its own RPM target and, if desired, its own VE/spark/AFR calibration zone. `$FF60-$FF87` remains unused cave space in this build for future work.

## Expected validation signature

On a warm validation drive:

- closed TPS above 1200 RPM: Idle Flag OFF, BLM cell not forced to 16, idle spark OFF, IAC CL OFF; closed-throttle VE may still be active below 1800 RPM.
- closed TPS below 1100 RPM: Idle Flag ON, BLM cell 16, idle spark ON, IAC CL permitted.
- TPS above 1.17%: normal part-load state and closed-loop eligibility.

The key test is that idle-related consumers should now transition together from one centralized state bit rather than each making an independent vehicle-state inference.