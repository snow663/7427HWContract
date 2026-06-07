# FUEL_SCHED_TIMER Contract

## Purpose

This subsystem schedules and services the two TBI-related HC11 timer/output-compare channels using TOC4 and TOC5/TIC4 support registers. It clears timer flags, arms timer interrupts, sets output-compare action bits, and writes 16-bit future compare values.

## Static Contract Finding

`FUEL_SCHED_TIMER` is not the final EFI pulsewidth handoff. The final normal-TBI EFI PW handoff is `$3FCE`. This subsystem appears to be the HC11 timer/output-compare support path that schedules and services TOC4/TOC5 events using timer compare registers and interrupt flags.

For minimal-OS planning, reproduce this subsystem only if bench testing proves `$3FCE` alone does not make the ASIC generate correct injector pulses. If `$3FCE` is sufficient, keep this contract as the stock-reference fallback and safety map.

## Timing Safety Margin

Both setup helpers apply the same minimum lead-time clamp:

```text
L77C7 TOC5/TIC4 setup:
  LDD L081F
  CPD #$06
  if below 6: D = #$0006
  D = D + TCNT ($300E)
  shadow -> L0821

L77F7 TOC4 setup:
  LDD L081F
  CPD #$06
  if below 6: D = #$0006
  D = D + TCNT ($300E)
  shadow -> L0823
```

Static value: minimum compare lead appears to be `6` timer counts. Exact real-time margin depends on the HC11 timer prescale configured in `TMSK2/OPTION` and should be bench-confirmed before a clean OS relies on this path.

## Hardware Registers

| Address | Name | Access | Width | Role | Required |
|---|---|---:|---:|---|---|
| `$301C/$301D` | TOC4 compare | R/W | 16 | Output compare channel 4 scheduled compare value | yes / bench-confirm |
| `$301E/$301F` | TOC5/TIC4 compare | R/W | 16 | Output compare channel 5 / TIC4 scheduled compare value | yes / bench-confirm |
| `$3020` | TCTL1 | RMW | 8/bit | Output compare action/mode bits | yes / bench-confirm |
| `$3022` | TMSK1 | RMW/W | 8/bit | Timer interrupt mask/enable bits | yes / bench-confirm |
| `$3023` | TFLG1 | R/W | 8/bit | Timer interrupt flags; write-one-to-clear | yes / bench-confirm |

## Contract Action Counts

| Action | Rows |
|---|---:|
| flag clear | 12 |
| compare read | 6 |
| output mode setup | 4 |
| compare write | 4 |
| interrupt enable | 3 |
| interrupt mask init | 2 |
| flag status read | 2 |
| interrupt disable | 2 |
| output mode clear/disable | 2 |

## Address Counts

| Address | Rows |
|---|---:|
| `0x301C` | 5 |
| `0x301E` | 5 |
| `0x3020` | 6 |
| `0x3022` | 7 |
| `0x3023` | 14 |

## Observed Write / Service Sequences

### `L77C7` — IRQ-called fuel timer setup helper — TOC5/TIC4

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0x77DD` | `STAA $23,X` | `0x3023` | flag clear | `A=0x08` | TFLG1 timer interrupt flags / write-one-clear / CLR FLAG, TFLG1 / indexed_resolved | high |
| `0x77DF` | `BSET $22,X,#$08` | `0x3022` | interrupt enable | `set 0x08` | TMSK1 timer interrupt mask / SET b3, TMSK1 TIC4/TOC5 INT ENABLE / indexed_resolved | high |
| `0x77E9` | `CPD $1E,X` | `0x301E` | compare read | `CPD` | TOC5/TIC4 compare / TIC4/TOC5 / indexed_resolved | high |
| `0x77EE` | `BSET $20,X,#$03` | `0x3020` | output mode setup | `set 0x03` | TCTL1 output compare action / indexed_resolved | high |
| `0x77F4` | `STD $1E,X` | `0x301E` | compare write | `D` | TOC5/TIC4 compare / TIC4/TOC5	VALUE / indexed_resolved | high |

### `L77F7` — IRQ-called fuel timer setup helper — TOC4

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0x780D` | `STAA $23,X` | `0x3023` | flag clear | `A=0x10` | TFLG1 timer interrupt flags / write-one-clear / CLR FLAG, TFLG1 / indexed_resolved | high |
| `0x780F` | `BSET $22,X,#$10` | `0x3022` | interrupt enable | `set 0x10` | TMSK1 timer interrupt mask / SET b4, TMSK1 TOC 4 INT ENABLE / indexed_resolved | high |
| `0x7819` | `CPD $1C,X` | `0x301C` | compare read | `CPD` | TOC4 compare / TOC 4 / indexed_resolved | high |
| `0x781E` | `BSET $20,X,#$0C` | `0x3020` | output mode setup | `set 0x0C` | TCTL1 output compare action / SET b2 & b3, TCTL1 OL4 & OM4 / indexed_resolved | high |
| `0x7824` | `STD $1C,X` | `0x301C` | compare write | `D` | TOC4 compare / TOC 4 VALUE / indexed_resolved | high |

### `L74D3` — IRQ/DRP/ref interrupt — global/support

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0x754D` | `STAA $23,X` | `0x3023` | flag clear | `A=0x01` | TFLG1 timer interrupt flags / write-one-clear / TFLG1 / indexed_resolved | high |
| `0x7597` | `BRSET $23,X,#$01,L75F7` | `0x3023` | flag status read | `bit test 0x01` | TFLG1 timer interrupt flags / write-one-clear / TFLG1, INPUT CAPT, / indexed_resolved | high |

### `L7650` — IRQ/DRP/ref interrupt — global/support

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0x76E1` | `STAA $23,X` | `0x3023` | flag clear | `A=0x01` | TFLG1 timer interrupt flags / write-one-clear / indexed_resolved | high |
| `0x772B` | `BRCLR $23,X,#$01,L774C` | `0x3023` | flag status read | `bit test 0x01` | TFLG1 timer interrupt flags / write-one-clear / indexed_resolved | high |
| `0x7731` | `STAA $23,X` | `0x3023` | flag clear | `A=0x01` | TFLG1 timer interrupt flags / write-one-clear / indexed_resolved | high |

### `LFC2F` — TIC/RTI vector handler — global/support

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0xFC31` | `STAA L3022` | `0x3022` | interrupt mask init | `A=0xA0` | TMSK1 timer interrupt mask / TMSK1 | high |
| `0xFC36` | `STAA L3023` | `0x3023` | flag clear | `A=0x5F` | TFLG1 timer interrupt flags / write-one-clear / TFLG1 | high |

### `LCE10` — TOC1 knock-window interrupt — global/support

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0xCE7E` | `STAA L3023` | `0x3023` | flag clear | `A=0x80` | TFLG1 timer interrupt flags / write-one-clear / TMR FLG 1 REG | high |

### `L785A` — TOC3/6.25ms major-loop interrupt — global/support

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0x7948` | `STAA L3023` | `0x3023` | flag clear | `A=0x20` | TFLG1 timer interrupt flags / write-one-clear | high |

### `L785A` — TOC4 interrupt — TOC4

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0x78DE` | `STAA $23,X` | `0x3023` | flag clear | `A=0x10` | TFLG1 timer interrupt flags / write-one-clear / TFLG1, / indexed_resolved | high |
| `0x78E4` | `BCLR $22,X,#$10` | `0x3022` | interrupt disable | `clear 0x10` | TMSK1 timer interrupt mask / SET b4, TOC4 INT ENABLE / indexed_resolved | high |
| `0x78E7` | `BCLR $20,X,#$04` | `0x3020` | output mode clear/disable | `clear 0x04` | TCTL1 output compare action / SET b2, TCTL1, OL4 TGGLE OC LINE / indexed_resolved | high |
| `0x78FC` | `ADDD $1C,X` | `0x301C` | compare read | `ADDD` | TOC4 compare / TOC4 / indexed_resolved | high |
| `0x7914` | `ADDD $1C,X` | `0x301C` | compare read | `ADDD` | TOC4 compare / TOC4 / indexed_resolved | high |
| `0x7929` | `BSET $20,X,#$04` | `0x3020` | output mode setup | `set 0x04` | TCTL1 output compare action / TCTL1, OL4 TOGGLE TOC4 OUT LINE / indexed_resolved | high |
| `0x793A` | `STD $1C,X` | `0x301C` | compare write | `D` | TOC4 compare / TOC4 / indexed_resolved | high |

### `L785A` — TOC5/TIC4 interrupt — TOC5/TIC4

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0x787A` | `STAA $23,X` | `0x3023` | flag clear | `A=0x08` | TFLG1 timer interrupt flags / write-one-clear / TFLAG / indexed_resolved | high |
| `0x7880` | `BCLR $22,X,#$08` | `0x3022` | interrupt disable | `clear 0x08` | TMSK1 timer interrupt mask / CLR b3, TMASK1, TIC4/TOC5 INHIB / indexed_resolved | high |
| `0x7883` | `BCLR $20,X,#$01` | `0x3020` | output mode clear/disable | `clear 0x01` | TCTL1 output compare action / CLR b0, TCTL1, OL5 DISCON FM PIN / indexed_resolved | high |
| `0x7898` | `ADDD $1E,X` | `0x301E` | compare read | `ADDD` | TOC5/TIC4 compare / TIC4/TOC5 / indexed_resolved | high |
| `0x78B0` | `ADDD $1E,X` | `0x301E` | compare read | `ADDD` | TOC5/TIC4 compare / TIC4/TOC5 / indexed_resolved | high |
| `0x78C5` | `BSET $20,X,#$01` | `0x3020` | output mode setup | `set 0x01` | TCTL1 output compare action / SET b0 / indexed_resolved | high |
| `0x78D6` | `STD $1E,X` | `0x301E` | compare write | `D` | TOC5/TIC4 compare / TIC4/TOC5	VALUE / indexed_resolved | high |

### `LFC11` — XIRQ/vector handler — global/support

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0xFC16` | `STAA L3023` | `0x3023` | flag clear | `A=0x01` | TFLG1 timer interrupt flags / write-one-clear | high |

### `L7459` — mainline/unknown — global/support

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0x745B` | `STAA L3023` | `0x3023` | flag clear | `A=0xFF` | TFLG1 timer interrupt flags / write-one-clear / TFLG 1 | high |
| `0x7469` | `STAA L3022` | `0x3022` | interrupt mask init | `A=0xA0` | TMSK1 timer interrupt mask / TMSK1 | high |

### `LCC4B` — mainline/unknown — global/support

| PC | Instruction | Target | Action | Source / bit | Notes | Confidence |
|---|---|---|---|---|---|---|
| `0xCC56` | `BSET $22,X,#$A0` | `0x3022` | interrupt enable | `set 0xA0` | TMSK1 timer interrupt mask / TMSK1 / indexed_resolved | high |

## Required New-OS Behavior

A new OS must reproduce this behavior only if bench testing proves the `$3FCE` EFI PW handoff is not sufficient by itself. If this path is required, reproduce:

1. safe minimum compare lead time (`>= 6` timer counts observed statically in setup helpers)
2. correct TFLG1 write-one-clear behavior before or during arm/service
3. correct TMSK1 interrupt-enable and interrupt-disable behavior
4. correct 16-bit TOC4/TOC5 compare writes
5. correct TCTL1 output mode setup/clear bits
6. correct BPW-derived timer extension behavior in the TOC4/TOC5 ISR paths
7. correct zero-fuel / DFCO behavior, preferably via `$3FCE = 0` if bench-proven

## Open Tests

- Verify whether `$3FCE` alone commands injector pulsewidth through the ASIC.
- Verify whether TOC4/TOC5 correspond directly to injector A/B or only support delayed/async scheduling.
- Verify output polarity at MCU pin vs injector driver output.
- Verify whether compare write order matters relative to TFLG1/TMSK1.
- Verify minimum usable compare lead time in real timer counts.
- Verify what happens if one channel is armed and the other is not.

## Minimal Current Conclusion

Stock code definitely maintains TOC4/TOC5 scheduling machinery. However, the focused fuel-PW handoff finding shows `$3FCE` is the explicit EFI PW register. Therefore, the clean OS should first prove `$3FCE` on the bench. Only recreate TOC4/TOC5 scheduling if `$3FCE` does not fully explain injector output timing.
