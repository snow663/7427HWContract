# 7427 V1 Planning Consolidation Audit

## Status

`AUDITED / CONSOLIDATED — 2026-08-13`

This audit reconciles the replacement-OS planning artifacts after the hybrid SD/Alpha-N, physical injector model, sensor-transfer, signal-conditioning, and configurable REF-geometry decisions.

It distinguishes **semantic design authority** from the older engine-off implementation scaffold.

## 1. Canonical authority order

Use the following sources in this order when implementation begins:

```text
1. docs/planning/V1_ENGINE_CONTROL_SCOPE.md
2. docs/planning/V1_*_FORMULA_CONTRACT.md and current setup/filter contracts
3. maps/planning/v1_configuration_variables.csv
4. maps/planning/v1_module_interface_matrix.csv
5. maps/planning/v1_calibration_manifest.csv + listed fragments
6. maps/planning/v1_table_geometry.csv
7. maps/planning/v1_degraded_operation_policy.csv
8. maps/telemetry/v1_adx_manifest.csv + listed fragments
9. docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md
10. source/replacement_os/* only as the current implementation scaffold, not as newer semantic authority
```

## 2. Consolidation corrections completed

### Module interfaces

The duplicate `v1_module_interface_matrix_v2.csv` was removed.

`maps/planning/v1_module_interface_matrix.csv` is now the only machine-readable module-interface authority and includes explicit layers for:

```text
calibration validation
raw acquisition
ADC count -> voltage conversion
sensor voltage -> engineering transfer
signal conditioning
sensor validation/substitution
rotation/reference geometry
physical configuration
BARO capture
lifecycle
air charge
combustion target
oxygen feedback
transient fuel
fuel mass
injector delivery
idle
knock
spark
pump
arbitration
preserved output islands
telemetry
```

The target-lambda / oxygen-feedback circular dependency is eliminated: target lambda is produced before feedback, and final fuel mass consumes the resulting feedback factor.

### Calibration organization

All current machine-readable calibration exposure fragments now live under:

```text
maps/planning/calibration_fragments/
```

The duplicate signal-conditioning fragment under `docs/planning/calibration_fragments/` was removed.

Canonical fragment list is controlled by:

```text
maps/planning/v1_calibration_manifest.csv
```

### Sensor transfers

The older hard-coded/two-point sensor entries in the engine/fuel fragment were removed as authority.

Canonical analog transfer architecture is now:

```text
RAW ADC
-> input VDC
-> VDC-to-engineering 1-D transfer table
-> filtering
-> validity/substitution
-> control engineering value
```

MAT/IAT is explicitly optional added hardware for the current L19 application.

All analog transfer tables have a fixed 16-point table capacity in V1 geometry. Linear sensors may simply populate a linear curve.

### Signal conditioning

Filtering is sensor-specific rather than one global GM-style smoothing value.

Canonical exposure now includes separate TPS/MAP position and rate filtering, slower CTS/MAT filtering, battery filtering, NB/WB filtering, per-signal spike limits, and REF period/edge plausibility controls.

REF edges are never delayed by generic debounce or low-pass filtering.

### Rotation/reference geometry

Editable physical/setup values now include:

```text
CYLINDER_COUNT
REF_EVENTS_PER_CRANK_REV
REF_TO_EVENT_TDC_OFFSET_DEG
```

Derived values include:

```text
REF_EVENTS_PER_ENGINE_CYCLE
REF_EVENT_SPACING_DEG
COMBUSTION_EVENT_SPACING_DEG
REF_EVENTS_PER_COMBUSTION_EVENT
```

For the intended V8 / 4 REF-events-per-crank-revolution case:

```text
8 cylinders
4 REF events / crank rev
8 REF events / 720-degree cycle
90 crank degrees / REF event
90 crank degrees / combustion event
1 REF event / combustion event
```

`REF_TO_EVENT_TDC_OFFSET_DEG` aligns the software crank coordinate to true event TDC. It does not mechanically change rotor-to-cap phasing.

V1 production scheduling must explicitly validate the REF/combustion relationship. Arbitrary non-1:1 trigger patterns require a future explicit synchronization/event-mapping strategy rather than being silently inferred from cylinder count.

### Fuel-delivery physical configuration

Injector characterization is now permanently separated into:

```text
INJECTOR_DESIGN_FLOW
INJECTOR_DESIGN_PRESSURE
OPERATING_FUEL_PRESSURE
```

with:

```text
EFFECTIVE_INJECTOR_FLOW =
    INJECTOR_DESIGN_FLOW
    * sqrt(OPERATING_FUEL_PRESSURE / INJECTOR_DESIGN_PRESSURE)
```

Fuel delivery geometry is also explicit:

```text
INJECTOR_COUNT
FUEL_DELIVERY_EVENTS_PER_ENGINE_CYCLE
ACTIVE_INJECTORS_PER_EVENT
```

These affect mass-to-event conversion only; they do not alter requested engine fuel mass.

### Spark/load axis

V1 main spark and knock-threshold load axis is frozen as:

```text
RPM x MAP kPa absolute
```

PE target lambda uses:

```text
RPM x MAP/BARO pressure ratio
```

The previously optional extra PE spark-correction surface is not part of the frozen V1 calibration exposure. High-load timing belongs in the main MAP-based spark table unless a later explicit feature revision adds another contributor.

### Learning

Long-term adaptive fuel learning is disabled in V1:

```text
LEARN_FACTOR = 1.000
```

Runtime NB/WB feedback remains supported. Any adaptive table learning is a future explicit feature rather than hidden runtime modification of VE or Alpha-N calibration.

### Degraded operation

Canonical sensor-failure behavior is now machine-readable in:

```text
maps/planning/v1_degraded_operation_policy.csv
```

Important MAP-failure behavior:

```text
MAP invalid + TPS/BARO valid:
    fuel air estimate may use AIR_MODE_AN_FALLBACK
    MAP remains invalid
    spark uses captured BARO as conservative load index
    TPS-based PE may remain available
    pressure-ratio PE is unavailable
    DFCO is inhibited
```

No substituted/fallback value is allowed to masquerade as a valid measured sensor.

## 3. Table geometry now frozen

`maps/planning/v1_table_geometry.csv` freezes table dimensions before ROM layout.

Major surfaces:

```text
Speed-density VE        16 x 16
Alpha-N filling         16 x 16
Main spark              16 x 16
Knock threshold         16 x 16
PE target lambda        16 x 8
Idle follower seed       8 x 8
```

Common 1-D axes:

```text
RPM primary             16 points
MAP primary             16 points
TPS primary             16 points
CTS primary             16 points
MAT primary             16 points
pressure ratio           8 points
TPS rate                 8 points
battery voltage          8 points
short duration          12 points
sensor voltage          16 points
```

Exact breakpoint values and binary fixed-point storage widths are intentionally left to calibration seeding / ROM-layout work. Geometry and semantic units are frozen.

## 4. ADX/telemetry audit

`maps/telemetry/v1_adx_manifest.csv` is the canonical telemetry manifest.

Core telemetry now exposes the complete diagnostic chain for important analog inputs:

```text
raw ADC
input VDC
unfiltered engineering value
filtered/control engineering value
validity
substitution/fault state
```

REF telemetry now exposes:

```text
raw event count
accepted event count
rejected edge count
period
age
validity
RPM
configured event count
configured TDC offset
derived event spacing
cylinder count
combustion spacing
REF/combustion ratio
```

Oxygen telemetry similarly exposes raw ADC, unfiltered voltage, filtered voltage, converted lambda/state, validity, and feedback contributors.

The existing 24-byte debug frame is only an engine-off bring-up frame. It is not the final ADX packet definition and cannot carry the complete planned channel set.

## 5. Current implementation scaffold audit

Current replacement-OS source contains only the early engine-off scaffold:

```text
source/replacement_os/core/safe_runtime.asm
source/replacement_os/core/debug_frame.asm
source/replacement_os/include/runtime_abi.inc
source/replacement_os/hal/adc_read.asm
source/replacement_os/hal/ref_read.asm
source/replacement_os/hal/gm_output_islands.asm
source/replacement_os/hal/HAL_API.md
```

The scaffold intentionally predates the current semantic plan.

Known implementation-vs-plan differences to fix during implementation:

```text
old lifecycle enum names -> replace with frozen lifecycle model
byte/count semantic sensor fields -> replace/extend with engineering-unit pipeline
hard-coded REF/RPM assumptions -> use configurable REF geometry
REQ_FUEL_PW placeholder -> upstream control must become fuel-mass based
telemetry 24-byte bring-up frame -> later packet allocation from ADX matrix
no SCI/ALDL transport implementation
no target linker/ORG/vector build
no full spark/EST preserved island
new filtering/validation/fallback modules not implemented
SD/Alpha-N air-charge manager not implemented
fuel/spark/idle algorithms not implemented
```

These are expected because assembly implementation was deliberately paused until planning was frozen.

## 6. Preserved output-island audit

Current `gm_output_islands.asm` contains preserved stock-compatible implementations for:

```text
synchronous fuel commit
asynchronous fuel commit
fuel pump commit
IAC step/phase commit
```

It explicitly does not yet contain the full spark/EST island. Spark must be ported as the complete rolling timing/dwell/latency state handoff, not as isolated hardware-register writes.

The preserved output-island module remains uncalled by the engine-off safe runtime.

## 7. Real current status

### Reverse engineering / hardware contract

```text
algorithm extraction             100% FROZEN
scheduler/lifecycle extraction   100% FROZEN
diagnostics/failsafe extraction  100% FROZEN
production calibration audit     100% FROZEN
software-facing HW contract      100% FROZEN
physical endpoint confirmation     0% intentionally deferred
```

### Replacement-OS planning

```text
V1 feature scope                  100%
control/formula semantics         100%
physical/setup model              100%
sensor transfer model             100%
signal conditioning model         100%
rotation/reference geometry       100% for V1 validated trigger relationship
module interfaces                 100%
calibration/XDF semantic exposure 100%
calibration table geometry        100%
ADX semantic channel definition   100%
degraded-operation policy         100%
ROM/RAM address/layout              0%
binary storage/scaling layout       0%
actual XDF generation               0%
actual ADX packet/file generation   0%
build/version manifest              0%
```

### Replacement-OS implementation

The earlier implementation estimate remains approximately:

```text
18%
```

because the safe scheduler/acquisition scaffold and several preserved output islands exist, but the new control algorithms, engineering-unit sensor pipeline, configurable REF geometry, serial transport, target layout, and complete spark island are not yet implemented.

## 8. Correct next gate

The project is now ready for **binary/memory architecture**, not yet target assembly.

Next order:

```text
1. choose binary fixed-point/storage encodings for every frozen semantic type
2. allocate ROM calibration blocks using frozen table geometry
3. allocate RAM runtime state and telemetry snapshot regions
4. allocate ALDL/SCI packet pages/frames from the ADX manifest
5. freeze linker/ORG/vector layout around preserved GM islands
6. freeze build/version manifest
7. refactor runtime_abi.inc to the consolidated semantic ABI
8. build the first target-linked engine-off observability image
9. complete and validate the full spark/EST preserved island
10. begin engine-running control implementation in frozen module order
```

No further broad algorithm extraction or architecture redesign is required before step 1 unless contradictory ROM/hardware evidence appears or V1 scope is intentionally changed.
