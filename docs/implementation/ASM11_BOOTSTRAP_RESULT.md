# ASM11 bootstrap build result

Date: 2026-08-14

## Toolchain actually used

The first replacement-ROM bootstrap was assembled on the user's Windows PC with:

- MGTEK ASM11
- 68HC11 Cross Assembler V1.26 Build 144 for WIN32 (x86)
- command form: `asm11 -l <source.asm>`

This supersedes the earlier MiniIDE GUI attempt that had invoked ASM12/68HC12.

## Source

`source/replacement_os/7427_bootstrap_miniide.asm`

This is the deliberately minimal Milestone-A image containing only:

- reset entry
- stock-proven HC11 register relocation/configuration
- COP service
- COP-serviced safe trap for every unowned interrupt
- complete vector table

It contains no production actuator command routines.

## Assembly result

ASM11 reported:

- 0 warnings
- 0 errors

The generated listing establishes the actual map:

- `RESET_ENTRY = $7100`
- `HAL_INIT_PROCESSOR_SAFE = $710C`
- `HAL_SERVICE_COP = $7126`
- `HAL_FATAL_SAFE_LOOP = $7131`
- `ROM_CODE_END = $7137` (first free byte after code)
- vector table begins at `$FFC0`
- all unowned vectors contain `$7131`
- external reset vector at `$FFFE` contains `$7100`

The emitted S-record contains executable records for `$7100-$7136` and `$FFC0-$FFFF`.

## BIN conversion policy

`tools/s19_to_64k_bin.py` converts ASM11 S-record output into a flat 65,536-byte image:

- address space `$0000-$FFFF`
- unspecified bytes filled with `$FF`
- S-record checksums verified during conversion
- reset vector reported after conversion
- SHA-256 reported for reproducibility

The first user-built bootstrap converted under this policy produced:

- size: 65,536 bytes
- reset vector: `$7100`
- SHA-256: `c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e`

## Milestone status

Milestone A — **assembler/toolchain + executable reset/vector skeleton: PASS**.

Next implementation work should move to read-only observability. Production output permissions remain disabled and no actuator authority should be enabled merely because the bootstrap assembles successfully.
