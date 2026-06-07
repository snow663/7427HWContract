# Fuel Pulsewidth Handoff v0.3

Source pass: `31_HAC_from_ORG_7100_to_end_NOWRAP.html` / committed source equivalent `source/31/BMHM_HAC_ORG_7100_to_end.asm`.

## Finding

For normal TBI mode, the final synchronized fuel pulsewidth is written to ASIC register `$3FCE`.

The relevant path is:

```text
fuel math -> L024E SYNC BPW
low-BPW offset / min-BPW correction
L024C = corrected SYNC BPW
L0250 = corrected BPW + bias / clamp
if not CPI/PFI mode:
    STD L3FCE
```

## Evidence

At `84BC`, D is loaded from `L024E` (`SYNC BPW`). If the async-pulse flag is clear, the code applies low-BPW correction, short-BPW flag logic, and min-BPW enforcement. It then stores D to `L024C` as `SYNC BPW`, adds `L0256` BPW bias, clamps to `32767`, stores D to `L0250` as `BPW`, checks AFR mode byte 1 bit 0, and in non-CPI/PFI mode writes D directly to `L3FCE`.

Key sequence:

```asm
84BC: LDD  L024E       ; SYNC BPW
84D6: LDX  #$4979      ; LOW BPW OFFSET vs BPW table
84DE: ADDD L024E       ; SYNC BPW
84E1: SUBD L4971       ; 31 usec offset bias
84E9: CPD  L496D       ; 488 usec min sync BPW
84F2: LDD  L496F       ; 488 usec sync BPW if too small
84F5: STD  L024C       ; SYNC BPW
84FA: ADDB L0256       ; BPW bias
8508: STD  L0250       ; BPW
850E: BRSET 0,X,#$01,L8517 ; CPI/PFI mode check
8512: STD  L3FCE       ; normal TBI EFI PW handoff
```

The diagnostic output-cycling routine confirms `$3FCE` meaning. It writes constant `197` and comments it as setting up `3msec PULSES`, then stores it to `$3FCE` with the source comment `SAVE TO EFI PW`.

```asm
FAEB: LDD #197        ; SET UP FOR 3msec PULSES
FAEE: STD L3FCE      ; SAVE TO EFI PW
FB41: LDD #$0000
FB44: STD L3FCE      ; clear EFI PW
```

## Important distinction

The CPU timer compare path still exists and uses BPW-derived values during crank/edge scheduling:

```asm
75D4: LDD L0250      ; BPW
75D7: ASLD           ; BPW x 2
75DD: ADDD $0E,X     ; free-running timer
75DF: STD L0825      ; TIC4/TOC5 result
75F3: STD $1E,X      ; TIC4/TOC5

7607: LDD L0250      ; BPW
760A: ASLD           ; BPW x 2
7610: ADDD $0E,X     ; CPU timer
7612: STD L0827
7626: STD $1C,X      ; TOC4
```

But for normal TBI fuel after the main fuel path, `$3FCE` is the direct EFI pulsewidth handoff register.

## Minimal OS implication

The next clean-OS fuel target should be:

```text
compute corrected effective BPW
apply low-BPW/min-BPW/deadtime policy
write 16-bit BPW to $3FCE
write zero to $3FCE for no-fuel/DFCO/output-off
```

Do not reproduce TOC4/TOC5 scheduling as the first approach unless bench testing proves `$3FCE` alone is insufficient on the 7427 hardware.

## Remaining proof item

Bench proof can be narrow:

```text
Change $3FCE while leaving ASIC/init/output state intact.
Verify injector output pulse width follows $3FCE.
Verify $3FCE = 0 disables injector pulse.
```

If that passes, the fuel-output contract is `$3FCE = EFI PW`, and the minimal OS does not need the stock TOC4/TOC5 fuel scheduler.
