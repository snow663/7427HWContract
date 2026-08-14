# 7427 Completion Status

## Primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
replacement ROM master: source/replacement_os/7427_rom.asm
```

## Canonical authorities

Semantic/planning audit:

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
```

Current implementation order:

```text
docs/implementation/ROM_FIRST_BUILD_PATH.md
```

Current working state:

```text
docs/WORKING_STATE.md
```

The consolidation audit remains authoritative for frozen V1 semantics. The ROM-first implementation document supersedes its older suggested pre-assembly ordering where that ordering attempted to freeze every binary/RAM address before an executable existed.

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

## Replacement-OS semantic planning status

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
```

The semantic/control planning gate is closed.

Exact binary storage widths, RAM addresses, calibration addresses, XDF addresses, and ADX packet offsets are now treated as implementation outputs. They become fixed when the ROM implementation actually creates the corresponding object.

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
maps/telemetry/v1_adx_manifest.csv
```

All current calibration exposure fragments live under:

```text
maps/planning/calibration_fragments/
```

## Frozen design highlights

### Air charge

Hybrid speed-density / Alpha-N produces one downstream quantity:

```text
AIR_MASS_CYCLE
```

Speed density is primary at steady state; Alpha-N supplies bounded high-load/transient prediction authority and the defined MAP-failure fallback route.

### Injector physical model

```text
EFFECTIVE_INJECTOR_FLOW =
    INJECTOR_DESIGN_FLOW
    * sqrt(OPERATING_FUEL_PRESSURE / INJECTOR_DESIGN_PRESSURE)
```

Fuel-delivery geometry is separately configured by injector count, delivery events per 720-degree cycle, and active injectors per event.

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

For the intended V8 / 4-REF-events-per-crank-revolution case, REF spacing and combustion spacing are both 90 crank degrees and the relationship is one REF event per combustion event.

### Spark/load

V1 main spark and knock-threshold load axis is:

```text
RPM x MAP kPa absolute
```

PE target lambda uses RPM x MAP/BARO pressure ratio.

### Learning

Long-term adaptive fuel learning is not part of V1:

```text
LEARN_FACTOR = 1.000
```

Runtime NB/WB feedback remains supported.

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

The first replacement-ROM master links these sources but does not call production output commits.

## Replacement-OS implementation status

```text
replacement-OS implementation   ~19%
complete engine-running image     0%
```

The implementation now contains a real target ROM master and vector layout in addition to the earlier engine-off semantic scaffold.

Current ROM-bootstrap components include:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/target_layout.inc
source/replacement_os/include/runtime_abi.inc
source/replacement_os/hal/init_safe.asm
source/replacement_os/hal/hal_ram.inc
source/replacement_os/core/safe_runtime.asm
source/replacement_os/core/debug_frame.asm
source/replacement_os/hal/adc_read.asm
source/replacement_os/hal/ref_read.asm
source/replacement_os/hal/gm_output_islands.asm
```

The first master currently provides:

```text
real external-reset vector
stock stack top $03FF
stock-proven HC11 register relocation $1000 -> $3000
stock-proven CPU-side reset register values
sequential low-RAM allocation
clear-only-allocated-RAM startup
all actuator permissions false
COP-serviced stable engine-off loop
safe trap for every unowned vector
```

It has not yet been verified with the final HC11 assembler/toolchain or inspected as a generated binary/map.

## Evidence correction found during bootstrap

The earlier ADC HAL mislabeled `$3008` as `HC11_OPTION`.

Stock BMHM `F275` proves `$3008` is relocated CPU PORTD and bits 3..5 are used as the external ADC/multiplexer selector. The actual relocated HC11 OPTION register used during reset is `$3039`.

That correction is now reflected in `source/replacement_os/hal/adc_read.asm`.

## Correct next gate

Proceed from the ROM outward:

```text
1. select/verify the HC11 assembler toolchain and assemble source/replacement_os/7427_rom.asm
2. inspect the actual binary/map and enforce RAM/ROM/vector collision checks
3. bring up read-only ADC acquisition
4. bring up read-only REF acquisition and configurable cranking RPM visibility
5. add the base scheduler timer interrupt
6. add SCI/ALDL engine-off debug transport
7. add calibration header/integrity and calibration objects as implemented algorithms require them
8. complete and validate the full spark/EST preserved island
9. implement engine-running control modules in frozen interface order
10. generate/maintain XDF and ADX definitions from the actual built layouts
```

No further broad algorithm extraction or architecture redesign is required unless V1 scope changes or contradictory ROM/hardware evidence appears.
