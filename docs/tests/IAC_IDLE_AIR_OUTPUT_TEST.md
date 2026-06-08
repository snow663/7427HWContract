# IAC Idle Air Output Test

## Goal

Prove the source-mapped IAC Enable/A/B output contract on hardware.

The source pass maps this path:

```text
L0007 actual/present position
L0008 desired/target position
L000A bit0 direction
L000A bits2/3 A/B ring candidates
L000A bit4 Enable candidate
L004C bits2/3/4 output shadow
L3062 hardware latch write
```

Bench testing must prove which physical pins are Enable, A, and B, whether the A/B ring matches the source model, and whether Enable is a continuous driver gate or a step-pulsed command.

## Required Signals

- IAC Enable candidate
- IAC A candidate
- IAC B candidate
- L3062 bits2/3/4 if bus trace is available
- L004C shadow byte if RAM trace is available
- L000A mode/output byte if RAM trace is available
- L0007 actual/present position
- L0008 desired/target position
- L0009 bit0 IAC reset in work
- L0002 major loop counter
- REF/RPM state if cadence depends on run loop
- battery/driver voltage state

## Core Test Matrix

| Test | Condition | Expected if source model is correct |
|---|---|---|
| desired = actual | force or observe equal L0007/L0008 | no count update; A/B holds; Enable remains governed by voltage gate |
| desired > actual | force L0008 greater than L0007 | direction bit0 clear candidate; actual increments after direction matched; A/B follows one ring direction |
| desired < actual | force L0008 less than L0007 | direction bit0 set candidate; actual decrements after direction matched; A/B follows opposite ring direction |
| direction reversal | switch desired across actual | direction bit changes before count update; avoids immediate wrong-way count step |
| voltage high/fault | force/simulate voltage gate if possible | Enable bit4 deasserts or changes according to source gate |
| reset in work | force/observe L0009 bit0 | stepping cadence gated by L0002 major-loop counter |
| output latch delay | trace L004C then L3062 | physical output follows L004C through LF400 latch service |

## Ring Proof Table

Record this table from scope and trace:

| current_state | desired-actual sign | next_state | actual_count_delta | latch_write | notes |
|---|---|---|---|---|---|
| none | positive | TBD | +1 or 0 on reversal | full/bitwise | |
| A | positive | TBD | +1 | full/bitwise | |
| A+B | positive | TBD | +1 | full/bitwise | |
| B | positive | TBD | +1 | full/bitwise | |
| none | negative | TBD | -1 or 0 on reversal | full/bitwise | |
| A | negative | TBD | -1 | full/bitwise | |
| A+B | negative | TBD | -1 | full/bitwise | |
| B | negative | TBD | -1 | full/bitwise | |

Static source candidate if bit2=A and bit3=B:

```text
direction bit0 = 0:
  none -> A -> A+B -> B -> none

direction bit0 = 1:
  none -> B -> A+B -> A -> none
```

## Atomicity Test

The source predicts:

```text
L000A mode byte update
-> SEI
-> L004C masked field update of bits2/3/4
-> CLI
-> later full-byte STAA L3062
```

Scope checks:

1. Do A/B change together at the physical pins or does one pin visibly lead?
2. Does the output pass through invalid intermediate states?
3. Is the observed hardware update a full-latch write or bitwise update?
4. Does L3062 update at a delayed cadence after L004C?

Classification:

```text
IAC-ATOMIC-A:
  full latch write; no observable invalid intermediate state

IAC-ATOMIC-B:
  full latch write but one pin physically slews/delays enough to matter

IAC-ATOMIC-C:
  source shadow is full-field, but hardware/driver behaves like bitwise transition

IAC-ATOMIC-D:
  static interpretation incomplete
```

## Enable Test

Source classification:

```text
Enable candidate = L000A bit4 -> L004C bit4 -> L3062 bit4 candidate
```

Bench checks:

1. Enable asserts after acceptable battery/driver voltage state.
2. Enable stays asserted while A/B phase changes during normal stepping.
3. Enable deasserts on voltage/fault/reset behavior if such condition can be safely simulated.
4. Enable is not pulsed once per step unless bench disproves the source classification.

Classification:

```text
IAC-EN-A:
  Enable is continuous driver/health gate.

IAC-EN-B:
  Enable is step-pulsed or cadence-pulsed.

IAC-EN-C:
  Enable is fault/reset only.

IAC-EN-D:
  bit4 is not physical Enable.
```

## Data To Record

```csv
test_name,event_index,l0007_actual,l0008_desired,error_sign,l000a_before,l000a_after,l004c_before,l004c_after,l3062_write,enable_state,a_state,b_state,actual_delta,reset_in_work,l0002,cadence_ms,path_result,notes
```

## Pass Criteria

```text
PASS:
  L0007/L0008 desired-actual compare controls direction/no-step behavior.
  L000A bits2/3 form a four-state A/B ring.
  Direction bit0 reverses ring direction.
  L000A bit4/L004C bit4/L3062 bit4 behavior is classified.
  L004C -> L3062 output latch path is confirmed.
  Step cadence gate is identified well enough to split the next contracts.
```

## Fail / Rework Criteria

```text
REWORK:
  physical A/B pins do not match L3062 bits2/3 candidate.
  A/B sequence is not a four-state ring.
  desired/actual compare does not correlate with actual physical step direction.
  Enable behavior is not bit4 or is not sourced from L004C.
  a different $3Fxx or 306x register directly drives IAC outputs.
```

## Next Contracts

If the source and bench agree on the ring model:

```text
IAC_PHASE_SEQUENCE_CONTRACT
IAC_ENABLE_FAULT_GATE_CONTRACT
IAC_INIT_PARK_CONTRACT
```

Still no IAC writer until those contracts define phase sequence, enable/fault behavior, and reset/park behavior.
