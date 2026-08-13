# V1 Engine Lifecycle Formula Contract

## Status

`DESIGN BASELINE — formula-first planning artifact`

This document defines engine lifecycle state, transition rules, and subsystem permissions before XDF/ADX layout or target assembly.

The design intentionally separates:

```text
PRIMARY LIFECYCLE STATE
    reset / stopped / cranking / running / key-off / shutdown

OPERATING QUALIFIERS
    afterstart / warmup / idle / PE / DFCO / oxygen feedback / knock
```

This avoids a combinatorial state machine where conditions such as warmup, idle, and PE are incorrectly treated as mutually exclusive lifecycle states.

## 1. Primary lifecycle states

```text
LIFE_RESET_SAFE
LIFE_KEYON_STOPPED
LIFE_CRANKING
LIFE_RUNNING
LIFE_KEYOFF_DELAY
LIFE_SHUTDOWN
```

A future explicit service/test state may be added, but no stock transmission/emissions lifecycle state belongs in V1.

## 2. Reset-safe state

Immediately after reset:

```text
all production output permissions = FALSE
fuel request = 0
spark request validity = FALSE
async-fuel pending = FALSE
fuel pump request = OFF until lifecycle logic explicitly permits it
IAC command permission = FALSE until initialization is complete
feedback integrators = reset/frozen
learned/adaptive updates = inhibited
```

Sensor acquisition, calibration validation, scheduler health, REF acquisition, and telemetry initialization may run.

Transition:

```text
LIFE_RESET_SAFE
    -> LIFE_KEYON_STOPPED
```

only after mandatory initialization and calibration-validity checks complete.

## 3. Rotation and REF freshness

Engine rotation is determined from REF/DRP timing rather than from an assumed RPM value alone.

Maintain:

```text
LAST_REF_PERIOD
REF_AGE
REF_VALID
ROTATION_VALID
```

Semantic timeout:

```text
REF_TIMEOUT = max(REF_TIMEOUT_MIN,
                  REF_TIMEOUT_MULTIPLIER * LAST_REF_PERIOD)

ROTATION_VALID = REF_VALID AND (REF_AGE <= REF_TIMEOUT)
```

This makes dropout detection scale with engine speed while retaining an absolute minimum timeout.

A missing/stale REF immediately prevents generation of new event-synchronous spark/fuel commands even before the longer stall state is confirmed.

## 4. Key-on stopped

Definition:

```text
ignition/power state valid
AND
ROTATION_VALID = FALSE
AND
key-off not qualified
```

Allowed behavior:

```text
sensor acquisition
BARO capture/qualification
fuel-pump prime sequence if enabled
IAC pre-position strategy if enabled
telemetry
diagnostics
```

Not allowed:

```text
normal synchronous fuel delivery
normal EST timing output
closed-loop oxygen correction
AE generation
DFCO
PE
```

Transition to cranking occurs on qualified REF/rotation.

## 5. Cranking state

Entry:

```text
LIFE_KEYON_STOPPED or post-stall stopped condition
AND
ROTATION_VALID = TRUE
AND
RUN_LATCH = FALSE
```

Cranking owns dedicated startup behavior:

```text
cranking fuel path
cranking spark path
cranking IAC/start-air behavior
fuel pump ON while qualified rotation exists
normal oxygen feedback inhibited
normal PE/DFCO inhibited
```

### Run-entry qualification

Define explicit semantic calibration values:

```text
RUN_ENTRY_RPM
RUN_ENTRY_CONFIRM_TIME
```

Run qualification:

```text
if RPM >= RUN_ENTRY_RPM continuously for RUN_ENTRY_CONFIRM_TIME:
    RUN_LATCH = TRUE
    LIFE_CRANKING -> LIFE_RUNNING
```

Run entry must use hysteresis/latching; it must not repeatedly switch between crank and run because RPM momentarily crosses one boundary.

## 6. Running state

Once `RUN_LATCH = TRUE`, the engine remains in `LIFE_RUNNING` while REF remains sufficiently fresh.

Low RPM by itself does not immediately return the engine to cranking. This gives stall-save and idle control a chance to recover the engine.

Running permits, subject to each module's own qualifier:

```text
normal air-charge estimation
normal fuel model
normal spark model
idle control
AE
PE
DFCO
NB/WB feedback
knock control
learning if retained
```

## 7. Stall/dropout handling

Two different concepts are retained:

```text
REF output-safety timeout
confirmed stall timeout
```

The shorter REF timeout prevents stale event commands.

Define:

```text
STALL_CONFIRM_TIME
```

If REF remains invalid for `STALL_CONFIRM_TIME` while previously running:

```text
RUN_LATCH = FALSE
fuel permission = FALSE
spark permission = FALSE
AE state = cleared
DFCO state = cleared
PE state = cleared
feedback integrators = frozen/reseed policy
idle integral = reset/reseed policy
```

If ignition remains on:

```text
LIFE_RUNNING -> LIFE_KEYON_STOPPED
```

A new REF sequence then enters `LIFE_CRANKING` and permits a normal restart.

## 8. Afterstart qualifier

`AFTERSTART_ACTIVE` is not a primary lifecycle state.

It begins exactly on the qualified transition:

```text
LIFE_CRANKING -> LIFE_RUNNING
```

Capture start conditions:

```text
CTS_AT_RUN_ENTRY
AFTERSTART_ELAPSED = 0
```

Recommended semantic model:

```text
AFTERSTART_EXCESS(t) =
    AFTERSTART_EXCESS_INITIAL(CTS_AT_RUN_ENTRY)
    * exp(-t / AFTERSTART_TAU(CTS_AT_RUN_ENTRY))

AFTERSTART_FACTOR = 1 + AFTERSTART_EXCESS
```

Implementation may use a precomputed discrete decay coefficient rather than calculating `exp()` at runtime, but the tuner-facing meaning remains an initial excess and a decay time constant.

`AFTERSTART_ACTIVE` clears when the remaining excess falls below a small explicit completion threshold or a bounded maximum duration expires.

A stall/restart starts a new afterstart event.

## 9. Warmup qualifier

Warmup is also a concurrent qualifier, not a lifecycle state.

The warmup fuel factor is already defined by coolant temperature:

```text
WARMUP_FACTOR = WARMUP_TABLE(CTS)
```

Define:

```text
WARMUP_ACTIVE = abs(WARMUP_FACTOR - 1.000) > WARMUP_NEUTRAL_EPSILON
```

Other temperature-dependent modules may expose their own hot-neutral endpoints.

There is no requirement for one global 'warmup complete' bit to alter unrelated modules.

## 10. Idle qualification

Idle is an operating qualifier inside `LIFE_RUNNING`.

Required entry conditions:

```text
LIFE_RUNNING
TPS <= IDLE_TPS_ENTER
RPM <= IDLE_RPM_ENTRY_MAX
DFCO_ACTIVE = FALSE
PE_ACTIVE = FALSE
conditions held for IDLE_ENTRY_DELAY
```

Exit occurs if any explicit exit condition is met:

```text
TPS >= IDLE_TPS_EXIT
RPM >= IDLE_RPM_EXIT_MAX
DFCO_ACTIVE = TRUE
PE_ACTIVE = TRUE
lifecycle leaves LIFE_RUNNING
```

Use hysteresis:

```text
IDLE_TPS_EXIT > IDLE_TPS_ENTER
IDLE_RPM_EXIT_MAX >= IDLE_RPM_ENTRY_MAX
```

No automatic-transmission P/N input and no A/C load state participate in V1 idle qualification.

## 11. PE qualification

PE is a running qualifier that changes target lambda rather than applying an unrelated hidden multiplier.

Use normalized manifold pressure and/or throttle demand:

```text
PRESSURE_RATIO = MAP / BARO
```

Define explicit entry requests:

```text
PE_LOAD_REQUEST = PRESSURE_RATIO >= PE_PRESSURE_RATIO_ENTER(RPM)
PE_TPS_REQUEST  = TPS >= PE_TPS_ENTER(RPM)
```

Preliminary V1 policy:

```text
PE_REQUEST = PE_LOAD_REQUEST OR PE_TPS_REQUEST
```

with:

```text
PE_ENTRY_DELAY
PE_PRESSURE_RATIO_EXIT(RPM)
PE_TPS_EXIT(RPM)
```

providing hysteresis and delay.

PE may not activate while cranking, DFCO-active, key-off, or stopped.

When active, PE owns:

```text
LAMBDA_TARGET = PE_LAMBDA_TARGET(RPM, selected_load_axis)
```

It does not alter VE, injector flow, or closed-loop calibration.

## 12. DFCO qualification

DFCO is a running fuel state.

Required entry conditions:

```text
LIFE_RUNNING
TPS <= DFCO_TPS_ENTER
RPM >= DFCO_RPM_ENTER
MAP <= DFCO_MAP_ENTER or PRESSURE_RATIO <= DFCO_PR_ENTER
PE_ACTIVE = FALSE
conditions held for DFCO_ENTRY_DELAY
```

Once active:

```text
REQUESTED_FUEL_MASS_CYCLE = 0
AE generation inhibited
NB/WB feedback integrators frozen
learning frozen
idle PI integration frozen
```

Exit conditions use separate hysteresis values:

```text
TPS >= DFCO_TPS_EXIT
OR RPM <= DFCO_RPM_EXIT
OR MAP >= DFCO_MAP_EXIT / pressure-ratio equivalent
OR lifecycle leaves LIFE_RUNNING
```

On exit, the idle/follower subsystem may receive an explicit `DFCO_EXIT_EVENT` for smooth return-to-idle airflow.

## 13. Closed-loop oxygen qualification

Feedback mode selection is independent from qualification.

Configured mode:

```text
OPEN_LOOP
NB_ONLY
WB_ONLY
DUAL
```

Even when configured, feedback is active only when all common conditions are satisfied:

```text
LIFE_RUNNING
not cranking
not DFCO
minimum run time satisfied
coolant threshold satisfied
required sensor valid
lambda target inside the selected feedback path's allowed region
```

Additional NB rule:

```text
NB feedback only near lambda = 1.000
```

WB may operate over a wider target-lambda region if explicitly enabled.

Loss of qualification freezes/reseeds the controller according to its own state contract; it does not modify base VE or target lambda.

## 14. Knock-control qualification

Knock response may run only when:

```text
LIFE_RUNNING
knock feature enabled
knock sensor/path valid
RPM/load inside qualified region
```

Cranking and stopped states command zero knock retard.

Invalid configured knock sensing invokes the separate diagnostic/failsafe policy rather than silently pretending there is no knock.

## 15. Key-off detection

The stock hardware does not provide V1 with a separately characterized dedicated ignition-switch semantic input, so the initial model retains the proven battery/ignition-state inference path.

Define:

```text
KEYOFF_VOLTAGE_THRESHOLD
KEYOFF_CONFIRM_TIME
```

Qualification:

```text
BATTERY_VOLTAGE <= KEYOFF_VOLTAGE_THRESHOLD
continuously for KEYOFF_CONFIRM_TIME
```

The final seed values may be derived from stock behavior, but the semantic variables remain explicit.

On key-off qualification:

```text
LIFE_* -> LIFE_KEYOFF_DELAY
```

and immediately:

```text
fuel permission = FALSE
spark permission = FALSE
fuel pump request = OFF
async-fuel pending = FALSE
PE = FALSE
DFCO = FALSE
feedback updates = frozen
learning writes = inhibited
```

No external engine-control load is intentionally kept powered merely to service the shutdown timer.

## 16. Key-off delay and shutdown

`LIFE_KEYOFF_DELAY` exists for internal housekeeping only.

Permitted work may include:

```text
final state bookkeeping
nonvolatile-data commit if retained
telemetry/service-state completion while power remains available
watchdog-safe shutdown sequencing
```

Define:

```text
KEYOFF_SHUTDOWN_DELAY
```

After the delay, or earlier if supply voltage can no longer support safe execution:

```text
LIFE_KEYOFF_DELAY -> LIFE_SHUTDOWN
```

All production outputs remain disabled throughout the key-off delay.

## 17. Fuel-pump lifecycle

Pump control is kept simple and explicit:

```text
KEYON prime:
    pump ON for FUEL_PUMP_PRIME_TIME if feature enabled

CRANKING:
    pump ON while qualified rotation exists

RUNNING:
    pump ON

confirmed stall:
    pump OFF

KEYOFF_DELAY / SHUTDOWN:
    pump OFF
```

Pump prime is not proof of engine rotation and must never grant spark/fuel-event permission by itself.

## 18. Output permission matrix

Conceptual permissions:

```text
STATE                FUEL   SPARK   IAC*   PUMP
RESET_SAFE            no      no     no     no
KEYON_STOPPED          no      no    prep   prime-only
CRANKING              yes     yes    yes    yes
RUNNING               yes     yes    yes    yes
KEYOFF_DELAY           no      no     no     no
SHUTDOWN               no      no     no     no
```

`IAC prep` means a deliberately defined pre-position action may be allowed before rotation; it does not mean unrestricted normal closed-loop idle stepping.

Actual preserved-output-island calls remain additionally gated by calibration validity, subsystem command validity, and hardware/output permission.

## 19. Physical/setup, behavioral, and derived values

Following the V1 physical-configuration policy, lifecycle parameters are classified intentionally.

### Physical/observed inputs

```text
BATTERY_VOLTAGE
REF timing
RPM derived from REF
TPS
MAP
BARO
CTS
```

### Behavioral calibration

```text
RUN_ENTRY_RPM
RUN_ENTRY_CONFIRM_TIME
REF_TIMEOUT_MULTIPLIER
REF_TIMEOUT_MIN
STALL_CONFIRM_TIME
IDLE_TPS_ENTER / EXIT
IDLE_RPM_ENTRY_MAX / EXIT_MAX
IDLE_ENTRY_DELAY
PE entry/exit thresholds and delay
DFCO entry/exit thresholds and delay
feedback qualification thresholds
KEYOFF_VOLTAGE_THRESHOLD
KEYOFF_CONFIRM_TIME
KEYOFF_SHUTDOWN_DELAY
FUEL_PUMP_PRIME_TIME
```

### Derived/read-only values

```text
REF_AGE
REF_TIMEOUT
ROTATION_VALID
RUN_LATCH
AFTERSTART_ELAPSED
AFTERSTART_FACTOR
WARMUP_ACTIVE
IDLE_ACTIVE
PE_ACTIVE
DFCO_ACTIVE
FEEDBACK_QUALIFIED
```

Derived state is observable in ADX but must not be independently editable.

## 20. Required ADX observability

At minimum:

```text
LIFECYCLE_STATE
REF_VALID
REF_AGE
REF_TIMEOUT
ROTATION_VALID
RPM
RUN_LATCH
AFTERSTART_ACTIVE
AFTERSTART_ELAPSED
AFTERSTART_FACTOR
WARMUP_ACTIVE
IDLE_ACTIVE
PE_LOAD_REQUEST
PE_TPS_REQUEST
PE_ACTIVE
DFCO_ACTIVE
FEEDBACK_CONFIG_MODE
FEEDBACK_QUALIFIED
KNOCK_QUALIFIED
KEYOFF_REQUEST
KEYOFF_TIMER
FUEL_PERMISSION
SPARK_PERMISSION
IAC_PERMISSION
PUMP_REQUEST
```

This allows every lifecycle-dependent change in fuel, spark, idle, feedback, and pump behavior to be explained from logged state.

## 21. Non-effect contract

```text
Lifecycle state grants or denies module operation; it does not retune module equations.
Afterstart owns only post-run-entry transient behavior.
Warmup terms remain temperature-model terms, not an all-purpose state switch.
Idle qualification selects idle control only.
PE changes target lambda only.
DFCO explicitly requests zero fuel and freezes incompatible controllers.
Key-off disables production outputs immediately; shutdown delay is internal housekeeping only.
No automatic-transmission, EGR, EVAP, AIR, or A/C state participates in V1 lifecycle logic.
```

Any future feature must enter through an explicitly named qualifier or module interface rather than by adding hidden conditions to these existing states.
