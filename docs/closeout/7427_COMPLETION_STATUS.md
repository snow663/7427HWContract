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

## Frozen reverse-engineering state

```text
algorithm extraction            100% FROZEN
scheduler/lifecycle             100% FROZEN
diagnostics/failsafe            100% FROZEN
calibration/tuning              100% FROZEN
V1 software-facing HW contract  100% FROZEN
physical endpoint confirmation    0% DEFERRED VALIDATION
replacement-OS implementation    18% ACTIVE; PLANNING GATE FIRST
complete runnable replacement     0%
```

## V1 scope

Engine-control-only replacement OS. Excluded from V1 executable scope:

```text
automatic transmission
EGR
EVAP
secondary AIR
A/C control / A/C idle compensation
```

Unused I/O remains reserved/documented for future expansion.

## Control-model planning now frozen

Committed planning authorities include:

```text
docs/planning/V1_ENGINE_CONTROL_SCOPE.md
docs/planning/V1_FUEL_CONTROL_FORMULA_CONTRACT.md
docs/planning/V1_SPARK_CONTROL_FORMULA_CONTRACT.md
docs/planning/V1_IDLE_CONTROL_FORMULA_CONTRACT.md
docs/planning/V1_AIR_CHARGE_FORMULA_CONTRACT.md
docs/planning/V1_PHYSICAL_CONFIGURATION_MODEL.md
docs/planning/V1_ENGINE_LIFECYCLE_FORMULA_CONTRACT.md
docs/planning/V1_SENSOR_SEMANTIC_VALIDATION_CONTRACT.md
docs/planning/V1_SENSOR_TRANSFER_CALIBRATION.md
```

V1 air charge is hybrid speed-density / Alpha-N with one downstream semantic output:

```text
AIR_MASS_CYCLE
```

Fuel is mass-based. Injector characterization separates design point from operating pressure:

```text
EFFECTIVE_INJECTOR_FLOW =
    INJECTOR_DESIGN_FLOW
    * sqrt(OPERATING_FUEL_PRESSURE / INJECTOR_DESIGN_PRESSURE)
```

Analog inputs are converted from raw ADC observations to VDC and then through sensor-specific transfer calibration into engineering units before control logic consumes them.

BARO is captured from qualified MAP before rotation and held for the run cycle.

## Module-interface planning

Current machine-readable interface authority:

```text
v1_module_interface_matrix_v2.csv
```

The corrected dependency order is:

```text
sensor semantics
-> air charge
-> combustion target / lambda target
-> oxygen feedback
-> fuel mass
-> delivery model
```

This avoids circular ownership between target-lambda generation and oxygen feedback.

## Calibration/XDF exposure planning

Machine-readable calibration fragments now cover:

```text
engine/fuel setup and tuning
spark
idle core
idle transition
```

Physical setup, behavioral tuning, and derived/read-only quantities are intentionally separated.

## ADX/telemetry planning

Current telemetry manifest:

```text
maps/telemetry/v1_adx_manifest.csv
```

It references:

```text
v1_adx_core.csv
v1_adx_fuel_core.csv
v1_adx_feedback.csv
v1_adx_spark.csv
v1_adx_idle.csv
v1_adx_injector_characterization.csv
v1_adx_delivery_duration.csv
v1_baro_policy.csv
```

Telemetry preserves raw diagnostics while exposing control-facing values in engineering units and showing intermediate contributors needed to explain final behavior.

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

Preserved command islands remain uncalled by the current safe engine-off runtime.

## Remaining planning gate

The formula, interface, calibration-exposure, and telemetry-definition stages are sufficiently frozen to proceed.

Remaining pre-assembly work is now:

```text
1. freeze ROM/RAM memory layout and telemetry snapshot allocation
2. freeze build/version manifest
3. reconcile target linker/ORG layout with preserved GM islands
4. build first target-linked engine-off observability image
```

The first target-linked image must keep all production-output permissions false while proving reset/startup, scheduler, sensor acquisition, REF visibility during cranking, lifecycle state, semantic telemetry, and calibration validity.
