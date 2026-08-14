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
replacement ROM master: source/replacement_os/7427_rom.asm
```

## Current authority

Detailed consolidated semantic/planning audit:

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
```

Current implementation-order authority:

```text
docs/implementation/ROM_FIRST_BUILD_PATH.md
```

Status summary:

```text
docs/closeout/7427_COMPLETION_STATUS.md
```

Machine-readable semantic/planning authorities:

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
```

The broad semantic/planning gate is closed.

Binary storage widths, exact RAM addresses, exact calibration addresses, XDF addresses, and ADX packet addresses are **implementation outputs**, not a new broad planning gate. They are fixed when the ROM implementation actually creates the corresponding object.

## ROM-first implementation policy

The executable image is now the placement authority.

```text
hardware-proven boundaries
    -> build/link replacement ROM
    -> allocate RAM/calibration objects as modules need them
    -> verify actual assembly/binary map
    -> define XDF from actual calibration layout
    -> define ADX from actual telemetry packet layout
```

Do not freeze a complete global RAM partition or complete fixed-point matrix ahead of the executable.

Current stock-proven placement anchors used by the first ROM master:

```text
stack top                    $03FF
additional stock-used RAM    $0800-$08FF
HC11 reset register base     $1000
HC11 relocated register base $3000
stock calibration/header     $4000+
first replacement code ORG   $7100
vector window                $FFC0-$FFFF
external reset vector        $FFFE
```

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
replacement-OS implementation   ~19%
complete engine-running image     0%
```

The source tree now contains a target ROM master in addition to the earlier engine-off scaffold. The new master has not yet been assembler/binary-map verified.

Current implementation components include:

- `source/replacement_os/7427_rom.asm`
- `source/replacement_os/include/target_layout.inc`
- `source/replacement_os/include/runtime_abi.inc`
- `source/replacement_os/core/safe_runtime.asm`
- `source/replacement_os/core/debug_frame.asm`
- `source/replacement_os/hal/init_safe.asm`
- `source/replacement_os/hal/hal_ram.inc`
- `source/replacement_os/hal/HAL_API.md`
- `source/replacement_os/hal/adc_read.asm`
- `source/replacement_os/hal/ref_read.asm`
- `source/replacement_os/hal/gm_output_islands.asm`

Implemented scaffold pieces:

```text
real target ROM master / ORG structure
real HC11 vector table with reset entry and safe traps
stock-proven $1000->$3000 HC11 register relocation
stock-proven CPU-side startup register values
incremental low-RAM allocation model
COP-serviced stable engine-off idle loop
safe initialization
6.25 ms semantic scheduler / 16-segment counter
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
assembler/toolchain verification of 7427_rom.asm
binary/map generation and collision checks
new lifecycle enum/state semantics
ADC-count -> VDC -> engineering transfer pipeline
sensor-specific filtering and validation/substitution
configurable REF event count / RPM scaling / TDC offset
hybrid SD/Alpha-N air-charge manager
mass-based fuel model and injector model
spark/idle/knock control algorithms
SCI/ALDL transport
final telemetry packet/page layout
calibration objects/addresses for implemented algorithms
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

The first ROM master links these modules but does not call any production output island.

## Current output policy

```text
fuel permission  = FALSE
spark permission = FALSE
IAC permission   = FALSE
pump permission  = FALSE
aux permission   = FALSE
```

That remains mandatory for the first target-linked image.

## Evidence correction during ROM bootstrap

The earlier ADC HAL called `$3008` `HC11_OPTION`. Stock `F275` proves `$3008` is relocated CPU PORTD and bits 3..5 are used as the external ADC/mux selector. The actual relocated HC11 OPTION register written during reset is `$3039`.

`source/replacement_os/hal/adc_read.asm` now uses the corrected PORTD/mux semantics.

## Next work order

```text
1. assemble/verify source/replacement_os/7427_rom.asm and inspect its map
2. add a build/map verifier that enforces RAM<stack and exact vector placement
3. bring up read-only ADC acquisition in the ROM loop/scheduler
4. bring up read-only REF acquisition and configurable cranking RPM visibility
5. add the base scheduler timer interrupt
6. add SCI/ALDL engine-off debug transport
7. add calibration header/integrity data and then real calibration objects as algorithms need them
8. complete the full spark/EST preserved island
9. implement engine-running modules in frozen interface order
10. generate/maintain XDF and ADX definitions from the actual built layouts
```

The first target-linked image must keep every production-output permission false while reset/startup, execution stability, input acquisition, REF/RPM visibility, scheduler timing, telemetry transport, and calibration integrity are proven.
