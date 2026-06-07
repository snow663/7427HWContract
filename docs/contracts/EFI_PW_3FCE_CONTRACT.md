# EFI PW $3FCE Contract

## Purpose

This contract documents the CPU-to-ASIC fuel pulsewidth handoff at `$3FCE/$3FCF`.

## Hypothesis

`$3FCE` is the final EFI pulsewidth command handoff into the Delco ASIC/hardware output engine. The HC11 timer compare scheduler remains documented as stock reference/fallback unless bench tests prove it is also required for injector output.

## Static Conclusion

- All observed `$3FCE` accesses are direct 16-bit `STD L3FCE` writes.
- No static map row shows an 8-bit `STAA/STAB`, read, or RMW access to `$3FCE`.
- A 68HC11 `STD` stores the high byte of `D` at `$3FCE` and the low byte at `$3FCF`, so `$3FCE/$3FCF` must be treated as a 16-bit pair.
- Diagnostic output cycling writes `#197` to `$3FCE` with the source comment `SET UP FOR 3msec PULSES` / `SAVE TO EFI PW`. Static unit inference: `197 / 3 ms ≈ 65.7 counts/ms`, matching the nearby low-BPW table convention of approximately `65.536 counts/ms`.
- `$0000` is written to `$3FCE` in the output-cycling disable path, making zero/off behavior a primary bench-test item.

## Hardware Addresses

| Address | Role | Width | Access | Required | Confidence |
|---|---|---:|---|---|---|
| `$3FCE` | EFI PW handoff candidate, high byte of 16-bit command | 16 | W | yes if confirmed | high static / bench required |
| `$3FCF` | EFI PW low byte, implied by `STD L3FCE` | 16 pair | implied W | yes if confirmed | high static / bench required |
| `$3FCC` | context / adjacent fuel-scheduler command candidate | 16 | W | context/test | context only |
| `$3FCD` | context / adjacent byte of `$3FCC` pair | 16 pair | implied W | context/test | no independent row |
| `$3FD0` | nearby context address | not seen | not seen | context/test | no independent static access row |

## Access Summary

```text
selected rows: 6
$3FCE rows: 4
$3FCC context rows: 2
access types: W only
widths: 16 only
primary instruction: STD L3FCE
```

## Static Access Rows

| PC | Address | Instruction | Access | Width | Value source | Routine | Action | Notes |
|---|---|---|---|---:|---|---|---|---|
| `0x74D6` | `0x3FCC` | `STD L3FCC` | W | 16 | `D=0xD000` | `L74D3` | context_command_or_enable | ASIC fuel/scheduler command candidate A |
| `0x8426` | `0x3FCE` | `STD L3FCE` | W | 16 | `D` | `L82ED` | fuel_calc_zero_or_transient_gate_write | ASIC EFI PW / fuel pulse-width handoff |
| `0x8512` | `0x3FCE` | `STD L3FCE` | W | 16 | `D=0x7FFF` static tracker; actual D is final corrected BPW | `L84F5` | normal_tbi_final_pw_write | ASIC EFI PW / fuel pulse-width handoff |
| `0xFADC` | `0x3FCC` | `STX L3FCC` | W | 16 | `X` | `LFA5B` | context_command_or_enable | ASIC fuel/scheduler command candidate A |
| `0xFAEE` | `0x3FCE` | `STD L3FCE` | W | 16 | `D=0x00C5` | `LFA5B` | diagnostic_3ms_pw_write | ASIC EFI PW / fuel pulse-width handoff; SAVE TO EFI PW |
| `0xFB44` | `0x3FCE` | `STD L3FCE` | W | 16 | `D=0x0000` | `LFA5B` | efi_pw_zero/off | ASIC EFI PW / fuel pulse-width handoff |

## Normal TBI Write Path

```text
84BC: LDD  L024E        ; SYNC BPW
84BF: BRCLR L003E,#$10,L84CB ; branch if async pulse flag not set
84C3: STD  L024C        ; sync BPW saved in async-flag path
...
84CB: BEQ  L84F5        ; zero BPW skips low-BPW correction path
84CD: CPD  #$0100       ; low-BPW region check
84D3: TBA
84D4: LDAB #32
84D6: LDX  #$4979       ; low BPW offset vs BPW
84D9: JSR  LF4BD        ; 2D lookup
84DC: TAB               ; low BPW offset
84DD: CLRA
84DE: ADDD L024E        ; sync BPW
84E1: SUBD L4971        ; 31 usec offset bias for small BPW
84E6: BCLR L003F,#$80   ; clear short BPW flag
84E9: CPD  L496D        ; 488 usec min sync BPW
84EF: BSET L003F,#$80   ; set short BPW flag
84F2: LDD  L496F        ; 488 usec sync BPW if below min
84F5: STD  L024C        ; sync BPW
84F8: BEQ  L8508        ; if zero, skip BPW bias
84FA: ADDB L0256        ; BPW bias / deadtime-like adder
84FD: ADCA #$00         ; carry/round into high byte
84FF: CPD  #32767       ; max clamp
8505: LDD  #32767       ; max value for BPW
8508: STD  L0250        ; working BPW
850B: LDX  #$400B       ; AFR mode byte 1
850E: BRSET 0,X,#$01,L8517 ; skip if CPI/PFI mode
8512: STD  L3FCE        ; normal TBI EFI PW handoff
```

## Write Dependency Chain

```text
$3FCE/$3FCF 16-bit EFI PW command
← D register at STD L3FCE
← normal TBI path: L024E sync BPW
← low-BPW offset table $4979 when BPW < $0100
← 31 usec offset bias $4971
← minimum sync BPW thresholds $496D/$496F
← BPW bias/deadtime adder L0256
← max clamp #32767
← working BPW L0250
← skipped/branched away for CPI/PFI mode bit $400B bit0

$3FCE zero write @ $8426
← non-CPI/PFI async/sync decision path
← clears EFI PW before ratio/math using $3FC0 and L024E

$3FCE diagnostic 3ms write @ $FAEE
← D = #197
← output cycling path

$3FCE zero/off write @ $FB44
← output cycling disable path
```

## Units

Static evidence says `$3FCE` is a 16-bit hardware pulsewidth unit, not raw milliseconds. The strongest clue is `#197` being documented as `3msec PULSES`, giving roughly `65.7 counts/ms`. Nearby comments describe the low-BPW table as `(msec + L496F) * 65.536`, so the working unit is likely:

```text
1 ms ≈ 65.536 counts
1 count ≈ 15.26 us
```

Bench measurement must lock this down.

## State / Timing Gating

- Normal TBI fuel path writes `$3FCE` after low-BPW correction, minimum BPW handling, BPW bias addition, max clamp, and `L0250` update.
- CPI/PFI mode branches around the normal `$3FCE` write and instead computes delay into `L081F`, so the clean TBI OS must keep the mode decision explicit.
- Diagnostic output cycling writes a fixed `$3FCE` command and later writes zero on disable.
- Refresh appears to be fuel-calc/event driven, not a blind main-loop register mirror; exact latch timing is a bench-test item.

## Required New-OS Behavior

The new OS must reproduce:

1. 16-bit write to `$3FCE/$3FCF` using correct byte order
2. hardware PW units, likely `ms * 65.536` until bench-proven
3. low-PW/minimum/off behavior required by the actual injector driver
4. `$0000` no-fuel/output-off behavior if confirmed
5. crank/run/idle/AE/DFCO state gating before the handoff
6. any companion enable/command writes such as `$3FCC/$3FEA` if bench testing shows they gate the output engine
7. interaction with TOC4/TOC5 only if `$3FCE` alone does not command final injector pulsewidth

## Bench Tests

See `docs/tests/EFI_PW_3FCE_BENCH_TEST.md`.

## Open Questions

- Does changing `$3FCE` alone change injector pulsewidth proportionally?
- Does `$0000` written to `$3FCE` suppress injector output?
- Are `$3FCC/$3FEA` required output-engine enables, mode words, or only diagnostic/prime support?
- Is the unit exactly `65.536 counts/ms`, or an ASIC timer derivative close to that?
- Are TOC4/TOC5 still required in normal TBI, or only stock scheduler scaffolding/secondary timing?
