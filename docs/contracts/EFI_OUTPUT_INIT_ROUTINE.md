# EFI Output Init Routine Contract

## Purpose

Define the provisional one-time EFI output hardware initialization routine for the new 7427 hardware-contract OS.

This routine owns initialization/state only. Runtime pulsewidth updates remain owned by `EFI_PW_WRITE`, which writes only `STD L3FCE`.

## Status

```text
static status: provisional
bench status: pending
path assumption: Path A-with-init
runtime writer: EFI_PW_WRITE owns only STD $3FCE
init routine: owns one-time ASIC fuel/output state
```

## Separation Rule

```text
EFI_OUTPUT_INIT:
  establish required ASIC/window/output mode state once

EFI_PW_WRITE:
  runtime pulsewidth update only
```

No fuel math, pulsewidth clamping, AE, PE, DFCO, or runtime pulsewidth command generation belongs in `EFI_OUTPUT_INIT`.

## Static Init Evidence Preserved

```text
0x715B STD 0,X
  clears even ASIC words from $3FC0 through before $3FFA

0x74D6 STD L3FCC
  D = $D000

0x74DF STD L3FEA
  D = $DFFF

0xFADC STX L3FCC
  diagnostic/output-cycling preload

0xFAE5 STX L3FEA
  diagnostic/output-cycling preload
```

## Current Interpretation

```text
ASIC window clear:
  strongly required init candidate

$3FCC/$3FEA:
  mode/preload candidates
  not yet proven required for normal $3FCE runtime fuel
  must remain conditional pending bench proof
```

## Active Init Behavior

The first provisional init routine actively performs only the ASIC-window clear:

```text
for X = $3FC0; X != $3FFA; X += 2:
  STD 0,X with D = $0000
```

This clears every even 16-bit ASIC word from `$3FC0` through `$3FF8`, including `$3FCC`, `$3FCE`, `$3FE8`, `$3FEA`, and `$3FF6`.

## Conditional Init Behavior

`$3FCC/$3FEA` preloads are present only as commented bench-gated candidates:

```asm
; Optional pending bench proof:
;              LDD   #$D000
;              STD   L3FCC
;              LDD   #$DFFF
;              STD   L3FEA
```

They are **not** active in the provisional routine.

## Required Preconditions

Before calling `EFI_OUTPUT_INIT`:

1. HC11 register relocation must already be complete.
2. The external ASIC register window must be decoded at `$3FC0-$3FFF`.
3. Outputs must be in a safe state, or the bench setup must be ready to observe transient output behavior.

After calling `EFI_OUTPUT_INIT`, runtime fuel output still requires `EFI_PW_WRITE` and the `$3FCE` bench proof.

## Required Non-Behavior

The provisional routine must not:

- call `EFI_PW_WRITE`
- perform runtime fuel pulsewidth commands other than the block clear resetting `$3FCE` to zero
- write TOC4/TOC5/timer scheduler registers `$301C`, `$301E`, `$3020`, `$3022`, or `$3023`
- actively preload `$3FCC/$3FEA` unless the build is intentionally changed after bench proof
- perform fuel math or modify fuel strategy state

## Static Verification

`tools/verify_efi_output_init.py` must confirm:

1. `EFI_OUTPUT_INIT` exists.
2. The ASIC clear loop targets `$3FC0` through before `$3FFA`.
3. Clear writes are 16-bit `STD 0,X` zero writes.
4. `$3FCE` is written only as part of the ASIC-window block clear.
5. The routine does not call `EFI_PW_WRITE`.
6. `$3FCC/$3FEA` active preloads are absent unless explicitly bench-gated and expected by the vector table.
7. The routine does not touch `$301C/$301E/$3020/$3022/$3023`.

## Bench Gate

This routine is provisional until bench tests classify one of:

```text
A-clean:
  $3FCE works without special custom init beyond normal hardware reset

A-with-global-init:
  $3FCE works after $3FC0-$3FF8 clear

A-with-3FCC-3FEA-init:
  $3FCE works only after $3FCC/$3FEA preload

C-runtime:
  $3FCC/$3FEA or another companion must be updated during each runtime command

B:
  injector output does not follow $3FCE
```

## Next Contract If Bench Proves Preloads Required

If `$3FCC/$3FEA` are proven required as one-time init state, this contract should be revised so the active init path becomes:

```asm
EFI_OUTPUT_INIT:
    ; clear ASIC window
    ; write proven $3FCC/$3FEA mode/preload values
    RTS
```

If `$3FCC/$3FEA` are proven runtime companions, they must not be hidden inside this routine; create a Path C runtime write/strobe contract instead.
