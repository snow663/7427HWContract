# ASM11 Milestone A Bootstrap Proof

## Result

Milestone A assembled successfully on the user's Windows PC with the installed MGTEK 68HC11 assembler.

```text
assembler: ASM11, 68HC11 Cross Assembler V1.26 Build 144 for WIN32 (x86)
source:    source/replacement_os/7427_bootstrap_miniide.asm
result:    0 warnings, 0 errors
```

Command used:

```bat
cd "C:\Program Files (x86)\MGTEK\MiniIDE"
asm11 -l "C:\Users\jakes\Downloads\7427_bootstrap_miniide.asm"
```

ASM11 generated an absolute Motorola S-record and listing.

## Listing-proven addresses

```text
STACK_TOP                  $03FF
ROM_EXEC_BASE              $7100
RESET_ENTRY                $7100
HAL_INIT_PROCESSOR_SAFE    $710C
HAL_SERVICE_COP            $7126
HAL_FATAL_SAFE_LOOP        $7131
ROM_CODE_END               $7137  ; first free byte after code
ROM_VECTOR_BASE            $FFC0
external reset vector      $FFFE -> $7100
```

The executable bytes occupy `$7100-$7136`. The complete 64-byte vector window occupies `$FFC0-$FFFF`.

All non-reset vectors in this milestone contain `$7131`, the COP-serviced safe trap. The reset vector at `$FFFE-$FFFF` contains `$7100`.

## Absolute S-record proof

The ASM11 S-record contains data records only for:

```text
$7100-$7136   bootstrap executable
$FFC0-$FFFF   vector table
```

No relocation is required when converting the S-record to a ROM image.

## Reproducible 64 KiB conversion

Repository tool:

```text
tools/s19_to_64k_bin.py
```

Policy:

```text
absolute S-record addresses are preserved
unrepresented bytes are filled with $FF
output size is exactly 65536 bytes
$FFFE reset vector remains at its absolute ROM address
```

For the first successful Milestone-A S-record, the resulting 64 KiB image was:

```text
size:    65536 bytes
reset:   $FFFE -> $7100
SHA256:  c8980013fb2223dfec6e6536f2e9f3815a66a9c555a50ac25989fbfe15b9279e
```

## What this proves

This closes the first ROM/toolchain gate:

```text
ASM11 syntax/toolchain works
$7100 executable placement works
HC11 instructions encode as expected
$FFC0-$FFFF vector placement works
$FFFE reset vector points to the replacement entry
absolute S-record output can be deterministically converted to a 64 KiB BIN
```

It does **not** prove live PCM execution, ADC behavior, REF behavior, serial transport, or any actuator output.

## Historical milestone boundary

Milestone A is closed. Milestone B subsequently received its own clean ASM11/listing/S19/BIN proof; see:

```text
docs/implementation/MILESTONE_B_BUILD_PROOF.md
```

Do not use this Milestone-A document to determine the current next gate. Current implementation state and work order are maintained in:

```text
docs/WORKING_STATE.md
docs/closeout/7427_IMPLEMENTATION_CONSOLIDATION_AUDIT_2026-08-19.md
```
