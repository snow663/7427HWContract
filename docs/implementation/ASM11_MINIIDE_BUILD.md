# MGTEK ASM11 / MiniIDE Build Target

## Selected assembler

The replacement ROM source targets the **MGTEK ASM11** 68HC11 cross-assembler supplied with MiniIDE.

MGTEK describes ASM11 as a Motorola 68HC11 cross-assembler that accepts common assembler syntax and can run either inside MiniIDE or from the command line.

The project should therefore prefer conservative ASM11-compatible source syntax rather than introduce toolchain-specific extensions that are not needed by the 7427 ROM.

## Master source

```text
source/replacement_os/7427_rom.asm
```

Open/assemble this file as the top-level source. It includes the RAM declarations, bootstrap/HAL modules, safe runtime, read-only input modules, preserved output islands, and vector table.

## Source syntax currently relied on

```text
INCLUDE
ORG
EQU
RMB
FCB
FDB
```

plus ordinary Motorola 68HC11 instruction mnemonics and semicolon comments.

No linker script is required for the first bootstrap. Placement is expressed directly by `ORG` and symbols in:

```text
source/replacement_os/include/target_layout.inc
```

## First PC build procedure

1. Open `source/replacement_os/7427_rom.asm` in MiniIDE.
2. Select ASM11 / 68HC11 assembly if MiniIDE exposes an assembler choice.
3. Assemble the master source without changing any addresses to make an error disappear.
4. Preserve the complete assembler listing and generated S-record/object output.
5. Record the exact MiniIDE/ASM11 version shown on the PC.
6. If assembly fails, preserve the first complete error list. Treat syntax/path errors separately from real address/range errors.

The first successful listing becomes the practical placement authority for runtime symbols and code labels.

## What must be checked in the first listing

```text
RESET_ENTRY             = $7100
STACK_TOP               = $03FF
RAM_ALLOC_END           < $03FF
ROM_CODE_END            < $FFC0
vector table begins     = $FFC0
external reset vector   = $FFFE -> RESET_ENTRY
```

Also verify that all included modules resolve exactly once and that there are no overlapping `ORG` ranges.

## First-image safety condition

A successful assembly is **not** yet an engine-running image.

The bootstrap must continue to satisfy all of the following:

```text
PERM_FUEL  never enabled
PERM_SPARK never enabled
PERM_IAC   never enabled
PERM_PUMP  never enabled
PERM_AUX   never enabled

no call to HAL_GM_FUEL_SYNC_COMMIT
no call to HAL_GM_FUEL_ASYNC_COMMIT
no call to HAL_GM_IAC_COMMIT
no call to HAL_GM_PUMP_COMMIT
no executable spark commit
```

The first hardware run is only intended to prove reset, processor relocation, stable execution, ROM/vector placement, and then read-only observability as those pieces are enabled.

## Output conversion policy

Do not define the final 64 KiB BIN conversion procedure until the actual ASM11 output generated on the user's PC has been inspected. The assembler output is expected to preserve absolute addresses; any S-record-to-BIN conversion must fill unrepresented ROM space deliberately and must preserve the `$FFFE` reset vector exactly.

Once the first successful ASM11 output and listing are available, add the exact reproducible command/build procedure to this document and automate conversion/verification in `tools/`.
