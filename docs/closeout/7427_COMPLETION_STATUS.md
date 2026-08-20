# 7427 Completion Status

## Primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
raw target BIN: 31/BMHM.BIN
BIN size: 65536 bytes
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
replacement modular ROM master: source/replacement_os/7427_rom.asm
selected assembler: MGTEK ASM11 / MiniIDE
proven assembler: ASM11 V1.26 Build 144 for WIN32 (x86)
```

## Canonical authority split

Current implementation/status authority:

```text
docs/WORKING_STATE.md
docs/closeout/7427_IMPLEMENTATION_CONSOLIDATION_AUDIT_2026-08-19.md
docs/implementation/ROM_FIRST_BUILD_PATH.md
docs/implementation/ASM11_MINIIDE_BUILD.md
```

Frozen semantic-planning authority:

```text
docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md
maps/planning/*.csv
maps/telemetry/v1_adx_manifest.csv
```

The 2026-08-13 planning audit remains valid for V1 semantics. Its historical implementation-next-step section is superseded by the 2026-08-19 implementation audit/current working state.

## Frozen reverse-engineering / semantic state

```text
algorithm extraction             100% FROZEN
scheduler/lifecycle extraction   100% FROZEN
diagnostics/failsafe extraction  100% FROZEN
production calibration audit     100% FROZEN
V1 software-facing HW contract   100% FROZEN
physical endpoint confirmation     0% intentionally deferred

V1 feature scope                  100% FROZEN
control/formula semantics         100% FROZEN
physical/setup model              100% FROZEN
sensor transfer model             100% FROZEN
signal-conditioning model         100% FROZEN
rotation/reference geometry       100% for validated V1 relationship
module interfaces                 100% FROZEN
calibration semantic exposure     100% FROZEN
calibration table geometry        100% FROZEN
telemetry semantic channels       100% FROZEN
degraded-operation policy         100% FROZEN
```

Binary addresses/widths, RAM placement, calibration placement, packet offsets, XDF addresses and ADX offsets are frozen incrementally from the implemented ROM rather than globally before assembly.

## Proven ROM implementation milestones

### Milestone A — reset/bootstrap/vectors

```text
source: source/replacement_os/7427_bootstrap_miniide.asm
ASM11: 0 warnings / 0 errors
code: $7100-$7136
vectors: $FFC0-$FFFF
reset: $FFFE -> $7100
BIN SHA256: c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

Proof: `docs/implementation/ASM11_BOOTSTRAP_PROOF.md`.

### Milestone B — read-only ADC/REF acquisition

```text
source: source/replacement_os/7427_inputs_miniide.asm
ASM11: 0 warnings / 0 errors
RAM: $0000-$0009
code: $7100-$71D7
vectors: $FFC0-$FFFF
reset: $FFFE -> $7100
BIN SHA256: 28462ef9dbf3b6f0de59b68662fb26916dc87abea35ff7d67a0d572d42f92848
```

Proof: `docs/implementation/MILESTONE_B_BUILD_PROOF.md`.

Milestone B proves the build/layout of the read-only acquisition image. Its `$3FC0` REF/DRP read is not yet live-REF proof because the stock ASIC/register startup sequence is intentionally absent.

### Milestone C — SCI/ALDL engine-off observability

Status:

```text
SOURCE IMPLEMENTED
ASSEMBLY/LISTING PROOF PENDING
BENCH PROOF PENDING
```

Source: `source/replacement_os/7427_aldl_tx_miniide.asm`.

Implemented source behavior includes 8192-baud SCI, the stock BMHM/TBI `$B93A` board-control baseline, low-byte `$3FFD bit2` ALDL driver control, SCI interrupt TX, and a 14-byte raw-input frame. It contains no production fuel/spark/IAC/pump/aux output authority.

## Current hard placement facts

```text
stock/replacement stack top       $03FF
replacement executable origin     $7100
relocated HC11 register base      $3000
vector region                     $FFC0-$FFFF
external reset vector             $FFFE
additional stock-proven RAM       $0800-$08FF
```

Milestone-specific RAM placement is proven from each assembly listing. The modular implementation continues to allocate runtime RAM incrementally rather than reserving artificial subsystem blocks.

## Current source roles

Maintainable modular authority:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/*.inc
source/replacement_os/core/*.asm
source/replacement_os/hal/*.asm
```

Self-contained proof stages:

```text
7427_bootstrap_miniide.asm   Milestone A
7427_inputs_miniide.asm      Milestone B
7427_aldl_tx_miniide.asm     Milestone C
```

`7427_rom_miniide.asm` is a flattened convenience form, not independent source authority.

## Preserved command islands

```text
Fuel synchronous     LOCKED ABI + PORTED
Fuel asynchronous    LOCKED ABI + PORTED
IAC                   LOCKED ABI + PORTED
Fuel pump             LOCKED ABI + PORTED
Spark/EST             LOCKED ABI; complete rolling-state port pending
MIL                   DEFERRED
Unused I/O            RESERVED
```

The observability milestones grant no production actuator authority.

## Important current hardware/software contracts

```text
$3008 = relocated PORTD / external ADC mux selector
$3039 = relocated HC11 OPTION
$3FFC/$3FFD stock BMHM/TBI baseline = $B93A
ALDL driver control = low-byte $3FFD bit2
async-fuel control = high-byte $3FFC bit2
```

Spark log interpretation is now explicitly locked in `docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md`:

```text
ALDL Spark Advance = post-normal-KR spark
ALDL Knock Retard  = amount removed by knock logic
```

## Current gaps

```text
Milestone-C assembly/listing/S19/BIN proof
live PCM execution proof
live ADC acquisition proof
minimum safe ASIC initialization for meaningful REF/cranking observability
engineering sensor conversion/filter/validation pipeline
configurable REF geometry/RPM scaling/TDC offset
hybrid SD/Alpha-N air-charge manager
mass-based fuel/injector model
spark/idle/knock control algorithms
full spark/EST preserved island
production telemetry packet/page
calibration ROM objects
actual XDF
actual production ADX
```

## Correct next gate

```text
1. assemble 7427_aldl_tx_miniide.asm with ASM11 V1.26
2. inspect listing/RAM/code/vectors/SCI ISR and absolute hardware accesses
3. validate S19 and convert to deterministic 64 KiB BIN
4. bench-run Milestone C engine-off and verify ALDL output/driver release
5. verify real ADC observations
6. establish minimum safe ASIC startup needed for REF/cranking observability
7. fold proven B/C behavior into the modular ROM master
8. implement engineering sensor pipeline + configurable REF geometry
9. complete spark/EST rolling-state island
10. continue engine-running modules in frozen interface order
11. generate XDF/ADX from actual built layouts
```
