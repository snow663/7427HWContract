# IAC Phase Sequence Test

## Goal

Bench-prove the source-mapped IAC A/B phase sequence.

This test only covers phase/ring behavior. Enable/fault behavior and park/reset behavior are separate contracts.

## Required Signals / Trace Values

- physical IAC A candidate
- physical IAC B candidate
- `L000A bit0` direction
- `L000A bits2/3` phase state
- `L004C bits2/3` output shadow
- `L3062 bits2/3` latch write if bus trace is available
- `L0007` actual/present count
- `L0008` desired/target count

## Static Ring Candidate

If source bit2 is physical A and bit3 is physical B:

```text
direction bit0 = 0:
  none -> A -> A+B -> B -> none
  0x00 -> 0x04 -> 0x0C -> 0x08 -> 0x00

direction bit0 = 1:
  none -> B -> A+B -> A -> none
  0x00 -> 0x08 -> 0x0C -> 0x04 -> 0x00
```

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| hold/no step | force or observe `L0007 == L0008` | A/B state holds; actual count delta is zero |
| direction0 ring | force `L0007 < L0008` after direction is settled | phase follows `0x00 -> 0x04 -> 0x0C -> 0x08 -> 0x00`; count increments |
| direction1 ring | force `L0007 > L0008` after direction is settled | phase follows `0x00 -> 0x08 -> 0x0C -> 0x04 -> 0x00`; count decrements |
| direction reversal | command error sign change | direction bit changes before first opposite count step if source model holds |
| latch timing | compare `L000A`, `L004C`, and physical pins | physical pins follow shadow/latch path without unmodeled state |
| physical pin swap | compare bit2/bit3 to scoped A/B | classify whether source A/B names are swapped physically |

## Ring Proof Capture Table

```csv
event_index,l0007_actual,l0008_desired,error_sign,l000a_before,l000a_after,source_ab_before,source_ab_after,physical_a_before,physical_b_before,physical_a_after,physical_b_after,l004c_before,l004c_after,l3062_write,actual_delta,classification,notes
```

## Atomicity Checks

Source prediction:

```text
L000A phase update
-> L004C masked shadow field update
-> full-byte L3062 latch write
```

Check:

1. Do A and B change together at the driver input?
2. Does the driver input pass through any uncommanded intermediate state?
3. Is physical transition delayed relative to `L004C` update?
4. Does `L3062` receive a full-byte write rather than bitwise output operations?

## Classifications

```text
PHASE-A:
  bit2 = physical A, bit3 = physical B, sequence as statically mapped.

PHASE-B:
  bit2/bit3 are swapped physically, but ring model is correct.

PHASE-C:
  source ring is correct, but external driver transforms states.

PHASE-D:
  latch write timing or hardware behavior adds unmodeled states.

PHASE-E:
  static interpretation incomplete.
```

## Pass Criteria

```text
PASS:
  source bits2/3 form the expected four-state ring.
  direction bit0 reverses ring order.
  no-step condition holds phase state.
  source actual count delta correlates with ring movement.
  physical A/B pin mapping is classified.
  latch atomicity is classified.
```

## Fail / Rework Criteria

```text
REWORK:
  A/B pins do not correlate with L000A bits2/3 or L004C bits2/3.
  ring sequence is not four-state.
  direction bit0 does not reverse ring order.
  actual count delta does not correlate with phase stepping.
  another output register directly overrides the phase pins.
```

## Next Contract

After this phase contract, continue with:

```text
IAC_ENABLE_FAULT_GATE_CONTRACT
```
