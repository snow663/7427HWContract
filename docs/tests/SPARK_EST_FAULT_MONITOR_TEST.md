# Spark EST Fault Monitor Test

## Goal

Determine whether the EST/Error 42 monitor is diagnostic-only, authority-gating, fallback-affecting, or tied to the shared `$3FEC->$3FE4` ACK/status path.

## Required Signals / Trace Values

- REF input
- EST output
- bypass wire/state
- RPM/ref simulator state
- `L004F bit6` monitor enable
- `L004F bit7` engine running
- `L0044 bit3` first DRP valid
- `L0050 bit2` recent DRP occurred
- `L3FCA` current monitor sample
- `L0205` prior monitor sample
- `L022C` EST error counter
- `L0044 bit7` locked ERR42A candidate
- `$3FEC`
- `$3FE4`
- `$3FE8/$3FE6`
- `$3FF6/$3FDC`
- Error 42 status if externally visible

Watched but not primary in captured static rows:

- `L022B`
- `L0204`

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| stock good EST path | stable run, valid EST | `L022C` stays clear or resets |
| simulated EST mismatch | freeze/mismatch monitor sample | `L022C` increments |
| force `L022C` near threshold | stable run | determine threshold/fault side effects |
| force `L004F bit6` clear | stable run | determine if spark authority continues with monitor disabled |
| force `L004F bit6` set | early run/crank | determine if monitor false-trips or affects authority |
| skip `$3FEC->$3FE4` | stable run | determine if monitor trips or authority changes |
| missing REF/dropout | running then dropout | monitor should gate/hold/fault safely |
| force locked ERR42A bit | stable run | determine if bypass/spark/fuel changes |
| compare `L0204/L022B` | same tests | verify they are not primary monitor state |

## Classifications

```text
MON-A:
  EST monitor is diagnostic-only; minimal OS can omit or keep disabled.

MON-B:
  EST monitor gates spark authority; minimal OS must reproduce enable/clear logic.

MON-C:
  EST monitor affects fallback/bypass behavior after fault.

MON-D:
  EST monitor shares $3FEC->$3FE4 ACK path with LA906; cannot omit mirror.

MON-E:
  static interpretation incomplete.
```

## Procedure

1. Capture stock good EST behavior at stable RPM with valid REF and normal bypass/EST transition.
2. Confirm `L004F bit6`, `L3FCA`, `L0205`, and `L022C` behavior in the good path.
3. Simulate EST mismatch by freezing or corrupting the monitor sample relationship if practical.
4. Observe whether `L022C` increments and whether `L0044 bit7` or other Error 42 state latches.
5. Force `L022C` near/at threshold and check bypass wire, EST output, `$3FE8/$3FE6`, fuel/run state, and limp behavior.
6. Force `L004F bit6` clear while running and determine whether EST authority continues.
7. Force `L004F bit6` set early and determine whether false monitoring causes authority or fault effects.
8. Skip/freeze `$3FEC->$3FE4` and determine whether it triggers monitor error, breaks LA906 handoff, or has no effect.
9. Run dropout/missing-REF case and verify monitor gating does not create a wild spark event.
10. Compare `L0204/L022B` activity to `L0205/L022C` to confirm the corrected static path.

## Data To Record

```csv
test_name,event_index,rpm_ref_hz,bypass_state,est_output_state,l004f,l0044,l0050,l3fca,l0205,l022c,l022b,l0204,l3fec,l3fe4,l3fe8,l3fe6,l3ff6,l3fdc,error42_state,fault_injected,path_result,notes
```

## Pass Criteria

```text
MON-A pass:
  disabling or omitting monitor behavior does not change EST authority, LA906 output effect, bypass state, fuel/run state, or safe dropout behavior.

MON-B pass:
  monitor enable/clear state directly gates EST authority or suppresses LA906 output effect.

MON-C pass:
  fault threshold forces module bypass, fallback spark, fuel/run changes, or limp behavior.

MON-D pass:
  skipping $3FEC->$3FE4 breaks monitor stability, authority transfer, or LA906 output continuity.
```

## Fail / Stop Conditions

Stop and preserve trace if:

- forcing `L022C` threshold causes uncontrolled spark timing.
- monitor disabled causes coil authority loss.
- `$3FEC->$3FE4` skip causes immediate output instability.
- `L0204/L022B` prove to be the true primary monitor state instead of `L0205/L022C`.
- Error 42 affects fuel/run behavior through a different untracked path.

## Expected Result To Prove

Static evidence currently supports this conservative hypothesis:

```text
L004F bit6 = monitor enable/control
L3FCA -> L0205 = monitor sample/delta path
L022C = EST error counter
Error 42 side effects on spark authority/fuel are not statically proven
$3FEC->$3FE4 remains shared ACK/status candidate
```

## Next Step

After this test/contract, write:

```text
docs/contracts/SPARK_MINIMAL_MODULE_BOUNDARY.md
```

That boundary should classify the EST monitor as required, optional, or disabled/simplified based on MON-A through MON-D.

Still no `SPARK_WRITE` or spark handoff stub until the module boundary is explicit.
