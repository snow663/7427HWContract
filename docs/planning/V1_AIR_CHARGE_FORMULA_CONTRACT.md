# V1 Air-Charge Formula Contract

## Status

`DESIGN BASELINE — formula-first planning artifact`

This document defines the V1 air-charge estimator used upstream of fuel, spark/load qualification, AE support, PE, DFCO, and diagnostics.

V1 uses a **hybrid speed-density / Alpha-N model**. Speed density remains the primary physically based steady-state estimator. Alpha-N supplies calibrated high-load resolution, throttle-position feed-forward during transients, and a possible degraded fallback if MAP is invalid.

The output boundary is always the same semantic quantity:

```text
AIR_MASS_CYCLE    modeled total air mass inducted by the complete engine per 720-degree cycle
```

Downstream fuel logic must consume `AIR_MASS_CYCLE`; it must not care whether that value came from speed density, Alpha-N, or a blend.

## 1. Inputs

```text
RPM
MAP_KPA_ABS
TPS_PERCENT
MAT_K
BARO_KPA_ABS
engine displacement Vd
speed-density VE table
Alpha-N filling table
sensor-validity state
```

No automatic-transmission, EGR, EVAP, AIR, or A/C state enters the air-charge model.

## 2. Barometric reference

For V1, barometric pressure is a semantic engine-state value. Initial barometric pressure may be captured from MAP while the engine is not producing manifold vacuum.

```text
BARO = qualified engine-off / key-on MAP
```

Any later running update strategy must be explicit and slow/qualified. It must not cause abrupt airflow changes.

Define normalized manifold pressure ratio:

```text
PRESSURE_RATIO = clamp(0, PR_MAX, MAP / BARO)
```

For a naturally aspirated engine this is normally near 0..1. This normalized ratio is preferred over a fixed absolute-MAP threshold when deciding high-load Alpha-N authority because it remains meaningful with altitude changes.

## 3. Speed-density estimator

For total engine displacement `Vd`, manifold absolute pressure `MAP`, absolute inlet-air temperature `MAT_K`, air specific gas constant `Rair`, and calibrated volumetric efficiency `VE_SD(RPM, MAP)`:

```text
AIR_SD = (MAP * Vd * VE_SD) / (Rair * MAT_K)
```

`AIR_SD` is air mass per complete 720-degree engine cycle.

### Ownership

`VE_SD` corrects the speed-density air estimate only. It must not compensate injector flow, fuel pressure, deadtime, short-pulse behavior, closed-loop bias, startup enrichment, or AE.

## 4. Alpha-N estimator

Alpha-N is expressed as a calibrated **effective filling fraction**, not as an arbitrary fuel multiplier.

Define:

```text
AN_FILLING = AN_FILLING_TABLE(RPM, TPS)
```

`AN_FILLING` is dimensionless and represents effective cylinder filling relative to ambient pressure at the current throttle angle and RPM.

The Alpha-N air estimate is:

```text
AIR_AN = (BARO * Vd * AN_FILLING) / (Rair * MAT_K)
```

This formulation automatically provides first-order barometric-pressure and inlet-temperature compensation while keeping the Alpha-N table itself dimensionless and physically interpretable.

At closed throttle `AN_FILLING` is small. Near wide-open throttle it may approach the engine's actual volumetric-efficiency region.

## 5. Hybrid blend equation

The two estimators produce the same units and are combined by one explicit authority term:

```text
AN_WEIGHT in [0, AN_WEIGHT_MAX]
SD_WEIGHT = 1 - AN_WEIGHT

AIR_MASS_CYCLE =
    AIR_SD + AN_WEIGHT * (AIR_AN - AIR_SD)
```

Equivalent form:

```text
AIR_MASS_CYCLE = AIR_SD * SD_WEIGHT + AIR_AN * AN_WEIGHT
```

The first form is preferred in documentation because it makes clear that Alpha-N is a bounded correction away from the speed-density baseline.

## 6. Steady-state Alpha-N authority

Normal idle/cruise operation should be dominated by speed density.

A small high-load Alpha-N base authority is permitted where MAP approaches BARO and absolute-MAP resolution becomes compressed.

Define:

```text
AN_BASE_WEIGHT = AN_BASE_WEIGHT_TABLE(PRESSURE_RATIO)
```

Recommended design behavior:

```text
low / medium pressure ratio    -> AN_BASE_WEIGHT near 0
high pressure ratio            -> AN_BASE_WEIGHT rises gradually
near BARO                      -> bounded high-load Alpha-N contribution
```

This is intentionally a small 1-D calibration. It must not become a second hidden VE surface.

## 7. Transient Alpha-N authority

Throttle motion provides immediate information about driver airflow demand before manifold pressure has fully responded.

Define filtered throttle rate:

```text
TPS_RATE = d(TPS_PERCENT) / dt
TIP_IN_RATE  = max(0,  TPS_RATE)
TIP_OUT_RATE = max(0, -TPS_RATE)
```

Independent authority requests are allowed because opening and closing transients need not behave identically:

```text
AN_TIPIN_REQUEST  = AN_TIPIN_WEIGHT(TIP_IN_RATE)
AN_TIPOUT_REQUEST = AN_TIPOUT_WEIGHT(TIP_OUT_RATE)
```

The transient authority state is bounded and decays explicitly rather than disappearing in one sample:

```text
AN_TRANSIENT_REQUEST = max(AN_TIPIN_REQUEST, AN_TIPOUT_REQUEST)

AN_TRANSIENT_STATE[n] =
    slew_or_decay(AN_TRANSIENT_STATE[n-1],
                  AN_TRANSIENT_REQUEST,
                  AN_TRANSIENT_RISE,
                  AN_TRANSIENT_DECAY)
```

The exact fixed-point implementation of `slew_or_decay` is deferred, but the semantic behavior is fixed: authority rises quickly when throttle moves and returns smoothly toward zero when throttle motion stops.

## 8. Final Alpha-N authority

```text
AN_WEIGHT_REQUEST = AN_BASE_WEIGHT + AN_TRANSIENT_STATE

AN_WEIGHT = clamp(0,
                  AN_WEIGHT_MAX,
                  AN_WEIGHT_REQUEST)
```

The V1 calibration should use conservative maximum authority initially. Alpha-N is intended to improve prediction, not to mask a poorly calibrated speed-density model.

## 9. Separation from acceleration enrichment

The hybrid air-charge estimator and acceleration enrichment solve different problems.

```text
Alpha-N transient authority:
    improves prediction of inducted AIR MASS when throttle moves

AE:
    adds transient FUEL MASS for fuel transport, wall wetting,
    atomization, and other mixture-delivery effects
```

Therefore:

```text
AIR_MASS_CYCLE -> base fuel calculation
AE_FUEL_MASS   -> additive downstream transient fuel term
```

AE must not be used merely to compensate a deliberately sluggish air-charge estimate, and Alpha-N must not be tuned to compensate injector/fuel-film behavior.

## 10. Sensor-validity behavior

The Air Charge Manager reports both source mode and validity.

Required semantic modes:

```text
AIR_MODE_SD
AIR_MODE_SD_AN_HYBRID
AIR_MODE_AN_FALLBACK
AIR_MODE_INVALID
```

Preliminary source selection:

```text
MAP valid + TPS valid:
    hybrid model permitted

MAP valid + TPS invalid:
    speed density only

MAP invalid + TPS valid + BARO valid:
    Alpha-N fallback may be used subject to the final failsafe contract

MAP invalid + TPS invalid:
    air model invalid
```

The final sensor/failsafe contract will define whether `AN_FALLBACK` permits normal operation or a reduced/safe operating envelope.

## 11. Calibration rollout strategy

The hybrid model should be commissioned in stages rather than trying to tune both surfaces simultaneously.

### Stage 1 — speed density only

```text
AN_WEIGHT_MAX = 0
```

Tune `VE_SD` until steady-state fuel prediction is correct across the normal operating map.

### Stage 2 — derive initial Alpha-N filling table

During qualified steady-state logging, derive an observed Alpha-N filling value from the already-correct speed-density airflow:

```text
AN_FILLING_OBSERVED =
    AIR_SD * Rair * MAT_K / (BARO * Vd)
```

Accumulate this by RPM/TPS cell to seed `AN_FILLING_TABLE`.

This makes the initial Alpha-N model agree with the tuned speed-density model in regions where both have good data.

### Stage 3 — enable high-load base blend

Introduce a small `AN_BASE_WEIGHT` only in high pressure-ratio regions and verify that steady-state delivered torque/fueling remains smooth.

### Stage 4 — enable transient authority

Enable `AN_TIPIN_WEIGHT` and, if useful, `AN_TIPOUT_WEIGHT`. Tune transient authority while observing air-model disagreement before altering AE.

### Stage 5 — tune true AE separately

After the air-charge response is satisfactory, tune additive AE for residual mixture error caused by fuel transport rather than airflow prediction.

## 12. Air-model disagreement diagnostic

Expose explicit disagreement:

```text
AIR_MODEL_DELTA = AIR_AN - AIR_SD

AIR_MODEL_ERROR_PERCENT =
    100 * (AIR_AN - AIR_SD) / max(AIR_SD, AIR_MIN_REFERENCE)
```

Large persistent disagreement under stable conditions indicates that one of the two airflow calibrations is wrong. It must not be silently hidden by the blend.

## 13. Likely XDF controls

Derived from this formula contract:

```text
speed-density VE table: RPM x MAP
Alpha-N filling table: RPM x TPS
Alpha-N base weight vs pressure ratio
Alpha-N tip-in authority vs positive TPS rate
Alpha-N tip-out authority vs negative TPS rate
Alpha-N transient rise
Alpha-N transient decay
Alpha-N maximum authority
barometric qualification thresholds if exposed
```

Normal tuning should not require changing the physical gas constant or other implementation constants.

## 14. Required ADX observability

At minimum:

```text
MAP_KPA_ABS
BARO_KPA_ABS
PRESSURE_RATIO
TPS_PERCENT
TPS_RATE
MAT_K
RPM
VE_SD_USED
AN_FILLING_USED
AIR_SD
AIR_AN
AIR_MODEL_DELTA
AIR_MODEL_ERROR_PERCENT
AN_BASE_WEIGHT
AN_TIPIN_REQUEST
AN_TIPOUT_REQUEST
AN_TRANSIENT_STATE
AN_WEIGHT
SD_WEIGHT
AIR_MASS_CYCLE
AIR_MODEL_MODE
AIR_MODEL_VALID
```

This makes it possible to see whether a throttle-response problem is caused by the speed-density estimate, Alpha-N estimate, blend authority, or true downstream AE/fuel-delivery behavior.

## 15. Non-effect contract

```text
VE_SD changes speed-density airflow estimation only.
AN_FILLING changes Alpha-N airflow estimation only.
AN base weight changes steady high-load blending only.
AN transient authority changes temporary SD/Alpha-N blend authority only.
Alpha-N does not directly add fuel.
AE does not rewrite either airflow model.
Injector calibration does not alter airflow estimation.
Closed-loop feedback does not alter either airflow table at runtime.
```

Any adaptive learning of either airflow model is a future explicit feature and is not implied by V1.

## 16. Downstream interface

The only primary airflow quantity delivered to the fuel model is:

```text
AIR_MASS_CYCLE
```

Optional supporting outputs such as pressure ratio, airflow disagreement, and model source may be consumed by PE, DFCO, diagnostics, and telemetry, but those modules must not reach into the private calibration/state of the Air Charge Manager.
