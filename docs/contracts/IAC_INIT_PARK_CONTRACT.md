# IAC Init / Park Contract

## Purpose

Document how stock code establishes IAC actual position and startup/crank target state.

This contract does not define idle strategy and does not create an IAC writer.

## Source Contracts

- `IAC_IDLE_AIR_OUTPUT_CONTRACT.md`
- `IAC_PHASE_SEQUENCE_CONTRACT.md`
- `IAC_ENABLE_FAULT_GATE_CONTRACT.md`

## Known Boundary

```text
L0007 = actual/present IAC position
L0008 = desired/target IAC position
L0009 bit0 = IAC motor reset-in-work candidate
L0009 bit2 = R/S requested candidate
L000A = IAC mode/output state byte
L4EB0 = 145 steps IAC park down
L4EB6 = 10.5 VDC minimum battery for IAC operations
```

## Working Hypothesis

Stock code makes `L0007` trustworthy through a reset-in-work / home-to-zero process and through conservative seeding when nonvolatile memory is invalid.

Park-down is not a direct actual-position write in the normal shutdown path. It is primarily a desired-position request:

```text
L4EB0 = 145 steps park down
A = L4EB0
JMP L9899
L9899: STAA L0008
```

The actual count `L0007` then moves toward `L0008` through the already-mapped desired/actual compare and A/B phase sequence if Enable and cadence allow movement.

## Required Questions

- What writes `L0007` before normal idle control?
- What writes `L0008` before crank/run?
- Is there a park/homing overstep?
- Is there a bad-shutdown recovery path?
- Is there a reset-in-work skip path?
- Does low voltage block park movement?
- Is Enable asserted before park motion?
- What value is loaded as actual after park completes?

## Static Source Sequence

### Startup setup call

```text
0x73DB  JSR L925E        ; GO SET UP IAC
```

### Setup routine / nonvolatile fail seed

```text
0x925E  LDAA L4EF2        ; 16% TPS upper limit for closed-loop IAC
0x9263  STAA L0885
0x9266  BRCLR L0046,#$40,L9272  ; branch if nonvolatile memory not bombed
0x926A  LDAA L4EB0        ; 145 steps IAC park down
0x926D  STAA L0007        ; IAC motor position
0x926F  JSR L92A4         ; seed IAC learned/default cells
```

### Bad-shutdown branch

```text
0x9272  BRSET L0004,#$08,L927B  ; bad shutdown
0x9276  JSR L92F1               ; normal shutdown/setup path
0x927B  JSR L93C5               ; bad-shutdown setup clear
```

### Reset-in-work service

```text
0x93E1  BRCLR L0009,#$01,L93F9  ; if reset not in work, skip
0x93E5  CLR L0008                ; desired target = 0 while reset is active
0x93E8  TST L0007                ; actual position
0x93EB  BEQ L93F0                ; if actual reached zero, finish reset
0x93ED  JMP L989B                ; otherwise return and keep reset active
0x93F0  BCLR L0009,#$01          ; clear reset-in-work
0x93F3  BSET L0009,#$04          ; set R/S requested candidate
0x93F6  JSR L92A4                ; reseed IAC learned/default cells
```

### Ignition-off park-down request

```text
0x93F9  BRCLR L0044,#$10,L940A  ; if not ignition-off, continue run/start logic
0x93FD  BRCLR L0009,#$04,L9407  ; if R/S not requested, skip park request
0x9401  LDAA L4EB0               ; 145 steps IAC park down
0x9404  JMP L9899                ; write desired position
```

### Common desired-position sink

```text
0x9899  STAA L0008
0x989B  RTS
```

## Static Classification

```text
PARK-A: partially supported
  The reset-in-work path drives desired to zero until actual reaches zero. That is a homing/reset process, but physical direction and mechanical stop must be bench-proven.

PARK-B: supported as a retained-state path
  If nonvolatile memory is not bombed and reset-in-work is not active, stock code does not blindly overwrite L0007 at every key-on.

PARK-C: supported
  Bad-shutdown and reset-in-work flags change setup behavior.

PARK-D: supported
  Stock loads L0008 desired/target using L9899. L4EB0 park-down requests write desired, not actual.

PARK-E: bench-gated
  Source says IAC operations are voltage-gated elsewhere. This contract does not prove physical Enable state during park motion.

PARK-F: not resolved for physical direction
  Static code proves target values and flags, but bench must determine open/closed direction and real mechanical stop behavior.
```

## Contract Rows

| Stage | PC | Instruction | Symbol | Role | Actual effect | Desired effect | Confidence |
|---|---|---|---|---|---|---|---|
| startup_iac_setup_entry | `0x73DB;0x925E-0x9263` | `JSR/LDAA/ASLA/ASLA/STAA L925E / L4EF2 / L0885` | `L0885` | iac_startup_setup_threshold | none | none | high_static |
| nonvolatile_memory_bombed_actual_seed | `0x9266-0x926F` | `BRCLR/LDAA/STAA/JSR L0046,#$40,L9272 / L4EB0 / L0007 / L92A4` | `L0007` | iac_actual_seed_after_nvm_fail | L0007 := L4EB0 (145) | none in this row | high_static |
| nonvolatile_memory_bombed_idle_cell_seed | `0x926F;0x92A4-0x92F0` | `JSR/LDAA/CMPA/LDAB/STAB/... L92A4; L4EB1/L4EB2/L4EB3/L4EB4/L4EB5 -> L029D/L029F/L02A0/L02A2/L02A7/L02A9/L02AA/L02AC/L02B1` | `IAC learned/integral cells` | iac_default_idle_cell_seed | none direct | none direct | high_static |
| bad_shutdown_branch_select | `0x9272-0x927B` | `BRSET/JSR/BRA/JSR L0004,#$08,L927B / L92F1 / L927E / L93C5` | `L0004 bit3` | iac_bad_shutdown_recovery_branch | none direct | none direct | high_static |
| bad_shutdown_setup_clear | `0x93C5-0x93CD` | `BRSET/LDAA/ANDA/STAA L0009,#$01,L93CF / L000A / #$0C / L000A` | `L000A` | iac_setup_clear_preserve_phase | none | none | high_static |
| reset_in_work_service_entry | `0x93E1-0x93ED` | `BRCLR/CLR/TST/BEQ/JMP L0009,#$01,L93F9 / L0008 / L0007 / L93F0 / L989B` | `L0009 bit0; L0008; L0007` | iac_reset_in_work_countdown_gate | tests L0007; if nonzero exits without clearing reset-in-work | L0008 := 0 while reset is in work | high_static |
| reset_complete_seed_and_request | `0x93F0-0x93F6` | `BCLR/BSET/JSR L0009,#$01 / L0009,#$04 / L92A4` | `L0009 bit0; L0009 bit2` | iac_reset_complete_seed | L0007 is accepted as zero/home | L0008 already zero from prior row | high_static |
| ignition_off_park_down_request | `0x93F9-0x9404` | `BRCLR/BRCLR/LDAA/JMP L0044,#$10,L940A / L0009,#$04,L9407 / L4EB0 / L9899` | `L0008` | iac_park_down_desired_request | none direct; later phase logic will move actual toward desired | L0008 := L4EB0 (145) | high_static |
| cold_prior_to_start_park_request | `0x9517-0x9534` | `LDAA/CMPA/BCS/LDAA/JMP L0006 / L4E91 / L9531 / L4EB0 / L9899` | `L0008` | iac_cold_start_park_request | none direct | L0008 := L4EB0 (145) | medium_static |
| desired_position_common_sink | `0x9883-0x989B` | `LDX/LSRD/.../STAA/RTS #L4E92 / computed table result / L0008` | `L0008` | iac_desired_position_sink | none direct | L0008 := A | high_static |

## Minimal-OS Requirement

A minimal OS must not step the IAC based on `L0007` until `L0007` is known valid or deliberately seeded.

Minimum safe options:

```text
Option 1: perform a stock-like reset/home sequence
  set reset-in-work
  command desired = 0
  step until actual reaches zero or timeout/overstep is complete
  clear reset-in-work
  seed actual as known-home

Option 2: deliberately seed actual to a conservative park-down value
  L0007 := park_down_max
  command desired to a known crank/start target
  accept that physical agreement requires bench proof or prior park

Option 3: retain previous actual position only if nonvolatile/retained RAM validity is proven
```

## Open Bench Questions

- Does desired `0` drive the IAC closed or open physically?
- Does `L4EB0 = 145` represent max-open, max-closed, or stock park-down count relative to airflow?
- During reset-in-work, does the motor physically overdrive to a stop before `L0007` reaches zero?
- Does `L0007` decrement/increment exactly one count per physical step during reset?
- Is Enable asserted during reset/park movement, and is it blocked at low voltage?
- Does bad-shutdown recovery force a new reset/home or only clear output mode state?
- What crank/start desired IAC value is used after park/reset completes?

## Out Of Scope For This Contract

```text
A/B phase order
Enable voltage/fault gate
closed-loop idle strategy
desired idle RPM calculation
IAC writer implementation
calibration-source indexing
```

## Next Contract

After this pass, the IAC side is ready for a source-side boundary README:

```text
source/minimal_os/iac/README.md
```

The calibration side remains parked until:

```text
CALIBRATION_SOURCE_INDEX
```
