# MGTEK ASM11 / MiniIDE Build Target

## Selected assembler

The replacement ROM targets **MGTEK ASM11**, the 68HC11 cross-assembler supplied with MiniIDE.

Proven tool:

```text
ASM11, 68HC11 Cross Assembler V1.26 Build 144 for WIN32 (x86)
```

Do not use `asm12.exe`; MiniIDE may default to the separate 68HC12 assembler.

## Proven command-line invocation

```bat
cd "C:\Program Files (x86)\MGTEK\MiniIDE"
asm11 -l "C:\path\to\source.asm"
```

`-l` requests the listing. ASM11 emits absolute Motorola S-record output (`.s19`) and a listing (`.lst`).

## Source roles

Maintainable modular authority:

```text
source/replacement_os/7427_rom.asm
source/replacement_os/include/*.inc
source/replacement_os/core/*.asm
source/replacement_os/hal/*.asm
```

Self-contained proof stages:

```text
source/replacement_os/7427_bootstrap_miniide.asm   Milestone A: bootstrap/vectors
source/replacement_os/7427_inputs_miniide.asm      Milestone B: read-only ADC/REF acquisition
source/replacement_os/7427_aldl_tx_miniide.asm     Milestone C: engine-off ALDL observability
```

`source/replacement_os/7427_rom_miniide.asm` is a flattened MiniIDE convenience form of the modular source, not independent authority.

The stage files intentionally avoid `INCLUDE` path problems during bring-up. Once a stage is proven, its verified behavior should be folded back into the modular master.

## Milestone A proof

Observed on the user's PC:

```text
0 warnings
0 errors
```

Listing proof:

```text
RESET_ENTRY                 $7100
HAL_INIT_PROCESSOR_SAFE     $710C
HAL_SERVICE_COP             $7126
HAL_FATAL_SAFE_LOOP         $7131
executable bytes            $7100-$7136
vector table                $FFC0-$FFFF
external reset vector       $FFFE -> $7100
```

Deterministic 64 KiB conversion:

```text
SHA256 c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

Authority: `docs/implementation/ASM11_BOOTSTRAP_PROOF.md`.

## Milestone B proof

Source:

```text
source/replacement_os/7427_inputs_miniide.asm
```

Observed build:

```text
0 warnings
0 errors
```

Listing proof:

```text
RAM_ALLOC_END                 $000A
RESET_ENTRY                   $7100
INPUT_SAMPLE_LOOP             $711A
HAL_INIT_PROCESSOR_INPUT_SAFE $712E
HAL_SERVICE_COP               $714F
HAL_ADC_SET_MUX_SELECT        $715A
HAL_ADC_START_WAIT            $716C
HAL_SAMPLE_PRIMARY_ADC        $7183
HAL_SAMPLE_COOLANT_BATTERY    $719C
HAL_SAMPLE_MAT                $71B5
HAL_CAPTURE_REF_PERIOD        $71CA
HAL_FATAL_SAFE_LOOP           $71D2
ROM_CODE_END                  $71D8
vector table                  $FFC0-$FFFF
external reset vector         $FFFE -> $7100
```

Deterministic 64 KiB conversion:

```text
SHA256 28462ef9dbf3b6f0de59b68662fb26916dc87abea35ff7d67a0d572d42f92848
```

Authority: `docs/implementation/MILESTONE_B_BUILD_PROOF.md`.

Important boundary: Milestone B builds a `$3FC0` read, but `$3FC0` is not yet proven meaningful REF data on a replacement image because the stock ASIC/register startup sequence is intentionally absent.

## Milestone C current target

Source:

```text
source/replacement_os/7427_aldl_tx_miniide.asm
```

Status:

```text
source implemented
assembly/listing proof pending
S19/BIN proof pending
bench proof pending
```

Milestone C extends B with:

```text
8192-baud SCI
stock BMHM/TBI $3FFC/$3FFD = $B93A startup baseline
ALDL external-driver RMW on low-byte $3FFD bit2
SCI interrupt transmit service
14-byte raw-input frame
no production actuator authority
```

Its next gate is exactly the same as the proven A/B process: ASM11 build, listing inspection, S19 validation, deterministic 64 KiB conversion, then engine-off bench observation.

## 64 KiB BIN conversion

ASM11 `.s19` files preserve absolute 16-bit target addresses. Convert without relocation using:

```text
tools/s19_to_64k_bin.py
```

Example:

```bat
python tools\s19_to_64k_bin.py input.s19 output_64k.bin
```

Conversion policy:

```text
image size             exactly 65536 bytes
unrepresented bytes    $FF
S-record addresses     preserved exactly
reset vector           remains at $FFFE
```

## Listing checks for every stage

```text
STACK_TOP               = $03FF
RAM_ALLOC_END           < $03FF when RAM exists
ROM_CODE_END            < $FFC0
vector table begins     = $FFC0
external reset vector   = $FFFE -> RESET_ENTRY
```

Also verify:

```text
no overlapping ORG regions
no address-truncation warnings
no branch-range errors
all ISR vectors point to intended handlers or the safe trap
all absolute hardware addresses match the current contracts
no production-output write path is reachable in observability images
```

ASM11 warnings about an address outside `$00-$FF` are **not** harmless when generated for a direct-page-only instruction. The Milestone-B ADC `BRSET` correction is the precedent: absolute `$3030` required an explicit extended `LDAA` + `BITA` test.

## Output safety condition

Through Milestone C:

```text
no fuel authority
no spark authority
no IAC authority
no pump authority
no auxiliary-output authority
```

A successful assembly proves the software image layout, not live hardware behavior. Bench proof remains a separate gate.
