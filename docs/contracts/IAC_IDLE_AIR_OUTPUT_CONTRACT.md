# IAC Idle Air Output Contract

## Purpose

Map the IAC Enable/A/B output contract from source. This is a source-proof pass for desired/actual position, A/B ring stepping, driver enable gating, output latch path, and step cadence gates.

No IAC writer is created by this contract.

## Working Hypothesis

The IAC driver has three CPU-side command inputs:

```text
Enable
A
B
```

Enable is likely a driver-enable/health gate. It is expected to assert after startup voltage/driver conditions are acceptable and remain asserted during normal operation. It may deassert for fault, reset, test, or driver-protection behavior.

A and B form a 2-bit step-state command. Direction is probably determined by choosing the next neighbor in a four-state ring, not by a dedicated direction signal.

Candidate stable states:

```text
00 = none
10 = A
11 = A+B
01 = B
```

Candidate sequence one direction:

```text
A -> A+B -> B -> none -> A
```

Candidate sequence opposite direction:

```text
A -> none -> B -> A+B -> A
```

The source must prove or disprove this.

## Source-Proven Core Result

```text
actual/present position = L0007
desired/target position = L0008
mode/output state byte  = L000A
direction bit           = L000A bit0
A/B ring bits           = L000A bits2/3
Enable candidate        = L000A bit4
output shadow           = L004C bits2/3/4
hardware latch write    = L004C -> L3062
```

The current source pass does not prove `$3FFC` as the primary IAC A/B/Enable output path. `$3FFC` remains an I/O-D-port suspect for other init/diagnostic paths, while the source-proven IAC path is `L000A -> L004C -> L3062`.

## Position/Error Logic

| PC | Instruction | Role | Static meaning | Confidence |
|---|---|---|---|---|
| `0x91C2` | `LDAA L0007` | actual position | load present IAC motor position | high |
| `0x91C4` | `CMPA L0008` | desired compare | compare actual against desired/target | high |
| `0x91C6` | `BNE L91CC` | no-step gate | equal means no step/count update | high |
| `0x91D4` | `BCC L91DF` | direction branch | actual >= desired path | high |
| `0x91D6/0x91DC` | `ANDB #$FE` / `INCA` | direction 0 path | actual < desired, increment actual after direction matched | high |
| `0x91DF/0x91E5` | `ORAB #$01` / `DECA` | direction 1 path | actual > desired, decrement actual after direction matched | high |
| `0x91E6` | `STAA L0007` | actual update | commit +1/-1 software position update | high |

Important behavior: when direction changes, the code can update the direction bit without immediately changing the actual count. This looks like a safe phase/direction reversal behavior.

## A/B Ring Logic

A/B source bits:

```text
L000A bit2 = A candidate
L000A bit3 = B candidate
```

Ring operation:

```text
0x91E8  BRSET L000A,#$0C,L91F6   ; both A+B set
0x91EC  BRCLR L000A,#$0C,L91F6   ; neither A nor B set
0x91F0  BITB #$01                ; direction bit
0x91FA  EORB #$04                ; toggle bit2/A candidate
0x91FE  EORB #$08                ; toggle bit3/B candidate
```

If bit2=A and bit3=B, static ring candidates are:

```text
direction bit0 = 0:
  none -> A -> A+B -> B -> none

direction bit0 = 1:
  none -> B -> A+B -> A -> none
```

This proves the A/B ring shape statically. Bench still must confirm which physical pin is A and which is B, and whether count-positive corresponds to open or closed airflow.

## Enable Gate

Enable candidate:

```text
L000A bit4 -> L004C bit4 -> L3062 bit4 candidate
```

Static evidence:

```text
0x91A7  CMPA #169     ; 16.9 V battery gate
0x91AB  ANDB #$EF     ; clear bit4 candidate on failed/high voltage path
0x91C0  ORAB #$10     ; set bit4 candidate on good path
```

Current classification: Enable is a driver-enable/health/voltage gate candidate, not a per-step pulse. Bench must confirm whether it stays asserted while A/B phase changes.

## A/B Update Atomicity

AB and BA are the same stable state electrically, but transition path can matter.

Static classification:

```text
update type: shadow full-field update, then full-byte hardware latch write

0x9200  STAB L000A    ; commit mode byte
0x9203  LDAA L004C    ; load output shadow
0x9205  ANDA #$E3     ; clear bits2/3/4
0x9207  ANDB #$1C     ; isolate L000A bits2/3/4
0x9209  ABA           ; merge into output shadow
0x920A  STAA L004C    ; shadow commit under SEI/CLI

0xF40F  LDAA L004C
0xF411  STAA L3062    ; hardware output latch write
```

The source does not show separate hardware `BSET/BCLR` operations for the A/B bits in the normal IAC step path. The normal path updates `L004C` as a masked field, then the board output service writes the full byte to `L3062`.

Bench classification still required:

```text
Do L3062 bits2/3/4 physically equal A/B/Enable?
Does any intermediate transient appear on the pins?
Is LF400 called at a cadence that can delay the physical step edge after L004C is updated?
```

## Step Cadence / Gating

Known gates:

```text
L0009 bit0 = IAC MOTOR Reset IN WORK
L0002 bits0/1 = major loop counter gate during reset-in-work path
L0864 = closed-loop enable delay after IAC qualifications
```

Cadence is not fully reduced to a timer equation in this pass. The step output routine is source-mapped; a follow-on `IAC_PHASE_SEQUENCE_CONTRACT` should classify step cadence and caller rate.

## Contract Rows

| Stage | PC | Instruction | Symbol | Role | Required? | Confidence |
|---|---|---|---|---|---|---|
| load_mode_word | `0x91A3` | `LDAB L000A` | `L000A` | iac_ab_state | yes | high_static |
| driver_voltage_high_gate | `0x91A7-0x91AD` | `CMPA/ANDB #169 / #$EF` | `L000A bit4` | iac_driver_enable_voltage_gate | yes | medium_high_static |
| driver_enable_set_good_voltage | `0x91BD-0x91C0` | `BCLR/ORAB L003E,#$04 / #$10` | `L000A bit4` | iac_enable_bit | yes | medium_high_static |
| load_actual_position | `0x91C2` | `LDAA L0007` | `L0007` | iac_actual_position | yes | high_static |
| compare_actual_to_desired | `0x91C4` | `CMPA L0008` | `L0008` | iac_desired_position | yes | high_static |
| no_step_equal | `0x91C6-0x91CA` | `BNE/ANDB/BRA L91CC / #$FE / L9200` | `L000A bit0` | iac_no_step | yes | high_static |
| reset_in_work_gate | `0x91CC-0x91D0` | `BRCLR/BRSET L0009,#$01 / L0002,#$03` | `L0009 bit0; L0002` | iac_step_cadence | yes | medium_high_static |
| actual_less_than_desired_direction | `0x91D4-0x91DD` | `BCC/ANDB/BRSET/INCA L91DF / #$FE / L000A,#$01 / INCA` | `L000A bit0; L0007` | iac_step_open_candidate | yes | high_static |
| actual_greater_than_desired_direction | `0x91DF-0x91E6` | `ORAB/BRCLR/DECA/STAA #$01 / L000A,#$01 / DECA / L0007` | `L000A bit0; L0007` | iac_step_close_candidate | yes | high_static |
| actual_position_store | `0x91E6` | `STAA L0007` | `L0007` | iac_actual_position | yes | high_static |
| ab_state_equal_test | `0x91E8-0x91EC` | `BRSET/BRCLR L000A,#$0C` | `L000A bits2-3` | iac_ab_state | yes | high_static |
| ab_toggle_bit2 | `0x91FA` | `EORB #$04` | `L000A bit2` | iac_a_bit | yes | high_static |
| ab_toggle_bit3 | `0x91FE` | `EORB #$08` | `L000A bit3` | iac_b_bit | yes | high_static |
| store_iac_mode_word | `0x9200` | `STAB L000A` | `L000A` | iac_ab_state | yes | high_static |
| shadow_latch_mask_clear | `0x9203-0x9207` | `LDAA/ANDA/ANDB L004C / #$E3 / #$1C` | `L004C; L000A bits2-4` | iac_full_latch_write | yes | high_static |
| shadow_latch_commit | `0x9209-0x920A` | `ABA/STAA L004C` | `L004C bits2-4` | iac_full_latch_write | yes | high_static |
| hardware_latch_write | `0xF40F-0xF411` | `LDAA/STAA L004C / L3062` | `L3062` | iac_full_latch_write | yes | high_static_for_latch_write_medium_for_bit_roles |
| startup_park_position_load | `0x926A-0x926D` | `LDAA/STAA L4EB0 / L0007` | `L0007` | iac_actual_position | yes | high_static |
| desired_position_seed | `0x929C-0x929E` | `LDAA/STAA L0007 / L0008` | `L0008` | iac_desired_position | yes | high_static |
| reset_in_work_set_and_zero | `0xA3FA-0xA404` | `BSET/STAA/STAA L0009,#$01 / L0008 / L0007` | `L0009 bit0; L0008; L0007` | iac_driver_disable_fault | yes | high_static |
| strategy_actual_decrement | `0x9B10` | `DEC L0007` | `L0007` | iac_actual_decrement | strategy_dependency_only | high_static |
| strategy_actual_increment | `0x9BD6` | `INC L0007` | `L0007` | iac_actual_increment | strategy_dependency_only | high_static |
| not_primary_3ffc_candidate | `0x713A/0x714A/0xFA43` | `STX/STD L3FFC` | `L3FFC` | unknown_iac_state | no_unless_later_dependency_proves | medium_static |

## Required New-OS Behavior

The minimal OS must reproduce or explicitly replace:

1. desired/actual compare using `L0007`/`L0008` equivalent state
2. no-step behavior when actual equals desired
3. safe direction reversal behavior before count update
4. A/B four-state ring sequencing
5. Enable gating behavior or a proven-safe replacement
6. shadow/latch update behavior into the physical output port
7. step cadence / next-step eligibility
8. reset/park/home behavior

## Open Questions

- Which physical pins are L3062 bits2/3/4?
- Does bit2=A and bit3=B match the harness/pinout, or are names swapped?
- Does actual-count +1 mean open or closed airflow?
- Is Enable bit4 required continuously during normal stepping?
- Does any fault path deassert Enable besides the voltage gate?
- What exact cadence/timer permits the next step?
- Is the IAC reset/park sequence simply a count model, or does it force steps until stall/seat?

## Next Contracts

If bench/source review preserves this model, split follow-on work into:

```text
IAC_PHASE_SEQUENCE_CONTRACT
IAC_ENABLE_FAULT_GATE_CONTRACT
IAC_INIT_PARK_CONTRACT
```

No IAC writer yet.
