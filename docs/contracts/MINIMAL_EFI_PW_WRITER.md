# Minimal EFI PW Writer Contract

## Purpose

Provide the minimal runtime fuel pulsewidth output writer for the new 7427 hardware-contract OS.

This contract intentionally separates runtime pulsewidth output from hardware initialization. The writer does not establish ASIC mode, output-driver state, diagnostic mode, or board latch state.

## Status

```text
static status: ready
bench status: pending
path assumption: Path A-with-init
```

Meaning:

```text
one-time ASIC/global init may be required
runtime fuel pulsewidth command is only STD $3FCE
```

## Hardware Assumption

`$3FCE/$3FCF` is the 16-bit EFI pulsewidth handoff in `1/65536 second` units.

```text
PW_ms = counts / 65.536
counts = round(PW_ms × 65.536)
```

## Runtime Behavior

```text
Input:
  D = desired pulsewidth counts in 1/65536 second units

Output:
  STD $3FCE
  RTS

No-fuel candidate:
  D = $0000 means no fuel/off if bench confirms
```

## Required Preconditions

Before this writer is valid, the caller/system must ensure:

1. HC11 register relocation is complete.
2. The ASIC/window/global initialization sequence is complete.
3. Any required `$3FCC/$3FEA` mode/preload state is established if Path A-with-init is bench-confirmed.
4. The caller owns all fuel math, limits, state, and safety decisions.
5. The caller has already converted final pulsewidth into `$3FCE` hardware units.

## Explicit Non-Responsibilities

This routine does **not** perform:

- VE or airflow fuel math
- injector deadtime correction
- low-pulsewidth transfer correction
- minimum/maximum pulse clamp
- AE, PE, DFCO, crank, warmup, or afterstart logic
- battery voltage correction
- companion ASIC mode writes
- TOC4/TOC5 scheduling
- output-driver enable/disable logic

## Assembly Contract

```asm
; -----------------------------------------------------------------------------
; EFI_PW_WRITE
;
; Minimal EFI pulsewidth writer for 7427 hardware-contract OS.
;
; Input:
;   D = EFI pulsewidth command in 1/65536 second units
;
; Unit:
;   PW_ms = D / 65.536
;
; Output:
;   Writes D to ASIC EFI pulsewidth handoff register $3FCE/$3FCF.
;
; Notes:
;   D = 0 is treated as no-fuel/off by design, pending bench confirmation.
;   This routine does not perform fuel math, clamping, deadtime, AE, PE, or DFCO.
;   Caller must provide final command value.
; -----------------------------------------------------------------------------

L3FCE          EQU   $3FCE

EFI_PW_WRITE:
               STD   L3FCE
               RTS
```

## Forbidden Runtime Writes In This Routine

The runtime writer must not touch these until bench proof requires a change:

```text
$3FCC  possible ASIC fuel/output mode/preload; init contract owns it
$3FEA  possible ASIC fuel/output mode/preload; init contract owns it
$301C  TOC4 compare; timer contract owns it
$301E  TOC5/TIC4 compare; timer contract owns it
$3020  TCTL1; timer contract owns it
$3022  TMSK1; timer contract owns it
$3023  TFLG1; timer contract owns it
```

## Static Test Requirement

`tools/verify_minimal_writer.py` must confirm:

1. exactly one hardware write instruction exists in `EFI_PW_WRITE`
2. the only hardware write is `STD L3FCE`
3. no forbidden companion/timer write appears
4. vectors use the `counts / 65.536` conversion
5. all vector write targets are `0x3FCE` with width `16`

## Bench Gate

This writer remains a contract/stub until bench testing confirms one of these:

```text
Path A-clean:
  STD $3FCE is sufficient after normal global boot/init.

Path A-with-init:
  STD $3FCE is the only runtime fuel command, but EFI_OUTPUT_INIT must first establish the proven ASIC mode/preload state.
```

If Path C-runtime is proven, this routine must be revised to include the required companion sequence or call a companion strobe routine.
