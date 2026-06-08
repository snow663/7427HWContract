# IAC Init / Park Test

## Goal

Determine how stock code makes `L0007` actual/present IAC position trustworthy, and classify stock park/reset behavior physically.

This test does not cover A/B phase order or Enable voltage-gate logic except where those affect actual park/reset motion.

## Required Signals / Trace Values

- physical IAC A candidate
- physical IAC B candidate
- physical IAC Enable candidate
- `L0007` actual/present IAC position
- `L0008` desired/target IAC position
- `L0009 bit0` reset-in-work candidate
- `L0009 bit2` R/S requested candidate
- `L000A` mode/output byte
- `L004C` output shadow
- `L3062` latch write if bus trace is available
- `L0046 bit6` nonvolatile-memory-bombed candidate
- `L0004 bit3` bad-shutdown candidate
- `L0044 bit4` ignition-off candidate
- `L00A7` battery volts VDC/10
- `L4EB0` park-down count

## Static Source Candidate

```text
nonvolatile memory bombed:
  0x926A LDAA L4EB0
  0x926D STAA L0007

reset in work:
  0x93E5 CLR L0008
  0x93E8 TST L0007
  0x93F0 BCLR L0009,#$01 when L0007 reaches zero
  0x93F3 BSET L0009,#$04

ignition off / R-S requested:
  0x9401 LDAA L4EB0
  0x9404 JMP L9899
  0x9899 STAA L0008
```

## Test Matrix

| Test | Condition | Expected if static model is correct |
|---|---|---|
| normal key-on after normal shutdown | retained state valid, no reset-in-work | `L0007` is not blindly overwritten; `L0008` follows startup/idle logic |
| nonvolatile memory bombed | force/observe `L0046 bit6` | `L0007 := L4EB0` and default IAC cells are seeded |
| reset-in-work active | force/observe `L0009 bit0` | `L0008 := 0`; stepping continues until `L0007 == 0`; then reset-in-work clears |
| ignition-off R/S requested | `L0044 bit4` and `L0009 bit2` active | `L0008 := L4EB0` through `L9899` |
| bad shutdown | force/observe `L0004 bit3` | setup path calls `L93C5`; Enable/direction cleared unless reset-in-work is active |
| cold prior to start | coolant below `L4E91` path | `L0008 := L4EB0` candidate before start |
| low-voltage startup | battery below threshold | classify whether physical park/reset motion is blocked by Enable gate |

## Physical Direction Tests

Capture actual airflow/motor movement while forcing known target states:

```text
Case A:
  L0008 = 0
  observe whether motor drives closed or open

Case B:
  L0008 = L4EB0 = 145
  observe whether motor drives park-down/open/closed
```

Record:

```csv
test_name,event_index,l0007_actual,l0008_desired,l0009,l000a,l004c,l3062_write,physical_enable,physical_a,physical_b,airflow_direction,motor_direction,mechanical_stop_observed,notes
```

## Reset-In-Work Proof

For reset-in-work:

1. Set/observe `L0009 bit0`.
2. Confirm `L0008` is repeatedly cleared to zero.
3. Confirm `L0007` walks toward zero through the phase contract.
4. Confirm `L0009 bit0` clears only when `L0007 == 0`.
5. Confirm `L0009 bit2` sets after reset completion.
6. Determine whether physical motor hits/overdrives a stop before software reaches zero.

## Park-Down Proof

For ignition-off/R-S requested park:

1. Set/observe `L0044 bit4` ignition-off candidate.
2. Set/observe `L0009 bit2` R/S requested candidate.
3. Confirm `L4EB0` is loaded into A.
4. Confirm `L9899` writes `L0008 := L4EB0`.
5. Scope A/B/Enable while actual moves toward desired.
6. Determine whether `145` is open, closed, or stock park-down overtravel.

## Classifications

```text
PARK-A:
  stock code overdrives IAC to a mechanical stop, then seeds/accepts L0007.

PARK-B:
  stock code trusts retained RAM/NVRAM or previous position when validity is good.

PARK-C:
  reset-in-work / bad-shutdown flags decide whether to re-home or clear setup state.

PARK-D:
  stock loads crank/start/park desired position into L0008 without directly homing.

PARK-E:
  Enable/voltage gate must be valid before park/reset motion occurs physically.

PARK-F:
  static interpretation incomplete.
```

## Pass Criteria

```text
PASS:
  all writes to L0007 and L0008 in init/park contexts are classified.
  reset-in-work behavior is proven or refuted.
  L4EB0 physical meaning is classified.
  0-count physical meaning is classified.
  bad-shutdown behavior is classified.
  Enable dependency during park/reset is classified.
```

## Fail / Rework Criteria

```text
REWORK:
  another path writes L0007 before normal control and was missed.
  physical direction does not match software count direction from phase contract.
  L0008 park command is overridden by another target path before motion occurs.
  Enable/fault gate prevents all observed reset/park movement.
  reset-in-work bit behavior does not correlate with L0007/L0008.
```

## Next Artifact

After this test contract, the next source-side artifact is:

```text
source/minimal_os/iac/README.md
```
