# IAC Phase Sequence Contract

## Purpose

Document the IAC A/B ring sequence used to move the stepper driver one step at a time.

This contract does not define Enable behavior, park/reset behavior, idle strategy, or desired IAC calculation. It does not create an IAC writer.

## Proven Source State

| Symbol | Role |
|---|---|
| `L0007` | actual/present IAC position |
| `L0008` | desired/target IAC position |
| `L000A bit0` | direction candidate |
| `L000A bit2` | A candidate |
| `L000A bit3` | B candidate |
| `L004C bits2/3` | output shadow |
| `L3062` | hardware latch write via `L004C` service |

## Static Ring

Bit values:

```text
none = 0x00 on bits2/3
A    = 0x04
B    = 0x08
A+B  = 0x0C
```

Direction bit clear:

```text
none -> A -> A+B -> B -> none
0x00 -> 0x04 -> 0x0C -> 0x08 -> 0x00
```

Direction bit set:

```text
none -> B -> A+B -> A -> none
0x00 -> 0x08 -> 0x0C -> 0x04 -> 0x00
```

Bench still has to decide whether source `A` is physically A or B at the driver pins, and whether count increment means open or closed airflow.

## Source Sequence

```text
0x91C2  LDAA L0007       ; actual/present position
0x91C4  CMPA L0008       ; compare actual to desired
0x91C6  BNE L91CC        ; equal means no step/count change

0x91D4  BCC L91DF        ; actual >= desired path
0x91D6  ANDB #$FE        ; direction bit0 clear candidate
0x91DC  INCA             ; actual count +1 after direction matched

0x91DF  ORAB #$01        ; direction bit0 set candidate
0x91E5  DECA             ; actual count -1 after direction matched
0x91E6  STAA L0007       ; commit actual count

0x91E8  BRSET L000A,#$0C,L91F6
0x91EC  BRCLR L000A,#$0C,L91F6
0x91F0  BITB #$01        ; choose ring neighbor from direction
0x91FA  EORB #$04        ; toggle bit2/A candidate
0x91FE  EORB #$08        ; toggle bit3/B candidate
0x9200  STAB L000A       ; commit phase state
```

## Phase Transition Table

| Direction bit | State before | A/B bits before | State after | A/B bits after | Count delta |
|---:|---|---:|---|---:|---|
| 0 | none | `0x00` | A | `0x04` | `+1` after direction matched |
| 0 | A | `0x04` | A+B | `0x0C` | `+1` |
| 0 | A+B | `0x0C` | B | `0x08` | `+1` |
| 0 | B | `0x08` | none | `0x00` | `+1` |
| 1 | none | `0x00` | B | `0x08` | `-1` after direction matched |
| 1 | B | `0x08` | A+B | `0x0C` | `-1` |
| 1 | A+B | `0x0C` | A | `0x04` | `-1` |
| 1 | A | `0x04` | none | `0x00` | `-1` |

Direction reversal can update `L000A bit0` before the actual count is changed. Treat the first reversal edge as a possible zero-count-delta phase/authority change until bench confirms behavior.

## Output Shadow / Latch Path

The phase bits are not written directly with hardware `BSET/BCLR` in the normal path.

```text
0x9203  LDAA L004C
0x9205  ANDA #$E3      ; clear L004C bits2/3/4
0x9207  ANDB #$1C      ; isolate L000A bits2/3/4
0x9209  ABA            ; merge
0x920A  STAA L004C     ; output shadow update

0xF40F  LDAA L004C
0xF411  STAA L3062     ; full-byte hardware latch write
```

Phase atomicity is therefore statically classified as shadow full-field update followed by full-byte latch write. Physical pin timing remains bench-gated.

## Contract Rows

| Stage | PC | Direction | Before | After | Count delta | Role | Confidence |
|---|---|---:|---|---|---|---|---|
| actual_desired_compare | `0x91C2-0x91C6` | unchanged if equal | any | hold if actual == desired | 0 if equal | desired_actual_compare | high_static |
| direction0_count_update | `0x91D4-0x91DD` | 0 | actual < desired | phase ring advances if direction already matched | +1 after direction matched; 0 on first reversal | direction0_step_candidate | high_static |
| direction1_count_update | `0x91DF-0x91E6` | 1 | actual > desired | phase ring reverses if direction already matched | -1 after direction matched; 0 on first reversal | direction1_step_candidate | high_static |
| dir0_none_to_a | `0x91E8-0x91FA` | 0 | none | A candidate | +1 after direction matched | iac_phase_ring_forward | high_static |
| dir0_a_to_ab | `0x91E8-0x91FA` | 0 | A candidate | A+B candidate | +1 | iac_phase_ring_forward | high_static |
| dir0_ab_to_b | `0x91E8-0x91FA` | 0 | A+B candidate | B candidate | +1 | iac_phase_ring_forward | high_static |
| dir0_b_to_none | `0x91E8-0x91FE` | 0 | B candidate | none | +1 | iac_phase_ring_forward | high_static |
| dir1_none_to_b | `0x91E8-0x91FE` | 1 | none | B candidate | -1 after direction matched | iac_phase_ring_reverse | high_static |
| dir1_b_to_ab | `0x91E8-0x91FA` | 1 | B candidate | A+B candidate | -1 | iac_phase_ring_reverse | high_static |
| dir1_ab_to_a | `0x91E8-0x91FE` | 1 | A+B candidate | A candidate | -1 | iac_phase_ring_reverse | high_static |
| dir1_a_to_none | `0x91E8-0x91FA` | 1 | A candidate | none | -1 | iac_phase_ring_reverse | high_static |
| shadow_to_latch | `0x9203-0x920A;0xF40F-0xF411` | not output directly | new L000A bits2/3 | L004C bits2/3 then L3062 bits2/3 candidate | already applied before latch update | phase_latch_atomicity | high_static_for_source_medium_for_physical_pins |

## Required New-OS Behavior

A future IAC module must reproduce or explicitly replace:

1. no-step hold when `actual == desired`
2. direction-bit selection from desired/actual sign
3. safe direction reversal before count update
4. four-state A/B ring sequence
5. shadow update of A/B bits
6. full latch write path to the physical driver input

## Open Bench Questions

- Is bit2 physically A and bit3 physically B, or swapped?
- Does actual count increment open or close the IAC?
- Does one latch write produce a clean atomic A/B transition at the driver input?
- Does every source step correspond to one physical motor step?
- Does `L3062` update immediately after `L004C`, or at a delayed output-service cadence?

## Out Of Scope For This Contract

```text
Enable/fault behavior
park/reset/home behavior
desired IAC calculation
idle-speed strategy
step cadence/rate-limit equation
IAC writer implementation
```
