# V1 Fuel-Control Formula Contract

## Status

`DESIGN BASELINE — formula-first planning artifact`

This document defines the mathematical ownership and data flow for the V1 fuel system before ROM layout, XDF generation, ADX generation, or target assembly.

The fundamental quantity is **fuel mass required by the engine**, not pulse width. Pulse width is produced only by the injector/delivery model at the hardware boundary.

Air-charge estimation is owned by `docs/planning/V1_AIR_CHARGE_FORMULA_CONTRACT.md`. The fuel model consumes the semantic output `AIR_MASS_CYCLE` and does not depend on whether it was produced by speed density, Alpha-N, or their V1 hybrid blend.

## 1. Core separation

```text
AIR CHARGE MANAGER
  -> AIR_MASS_CYCLE per complete 720-degree engine cycle

COMBUSTION TARGET
  -> target lambda

FUEL DEMAND
  -> requested fuel mass per engine cycle

STARTUP / WARMUP / TRANSIENT / FEEDBACK
  -> explicit fuel-mass or bounded correction contributions

DELIVERY SCHEDULER
  -> fuel mass required per injector event

INJECTOR MODEL
  -> required electrical pulse width

PRESERVED GM FUEL COMMAND ISLAND
  -> hardware-facing command only
```

No airflow-model calibration, lambda, warmup, feedback, or transient-fuel calculation is allowed to depend on the electrical output polarity or stock hardware-register encoding.

## 2. Units

Preferred semantic units:

```text
pressure              kPa absolute for MAP; psi gauge for TBI fuel pressure configuration
volume                liters or cubic meters internally as required
absolute temperature  kelvin
engine speed           rpm
air mass               mg per complete engine cycle
fuel mass              mg per complete engine cycle
injector flow          mg/ms per injector internally; lb/hr may be tuner-facing
lambda                  ratio
pulse width             ms semantically; fixed-point timer count only at final adapter
```

## 3. Air-charge input boundary

The fuel model receives:

```text
AIR_MASS_CYCLE
```

from the V1 Air Charge Manager.

The current V1 Air Charge Manager uses hybrid speed-density / Alpha-N estimation and separately exposes its internal contributors for TunerPro observability.

The fuel calculation itself must not reach into:

```text
VE_SD
AN_FILLING
AN_WEIGHT
MAP-to-airflow internals
TPS-to-airflow internals
```

Those belong exclusively to the Air Charge Manager.

This separation permits future replacement or extension of the airflow estimator without rewriting the fuel-demand, closed-loop, startup, transient-fuel, or injector-delivery equations.

## 4. Combustion target and base fuel mass

Let:

```text
AFR_STOICH = stoichiometric air/fuel mass ratio for the configured fuel
LAMBDA_TARGET = desired lambda for the current operating state
```

Then:

```text
BASE_FUEL_MASS_CYCLE = AIR_MASS_CYCLE / (AFR_STOICH * LAMBDA_TARGET)
```

Normal operation may use `LAMBDA_TARGET = 1.000`. Power enrichment changes the **target lambda**, rather than hiding enrichment inside an unrelated multiplier.

## 5. Startup and warmup ownership

Three separate controls are retained.

### Cranking

Cranking owns its own fuel-mass request because airflow estimation during cranking is a special operating state.

```text
CRANK_FUEL_MASS_CYCLE = f(coolant_temperature, crank_state)
```

Optional later refinements may include cranking MAP or cranking RPM, but V1 must not require those terms merely to duplicate stock complexity.

### Afterstart

After first qualified run events:

```text
AFTERSTART_FACTOR[n] = 1 + AFTERSTART_EXCESS_INITIAL(CTS) * AFTERSTART_DECAY[n]
```

with:

```text
0 <= AFTERSTART_DECAY <= 1
AFTERSTART_DECAY -> 0 as afterstart expires
```

### Warmup

```text
WARMUP_FACTOR = f(CTS)
```

with hot-engine endpoint:

```text
WARMUP_FACTOR = 1.000
```

For normal running before transient fuel:

```text
STEADY_FUEL_MASS_CYCLE = BASE_FUEL_MASS_CYCLE * WARMUP_FACTOR * AFTERSTART_FACTOR
```

Cranking uses the cranking path instead of blindly stacking every run-state enrichment.

## 6. Power enrichment

PE owns target lambda rather than an arbitrary hidden fuel multiplier.

When PE is inactive:

```text
LAMBDA_TARGET = NORMAL_LAMBDA_TARGET
```

When PE is active:

```text
LAMBDA_TARGET = PE_LAMBDA_TARGET(RPM, LOAD)
```

The final load variable used for PE qualification will be defined in the lifecycle/load contract. Qualification, hysteresis, and delay are state-machine terms and are not embedded into airflow or injector calibration.

## 7. Acceleration enrichment / transient fuel

AE is an **additive fuel-mass contribution**, not an airflow-model alteration.

Positive throttle and MAP rates may create independent residual transient-fuel requests:

```text
AE_TPS_INPUT = max(0, dTPS/dt)
AE_MAP_INPUT = max(0, dMAP/dt)

AE_NEW = K_TPS(CTS) * AE_TPS_INPUT
       + K_MAP(CTS) * AE_MAP_INPUT
```

A persistent transient state decays explicitly:

```text
AE_STATE[n] = clamp(0, AE_MAX,
                    AE_STATE[n-1] * AE_DECAY + AE_NEW)
```

and:

```text
AE_FUEL_MASS_CYCLE = AE_STATE
```

Thus:

```text
FUEL_MASS_BEFORE_FEEDBACK = STEADY_FUEL_MASS_CYCLE + AE_FUEL_MASS_CYCLE
```

The hybrid Alpha-N transient authority upstream improves **air-charge prediction** when throttle moves. AE remains downstream and is tuned only for residual fuel-transport behavior such as wall wetting, atomization, and mixture-delivery lag.

Exact sample period and fixed-point scaling will be chosen during scheduler/implementation planning, but the semantic equation is fixed.

## 8. DFCO

DFCO is an explicit fuel state, not a disguised calibration multiplier.

When DFCO is qualified and active:

```text
REQUESTED_FUEL_MASS_CYCLE = 0
AE generation = inhibited
feedback integrators = frozen
```

Exit behavior may use a separately named re-entry ramp if testing shows one is useful. Such a ramp must remain independent of airflow calibration and normal closed-loop correction.

## 9. Closed-loop feedback manager

Selectable modes:

```text
OPEN_LOOP
NB_ONLY
WB_ONLY
DUAL
```

The feedback manager outputs exactly one bounded semantic correction:

```text
FEEDBACK_FACTOR
```

Open loop:

```text
FEEDBACK_FACTOR = 1.000
```

### Narrowband path

Narrowband is a stoichiometric rich/lean integrator.

Define:

```text
NB_SIGN = +1 when qualified lean
          -1 when qualified rich
           0 when invalid/frozen
```

Then:

```text
NB_BIAS[n] = clamp(NB_MIN, NB_MAX,
                   NB_BIAS[n-1] + NB_KI * NB_SIGN)
```

NB control is only eligible near stoichiometric target lambda.

In `NB_ONLY`:

```text
FEEDBACK_FACTOR = NB_BIAS
```

### Wideband path

Define normalized lambda error so lean is positive:

```text
WB_ERROR = (LAMBDA_MEASURED / LAMBDA_TARGET) - 1
```

Then:

```text
WB_I[n] = clamp(WB_I_MIN, WB_I_MAX,
                WB_I[n-1] + WB_KI * WB_ERROR)

WB_FACTOR = clamp(WB_MIN, WB_MAX,
                  1 + WB_KP * WB_ERROR + WB_I[n])
```

In `WB_ONLY`:

```text
FEEDBACK_FACTOR = WB_FACTOR
```

### Dual mode

Wideband remains the primary quantitative controller. Narrowband provides only a slow, tightly bounded stoichiometric centering bias when target lambda is near 1.000 and both sensors are valid.

```text
DUAL_NB_BIAS[n] = clamp(DUAL_NB_MIN, DUAL_NB_MAX,
                        DUAL_NB_BIAS[n-1] + DUAL_NB_KI * NB_SIGN)

FEEDBACK_FACTOR = clamp(FB_MIN, FB_MAX,
                        WB_FACTOR * DUAL_NB_BIAS)
```

`DUAL_NB_KI` and authority are intentionally much smaller than the WB path. The NB bias freezes outside its stoichiometric qualification window.

This hierarchy prevents two independent fast controllers from fighting each other.

## 10. Optional learned correction

If V1 retains long-term learning, it is separate from instantaneous feedback:

```text
LEARN_FACTOR
```

It is updated only under explicitly qualified steady-state conditions and is bounded.

The runtime fuel request becomes:

```text
RUN_FUEL_MASS_CYCLE =
    (STEADY_FUEL_MASS_CYCLE * LEARN_FACTOR * FEEDBACK_FACTOR)
    + AE_FUEL_MASS_CYCLE
```

If learning is disabled:

```text
LEARN_FACTOR = 1.000
```

Feedback and learning must never modify the stored speed-density VE table or Alpha-N filling table directly during normal runtime.

## 11. TBI injector pressure/flow model

For this TBI configuration the injectors discharge above the throttle plates and are not subjected to manifold vacuum. The injector pressure differential is therefore represented by configured **fuel gauge pressure**.

Let:

```text
FLOW_RATED = injector mass-flow rating at P_RATED
P_RATED = pressure at which FLOW_RATED was characterized
P_FUEL_GAUGE = actual configured operating fuel pressure
```

Then:

```text
FLOW_EFFECTIVE = FLOW_RATED * sqrt(P_FUEL_GAUGE / P_RATED)
```

MAP is not part of this injector-flow equation.

`FLOW_EFFECTIVE` should normally be derived from the physical setup rather than manually tuned to correct airflow estimation or short-pulse behavior.

## 12. Delivery scheduling abstraction

Fuel demand is calculated per complete engine cycle. Physical pulse scheduling is a separate delivery concern.

Define driver configuration constants/state:

```text
EVENTS_PER_ENGINE_CYCLE
ACTIVE_INJECTORS_PER_EVENT
```

Then the ideal fuel mass required from each active injector on each event is:

```text
FUEL_MASS_PER_INJECTOR_EVENT =
    REQUESTED_FUEL_MASS_CYCLE
    / (EVENTS_PER_ENGINE_CYCLE * ACTIVE_INJECTORS_PER_EVENT)
```

These delivery terms belong to the preserved-driver compatibility contract, not to the tuner-facing air/fuel model.

## 13. Ideal injector open time

With effective injector mass flow in compatible mass/time units:

```text
IDEAL_OPEN_TIME = FUEL_MASS_PER_INJECTOR_EVENT / FLOW_EFFECTIVE
```

This is the ideal linear hydraulic delivery time before electrical opening delay and short-pulse nonlinearity are applied.

## 14. Short-pulse model

Short-pulse behavior is an injector characteristic and must not be corrected by falsifying injector flow or either airflow model.

Define an inverse transfer function:

```text
HYDRAULIC_COMMAND_TIME = SHORT_PULSE_INVERSE(IDEAL_OPEN_TIME)
```

Requirements:

```text
at sufficiently long PW: SHORT_PULSE_INVERSE(x) -> x
at short PW: curve/table supplies only the nonlinear correction required by the injector
```

A small 1-D table indexed by ideal open time is preferred because it is directly characterizable on the bench and easy to visualize in TunerPro.

## 15. Injector deadtime

Electrical opening delay is separately modeled versus battery voltage:

```text
DEADTIME = DEADTIME_TABLE(BATTERY_VOLTAGE)
```

Final semantic command time:

```text
COMMAND_PW_MS = HYDRAULIC_COMMAND_TIME + DEADTIME
```

Optional hard minimum/maximum command limits are applied only after this calculation and are separately named safety/driver limits.

## 16. Final fuel equation by engine state

### Cranking

```text
REQUESTED_FUEL_MASS_CYCLE = CRANK_FUEL_MASS_CYCLE
```

### Running, non-DFCO

```text
REQUESTED_FUEL_MASS_CYCLE =
    (BASE_FUEL_MASS_CYCLE
     * WARMUP_FACTOR
     * AFTERSTART_FACTOR
     * LEARN_FACTOR
     * FEEDBACK_FACTOR)
    + AE_FUEL_MASS_CYCLE
```

PE acts through `LAMBDA_TARGET` used by `BASE_FUEL_MASS_CYCLE`.

### DFCO

```text
REQUESTED_FUEL_MASS_CYCLE = 0
```

### Delivery

```text
REQUESTED_FUEL_MASS_CYCLE
 -> event/injector division
 -> pressure-corrected injector flow
 -> ideal open time
 -> short-pulse inverse transfer
 -> deadtime
 -> command PW
 -> stock-compatible fuel command count
 -> preserved GM fuel output island
```

## 17. Required future XDF controls derived from the formulas

Air-model calibration is owned by the Air Charge Manager contract.

Likely tuner-facing physical/setup values:

```text
engine displacement
stoichiometric AFR or fuel stoich definition
injector rated flow
injector rating pressure
operating fuel gauge pressure
injector deadtime vs battery
short-pulse correction curve
```

Likely normal fuel-tune values:

```text
normal target lambda if made variable
PE target lambda
cranking fuel mass vs CTS
afterstart initial excess vs CTS
afterstart decay
warmup factor vs CTS
AE TPS gain
AE MAP gain
AE decay
feedback gains/authority/qualification
optional learning authority/rate
DFCO qualification/re-entry terms
```

Air Charge Manager XDF controls include the speed-density VE table, Alpha-N filling table, and blend-authority calibrations and are documented separately.

No address or binary representation is assigned here.

## 18. Required ADX observability derived from the formulas

At minimum expose fuel-side values:

```text
AIR_MASS_CYCLE
LAMBDA_TARGET
BASE_FUEL_MASS_CYCLE
CRANK_FUEL_MASS_CYCLE
WARMUP_FACTOR
AFTERSTART_FACTOR
AE_TPS_INPUT
AE_MAP_INPUT
AE_FUEL_MASS_CYCLE
FEEDBACK_MODE
NB_SIGN
NB_BIAS
WB_ERROR
WB_FACTOR
DUAL_NB_BIAS
FEEDBACK_FACTOR
LEARN_FACTOR
REQUESTED_FUEL_MASS_CYCLE
FLOW_EFFECTIVE
IDEAL_OPEN_TIME
SHORT_PULSE_CORRECTION / HYDRAULIC_COMMAND_TIME
DEADTIME
COMMAND_PW_MS
FINAL_STOCK_PW_COUNT
DFCO_STATE
```

The matching Air Charge Manager ADX channels expose `AIR_SD`, `AIR_AN`, model disagreement, and blend authority so TunerPro can distinguish airflow-model errors from downstream fuel-delivery errors.

## 19. Non-effect contract

The following separations are mandatory:

```text
Air Charge Manager changes modeled air mass only.
Injector flow/pressure changes delivery conversion only.
Deadtime changes electrical opening compensation only.
Short-pulse calibration changes nonlinear injector delivery only.
Warmup changes cold run fuel only.
Afterstart changes post-start transient enrichment only.
AE changes residual transient additive fuel only.
PE changes target lambda only.
NB/WB feedback changes one bounded feedback factor only.
DFCO explicitly commands zero fuel rather than corrupting another calibration.
```

Breaking one of these separations requires an explicit architecture revision rather than an undocumented implementation shortcut.
