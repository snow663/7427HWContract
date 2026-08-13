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

## Canonical audit authority

Current detailed status and authority map:

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
```

Use that audit when this summary and an older planning artifact appear to disagree.

## Frozen reverse-engineering / hardware-contract state

```text
algorithm extraction             100% FROZEN
scheduler/lifecycle extraction   100% FROZEN
diagnostics/failsafe extraction  100% FROZEN
production calibration audit     100% FROZEN
V1 software-facing HW contract   100% FROZEN
physical endpoint confirmation     0% INTENTIONALLY DEFERRED
```

Do not reopen the frozen extraction categories unless contradictory executable/ROM evidence appears or V1 scope is intentionally expanded.

## V1 executable scope

V1 is engine-control only.

Excluded:

```text
automatic transmission
EGR
EVAP
secondary AIR
A/C compressor control
A/C idle-up / load compensation
```

Unused I/O remains reserved/documented for future expansion.

## Replacement-OS planning status

```text
V1 feature scope                   100%
control/formula semantics          100%
physical/setup model               100%
sensor transfer model              100%
signal-conditioning model          100%
rotation/reference geometry        100% for V1 validated trigger relationship
module interfaces                  100%
calibration/XDF semantic exposure  100%
calibration table geometry         100%
ADX semantic channel definition    100%
degraded-operation policy          100%
ROM/RAM address layout               0%
binary fixed-point/storage layout    0%
actual XDF generation                0%
actual ADX packet/file generation    0%
build/version manifest               0%
```

The semantic/control planning gate is now closed. The remaining pre-assembly gate is binary/memory/build architecture.

## Current planning authorities

### Formula / behavior

```text
docs/planning/V1_ENGINE_CONTROL_SCOPE.md
docs/planning/V1_AIR_CHARGE_FORMULA_CONTRACT.md
docs/planning/V1_FUEL_CONTROL_FORMULA_CONTRACT.md
docs/planning/V1_SPARK_CONTROL_FORMULA_CONTRACT.md
docs/planning/V1_IDLE_CONTROL_FORMULA_CONTRACT.md
docs/planning/V1_ENGINE_LIFECYCLE_FORMULA_CONTRACT.md
docs/planning/V1_SENSOR_SEMANTIC_VALIDATION_CONTRACT.md
docs/planning/V1_SENSOR_TRANSFER_CALIBRATION.md
docs/planning/V1_SIGNAL_CONDITIONING_FILTER_CONTRACT.md
docs/planning/V1_PHYSICAL_CONFIGURATION_MODEL.md
docs/planning/V1_ROTATION_REFERENCE_CONFIGURATION.md
```

### Machine-readable planning

```text
maps/planning/v1_configuration_variables.csv
maps/planning/v1_module_interface_matrix.csv
maps/planning/v1_calibration_manifest.csv
maps/planning/v1_table_geometry.csv
maps/planning/v1_degraded_operation_policy.csv
```

There is no longer a separate `v1_module_interface_matrix_v2.csv`; the canonical interface matrix has been consolidated back to `v1_module_interface_matrix.csv`.

All current calibration exposure fragments live under:

```text
maps/planning/calibration_fragments/
```

### Telemetry

Canonical manifest:

```text
maps/telemetry/v1_adx_manifest.csv
```

It includes core sensor/REF/air-charge telemetry, fuel, feedback, spark, idle, injector characterization, fuel-delivery geometry/duration, and BARO policy.

## Frozen design highlights

### Air charge

Hybrid speed-density / Alpha-N produces one downstream quantity:

```text
AIR_MASS_CYCLE
```

Speed density is primary at steady state; Alpha-N supplies bounded high-load and transient prediction authority.

### Injector physical model

```text
EFFECTIVE_INJECTOR_FLOW =
    INJECTOR_DESIGN_FLOW
    * sqrt(OPERATING_FUEL_PRESSURE / INJECTOR_DESIGN_PRESSURE)
```

Design flow/design pressure describe the injector. Operating pressure describes the regulator setting. Effective IFR is derived/read-only.

Fuel delivery geometry is separately configured by injector count, delivery events per 720-degree cycle, and active injectors per event.

### Sensors

Analog control inputs use:

```text
RAW ADC
-> VDC
-> VDC-to-engineering transfer table
-> sensor-specific filtering
-> validity/substitution
-> control engineering value
```

MAT/IAT is optional added hardware on the current L19 application.

### BARO

BARO is captured from valid filtered MAP before rotation/cranking and held for the run cycle.

### Rotation/reference geometry

Editable setup includes:

```text
CYLINDER_COUNT
REF_EVENTS_PER_CRANK_REV
REF_TO_EVENT_TDC_OFFSET_DEG
```

For an 8-cylinder / 4-REF-events-per-crank-revolution setup, the derived REF and combustion spacing are both 90 crank degrees and the relationship is one REF event per combustion event.

REF offset aligns the software crank coordinate to true event TDC; it does not mechanically change rotor-to-cap phasing.

### Filtering

ADC/digital filtering is explicit and sensor-specific. TPS/MAP remain fast; CTS/MAT are slower; NB/WB preserve feedback dynamics. REF edges are timestamped directly and only screened for physically impossible/implausible events rather than delayed by generic debounce.

### Spark/load

V1 main spark and knock-threshold load axis is:

```text
RPM x MAP kPa absolute
```

PE target lambda uses RPM x MAP/BARO pressure ratio. The optional extra PE spark-correction surface is not part of frozen V1.

### Learning

Long-term adaptive fuel learning is not part of V1:

```text
LEARN_FACTOR = 1.000
```

NB/WB runtime feedback remains supported.

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

The current safe runtime does not call the preserved output-island module.

## Replacement-OS implementation status

```text
replacement-OS implementation   ~18%
complete runnable replacement     0%
```

Current source is an engine-off scaffold, not an implementation of the newly frozen semantic model.

Known implementation gaps include:

```text
runtime ABI still uses earlier byte/count placeholders and old lifecycle enum names
engineering-unit sensor pipeline not implemented
signal-conditioning/validation/substitution modules not implemented
configurable REF geometry/RPM scaling not implemented
hybrid SD/Alpha-N air-charge manager not implemented
mass-based fuel algorithm not implemented
spark/idle control algorithms not implemented
SCI/ALDL transport not implemented
final ADX packet/page layout not allocated
ROM/RAM/linker/ORG/vector layout not frozen
full spark/EST preserved island not ported
```

## Correct next gate

Proceed in this order:

```text
1. choose binary fixed-point/storage encodings for every frozen semantic type
2. allocate ROM calibration blocks using frozen table geometry
3. allocate RAM runtime state and telemetry snapshot regions
4. allocate ALDL/SCI packet pages/frames from the ADX manifest
5. freeze linker/ORG/vector layout around preserved GM islands
6. freeze build/version manifest
7. refactor runtime_abi.inc to the consolidated semantic ABI
8. build first target-linked engine-off observability image
9. complete and validate the full spark/EST preserved island
10. begin engine-running control implementation in frozen module order
```

No further broad algorithm extraction or architecture redesign is required before step 1 unless V1 scope changes or contradictory ROM/hardware evidence appears.
