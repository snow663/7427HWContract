# 7427 Completion Status

## Primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

## Current status

| Category | Current | Status |
|---|---:|---|
| Algorithm extraction | **100%** | **FROZEN** |
| Scheduler/lifecycle | **100%** | **FROZEN** |
| Diagnostics/failsafe | **100%** | **FROZEN** |
| Calibration/tuning | **100%** | **FROZEN** |
| V1 software-facing hardware contract | **100%** | **FROZEN FOR FIRST ENGINE-CONTROL SCOPE** |
| Physical endpoint confirmation | **0%** | **DEFERRED VALIDATION / FUTURE NATIVE-DRIVER WORK** |
| Replacement-OS implementation | **18%** | **ACTIVE; PRE-ASSEMBLY FORMULA/PLANNING GATE FIRST** |
| Complete runnable replacement | **0%** | **AFTER PLANNING + TARGET-LINKED BUILD** |

## V1 architecture decision

```text
custom control algorithms
→ semantic requests
→ compatibility/arbitration layer
→ preserved GM command islands
→ existing 7427 hardware
```

V1 scope authority:

- `docs/planning/V1_ENGINE_CONTROL_SCOPE.md`
- `docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md`

Excluded from V1 executable scope:

```text
automatic transmission
EGR
EVAP
secondary AIR
A/C control / A/C idle compensation
```

Unused I/O is reserved/documented for future applications rather than carrying dead runtime logic.

## Preserved command-island state

```text
Fuel synchronous     LOCKED ABI + PORTED
Fuel asynchronous    LOCKED ABI + PORTED
IAC                   LOCKED ABI + PORTED
Fuel pump             LOCKED ABI + PORTED
Spark/EST             LOCKED ABI; complete rolling-state port pending
MIL                   DEFERRED
Unused I/O            RESERVED FOR FUTURE USE
```

The preserved command-island module is not currently called by the engine-off runtime.

## Replacement OS components already present

```text
semantic runtime ABI
actuator-disabled safe initialization
6.25 ms semantic scheduler / 16-segment counter
REF event ingestion and dropout-safe state
key-off/shutdown semantic states
calibration-validity gate
semantic command arbitration
read-only TPS/MAP/O2/coolant/MAT/battery acquisition paths
read-only REF-period handoff
24-byte semantic debug frame builder with checksum
preserved fuel sync/async, IAC and pump command-island module
```

## Pre-assembly formula/control-model gate

Formula design now precedes XDF/ADX/interface/memory implementation.

Committed formula contracts:

- `docs/planning/V1_FUEL_CONTROL_FORMULA_CONTRACT.md`
- `docs/planning/V1_SPARK_CONTROL_FORMULA_CONTRACT.md`
- `docs/planning/V1_IDLE_CONTROL_FORMULA_CONTRACT.md`

### Fuel-model baseline

The V1 fuel system is **fuel-mass based, not pulse-width based**.

```text
speed-density air mass
→ target lambda
→ requested fuel mass per 720-degree engine cycle
→ startup/warmup/transient/feedback contributions
→ event/injector delivery division
→ pressure-corrected injector flow
→ short-pulse model
→ voltage deadtime
→ command PW
→ preserved GM fuel command island
```

For the TBI injector arrangement:

```text
FLOW_EFFECTIVE = FLOW_RATED * sqrt(P_FUEL_GAUGE / P_RATED)
```

MAP is not part of injector differential pressure because the injectors discharge above the throttle plates.

Mandatory ownership separation:

```text
VE                  -> engine air model only
fuel pressure/flow  -> injector delivery conversion only
deadtime            -> electrical opening compensation only
short-pulse curve   -> injector nonlinearity only
warmup              -> cold run enrichment only
afterstart          -> post-start enrichment only
AE                  -> additive transient fuel only
PE                  -> target lambda only
NB/WB feedback      -> one bounded feedback factor only
DFCO                -> explicit zero-fuel state
```

### Spark-model baseline

```text
crank spark or main/idle base spark
+ CTS correction
+ MAT correction
+ optional explicit high-load correction
+ fast idle spark correction
- knock retard
→ final spark clamp
→ preserved GM EST/ASIC island
```

### Idle-model baseline

```text
IAC airflow loop = slow PI / long-term control
idle spark loop  = fast bounded damping
```

IAC target is composed from independently observable base, startup, follower, PI, and stall-save contributions. No automatic-transmission or A/C load terms exist.

## Remaining planning order

Before target assembly/integration:

```text
1. freeze lifecycle/state and sensor-validation formulas
2. review/finalize fuel, spark, and idle formula contracts
3. freeze V1 module interfaces
4. generate calibration/XDF exposure matrix from formulas
5. generate telemetry/ADX matrix from formulas
6. freeze ROM/RAM memory layout
7. freeze build/version manifest
```

Every tuner-facing control must have:

```text
stable semantic ID
engineering units/range
one documented intended effect
explicit non-effects
owning formula/module
matching ADX observability where practical
```

XDF and ADX definitions must derive from the same semantic definitions used by firmware so names, scaling, addresses, and meaning cannot silently drift.

## Following major gate

After the formula/planning gate is frozen, build the first target-linked engine-off observability image with all production-output permissions false and preserved command islands uncalled.
