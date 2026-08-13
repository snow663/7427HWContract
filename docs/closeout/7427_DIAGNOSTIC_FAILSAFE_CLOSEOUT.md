# 7427 Diagnostic / Failsafe Closeout

## Purpose

Freeze replacement-relevant validation, substitution, and safe-state behavior independently from OEM DTC counting/reporting.

Rule:

```text
fault detector / DTC state != fallback
```

A replacement OS may report faults differently, but it must preserve or deliberately replace behavior that materially protects or changes fuel, spark, idle, startup/shutdown, or actuator permission.

## Semantic fault-handling pipeline

```text
raw input / event
→ plausibility / timeout / consistency validation
→ VALID | DEGRADED | INVALID
→ substitute / clamp / inhibit / safe-state policy
→ engine/control state
→ production algorithms
→ semantic commands
→ arbitration / permission
```

No algorithm consumes a raw hardware fault bit directly in the clean replacement architecture.

## Material production-control matrix

| Fault / invalid state | Stock source evidence | Material stock behavior | Replacement semantic policy | DTC clone required? |
|---|---|---|---|---|
| MAP invalid / Error 33/34 family | `L7BA7+`, `L4E68-L4E6A` | During valid run context, estimate substitute MAP from TPS/RPM using calibrated coefficient/bias; otherwise clamp/fallback to calibrated default `L4E68` (source comment 90.8 kPa). | `map.valid=false`; use bounded TPS/RPM MAP estimate when engine-state inputs are valid, else calibrated safe default; expose degraded flag. | No. Reporting optional. |
| TPS high/low invalid / Error 21/22 family | `LB172+`, `L5B22` | Load calibrated default TPS before filtering; source comment gives 35% default. | `tps.valid=false`; substitute calibrated default or a clean bounded limp value; disable transient decisions that require trustworthy delta-TPS. | No. |
| Coolant high/low invalid / Error 14/15 family | `LC9C0+`, `L5B17` | Substitute calibrated coolant default before filter; source comment gives 90 C. | `cts.valid=false`; substitute calibrated safe-warm temperature so enrichment/idle/spark do not remain indefinitely cold; expose fault. | No. |
| MAT/IAT invalid / Error 23/25 family | `LDC7E+`, `L4E48` | Use calibrated MAT default; source comment gives -18 C. | `iat.valid=false`; use calibrated default and disable any correction that would become unsafe from implausible temperature. | No. |
| O2 invalid / Error 13 family | O2 diagnostic path and closed-loop qualification paths | DTC state is reporting; material behavior is that invalid/not-ready oxygen feedback must not drive closed-loop correction. | `o2.valid=false` forces open-loop/no O2 trim update; retain last learned value only if explicitly desired and bounded. | No. |
| Knock sensor/circuit invalid / Error 43 | `AAAC-AAB3`, `L4E77` | Spark path applies fixed calibrated knock-fail retard; source comment at `L4E77` indicates 4 deg. | `knock.valid=false` selects calibrated fixed protective retard and disables knock learning/update. | No. |
| EST monitor / Error 42 | `SPARK_EST_FAULT_MONITOR_CONTRACT.md` and `ABxx/ACxx` monitor state | Source proves monitor/counter/status behavior but does not prove that DTC state itself forces bypass, kills fuel, or blocks the timing calculation. `$3FEC->$3FE4` remains possible shared HW handshake. | Keep EST-monitor reporting separate. Do not invent a fallback from DTC42. Physical authority/ACK behavior remains HAL/bench-gated. A replacement may implement an independent spark-authority watchdog. | No, unless compatibility desired. |
| REF/DRP missing / invalid period | REF/DRP event paths, run flags, boot/safe-state contracts | Loss of trustworthy reference invalidates RPM/run timing and leads to run/fuel state clearing/dropout behavior. | Invalidate `engine_ref_valid`; force fuel no-pulse, spark safe/bypass intent, cancel period-dependent control, preserve IAC hold/safe target. | No. This is a safety state, not primarily a DTC. |
| Battery undervoltage / ignition-off qualification | `L8613+`, `L91A3+` | Battery thresholds participate in ignition-off/low-battery state and IAC movement permission; IAC stepper is inhibited at inappropriate voltage. | `battery.valid/low/off` state gates output permissions; no stepper motion below configured operating threshold; key-off state enters shutdown lifecycle. | No. |
| Battery overvoltage affecting IAC | `L91A3-L91B8` | Source compares battery against 16.9 V and alters IAC enable candidate / low-battery-style inhibit path. | Bound IAC permission to validated supply window. Exact electrical threshold is calibration/endpoint policy, not hardcoded HAL behavior. | No. |
| NVRAM / retained-state invalid | boot/init paths around `L723C+`, IAC init/park path | Learned/retained state is rejected and safe/default seeds are used; IAC retained states are reinitialized. | Validate retained block/checksum/version; on failure use deterministic defaults for BLM/idle learning/park state. | No. |
| Calibration/ROM integrity invalid | boot checksum gate `L71D3+` | Stock verifies additive checksum and mask ID before normal boot path. | Replacement uses its own calibration header/version/checksum/CRC; invalid calibration prevents production actuator enable and reports development fault. | No need to reproduce GM checksum algorithm if replacement image format differs. |
| Scheduler overrun | `L793D+ / L7958+` major-loop overrun checks | Stock detects a missed 6.25 ms period and records state. | Runtime measures task deadline/overrun; repeated or critical overruns inhibit production actuator permission or enter safe state. | No. |
| COP/watchdog failure | boot/COP service paths | Processor watchdog protects against dead control execution. | Service watchdog only from healthy scheduler path; failure resets into actuator-disabled boot state. | No. |
| IAC requested direction change | `L91C2-L91E6` | Direction bit changes before position changes, causing a zero-step direction reversal. | Preserve as command-state invariant to avoid phase/count discontinuity. | Not a diagnostic. |
| IAC actual/desired count corrupt/out of range | IAC init/park/limit logic | Stock bounds/seeds state and parks/resets under selected conditions. | Range-check software position; on corruption disable motion and require deterministic re-home/park procedure behind permission gate. | Optional diagnostic. |

## Error reporting versus fallback

The following categories may be simplified without losing replacement behavior:

- OEM error counters and hysteresis packing;
- current-vs-history bit placement;
- ALDL DTC presentation format;
- service-tool latches that do not alter production command permission;
- transmission and emissions DTCs for excluded subsystems.

Preserve the *cause, qualification, and material response* where the response changes engine control.

## Replacement validity state

Recommended clean state representation:

```text
enum Validity {
    VALID,
    DEGRADED_SUBSTITUTE,
    INVALID_INHIBIT
}

SensorSnapshot {
    map, tps, cts, iat, o2, battery, baro, ref_period, ...
    validity per signal
}

ControlHealth {
    ref_valid
    calibration_valid
    scheduler_healthy
    watchdog_healthy
    spark_authority_valid
    fuel_output_permission
    iac_output_permission
}
```

Algorithms consume semantic values and validity/substitution results. They do not read DTC RAM words or hardware status registers directly.

## Closed status

For semantic production-control scope, diagnostics/failsafe extraction is **100% complete and frozen**.

Remaining work belongs to:

- HAL behavior of hardware fault/status registers;
- connector/pin/electrical bench confirmation;
- physical actuator response;
- optional compatibility DTC/ALDL formatting.
