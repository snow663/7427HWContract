# V1 Sensor Semantic and Validation Contract

## Status

`DESIGN BASELINE — formula-first planning artifact`

This document defines how V1 turns hardware observations into trustworthy semantic engine values. It separates raw acquisition, engineering conversion, filtering, validation, substitution/fallback, and module qualification.

The central rule is:

```text
RAW VALUE
  -> engineering conversion
  -> filtering where appropriate
  -> validity/plausibility evaluation
  -> semantic value + validity metadata
  -> module-specific fallback/qualification
```

No control module is allowed to infer sensor validity merely from a plausible-looking substituted number.

## 1. Required semantic channels

V1 primary inputs:

```text
REF / RPM
TPS
MAP
BARO derived from qualified MAP
MAT / IAT
CTS
battery voltage
narrowband O2 optional
wideband O2 optional
knock input optional
```

Unused stock hardware endpoints remain `RESERVED_UNUSED_V1` and are not sampled merely because the stock OS used them.

## 2. Value layers

Each sensor should expose, where applicable:

```text
RAW              direct ADC/register/event observation
ENG              converted engineering value
FILTERED         value after explicit signal filtering
VALID            boolean semantic validity
SUBSTITUTED      boolean indicating control fallback is in use
CONTROL          value supplied to a module when that module permits substitution
FAULT_REASON     compact reason/state code
```

ADX should expose enough of these layers to distinguish a bad sensor from a bad conversion, filter, or fallback.

## 3. Sensor state model

Recommended common state:

```text
SENSOR_DISABLED
SENSOR_VALID
SENSOR_INVALID_RANGE
SENSOR_INVALID_RATE
SENSOR_INVALID_PLAUSIBILITY
```

`DISABLED` is not a fault for optional hardware such as NB, WB, or knock when the feature is intentionally disabled.

A sensor can additionally report:

```text
LAST_VALID_AVAILABLE
SUBSTITUTION_ACTIVE
```

without changing the underlying invalid state.

## 4. Common validation timing

To avoid one noisy sample causing state chatter, validity changes use explicit qualification timers/counts:

```text
INVALID_CONFIRM_TIME
VALID_RECOVERY_TIME
```

These may be common defaults or sensor-specific values.

A hard impossible electrical value may invalidate immediately if safety requires it.

## 5. TPS conversion

TPS is a physical/setup-calibrated linear sensor.

Preferred tuner-facing setup:

```text
TPS_CLOSED_V
TPS_WOT_V
```

Conversion:

```text
TPS_PERCENT = clamp(0, 100,
    100 * (TPS_V - TPS_CLOSED_V)
        / (TPS_WOT_V - TPS_CLOSED_V))
```

Derived:

```text
TPS_RATE = d(TPS_PERCENT) / dt
```

Validation includes:

```text
electrical min/max voltage
maximum believable rate where useful
TPS_CLOSED_V < TPS_WOT_V configuration sanity
```

### TPS invalid behavior

TPS invalid does not automatically substitute 'closed throttle'.

Required consequences:

```text
hybrid air model -> speed-density only if MAP valid
idle qualification -> inhibited unless a future explicit alternate qualifier is defined
DFCO qualification -> inhibited
TPS-based PE request -> inhibited; load-based PE remains available
AE TPS-rate term -> inhibited; MAP-rate term may remain available
```

A last-valid or configured control value may be retained for display/limited calculations, but its invalid status must remain visible to every consumer.

## 6. MAP conversion

MAP uses a generic two-point transfer so alternate sensor ranges can be supported without rewriting code.

Physical/setup calibration:

```text
MAP_V_LOW
MAP_KPA_LOW
MAP_V_HIGH
MAP_KPA_HIGH
```

Conversion:

```text
MAP_KPA_ABS =
    MAP_KPA_LOW
  + (MAP_V - MAP_V_LOW)
    * (MAP_KPA_HIGH - MAP_KPA_LOW)
    / (MAP_V_HIGH - MAP_V_LOW)
```

Validation includes electrical range, engineering range, and optional rate/plausibility checks.

### MAP invalid behavior

```text
speed-density estimate invalid
Alpha-N fallback may be permitted if TPS + BARO valid
MAP-based spark/load paths use the explicit fallback policy
MAP-based PE/DFCO qualifiers are inhibited or replaced only by explicitly allowed alternate qualifiers
```

MAP is never silently replaced by a fixed kPa number while being reported as valid.

## 7. BARO derivation

BARO is a semantic derived value, not a separate V1 sensor.

Preferred initial capture:

```text
if LIFE_KEYON_STOPPED
AND MAP valid
AND engine not producing manifold vacuum:
    BARO = MAP
```

`BARO_VALID` is independent from current `MAP_VALID` after a qualified value has been captured.

Running BARO updates, if later retained, must be slow and explicitly qualified near atmospheric manifold pressure so boost/load transients cannot rewrite barometric reference.

Derived:

```text
PRESSURE_RATIO = MAP / BARO
```

only when both values are valid.

## 8. MAT / IAT conversion

The stock thermistor circuit is nonlinear. V1 uses an explicit conversion table/curve:

```text
MAT_C = MAT_TRANSFER(RAW_MAT)
MAT_K = MAT_C + 273.15
```

The exact stored table representation is deferred to ROM/layout planning.

Validation includes raw electrical endpoints and plausible temperature range.

### MAT invalid behavior

Air-charge calculation requires a bounded temperature estimate. Define a separately named fallback:

```text
MAT_FALLBACK_C
```

When MAT is invalid:

```text
MAT_CONTROL_C = MAT_FALLBACK_C
MAT_SUBSTITUTED = TRUE
```

Temperature-dependent spark correction may use its own conservative invalid-input policy rather than assuming the substituted value is a real measurement.

The fallback is not a tuner correction for normal heat-soak behavior.

## 9. CTS conversion

CTS also uses an explicit thermistor transfer:

```text
CTS_C = CTS_TRANSFER(RAW_CTS)
```

Validation includes electrical endpoints, plausible temperature range, and optional warmup-rate plausibility.

CTS affects multiple cold-start/warmup functions, therefore invalid CTS must remain explicit.

Define:

```text
CTS_FALLBACK_C
```

for calculations that require a bounded value, but each module retains authority over its invalid-CTS response.

Examples:

```text
cranking fuel may use a defined conservative fallback
warmup enrichment may use bounded fallback
idle target/startup air may use bounded fallback
spark CTS correction may use a separately safe neutral/protective rule
```

A substituted CTS value must never clear the sensor fault or be logged as measured temperature.

## 10. Battery-voltage conversion

Battery input is converted by explicit scale/offset:

```text
BATTERY_V = BATTERY_RAW * BATTERY_SCALE + BATTERY_OFFSET
```

`BATTERY_SCALE` and `BATTERY_OFFSET` are hardware/setup values, not normal tuning variables.

Battery voltage is used by:

```text
injector deadtime
key-off inference
low-voltage diagnostic/protective logic
```

If the battery channel becomes invalid while the engine is running, deadtime may use:

```text
BATTERY_FALLBACK_V
```

while key-off logic must not declare key-off solely from an invalid battery measurement.

## 11. Narrowband O2

NB is optional.

Semantic values:

```text
NB_VOLTAGE
NB_VALID
NB_RICH_LEAN_STATE
NB_SWITCH_ACTIVITY
```

Validation/qualification may include:

```text
feature enabled
warmup/run-time eligibility
voltage inside electrical bounds
minimum switching/activity criteria when closed-loop operation expects switching
```

If NB is disabled or invalid:

```text
NB contribution = unavailable
```

It does not disturb open-loop base fuel.

## 12. Wideband O2

WB is optional and assumed to enter V1 through an analog controller output unless a future digital interface is explicitly added.

Use a generic two-point transfer:

```text
WB_V_LOW
WB_LAMBDA_LOW
WB_V_HIGH
WB_LAMBDA_HIGH
```

Conversion:

```text
WB_LAMBDA =
    WB_LAMBDA_LOW
  + (WB_V - WB_V_LOW)
    * (WB_LAMBDA_HIGH - WB_LAMBDA_LOW)
    / (WB_V_HIGH - WB_V_LOW)
```

Validation includes configured electrical range and physically meaningful lambda bounds.

If WB is invalid:

```text
WB contribution unavailable
DUAL mode may fall back to NB behavior if NB remains qualified
WB_ONLY falls back to open-loop base fuel unless a different explicit policy is selected
```

No invalid WB value is allowed to continue integrating fuel correction.

## 13. REF / RPM

REF is safety-critical and has no numerical substitution for production spark/fuel scheduling.

Semantic values:

```text
REF_VALID
LAST_REF_PERIOD
REF_AGE
ROTATION_VALID
RPM
```

Derived RPM follows the characterized REF event relationship and timer scale. The exact integer scaling belongs to implementation, but the semantic relationship is:

```text
RPM = K_REF / REF_PERIOD
```

where `K_REF` is determined by timer frequency and REF events per revolution.

If REF becomes stale beyond lifecycle timeout:

```text
ROTATION_VALID = FALSE
new synchronous fuel/spark event commands inhibited
```

There is no fake RPM fallback for actuator scheduling.

## 14. Knock input

Knock is optional.

V1 stock-compatible observation uses the known knock pulse/event accumulation path.

Semantic outputs should be normalized above raw hardware representation:

```text
KNOCK_RAW_DELTA
KNOCK_ACTIVITY
KNOCK_EVENT / severity
KNOCK_VALID
```

A possible normalized activity metric is:

```text
KNOCK_ACTIVITY = event_count_delta / observation_window
```

Threshold/gain qualification may depend on RPM/load, but the raw event acquisition must remain separately observable.

If knock control is configured but sensing is invalid, the frozen diagnostic/failsafe policy defines the protective response. Invalid sensing is not equivalent to zero knock.

## 15. Filtering policy

Filters must be signal-specific and observable where they materially affect control response.

General first-order form:

```text
Y[n] = Y[n-1] + ALPHA * (X[n] - Y[n-1])
```

Do not use one global filter constant for unrelated sensors.

Examples:

```text
TPS position may use minimal filtering; TPS rate may use dedicated smoothing
MAP may use modest filtering while retaining transient response
CTS/MAT may use slow filtering
O2 filtering must not destroy the dynamics required by the selected feedback controller
```

Filter constants belong to advanced/developer calibration unless routine tuning genuinely benefits from exposing them.

## 16. Substitution policy

Substitution is explicit and module-aware.

A substituted value consists of:

```text
CONTROL_VALUE
SUBSTITUTED = TRUE
SOURCE/REASON
```

Rules:

```text
substitution never changes SENSOR_VALID to TRUE
substitution never hides the fault from ADX
safety-critical timing inputs such as REF are not numerically substituted
optional feedback sensors simply lose feedback authority when unavailable
module-specific behavior may differ for the same invalid sensor
```

This avoids the stock-style ambiguity where a plausible fallback number can look indistinguishable from a real measurement.

## 17. Physical/setup values versus behavioral tuning

Physical/setup examples:

```text
TPS closed/WOT voltages
MAP two-point transfer
MAT transfer definition
CTS transfer definition
battery scale/offset
WB voltage/lambda transfer
sensor electrical limits
```

Behavioral calibration examples:

```text
idle TPS thresholds
PE thresholds
DFCO thresholds
feedback gains/authority
knock thresholds/gains
```

Derived/read-only examples:

```text
TPS_PERCENT
TPS_RATE
MAP_KPA_ABS
BARO_KPA_ABS
PRESSURE_RATIO
MAT_C / MAT_K
CTS_C
BATTERY_V
WB_LAMBDA
RPM
sensor validity/substitution state
```

A behavioral problem must not be corrected by falsifying a physical sensor transfer unless the transfer itself is actually wrong.

## 18. Required ADX observability

At minimum expose:

```text
raw TPS / TPS volts / TPS percent / TPS rate / TPS validity
raw MAP / MAP volts / MAP kPa / MAP validity
BARO / BARO validity / pressure ratio
raw MAT / MAT C / MAT control C / MAT validity / substitution
raw CTS / CTS C / CTS control C / CTS validity / substitution
raw battery / battery V / battery validity / substitution
NB voltage / NB state / NB validity / switching state
WB voltage / WB lambda / WB validity
REF period / REF age / REF validity / rotation valid / RPM
knock raw delta / knock activity / knock validity
```

The exact ALDL packet allocation is deferred to the ADX/telemetry matrix.

## 19. Non-effect contract

```text
Sensor transfer calibration converts hardware observations only.
Sensor validity reports trustworthiness only.
Substitution supplies an explicit bounded fallback only where allowed.
A substitution never masquerades as a valid measurement.
Optional O2 or knock hardware can be disabled without creating a fault.
REF cannot be substituted for production spark/fuel scheduling.
No excluded transmission, EGR, EVAP, AIR, or A/C input is required by V1.
```
