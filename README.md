# 7427HWContract

Working repository for the GM 16197427 `7427` PCM hardware-contract reverse-engineering and replacement-OS project.

The repository is the project state. Git history is the version record; exported ZIPs/CSVs are not the primary working record.

## Objective

Build a clean engine-control OS for the `7427` using the stock `$31` BMHM/HAC executable as the software/hardware authority where appropriate.

V1 engine-control scope includes speed-density TBI fuel, bounded Alpha-N assistance/fallback, spark, IAC/idle, AE/PE/DFCO, crank/warmup/afterstart fuel, injector low-PW correction, oxygen feedback, knock handling, and ALDL/debug visibility.

Automatic-transmission strategy, TCC, EGR, EVAP, secondary AIR, and A/C control are outside V1 unless hardware-required. Unused I/O remains reserved/documented.

## Authority order

Use these as current authority:

```text
1. docs/WORKING_STATE.md
2. docs/closeout/7427_IMPLEMENTATION_CONSOLIDATION_AUDIT_2026-08-19.md
3. docs/closeout/7427_COMPLETION_STATUS.md
4. docs/implementation/ROM_FIRST_BUILD_PATH.md
5. docs/implementation/ASM11_MINIIDE_BUILD.md
6. current docs/contracts/*.md and maps/contracts/*.csv for proven hardware behavior
7. docs/closeout/7427_V1_PLANNING_CONSOLIDATION_AUDIT.md for frozen V1 semantic planning
```

The 2026-08-13 planning audit remains semantic-design authority. Its old implementation-next-step section is historical and is superseded by the current working state and 2026-08-19 implementation audit.

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

The executable image is the placement authority. RAM, calibration, XDF addresses, and ADX packet offsets are frozen incrementally as real implementation requires them; they are not globally preallocated in advance.

## Current implementation checkpoint

### Milestone A — bootstrap/vector proof: PROVEN

Source:

```text
source/replacement_os/7427_bootstrap_miniide.asm
```

Proof:

```text
ASM11 V1.26 Build 144
0 warnings / 0 errors
code $7100-$7136
vector table $FFC0-$FFFF
reset $FFFE -> $7100
64 KiB BIN SHA256 c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

Authority: `docs/implementation/ASM11_BOOTSTRAP_PROOF.md`.

### Milestone B — read-only input acquisition: PROVEN BUILD

Source:

```text
source/replacement_os/7427_inputs_miniide.asm
```

Proof:

```text
ASM11 V1.26 Build 144
0 warnings / 0 errors
RAM $0000-$0009
code $7100-$71D7
reset $FFFE -> $7100
64 KiB BIN SHA256 28462ef9dbf3b6f0de59b68662fb26916dc87abea35ff7d67a0d572d42f92848
```

Authority: `docs/implementation/MILESTONE_B_BUILD_PROOF.md`.

Milestone B samples the proven ADC paths and reads `$3FC0`; that `$3FC0` read is **not yet live-REF proof** because the stock ASIC/register island normally receives startup initialization that Milestone B deliberately omits.

### Milestone C — engine-off ALDL observability: SOURCE READY, NOT YET PROVEN

Source:

```text
source/replacement_os/7427_aldl_tx_miniide.asm
```

Current implementation adds:

```text
8192-baud SCI transmit path
stock BMHM/TBI $3FFC/$3FFD = $B93A startup baseline
ALDL external-driver control on low byte $3FFD bit2
14-byte raw-input debug frame
SCI interrupt transmit service
all production actuator outputs still disabled/absent
```

Authority for the stock handoff: `docs/contracts/ALDL_SCI_HANDSHAKE.md`.

The next proof is to assemble Milestone C with the proven ASM11 toolchain, inspect the listing/S19/BIN, then bench-test it on the PCM with no actuator authority.

## Maintainable source vs proof-stage sources

Long-term maintainable modular authority:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/*.inc
source/replacement_os/core/*.asm
source/replacement_os/hal/*.asm
```

Self-contained `*_miniide.asm` files are deliberate bring-up/proof stages for the user's ASM11/MiniIDE workflow. They are not independent long-term implementations. Once a stage is proven, its verified behavior should be folded back into the modular master rather than maintaining two drifting codebases.

## Preserved output islands

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

No current observability milestone grants fuel, spark, IAC, pump, or auxiliary-output authority.

## Spark/ALDL interpretation proof

`docs/contracts/SPARK_ALDL_KR_ORDERING_CONTRACT.md` locks down a tuning-critical `$31` fact:

```text
ALDL Spark Advance = post-normal-KR spark value
ALDL Knock Retard  = amount removed by knock logic
```

Do not subtract logged KR from logged Spark Advance a second time. The contract traces `L01FD -> L01EE`, the explicit KR subtraction, `L01EE -> L01F0`, and the ALDL `$31F0 -> $01F0` address alias.

## Frozen semantic planning

Machine-readable semantic requirements remain:

```text
maps/planning/v1_configuration_variables.csv
maps/planning/v1_module_interface_matrix.csv
maps/planning/v1_calibration_manifest.csv
maps/planning/v1_table_geometry.csv
maps/planning/v1_degraded_operation_policy.csv
maps/telemetry/v1_adx_manifest.csv
```

These define required concepts and geometry, not preassigned binary placement.

## Toolchain / verification

Selected and proven assembler:

```text
MGTEK ASM11 / MiniIDE
ASM11 V1.26 Build 144 for WIN32 (x86)
```

Utilities:

```text
tools/verify_rom_bootstrap.py
tools/s19_to_64k_bin.py
```

## Next work order

```text
1. assemble source/replacement_os/7427_aldl_tx_miniide.asm with proven ASM11 V1.26
2. inspect listing, RAM allocation, code end, vectors, SCI ISR and all absolute addresses
3. validate S19 and convert to deterministic 64 KiB BIN
4. bench-run Milestone C engine-off and verify ALDL frame/driver behavior
5. verify raw ADC acquisition on the real PCM
6. determine minimum safe ASIC initialization required for meaningful REF/cranking observability
7. fold proven Milestone B/C behavior into the modular ROM master
8. implement engineering sensor conversion/filter/validation and configurable REF geometry
9. complete the full spark/EST preserved island
10. implement engine-running control modules in frozen semantic-interface order
11. derive XDF/ADX definitions from the actual built ROM and telemetry layouts
```

## Working rule

Use stable filenames for current authority. Let Git history preserve versions. Avoid parallel `almost same` copies unless they are deliberate proof stages or releases.
