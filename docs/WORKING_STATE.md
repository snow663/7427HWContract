# Working State

This repository is the working directory for the 7427 hardware-contract and replacement-OS project. Git history is the version record.

## Current primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
working executable source: source/31/BMHM_HAC_ORG_7100_to_end.asm
```

## Current authority

Detailed consolidated audit:

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
```

Status summary:

```text
docs/closeout/7427_COMPLETION_STATUS.md
```

Machine-readable planning authorities:

```text
maps/planning/v1_configuration_variables.csv
maps/planning/v1_module_interface_matrix.csv
maps/planning/v1_calibration_manifest.csv
maps/planning/v1_table_geometry.csv
maps/planning/v1_degraded_operation_policy.csv
maps/telemetry/v1_adx_manifest.csv
```

## Architecture

```text
CALIBRATION / XDF
    ↓
ENGINEERING-UNIT INPUT + CONTROL SYSTEM
    ↓
SEMANTIC REQUESTS / ARBITRATION
    ↓
PRESERVED GM COMMAND ISLANDS + HAL
    ↓
7427 HARDWARE
```

The first-running-engine route preserves verified stock software-to-hardware command behavior. Full electrical characterization is not a prerequisite for the V1 software contract.

## Frozen reverse-engineering status

```text
algorithm extraction             100%
scheduler/lifecycle extraction   100%
diagnostics/failsafe extraction  100%
production calibration audit     100%
V1 software-facing HW contract   100%
physical endpoint confirmation     0% intentionally deferred
```

Do not reopen the frozen extraction categories unless new executable/ROM evidence materially contradicts them or V1 scope is deliberately expanded.

## Replacement-OS planning status

```text
V1 feature scope                   100%
control/formula semantics          100%
physical/setup model               100%
sensor transfer model              100%
signal conditioning                100%
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

The broad semantic/planning gate is closed. The current task frontier is binary representation and memory architecture.

## Key frozen V1 setup decisions

```text
hybrid air model            speed-density + bounded Alpha-N
main spark load axis        RPM x MAP kPa absolute
PE target load axis         RPM x MAP/BARO pressure ratio
BARO                        valid MAP captured before rotation and held for run
MAT/IAT                     optional added sensor
analog sensor transfer      VDC -> engineering-unit 1-D table
fuel learning               disabled in V1; LEARN_FACTOR=1.000
```

Editable physical geometry includes:

```text
engine displacement
cylinder count
REF events per crank revolution
signed REF-to-event-TDC offset
injector count
fuel-delivery events per 720-degree cycle
active injectors per delivery event
injector design flow
injector design pressure
operating fuel pressure
```

Derived values are read-only.

## Current implementation status

```text
replacement-OS implementation   ~18%
complete runnable replacement     0%
```

The source tree is still the earlier engine-off scaffold and intentionally trails the now-frozen semantic plan.

Current implementation components:

- `source/replacement_os/include/runtime_abi.inc`
- `source/replacement_os/core/safe_runtime.asm`
- `source/replacement_os/core/debug_frame.asm`
- `source/replacement_os/hal/HAL_API.md`
- `source/replacement_os/hal/adc_read.asm`
- `source/replacement_os/hal/ref_read.asm`
- `source/replacement_os/hal/gm_output_islands.asm`

Implemented scaffold pieces:

```text
safe initialization
6.25 ms scheduler / 16-segment counter
basic REF-event/dropout scaffold
key-off/shutdown safe state
calibration-validity gate
semantic request/arbitration scaffold
read-only ADC/REF acquisition paths
24-byte bring-up debug frame builder
preserved sync/async fuel, IAC and pump command modules
```

Not yet implemented from the consolidated plan:

```text
new lifecycle enum/state semantics
ADC-count -> VDC -> engineering transfer pipeline
sensor-specific filtering and validation/substitution
configurable REF event count / RPM scaling / TDC offset
hybrid SD/Alpha-N air-charge manager
mass-based fuel model and injector model
spark/idle/knock control algorithms
SCI/ALDL transport
final telemetry packet/page layout
ROM/RAM/linker/ORG/vector layout
full spark/EST preserved island
```

## Preserved command islands

Authority:

- `docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md`
- `source/replacement_os/hal/gm_output_islands.asm`

Current state:

```text
fuel synchronous   LOCKED + PORTED
fuel async / AE    LOCKED + PORTED
IAC                LOCKED + PORTED
fuel pump          LOCKED + PORTED
spark / EST        ABI LOCKED; complete rolling-state port pending
MIL                deferred
unused I/O         reserved
```

The current safe runtime does not call these output modules.

## Current output policy

```text
fuel permission  = FALSE
spark permission = FALSE
IAC permission   = FALSE
pump permission  = FALSE
aux permission   = FALSE
```

That remains mandatory for the first target-linked image.

## Next work order

```text
1. fixed-point/storage encoding matrix
2. ROM calibration allocation from frozen table geometry
3. RAM runtime-state and telemetry-snapshot allocation
4. ALDL/SCI packet-page allocation
5. linker/ORG/vector layout around preserved islands
6. build/version manifest
7. refactor runtime_abi.inc to the consolidated semantic ABI
8. first target-linked engine-off observability image
9. full spark/EST preserved island
10. engine-running modules in frozen interface order
```

The first target-linked image must still keep every production-output permission false while proving reset/startup, scheduler, engineering sensor acquisition, configurable REF/RPM visibility during cranking, lifecycle/validity state, telemetry transport, and calibration integrity.
