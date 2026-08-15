# MGTEK ASM11 / MiniIDE Build Target

## Selected assembler

The replacement ROM source targets the **MGTEK ASM11** 68HC11 cross-assembler supplied with MiniIDE.

The user's installed/proven tool is:

```text
ASM11, 68HC11 Cross Assembler V1.26 Build 144 for WIN32 (x86)
```

Do not use `asm12.exe`; MiniIDE may default to the separate 68HC12 assembler.

## Proven command-line invocation

The assembler executable is installed at:

```text
C:\Program Files (x86)\MGTEK\MiniIDE\asm11.exe
```

A proven build command is:

```bat
cd "C:\Program Files (x86)\MGTEK\MiniIDE"
asm11 -l "C:\path\to\source.asm"
```

`-l` requests the listing. ASM11 emits absolute Motorola S-record output (`.s19`) and a listing (`.lst`).

## Build sources

Maintainable modular master:

```text
source/replacement_os/7427_rom.asm
```

Self-contained PC bring-up stages:

```text
source/replacement_os/7427_bootstrap_miniide.asm   Milestone A: reset/bootstrap/vectors
source/replacement_os/7427_inputs_miniide.asm      Milestone B: read-only ADC/REF acquisition
```

The self-contained files intentionally remove `INCLUDE` path setup from the first PC tests. The modular source tree remains the long-term implementation authority.

## Source syntax relied on

```text
INCLUDE
ORG
EQU
RMB
FCB
FDB
```

plus ordinary Motorola 68HC11 instruction mnemonics and semicolon comments.

No linker script is required for the current stages. Placement is expressed directly by `ORG` and symbols.

## Milestone-A proof

Milestone A assembled on the user's PC with:

```text
0 warnings
0 errors
```

The actual ASM11 listing proved:

```text
RESET_ENTRY                 $7100
HAL_INIT_PROCESSOR_SAFE     $710C
HAL_SERVICE_COP             $7126
HAL_FATAL_SAFE_LOOP         $7131
executable bytes            $7100-$7136
vector table                $FFC0-$FFFF
external reset vector       $FFFE -> $7100
```

See:

```text
docs/implementation/ASM11_BOOTSTRAP_PROOF.md
```

## 64 KiB BIN conversion

ASM11's `.s19` preserves the absolute 16-bit target addresses. Convert it without relocation using:

```text
tools/s19_to_64k_bin.py
```

Example:

```bat
python tools\s19_to_64k_bin.py 7427_bootstrap_miniide.s19 7427_bootstrap_64k.bin
```

Conversion policy:

```text
image size             exactly 65536 bytes
unrepresented bytes    $FF
S-record addresses     preserved exactly
reset vector            remains at $FFFE
```

The first proven Milestone-A conversion produced:

```text
reset vector: $7100
SHA256: c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

## Listing checks for every stage

```text
STACK_TOP               = $03FF
RAM_ALLOC_END           < $03FF when RAM exists
ROM_CODE_END            < $FFC0
vector table begins     = $FFC0
external reset vector   = $FFFE -> RESET_ENTRY
```

Also verify that there are no overlapping ORG ranges, address-truncation warnings, or branch-range errors.

ASM11 warnings about an address being outside `$00-$FF` are **not** harmless when emitted for a direct-page-only instruction. The ADC `BRSET` issue discovered during bring-up is the example: absolute `$3030` had to be replaced with an explicit extended `LDAA` + `BITA` test.

## Output safety condition

A successful assembly is not yet an engine-running image.

Through the observability stages:

```text
no fuel authority
no spark authority
no IAC authority
no pump authority
no auxiliary-output authority
```

Milestone A contains no actuator command routines. Milestone B adds only CPU/ADC/mux configuration and read-only input acquisition. Production output commits remain outside the execution path until explicitly enabled later one permission at a time.
