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
selected assembler: MGTEK ASM11 / MiniIDE
proven assembler version: ASM11 V1.26 Build 144 for WIN32 (x86)
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

ROM-first implementation authority:

```text
docs/implementation/ROM_FIRST_BUILD_PATH.md
docs/implementation/ASM11_MINIIDE_BUILD.md
docs/implementation/ASM11_BOOTSTRAP_PROOF.md
source/replacement_os/7427_rom.asm
source/replacement_os/include/target_layout.inc
```

Machine-readable planning authorities remain semantic requirements, not preassigned binary placement:

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
SEMANTIC / PHYSICAL CONTROL REQUIREMENTS
    ↓
IMPLEMENTED ROM + RUNTIME STATE
    ↓
SEMANTIC REQUESTS / ARBITRATION
    ↓
PRESERVED GM COMMAND ISLANDS + HAL
    ↓
7427 HARDWARE

built ROM / packet layout
    ↓
XDF / ADX definitions
```

The first-running-engine route preserves verified stock software-to-hardware command behavior. Full electrical characterization is not a prerequisite for the V1 software contract.

The executable is now the placement authority. Calibration and runtime objects receive concrete representations and addresses as their consuming modules are implemented. XDF/ADX files describe those built layouts afterward rather than dictating them in advance.

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

These semantic decisions are frozen requirements. They are not a requirement to pre-freeze every future byte width, RAM address, calibration address, or packet offset before implementation.

## ROM-first implementation state

Implemented/proven on the current ROM-first branch:

```text
stock-proven stack top             $03FF
replacement executable origin      $7100
HC11 relocated register base       $3000
vector window                       $FFC0-$FFFF
external reset vector               $FFFE -> RESET_ENTRY
runtime RAM allocation              sequential from $0000
additional proven RAM               $0800-$08FF reserved until needed
selected assembler                  MGTEK ASM11 / MiniIDE
proven ASM11 build                  V1.26 Build 144, 0 warnings / 0 errors
Milestone-A executable              $7100-$7136
Milestone-A vector table            $FFC0-$FFFF
Milestone-A 64K BIN SHA256          c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
structural bootstrap verifier       tools/verify_rom_bootstrap.py
S19 -> 64K BIN converter            tools/s19_to_64k_bin.py
```

Milestone-A proof authority:

```text
docs/implementation/ASM11_BOOTSTRAP_PROOF.md
source/replacement_os/7427_bootstrap_miniide.asm
```

The first image deliberately does not pre-partition RAM by subsystem and does not allocate final calibration blocks before their code exists.

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

## Current implementation components

```text
source/replacement_os/7427_rom.asm
source/replacement_os/7427_bootstrap_miniide.asm
source/replacement_os/7427_inputs_miniide.asm
source/replacement_os/include/target_layout.inc
source/replacement_os/include/runtime_abi.inc
source/replacement_os/core/safe_runtime.asm
source/replacement_os/core/debug_frame.asm
source/replacement_os/hal/HAL_API.md
source/replacement_os/hal/hal_ram.inc
source/replacement_os/hal/init_safe.asm
source/replacement_os/hal/adc_read.asm
source/replacement_os/hal/ref_read.asm
source/replacement_os/hal/gm_output_islands.asm
```

Implemented scaffold pieces:

```text
real ROM master / reset vector
source-proven HC11 register relocation
minimum safe processor initialization
sequential runtime RAM allocation
safe initialization
6.25 ms semantic scheduler scaffold
basic REF-event/dropout scaffold
key-off/shutdown safe state
calibration-validity gate
semantic request/arbitration scaffold
read-only ADC/REF acquisition modules
24-byte bring-up debug frame builder
preserved sync/async fuel, IAC and pump command modules
proven ASM11 Milestone-A bootstrap build and deterministic 64K conversion
```

Not yet implemented/integrated/proven:

```text
clean ASM11 Milestone-B input-acquisition build/listing
live PCM execution/bench proof
read-only acquisition proof on live PCM
engineering ADC-count -> VDC -> engineering transfer pipeline
sensor-specific filtering and validation/substitution
configurable REF event count / RPM scaling / TDC offset
hybrid SD/Alpha-N air-charge manager
mass-based fuel model and injector model
spark/idle/knock control algorithms
SCI/ALDL transport
final telemetry packet/page
calibration ROM objects and actual XDF
full spark/EST preserved island
```

## Preserved command islands

Authority:

```text
docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md
source/replacement_os/hal/gm_output_islands.asm
```

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

The current ROM master links the completed preserved islands but does not call their production commit functions.

## Current output policy

```text
fuel permission  = FALSE
spark permission = FALSE
IAC permission   = FALSE
pump permission  = FALSE
aux permission   = FALSE
```

That remains mandatory through the first target-linked observability image.

## Current work order

```text
1. assemble source/replacement_os/7427_inputs_miniide.asm with proven ASM11 V1.26
2. inspect its actual listing, RAM allocation, input addresses and vectors
3. convert the clean absolute S19 to a 64 KiB BIN with tools/s19_to_64k_bin.py
4. add SCI/ALDL debug transport while keeping all actuator authority absent
5. bench-observe ADC/REF values on the real PCM
6. implement engineering sensor pipeline and allocate its RAM/calibration as required
7. implement lifecycle/REF geometry and allocate required state/calibration
8. continue engine-control modules in frozen semantic interface order
9. derive XDF/ADX definitions from the resulting ROM/packet layouts
```

For each module:

```text
implement behavior
→ choose only the representation actually required
→ allocate ROM/RAM
→ assemble
→ inspect map/listing
→ lock externally depended-on representation
→ expose it in XDF/ADX when appropriate
```

This prevents planning artifacts from becoming artificial hardware constraints while still keeping every address collision and external ABI explicit.
