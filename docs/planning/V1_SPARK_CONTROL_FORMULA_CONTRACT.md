# V1 Spark-Control Formula Contract

## Status

`DESIGN BASELINE — formula-first planning artifact`

This document defines the V1 spark-control mathematics before XDF/ADX layout or target assembly.

The spark algorithm owns **desired combustion timing in crank degrees**. The preserved GM EST/ASIC command island owns conversion from the final semantic timing request into hardware timing state.

## 1. Top-level model

```text
engine state
  + RPM/load
  + temperatures
  + idle controller contribution
  + optional knock response
      -> desired final spark timing
      -> safety clamps
      -> preserved GM EST/ASIC handoff
```

No automatic-transmission, EGR, AIR, EVAP, or A/C state may enter the V1 spark equation.

## 2. Units and sign convention

```text
spark timing      crank degrees BTDC
advance           positive
retard            negative contribution
RPM               rpm
load axis          MAP kPa absolute for V1 unless later explicitly revised
```

All tuner-facing spark values are displayed directly in degrees rather than stock encoded counts.

## 3. Operating-state base timing

V1 has three explicit base-timing states.

### Cranking

```text
BASE_SPARK = CRANK_SPARK(CTS)
```

Crank timing is independent of the normal running spark table.

### Running, non-idle

```text
BASE_SPARK = MAIN_SPARK_TABLE(RPM, MAP)
```

Bilinear interpolation is preferred between table cells.

### Idle-qualified

```text
BASE_SPARK = IDLE_BASE_SPARK(CTS)
```

Idle base timing is intentionally independent of the main table so a tuner can change steady idle timing without reshaping nearby low-load driving cells.

Entry/exit between idle and non-idle base timing uses an explicit bounded transition/blend rather than an instantaneous discontinuity.

Define:

```text
IDLE_BLEND in [0,1]

STATE_BASE_SPARK =
    MAIN_SPARK * (1 - IDLE_BLEND)
  + IDLE_BASE_SPARK * IDLE_BLEND
```

During cranking, the crank path supersedes this blend.

## 4. Temperature corrections

Coolant and inlet-air corrections are independent additive terms:

```text
CTS_SPARK_CORR = CTS_SPARK_TABLE(CTS)
MAT_SPARK_CORR = MAT_SPARK_TABLE(MAT)
```

Hot-normal endpoints should ordinarily be zero unless intentionally calibrated otherwise.

Temperature corrections do not rewrite the main spark table and do not alter knock state.

## 5. Optional power/load correction

If a dedicated PE/high-load spark correction is retained:

```text
PE_SPARK_CORR = PE_ACTIVE ? PE_SPARK_TABLE(RPM, MAP) : 0
```

This term is explicit and additive. If testing shows the main RPM/MAP table alone provides adequate high-load control, this entire term may be omitted from V1 rather than retained as dead calibration.

## 6. Idle spark controller

Idle spark is a fast RPM-stabilization actuator and is separate from the slower IAC airflow controller.

Define:

```text
RPM_ERROR = TARGET_IDLE_RPM - RPM_ACTUAL
```

Positive error means engine speed is too low and therefore requests positive spark advance.

A bounded proportional-plus-rate controller is preferred for spark so it does not accumulate a second long-term integral correction that fights the IAC loop:

```text
IDLE_SPARK_P = IDLE_SPARK_KP * RPM_ERROR

RPM_RATE = RPM_ACTUAL[n] - RPM_ACTUAL[n-1]
IDLE_SPARK_D = -IDLE_SPARK_KD * RPM_RATE

IDLE_SPARK_CORR = clamp(IDLE_SPARK_MIN,
                        IDLE_SPARK_MAX,
                        IDLE_SPARK_P + IDLE_SPARK_D)
```

When idle control is not qualified:

```text
IDLE_SPARK_CORR = 0
```

This gives IAC ownership of long-term airflow while spark supplies fast damping.

## 7. Knock response

Knock control is optional.

Define a qualified knock event or normalized knock severity from the validated knock input:

```text
KNOCK_EVENT >= 0
```

Retard state is nonnegative:

```text
KNOCK_RETARD >= 0
```

On qualified knock:

```text
KNOCK_RETARD[n] = clamp(0, KNOCK_RETARD_MAX,
                        KNOCK_RETARD[n-1]
                        + KNOCK_ADD * KNOCK_EVENT)
```

Without qualified knock, retard recovers toward zero at a calibrated rate:

```text
KNOCK_RETARD[n] = max(0,
                      KNOCK_RETARD[n-1] - KNOCK_RECOVERY_RATE * dt)
```

If knock control is disabled:

```text
KNOCK_RETARD = 0
```

If the knock input is configured but invalid, the frozen diagnostic/failsafe policy supplies the explicitly defined protective response rather than silently treating invalid as no knock.

## 8. Preliminary desired spark

For running operation:

```text
SPARK_PRECLAMP =
    STATE_BASE_SPARK
  + CTS_SPARK_CORR
  + MAT_SPARK_CORR
  + PE_SPARK_CORR
  + IDLE_SPARK_CORR
  - KNOCK_RETARD
```

Cranking may use its own reduced correction set if the final lifecycle design requires it. Any excluded correction must be explicit in the state contract.

## 9. Limits and safety clamps

Final desired timing is bounded:

```text
FINAL_SPARK = clamp(SPARK_MIN_LIMIT,
                    SPARK_MAX_LIMIT,
                    SPARK_PRECLAMP)
```

Additional state-specific safety ceilings/floors may exist, but each must be separately named and observable. No hidden shared clamp may be used to implement an unrelated feature.

## 10. Output boundary

The spark algorithm stops at:

```text
FINAL_SPARK  [degrees BTDC]
```

The preserved GM spark/EST island owns:

```text
REF-period timing conversion
latency compensation required by the stock handoff
rolling fall timing state
dwell-related hardware state
ASIC register ordering/access delays
EST/BYPASS hardware-facing behavior retained from the stock path
```

Those hardware concerns must not leak back into the tuner-facing spark equations.

## 11. Likely XDF controls derived from this model

```text
main spark table, RPM x MAP
crank spark vs CTS
idle base spark vs CTS
idle transition rate/blend behavior
CTS spark correction
MAT spark correction
optional PE/high-load correction
idle spark Kp
idle spark Kd
idle spark authority min/max
knock add/gain
knock maximum retard
knock recovery rate
spark absolute min/max limits
```

Any term omitted from the final algorithm is also omitted from the XDF.

## 12. Required ADX observability

```text
SPARK_STATE
MAIN_SPARK
CRANK_SPARK
IDLE_BASE_SPARK
IDLE_BLEND
STATE_BASE_SPARK
CTS_SPARK_CORR
MAT_SPARK_CORR
PE_SPARK_CORR
RPM_ERROR
RPM_RATE
IDLE_SPARK_P
IDLE_SPARK_D
IDLE_SPARK_CORR
KNOCK_EVENT
KNOCK_RETARD
SPARK_PRECLAMP
FINAL_SPARK
SPARK_CLAMP_ACTIVE
```

The ADX must make it possible to explain every degree added to or removed from final timing.

## 13. Non-effect contract

```text
Main spark table controls normal RPM/load base timing only.
Idle base spark controls idle base timing only.
Idle spark gains control fast idle RPM stabilization only.
CTS correction changes temperature timing only.
MAT correction changes inlet-temperature timing only.
Knock calibration changes knock response only.
Spark limits bound final timing only.
No excluded stock subsystem is allowed to alter any spark term.
```
