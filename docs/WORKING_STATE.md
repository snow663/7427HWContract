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
working stock executable source: source/31/BMHM_HAC_ORG_7100_to_end.asm
replacement modular ROM master: source/replacement_os/7427_rom.asm
selected assembler: MGTEK ASM11 / MiniIDE
proven assembler: ASM11 V1.26 Build 144 for WIN32 (x86)
```

## Current authority

Implementation/current-state authority:

```text
docs/WORKING_STATE.md
docs/closeout/7427_IMPLEMENTATION_CONSOLIDATION_AUDIT_2026-08-19.md
docs/closeout/7427_COMPLETION_STATUS.md
docs/implementation/ROM_FIRST_BUILD_PATH.md
docs/implementation/ASM11_MINIIDE_BUILD.md
```

Frozen semantic-planning authority:

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
docs/planning/V1_*.md
maps/planning/v1_configuration_variables.csv
maps/planning/v1_module_interface_matrix.csv
maps/planning/v1_calibration_manifest.csv
maps/planning/v1_table_geometry.csv
maps/planning/v1_degraded_operation_policy.csv
maps/telemetry/v1_adx_manifest.csv
```

The 2026-08-13 planning audit remains authoritative for frozen semantics, but its historical implementation-next-step section is superseded by this file and the 2026-08-19 implementation audit.

## Architecture / placement policy

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

The executable is the placement authority. Runtime/calibration objects get concrete widths and addresses as implementation creates them. XDF/ADX describes those built layouts afterward.

## Frozen reverse-engineering state

```text
algorithm extraction             100% FROZEN
scheduler/lifecycle extraction   100% FROZEN
diagnostics/failsafe extraction  100% FROZEN
production calibration audit     100% FROZEN
V1 software-facing HW contract   100% FROZEN
physical endpoint confirmation     0% intentionally deferred
```

Do not reopen these broad extraction categories unless contradictory executable/ROM evidence appears or V1 scope changes.

## Frozen V1 semantic planning

```text
feature scope                     100%
control/formula semantics         100%
physical/setup model              100%
sensor transfer model             100%
signal conditioning               100%
rotation/reference geometry        100% for validated V1 relationship
module interfaces                 100%
calibration semantic exposure     100%
calibration table geometry        100%
telemetry semantic channels       100%
degraded-operation policy         100%
```

## ROM-first implementation checkpoint

### Milestone A — bootstrap/vector image: PROVEN

```text
source: source/replacement_os/7427_bootstrap_miniide.asm
ASM11:  0 warnings / 0 errors
code:   $7100-$7136
vectors:$FFC0-$FFFF
reset:  $FFFE -> $7100
BIN:    65536 bytes
SHA256: c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

Proof: `docs/implementation/ASM11_BOOTSTRAP_PROOF.md`.

### Milestone B — read-only ADC/REF acquisition image: PROVEN BUILD

```text
source: source/replacement_os/7427_inputs_miniide.asm
ASM11:  0 warnings / 0 errors
RAM:    $0000-$0009
code:   $7100-$71D7
vectors:$FFC0-$FFFF
reset:  $FFFE -> $7100
BIN:    65536 bytes
SHA256: 28462ef9dbf3b6f0de59b68662fb26916dc87abea35ff7d67a0d572d42f92848
```

Proof: `docs/implementation/MILESTONE_B_BUILD_PROOF.md`.

Milestone B proves the source can build with the input-path addresses and allocation shown in its listing. It does **not** prove live REF observability from `$3FC0`; the stock firmware initializes the `$3FC0-$3FFA` ASIC/register island and Milestone B deliberately does not.

### Milestone C — engine-off ALDL observability image: SOURCE READY / UNPROVEN

```text
source: source/replacement_os/7427_aldl_tx_miniide.asm
frame:  14-byte raw-input frame
SCI:    8192 baud
board baseline: $3FFC/$3FFD = $B93A before ALDL RMW
ALDL driver: low byte $3FFD bit2
actuator authority: none
```

`docs/contracts/ALDL_SCI_HANDSHAKE.md` is the stock handoff authority.

Milestone C has not yet received the same ASM11 listing/S19/BIN proof as A and B and has not been bench-run on the PCM.

## Maintainable source model

Long-term modular source authority:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/target_layout.inc
source/replacement_os/include/runtime_abi.inc
source/replacement_os/core/*.asm
source/replacement_os/hal/*.asm
source/replacement_os/hal/*.inc
```

Proof-stage sources:

```text
source/replacement_os/7427_bootstrap_miniide.asm   Milestone A
source/replacement_os/7427_inputs_miniide.asm      Milestone B
source/replacement_os/7427_aldl_tx_miniide.asm     Milestone C
```

The `*_miniide.asm` sources are deliberate self-contained proof vehicles. Proven changes must be folded into the modular tree; they must not become a permanently divergent second implementation.

`source/replacement_os/7427_rom_miniide.asm` is only a flattened convenience form of the modular tree and is not independent authority.

## Important proven corrections/contracts

### ADC/register correction

```text
$3008 = relocated CPU PORTD / external ADC-mux selector
$3039 = relocated HC11 OPTION register
```

### ALDL board-control baseline

Stock BMHM/TBI startup establishes:

```text
$3FFC/$3FFD = $B93A
```

before normal serial activity. ALDL external-driver control is low-byte `$3FFD bit2`; async-fuel control uses high-byte `$3FFC bit2` and is a distinct control.

### ALDL spark / knock-retard ordering

Authority: `docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md`.

```text
ALDL Spark Advance = post-normal-KR spark
ALDL Knock Retard  = amount normal knock logic removed
```

Do not subtract KR from logged Spark Advance again. Approximate pre-KR demand is `logged spark + KR`, subject to serialized ALDL sampling skew.

## Preserved command islands

```text
fuel synchronous   LOCKED + PORTED
fuel async / AE    LOCKED + PORTED
IAC                LOCKED + PORTED
fuel pump          LOCKED + PORTED
spark / EST        ABI LOCKED; complete rolling-state port pending
MIL                deferred
unused I/O         reserved
```

Authority:

```text
docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md
source/replacement_os/hal/gm_output_islands.asm
```

## Current output policy

Through the observability milestones:

```text
fuel permission  = FALSE
spark permission = FALSE
IAC permission   = FALSE
pump permission  = FALSE
aux permission   = FALSE
```

## Implemented/proven vs pending

Proven/build-verified:

```text
ASM11 toolchain and absolute S19 workflow
Milestone-A reset/bootstrap/vector image
Milestone-B input-acquisition image
S19 checksum validation / deterministic 64 KiB conversion
stock register relocation and ADC mux addresses used by Milestone B
```

Implemented in source but not yet build/bench-proven:

```text
Milestone-C SCI/ALDL engine-off telemetry image
```

Pending:

```text
live PCM execution proof for replacement images
live ADC acquisition proof
minimum safe ASIC initialization and live REF/cranking proof
engineering ADC-count -> VDC -> engineering transfer pipeline
sensor-specific filtering / validity / substitution
configurable REF event count, RPM scaling and TDC offset
hybrid SD/Alpha-N air-charge manager
mass-based fuel/injector model
spark/idle/knock control algorithms
full spark/EST preserved island
final telemetry packet/page
calibration ROM objects and actual XDF
actual production ADX
```

## Current work order

```text
1. assemble source/replacement_os/7427_aldl_tx_miniide.asm with ASM11 V1.26
2. inspect its listing, RAM allocation, code end, vectors, SCI ISR and absolute accesses
3. checksum-validate S19 and convert to deterministic 64 KiB BIN
4. bench-run Milestone C engine-off and verify ALDL frame/driver release behavior
5. bench-verify ADC values
6. determine/implement the minimum safe ASIC initialization required for meaningful REF/cranking observability
7. fold proven B/C behavior into source/replacement_os/7427_rom.asm and modular HAL/core files
8. implement engineering sensor pipeline and configurable REF geometry
9. complete preserved spark/EST rolling-state handoff
10. continue engine-running modules in frozen semantic interface order
11. derive XDF/ADX from actual ROM/packet layouts
```

For each module:

```text
implement behavior
-> choose only the representation actually required
-> allocate ROM/RAM
-> assemble
-> inspect map/listing
-> lock externally depended-on representation
-> expose it in XDF/ADX when appropriate
```
