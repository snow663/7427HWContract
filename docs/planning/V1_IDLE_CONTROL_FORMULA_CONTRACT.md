# V1 Idle-Control Formula Contract

## Status

`DESIGN BASELINE — formula-first planning artifact`

This document defines V1 idle-control ownership and equations before XDF/ADX layout or target assembly.

The clean idle system owns desired idle speed and desired IAC position. The preserved GM IAC output island owns only the final step/phase hardware behavior.

## 1. Control structure

V1 idle control uses two coordinated actuators with different jobs:

```text
IAC airflow loop  -> slow / long-term speed control
idle spark loop   -> fast / short-term damping
```

The IAC loop may integrate steady RPM error. The idle spark loop must not carry an independent long-term integral term that can fight the IAC controller.

No automatic-transmission, P/N, gear-load, or A/C compensation exists in V1.

## 2. Idle qualification

Idle control is eligible only when the explicit idle-state qualifier is true.

Inputs may include:

```text
TPS closed/near-closed state
RPM window
vehicle-speed state only if VSS is later retained
DFCO/return-to-idle state
crank/run state
```

The exact thresholds are calibration/state-machine terms and must be separately named.

## 3. Target idle speed

Base target:

```text
TARGET_IDLE_BASE = TARGET_IDLE_RPM(CTS)
```

Optional post-start offset:

```text
TARGET_IDLE_RPM = TARGET_IDLE_BASE + STARTUP_RPM_OFFSET
```

with:

```text
STARTUP_RPM_OFFSET -> 0 as startup decay completes
```

Hot idle therefore converges to the direct tuner-facing target table rather than an indirect hidden offset.

## 4. Base IAC position / airflow feedforward

The long-term feedforward term is:

```text
IAC_BASE = BASE_IAC_POSITION(CTS)
```

This is an engine-airflow calibration. It is not used to compensate injector fueling, spark timing, or excluded loads.

Startup air is separate:

```text
IAC_STARTUP_AIR = STARTUP_AIR_INITIAL(CTS) * STARTUP_AIR_DECAY
```

with decay toward zero after start.

## 5. RPM error

```text
RPM_ERROR = TARGET_IDLE_RPM - RPM_ACTUAL
```

Positive error means RPM is below target and requests more airflow.

A configurable deadband may be applied:

```text
RPM_ERROR_EFFECTIVE = 0, if abs(RPM_ERROR) <= IDLE_RPM_DEADBAND
RPM_ERROR_EFFECTIVE = RPM_ERROR otherwise
```

## 6. IAC proportional term

```text
IAC_P = IAC_KP * RPM_ERROR_EFFECTIVE
```

This term responds immediately and returns toward zero as RPM error disappears.

## 7. IAC integral term

```text
IAC_I[n] = clamp(IAC_I_MIN,
                 IAC_I_MAX,
                 IAC_I[n-1] + IAC_KI * RPM_ERROR_EFFECTIVE)
```

Anti-windup rules:

```text
freeze or back-calculate integral when final IAC target is saturated
freeze integral when idle qualification is false
reset/reseed integral during explicit lifecycle transitions rather than allowing stale state
```

The integral term owns steady airflow correction only.

## 8. Derivative policy

V1 does not require an IAC derivative term by default. RPM derivative is noisy and fast disturbance damping is already assigned to idle spark.

If later testing proves an IAC D term useful, it must be added as an explicit architecture revision rather than hidden inside follower or proportional calibration.

Initial V1 equation therefore uses PI airflow control.

## 9. Follower / dashpot term

Return-to-idle airflow is a separate state variable:

```text
IAC_FOLLOWER[n] = max(0,
                      IAC_FOLLOWER[n-1] - FOLLOWER_DECAY * dt)
```

On a qualified throttle-close / return-to-idle event, follower is seeded from a calibrated function of the preceding operating state, for example:

```text
IAC_FOLLOWER = FOLLOWER_SEED(RPM, TPS_CHANGE)
```

The final seed dimensionality should be kept only as complex as testing requires.

Follower airflow is explicitly transient. It must not alter the learned/base IAC position.

## 10. Stall-save / recovery term

A dedicated recovery term may be activated when RPM falls below a separately calibrated stall-save threshold:

```text
STALL_DEFICIT = max(0, STALL_SAVE_RPM - RPM_ACTUAL)
IAC_STALL_SAVE = clamp(0, STALL_SAVE_MAX,
                       STALL_SAVE_GAIN * STALL_DEFICIT)
```

It returns to zero when stall-save qualification clears.

This term exists to recover from a large disturbance and is not normal idle trim.

## 11. Preliminary IAC target

```text
IAC_TARGET_PRECLAMP =
    IAC_BASE
  + IAC_STARTUP_AIR
  + IAC_FOLLOWER
  + IAC_P
  + IAC_I
  + IAC_STALL_SAVE
```

## 12. IAC position limits and rate limit

```text
IAC_TARGET_CLAMPED = clamp(IAC_MIN_POSITION,
                           IAC_MAX_POSITION,
                           IAC_TARGET_PRECLAMP)
```

Desired-position motion may be rate limited before reaching the preserved GM stepper island:

```text
IAC_TARGET[n] = slew_limit(IAC_TARGET[n-1],
                           IAC_TARGET_CLAMPED,
                           IAC_OPEN_RATE,
                           IAC_CLOSE_RATE)
```

This gives opening/closing speed their own calibration instead of embedding rate effects into PI gains.

## 13. Coordination with idle spark

Idle spark uses the same:

```text
RPM_ERROR = TARGET_IDLE_RPM - RPM_ACTUAL
```

but provides fast bounded timing correction.

The IAC integral term owns long-term correction. Idle spark should return toward zero mean correction once IAC airflow has caught up.

This division prevents the two loops from fighting for steady-state authority.

## 14. DFCO / return-to-idle behavior

While DFCO is active, normal idle PI integration is frozen.

On DFCO exit / return-to-idle:

```text
follower/transition airflow may be active
PI state is resumed or explicitly reseeded
```

No DFCO calibration is allowed to silently rewrite base idle airflow.

## 15. Startup behavior

After crank-to-run transition:

```text
TARGET_IDLE_RPM = TARGET_IDLE_BASE + STARTUP_RPM_OFFSET
IAC feedforward  = IAC_BASE + IAC_STARTUP_AIR
```

Both startup-specific terms decay independently toward zero.

This lets a tuner separately fix:

```text
engine starts then RPM target is too high/low -> startup RPM offset
engine starts but lacks/exceeds bypass air     -> startup air
steady hot idle airflow wrong                  -> base IAC position
steady RPM error                               -> PI behavior/base air
```

## 16. Output boundary

The idle algorithm stops at:

```text
IAC_TARGET  [software position/count]
```

The preserved GM IAC island owns:

```text
actual-position tracking
direction state
zero-step direction reversal
A/B phase ring
port shadow merge
hardware output commit
```

No electrical phase/polarity detail belongs in the idle-control equations.

## 17. Likely XDF controls

```text
target idle RPM vs CTS
startup RPM offset vs CTS
startup RPM decay
base IAC position vs CTS
startup air vs CTS
startup air decay
idle RPM deadband
IAC Kp
IAC Ki
IAC integral min/max
IAC position min/max
IAC open/close slew rates
follower seed calibration
follower decay
stall-save RPM
stall-save gain
stall-save maximum
idle qualification thresholds/hysteresis
```

## 18. Required ADX observability

```text
IDLE_STATE
TARGET_IDLE_BASE
STARTUP_RPM_OFFSET
TARGET_IDLE_RPM
RPM_ACTUAL
RPM_ERROR
RPM_ERROR_EFFECTIVE
IAC_BASE
IAC_STARTUP_AIR
IAC_FOLLOWER
IAC_P
IAC_I
IAC_STALL_SAVE
IAC_TARGET_PRECLAMP
IAC_TARGET_CLAMPED
IAC_TARGET
IAC_ACTUAL_POSITION
IAC_DIRECTION_STATE
IAC_SATURATED
```

## 19. Non-effect contract

```text
Target RPM changes desired speed only.
Base IAC position changes steady feedforward air only.
Startup air changes post-start bypass air only.
Startup RPM offset changes post-start desired speed only.
IAC Kp/Ki change closed-loop airflow response only.
Follower changes return-to-idle transient air only.
Stall-save changes large-disturbance recovery only.
Idle spark is the fast timing actuator and does not rewrite IAC state.
No automatic-transmission or A/C compensation exists in V1.
```
