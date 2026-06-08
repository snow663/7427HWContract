# IAC Enable / Fault Gate Contract

## Purpose

Document the enable/disable logic for the IAC driver command path.

This contract covers only the Enable path. It does not define A/B phase order, park/reset movement, desired IAC calculation, idle strategy, or create an IAC writer.

## Known Boundary

Phase command path is owned by:

- `IAC_PHASE_SEQUENCE_CONTRACT.md`

This contract owns:

```text
L000A bit4
→ L004C bit4
→ L3062 bit4 candidate
```

## Working Hypothesis

IAC Enable is a driver-enable / health gate, not a per-step pulse.

It likely asserts after startup voltage/driver conditions are acceptable and remains asserted during normal operation. It may clear for low/high voltage, bad shutdown/setup, reset, test, or protection behavior.

## Static Clues

| Clue | Candidate meaning | Static result |
|---|---|---|
| `LDAA L00A7` | battery voltage source | source comment: `BAT VOLTS, VDC/10` |
| `CMPA #169` | high-voltage threshold | source comment: `16.9 VDC` |
| `ANDB #$EF` | clear Enable bit | clears bit4 candidate |
| `ORAB #$10` | set Enable bit | sets bit4 candidate |
| `BSET L003E,#$04` | low-battery/protection flag | set when voltage gate fails |
| `BCLR L003E,#$04` | clear low-battery/protection flag | good path before Enable set |
| `ANDA #$0C` in `L93C5` | setup clear | preserves A/B bits, clears Enable and direction |
| `L004C -> L3062` | full output latch write | physical pin mapping bench-gated |

## Source-Proven Enable Chain

```text
0x91A3  LDAB L000A       ; mode/output byte
0x91A5  LDAA L00A7       ; BAT VOLTS, VDC/10
0x91A7  CMPA #169        ; 16.9 VDC threshold
0x91AB  ANDB #$EF        ; clear bit4 candidate if above threshold

0x91B3  CMPA L4EB6       ; low-voltage threshold candidate
0x91B8  BSET L003E,#$04  ; set low battery/protection flag

0x91BD  BCLR L003E,#$04  ; clear low battery/protection flag
0x91C0  ORAB #$10        ; set bit4 candidate

0x9200  STAB L000A       ; commit mode byte
0x9203  LDAA L004C
0x9205  ANDA #$E3        ; clear bits2/3/4 in output shadow
0x9207  ANDB #$1C        ; isolate L000A bits2/3/4
0x920A  STAA L004C       ; commit output shadow

0xF40F  LDAA L004C
0xF411  STAA L3062       ; full-byte hardware latch write
```

## Enable Decision Model

```text
if L00A7 > 169:
  clear L000A bit4 candidate
  set L003E bit2 low-battery/protection flag path
  skip phase/update compare

else if L0044 bit4 set:
  clear L003E bit2
  set L000A bit4 candidate

else if L00A7 > L4EB6:
  clear L003E bit2
  set L000A bit4 candidate

else:
  set L003E bit2 low-battery/protection flag
  skip ORAB #$10
```

Current interpretation: `L00A7` is proven as the compared variable. `#169` is the high voltage threshold candidate. `L4EB6` is the low voltage threshold candidate. `L003E bit2` is the low-battery/protection flag associated with this gate.

## Enable Is Not Step-Pulsed In The Source Path

When `desired == actual`, the no-step path clears direction bit0 but does not clear bit4. Therefore Enable remains governed by the voltage/status gate, not by step demand.

If the voltage gate fails, the code branches to `L9200` before desired/actual compare and A/B ring update. That means the source path can hold/commit mode state without stepping when Enable is not allowed.

## Setup / Bad-Shutdown Clear Path

A separate setup path calls `L93C5` from the bad-shutdown branch:

```text
0x9272  BRSET L0004,#$08,L927B   ; bad shutdown candidate
0x927B  JSR L93C5

0x93C5  BRSET L0009,#$01,L93CF   ; skip if IAC reset in work
0x93C9  LDAA L000A
0x93CB  ANDA #$0C                ; preserve A/B only
0x93CD  STAA L000A               ; clear Enable and direction
```

This supports treating Enable as a startup/setup/fault gate rather than a per-step pulse.

## Contract Rows

| Stage | PC | Instruction | Symbol | Role | Enable condition | Disable condition | Confidence |
|---|---|---|---|---|---|---|---|
| load_enable_mode_byte | `0x91A3` | `LDAB L000A` | `L000A bit4` | iac_enable_bit | preserved until voltage/status gate decides | may be cleared by voltage/setup gates | high_static |
| load_battery_voltage | `0x91A5` | `LDAA L00A7` | `L00A7` | iac_voltage_sufficient_gate | voltage value loaded for comparison | out-of-range voltage branches clear/skip enable | high_static |
| high_voltage_threshold | `0x91A7-0x91AD` | `CMPA/BLS/ANDB/BRA #169 / L91AF / #$EF / L91B8` | `L000A bit4` | iac_enable_clear | L00A7 <= 169 continues to normal gate | L00A7 > 169 clears bit4 and sets low-battery/protection flag path | high_static |
| ignition_off_bypass_gate | `0x91AF` | `BRSET L0044,#$10,L91BD` | `L0044 bit4` | iac_enable_set | L0044 bit4 set branches to enable/good path | if not set, low-voltage threshold L4EB6 is checked | medium_static |
| low_voltage_threshold | `0x91B3-0x91B8` | `CMPA/BHI/BSET L4EB6 / L91BD / L003E,#$04` | `L4EB6; L003E bit2` | iac_voltage_low_disable | L00A7 > L4EB6 branches to good path and sets Enable | L00A7 <= L4EB6 sets L003E bit2 low battery and skips ORAB #$10 | high_static |
| good_voltage_enable_set | `0x91BD-0x91C0` | `BCLR/ORAB L003E,#$04 / #$10` | `L000A bit4; L003E bit2` | iac_enable_set | voltage/status gate passes | not applicable in this row | high_static |
| no_step_enable_refresh | `0x91C2-0x91CA` | `LDAA/CMPA/BNE/ANDB/BRA L0007 / L0008 / L91CC / #$FE / L9200` | `L000A bit4` | iac_enable_bit | Enable remains set if voltage/status gate passed | no-step does not clear Enable | high_static |
| mode_byte_commit | `0x9200` | `STAB L000A` | `L000A bit4` | iac_enable_bit | committed if set in B | committed clear if cleared/skipped | high_static |
| shadow_field_update | `0x9203-0x920A` | `LDAA/ANDA/ANDB/ABA/STAA L004C / #$E3 / #$1C / L004C` | `L004C bit4` | iac_output_shadow_update | L000A bit4 copied into L004C bit4 | cleared L000A bit4 clears L004C bit4 | high_static |
| hardware_latch_write | `0xF40F-0xF411` | `LDAA/STAA L004C / L3062` | `L3062 bit4 candidate` | iac_latch_write | physical bit4 follows L004C bit4 if mapping is correct | physical bit4 clears with L004C bit4 if mapping is correct | high_static_for_latch_write_medium_for_physical_enable |
| bad_shutdown_setup_clear | `0x9272-0x927B;0x93C5-0x93CD` | `BRSET/JSR/LDAA/ANDA/STAA L0004,#$08,L927B / L93C5 / L000A / #$0C / L000A` | `L000A bit4` | iac_reset_disable | not enabled by this path | if L0009 bit0 clear, L000A is reduced to A/B bits only, clearing Enable and direction | high_static |

## Required New-OS Behavior

A future IAC module must reproduce or explicitly replace:

1. battery/driver voltage qualification before asserting Enable
2. bit4 set/clear behavior in the IAC mode byte
3. `L000A bit4 -> L004C bit4` shadow propagation
4. `L004C -> L3062` physical latch behavior if bit4 is confirmed as Enable
5. setup/bad-shutdown clear behavior or an equivalent safe default
6. low-battery/protection flag behavior if it affects other modules

## Open Bench Questions

- Is `L3062 bit4` physically the IAC driver Enable pin?
- Does Enable remain asserted while A/B holds or steps normally?
- Does high-voltage or low-voltage testing deassert the physical Enable pin?
- Does a setup/bad-shutdown clear produce a physical Enable deassertion?
- Does clearing Enable prevent physical IAC motion even if A/B bits change?
- Does the external driver have additional health/fault behavior not visible in source?

## Out Of Scope For This Contract

```text
A/B phase sequence
park/reset/home movement
desired IAC calculation
idle-speed strategy
step cadence/rate-limit equation
IAC writer implementation
```

## Next Contract

```text
IAC_INIT_PARK_CONTRACT
```
