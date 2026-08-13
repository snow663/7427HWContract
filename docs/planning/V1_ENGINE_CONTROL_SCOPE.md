# V1 Engine-Control Scope

## Purpose

Freeze the retained feature set for the first clean 16197427 / $31 replacement OS before calibration, telemetry, memory, and assembly layout are designed.

The V1 OS is intentionally an engine-control system, not a stock-feature clone.

## Retained top-level systems

```text
SPARK CONTROL
FUEL DELIVERY
IDLE CONTROL
ENGINE LIFECYCLE / STARTUP / SHUTDOWN
SENSOR ACQUISITION + VALIDATION / SUBSTITUTION
DEVELOPMENT / TUNERPRO TELEMETRY
```

Everything in V1 must support one of those responsibilities directly.

## Explicitly excluded from V1 executable scope

```text
automatic-transmission control
EGR
EVAP
secondary AIR injection
A/C compressor control
A/C idle-up / A/C load compensation
stock emissions-management logic not required for basic engine control
unused stock diagnostic/service logic tied only to excluded systems
```

These features must not consume runtime code, RAM state, scheduler slots, calibration space, XDF clutter, or ADX bandwidth in the V1 implementation.

Historical stock definitions may remain in reference/disassembly material, but they are not part of the new OS.

## Fuel-control scope

Retain a clean fuel system with explicit, separately owned functions:

```text
base/load fuel calculation
injector characterization
cranking fuel
post-start / afterstart enrichment
warmup enrichment
acceleration enrichment / transient fuel
power enrichment
DFCO / decel fuel behavior
closed-loop feedback manager
optional learned correction if retained in the final V1 design
final synchronous fuel command
asynchronous / AE pulse command where required
fuel-pump lifecycle control
```

The calibration model must avoid using one parameter to compensate for unrelated behaviors when a dedicated parameter can be provided.

## Closed-loop feedback architecture

Both narrowband and wideband oxygen feedback are first-class optional inputs.

Required selectable modes:

```text
OPEN_LOOP
NB_ONLY
WB_ONLY
DUAL
```

Rules:

1. Open-loop operation must be complete and fully usable with no oxygen-feedback dependency.
2. Narrowband feedback may be enabled without a wideband sensor.
3. Wideband feedback may be enabled without a narrowband sensor.
4. Both sensors may be installed and used together.
5. NB and WB controllers must not independently multiply fuel and fight one another.
6. Both sensors feed one Fuel Feedback Manager, which produces one bounded final feedback correction.
7. Sensor validity, operating-region qualification, authority, learning, and fallback behavior are explicit and independently observable in the ADX.
8. Failure or disabling of either feedback path must not disturb base open-loop fueling.

The exact `DUAL` fusion strategy is a pre-assembly design item. It must define each sensor's role and prevent overlapping uncontrolled integrators.

## Spark-control scope

Retain a clean spark system with explicit contributions such as:

```text
base/main spark
startup / crank-to-run behavior
idle spark control
coolant correction
inlet-air-temperature correction
load / power-enrichment correction where desired
knock response if enabled
limits / clamps / safety retard
final timing command
preserved GM EST / ASIC output-command island
```

Excluded subsystems must not influence spark state.

## Idle-control scope

Retain a clean idle system with explicit contributions such as:

```text
desired idle RPM
base idle airflow / IAC position
startup air
warmup idle behavior
proportional response
integral response
optional derivative / follower behavior
stall-save / recovery behavior
idle spark contribution
DFCO / return-to-idle transition behavior
```

No automatic-transmission P/N or gear-load compensation and no A/C load compensation exist in V1.

## Supporting engine functions

The following are retained because the three primary systems depend on them:

```text
reset / initialization
6.25 ms scheduler and required event timing
REF / DRP processing and RPM
crank / run qualification
stall / dropout handling
key-off delayed shutdown
battery / ignition-state handling
sensor acquisition
sensor plausibility / substitution
calibration integrity
watchdog / scheduler health
ALDL / development telemetry
```

## Calibration / TunerPro policy

The XDF exposes useful tuning intent, not every internal variable.

Every exposed parameter requires:

```text
stable semantic ID
clear tuner-facing name
engineering units and legal range
owning module
one documented intended effect
explicit non-effects
matching ADX observability where practical
```

Where stock behavior used a shared calibration with undesirable side effects, V1 should split it into independent semantic controls when RAM/ROM/runtime cost is reasonable.

## ADX policy

The ADX should expose both final results and important contributors so calibration effects can be verified directly.

Examples:

```text
fuel: base, injector correction, startup/warmup, AE, PE, feedback, learned correction, final PW
spark: base, temperature corrections, idle correction, knock correction, final spark
idle: target RPM, base position/air, P/I/D/follower contributions, final IAC target
feedback: NB validity/error/state, WB validity/lambda/error/state, selected mode, final feedback correction
lifecycle: crank/run/dropout/key-off state, REF validity, RPM
```

## Unused I/O policy

Any hardware endpoint not used by V1 is not discarded or repurposed casually.

Each unused endpoint is to be recorded as:

```text
RESERVED_UNUSED_V1
original known/candidate stock function
known software/hardware address information
whether electrically characterized
whether safe state is known
future-use notes
```

Unused endpoints are reserved for later applications such as additional sensors, outputs, vehicle functions, data acquisition, or native-driver expansion.

They do not receive runtime logic in V1 unless deliberately promoted through a future feature revision.

## V1 architectural summary

```text
SENSORS / REF
      ↓
VALIDATION + ENGINE STATE
      ↓
┌──────────────┬──────────────┬──────────────┐
│ FUEL CONTROL │ SPARK CONTROL│ IDLE CONTROL │
└──────┬───────┴──────┬───────┴──────┬───────┘
       │              │              │
       └──── semantic requests ──────┘
                      ↓
             SAFETY / ARBITRATION
                      ↓
            PRESERVED GM COMMAND ISLANDS
                      ↓
                 7427 HARDWARE
```

No automatic-transmission, EGR, EVAP, AIR, or A/C control module belongs in this V1 path.

## Planning consequence

The five pre-assembly planning artifacts must now be generated only from this scope:

```text
1. calibration / XDF exposure matrix
2. telemetry / ADX matrix
3. module interface matrix
4. ROM/RAM memory layout
5. build/version manifest
```

Anything excluded here is not allowed to re-enter those artifacts merely because stock BMHM contained it.
