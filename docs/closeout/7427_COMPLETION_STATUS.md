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
selected assembler: MGTEK ASM11 / MiniIDE
```

## Canonical audit authority

Current detailed reverse-engineering/semantic authority map:

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
```

Current executable implementation authority:

```text
docs/implementation/ROM_FIRST_BUILD_PATH.md
docs/implementation/ASM11_MINIIDE_BUILD.md
docs/WORKING_STATE.md
source/replacement_os/7427_rom.asm
```

The consolidated planning audit remains authoritative for frozen control semantics. It no longer dictates that all binary representations and addresses must be frozen before an executable ROM is built.

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

Binary representation, RAM placement, calibration placement, packet offsets, XDF addresses, and ADX offsets are now frozen incrementally from the implemented executable rather than globally before assembly.

## ROM-first implementation status

The first target ROM master now exists.

```text
source/replacement_os/7427_rom.asm
```

Current hard/proven placement anchors:

```text
stock/replacement stack top       $03FF
replacement executable origin     $7100
relocated HC11 register base      $3000
vector region                     $FFC0-$FFFF
external reset vector             $FFFE
additional stock-proven RAM       $0800-$08FF
```

Current runtime state is allocated sequentially from low RAM by assembly-time `RMB` declarations. No artificial subsystem blocks are frozen in advance.

Selected assembler:

```text
MGTEK ASM11 / MiniIDE
```

The next executable proof is a successful ASM11 assembly and inspection of its listing/output.

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

### Machine-readable semantic planning

```text
maps/planning/v1_configuration_variables.csv
maps/planning/v1_module_interface_matrix.csv
maps/planning/v1_calibration_manifest.csv
maps/planning/v1_table_geometry.csv
maps/planning/v1_degraded_operation_policy.csv
```

These specify required concepts, geometry and behavior. They are inputs to implementation, not a preassigned memory map.

### Telemetry

Canonical semantic manifest:

```text
maps/telemetry/v1_adx_manifest.csv
```

Actual packet offsets will be assigned when the transport/packet is implemented, then the ADX will describe that packet.

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

The first ROM master links the existing completed output-island source but does not call its production commit routines.

## First-image safety state

```text
fuel permission  = FALSE
spark permission = FALSE
IAC permission   = FALSE
pump permission  = FALSE
aux permission   = FALSE
```

Unowned interrupt vectors route to a COP-serviced safe loop. Only external reset enters the replacement reset path.

## Current implementation gaps

```text
successful ASM11 assembly/listing inspection not yet performed
live read-only ADC calls not yet integrated
live REF/cranking observability not yet integrated
engineering sensor pipeline not implemented
configurable REF geometry/RPM scaling not implemented
hybrid SD/Alpha-N manager not implemented
mass-based fuel algorithm not implemented
spark/idle control algorithms not implemented
SCI/ALDL transport not implemented
final telemetry packet/page not implemented
calibration objects not yet allocated into replacement ROM
actual XDF not generated
actual ADX not generated
full spark/EST preserved island not ported
```

## Correct next gate

Proceed in this order:

```text
1. assemble source/replacement_os/7427_rom.asm with MGTEK ASM11 / MiniIDE
2. inspect listing, RAM symbols, code end, ORG regions, vectors and assembler output
3. freeze the verified bootstrap/toolchain facts
4. integrate read-only ADC acquisition into live replacement execution
5. integrate REF acquisition and cranking observability
6. add SCI/ALDL read-only debug transport
7. implement sensor conversion/filter/validation, allocating ROM/RAM as required
8. implement lifecycle and configurable REF geometry
9. continue engine-control modules in frozen semantic interface order
10. generate XDF and ADX definitions from the actual built layouts
```

For every implementation step, choose the narrowest binary representation that satisfies the module, assemble it, inspect the map/listing, and only then freeze addresses/encodings that have become external interfaces.

No broad algorithm extraction or full-memory preallocation is required before step 1 unless V1 scope changes or contradictory ROM/hardware evidence appears.
