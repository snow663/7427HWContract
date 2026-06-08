# Spark Init State Test

## Goal

Determine how stock code seeds spark rolling state before the first valid `LA906` spark handoff.

## Required Signals / Trace Values

- REF input
- EST output
- bypass line
- RPM/run flag
- `$3FC0`
- `L005F/L0060`
- `L01EC`
- `$3FF6`
- `$3FDC`
- `$3FE8`
- `$3FE6`
- `$3FEC`
- `$3FE4`
- first `LA906` entry marker / `D_AB97` if traceable
- crank-to-run threshold marker

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| key-on/no-ref | no RPM | safe cleared/default state |
| crank low RPM | bypass active | period basis begins forming |
| crank-to-run threshold | RPM crosses run gate | rolling state seeded before/with first LA906 |
| first EST event | first run spark | `$3FE8/$3FE6` valid, no wild jump |
| missing REF after run | simulated dropout | spark output safe/held/faulted |
| forced bad seed | corrupt `$3FF6/$3FDC` | determine failure mode |
| stock restart | hot restart | seed behavior repeats cleanly |
| zero-seed test | force `$3FF6/$3FDC=$0000` at first LA906 | determine whether global-clear zero is safe |

## Classifications

```text
INIT-A:
  $3FF6/$3FDC are seeded from hardware capture/period state before first LA906.

INIT-B:
  $3FF6/$3FDC are only valid after one or more LA906 iterations.

INIT-C:
  startup/bypass mode avoids ASIC spark handoff until rolling state is valid.

INIT-D:
  $3FEC->$3FE4 mirror seeds/acks the first valid state.

INIT-E:
  static model incomplete.
```

## Procedure

1. Run key-on/no-ref and capture ASIC window state after global clear.
2. Begin low-RPM crank simulation with bypass active if available.
3. Capture `$3FC0`, `L005F/L0060`, and `L01EC` as the first REF/DRP periods are accepted.
4. Identify the exact run/EST gate where the first `LA906` path executes.
5. Capture `$3FF6` and `$3FDC` immediately before the first `ADDD L3FF6` and `ADDD L3FDC` reads.
6. Capture first `$3FE8` and `$3FE6` writes and compare them against expected sane timing.
7. Capture first `$3FEC->$3FE4` mirror after the paired timing writes.
8. Simulate missing REF after run and observe whether output is held, cleared, faulted, or allowed to drift.
9. Force bad `$3FF6/$3FDC` seeds, one at a time, and record failure behavior.
10. Repeat as hot restart and verify whether seed behavior changes.

## Data To Record

```csv
test_name,event_index,ref_state,rpm_ref_hz,run_flag,bypass_state,l3fc0,l005f,l01ec,l3ff6_before,l3fdc_before,d_ab97,l3fe8,l3fe6,l3fdc_after,l3ff6_after,l3fec,l3fe4,est_offset_deg,path_result,notes
```

## Pass Criteria

```text
INIT-A pass:
  $3FF6/$3FDC have non-garbage seeded values before first LA906 and first $3FE8/$3FE6 writes are sane.

INIT-B pass:
  first LA906 iteration bootstraps $3FF6/$3FDC, and stock code prevents unsafe EST output until that bootstrap is valid.

INIT-C pass:
  bypass/startup mode blocks ASIC spark handoff until L005F/L01EC/$3FF6/$3FDC are valid.

INIT-D pass:
  $3FEC->$3FE4 mirror is required for first valid event or subsequent events.
```

## Fail / Stop Conditions

Stop and preserve trace if:

- first run EST event jumps wildly when `$3FF6/$3FDC` are bad.
- LA906 executes before valid `L005F`/period basis exists.
- `$3FE8/$3FE6` are written before bypass-to-EST transition is safe.
- missing REF allows rolling state to free-run into invalid spark output.
- hot restart uses a different seed path not represented in this contract.

## Expected Minimal-OS Requirement

If stock behavior is confirmed, the minimal OS should implement:

```text
SPARK_INIT_STATE:
  clear/default output state
  wait for valid REF/DRP period
  seed or validate L005F/L01EC/$3FF6/$3FDC
  block LA906-style handoff until state is valid
  transition bypass-to-EST without a wild first event
```

## Next Step

If bypass/EST transition is not fully explained by this test, create:

```text
docs/contracts/SPARK_BYPASS_EST_TRANSITION.md
maps/contracts/spark_bypass_est_transition.csv
docs/tests/SPARK_BYPASS_EST_TRANSITION_TEST.md
```

Do not create a spark handoff stub until init state and bypass/EST transition are classified.
