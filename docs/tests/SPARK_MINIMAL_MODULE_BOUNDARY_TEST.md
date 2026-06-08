# Spark Minimal Module Boundary Test

## Goal

Exercise the full spark boundary without creating a spark writer. Prove which submodules are required, which are bench-gated, and whether the EST monitor can remain disabled/simplified.

## Required Signals / Trace Values

- REF input
- RPM/ref simulator state
- bypass wire/state
- EST output
- `L0044 bit3` first DRP valid
- `L0050 bit2` recent DRP occurred
- `L0210` qualifying DRP/ref counter
- `L004F bit7` engine running
- `L004F bit6` EST monitor enable
- `L005F/L0060` period basis
- `L0201` latency correction
- `L3FC0` anchor/period source
- `D_AB97` if traceable
- `$3FF6/$3FDC/L01EC`
- `$3FE8/$3FE6`
- `$3FEC/$3FE4`
- `L3FCA/L0205/L022C`
- Error 42 visible state if available

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| stock baseline | fixed RPM, normal run | all boundary inputs/outputs stable and ordered |
| crank-to-run | ramp through threshold | run qualifier, period seed, rolling state, and EST authority occur in safe order |
| EST monitor disabled | force/hold monitor disabled | spark authority still works if MON-A true |
| forced desired spark step | stable RPM, +5/-5 deg | conversion and handoff move EST timing predictably |
| bad rolling seed | corrupt `$3FF6/$3FDC` before first handoff | bypass/run gate prevents wild first event or seed is required |
| skipped `$3FEC->$3FE4` | stable run | determine whether timing, authority, or monitor fails |
| missing REF/dropout | run then remove/garble REF | output holds/disables/faults safely |
| Error 42 threshold | force `L022C`/fault state | determine diagnostic-only vs fallback/authority side effect |

## Boundary Classifications

```text
BOUND-A:
  Required modules are sufficient with EST monitor disabled/simplified.

BOUND-B:
  $3FEC->$3FE4 mirror is required for handoff, monitor, or authority.

BOUND-C:
  EST monitor is required for authority/fallback and cannot be omitted.

BOUND-D:
  first-event seed must be explicit before LA906-style handoff.

BOUND-E:
  conversion/rolling/handoff split is incomplete.
```

## Procedure

1. Capture stock baseline at fixed RPM with normal bypass-to-EST transition.
2. Verify run qualification order: first DRP valid, RPM threshold, event count, engine-running set.
3. Verify period/conversion basis before handoff: `L005F/L0060`, `L0201`, `L3FC0`, and `D_AB97` if visible.
4. Verify rolling state before and after first handoff: `$3FF6`, `$3FDC`, `L01EC`.
5. Verify paired output writes: `$3FE8` and `$3FE6` relative to EST output.
6. Disable or hold `L004F bit6` if practical and verify whether EST authority continues.
7. Force desired spark +5/-5 degrees and compare EST output timing movement.
8. Corrupt `$3FF6/$3FDC` before first handoff and determine whether bypass/run gating prevents a wild event.
9. Skip or freeze `$3FEC->$3FE4` and observe LA906 continuity, authority, and monitor behavior.
10. Trigger Error 42 threshold behavior and verify whether spark/fuel/bypass changes.
11. Run missing-REF/dropout and verify safe output behavior.

## Data To Record

```csv
test_name,event_index,rpm_ref_hz,bypass_state,est_output_state,l0044,l0050,l0210,l004f,l005f,l0201,l3fc0,d_ab97,l01ec,l3ff6,l3fdc,l3fe8,l3fe6,l3fec,l3fe4,l3fca,l0205,l022c,error42_state,path_result,notes
```

## Pass Criteria

```text
required modules pass:
  run qualify, authority, conversion, rolling state, ASIC handoff, and dropout safe state all behave in safe order.

monitor optional pass:
  EST monitor disabled/simplified does not affect authority, timing, fuel, or safe dropout behavior.

mirror required pass:
  skipping $3FEC->$3FE4 breaks ACK/status, authority, monitor, or LA906 continuity.

first seed required pass:
  bad or zero rolling state produces unsafe command unless explicit seed/gate exists.
```

## Stop / Preserve Trace Conditions

Stop and preserve trace if:

- bad rolling seed creates an uncontrolled EST output.
- EST monitor disabled kills coil authority.
- `$3FEC->$3FE4` skip causes immediate instability.
- Error 42 threshold changes fuel/run behavior through an untracked path.
- `$3FE8/$3FE6` do not correlate with EST output timing.

## Expected Next Artifact

If this boundary holds, create only documentation/API layout next:

```text
source/minimal_os/spark/README.md
```

That README may define planned module APIs and call order. It must not implement `SPARK_WRITE` or a handoff stub yet.
