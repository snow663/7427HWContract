# Spark LA906 Output Sequence Test

## Goal

Determine which LA906 writes directly affect EST timing and which are required rolling/handshake state.

## Required Signals

- REF input
- EST output
- bypass line
- writes to `$3FE8`
- writes to `$3FE6`
- writes to `$3FDC`
- writes to `$3FF6`
- read `$3FEC`
- write `$3FE4`
- `D_AB97` / LA906 entry value if traceable
- `L01EC` if traceable
- measured EST offset relative to REF

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| stock fixed RPM | baseline | all LA906 writes repeat predictably |
| force `D_AB97 + delta` | fixed RPM | `$3FE8/$3FE6` shift predictably |
| freeze `$3FE8` | fixed RPM | identify if EST timing stops/changes |
| freeze `$3FE6` | fixed RPM | identify if EST timing stops/changes |
| freeze `$3FF6` | fixed RPM | identify rolling anchor requirement |
| freeze `$3FDC` | fixed RPM | identify prior-state requirement |
| skip `$3FEC→$3FE4` mirror | fixed RPM | identify handshake/ack requirement |
| vary RPM fixed spark | RPM sweep | rolling state scales with period |
| spark step fixed RPM | +5°/-5° | command registers move with spark |

## Classifications

```text
SEQ-A:
  $3FE8 is the primary spark timing command.

SEQ-B:
  $3FE6 is the primary spark timing command.

SEQ-C:
  $3FE8/$3FE6 are a required pair.

SEQ-D:
  $3FF6/$3FDC must be maintained as rolling timing state.

SEQ-E:
  $3FEC→$3FE4 mirror is required handshake/ack.

SEQ-F:
  static interpretation incomplete.
```

## Procedure

1. Capture a stock fixed-RPM baseline with `D_AB97`, `$3FE8`, `$3FE6`, `$3FDC`, `$3FF6`, `$3FEC`, `$3FE4`, and EST output.
2. Force a small positive and negative `D_AB97` delta while RPM is fixed.
3. Observe whether `$3FE8` and `$3FE6` shift together, separately, or in opposite directions.
4. Freeze `$3FE8` while leaving the rest of LA906 stock and observe EST output.
5. Freeze `$3FE6` while leaving the rest of LA906 stock and observe EST output.
6. Freeze `$3FF6` and then `$3FDC` separately to test rolling-state dependence.
7. Block or skip the `$3FEC→$3FE4` mirror if practical and observe EST output/fault/status behavior.
8. Sweep RPM at fixed spark and verify rolling-state values scale with period.
9. Step spark +5°/-5° at fixed RPM and verify command-register motion matches the conversion equation.

## Data To Record

```csv
test_name,rpm_ref_hz,d_ab97,l01ec,l3fe8,l3fe6,l3fdc,l3ff6,l3fec,l3fe4,est_offset_deg,bypass_state,freeze_target,mirror_skipped,path_result,notes
```

## Pass Criteria

```text
SEQ-C pass:
  $3FE8 and $3FE6 both move with D_AB97/spark changes,
  freezing either disrupts EST timing or output stability,
  both must be reproduced in a minimal handoff.

SEQ-D pass:
  freezing $3FF6 or $3FDC breaks continuity, causes jitter, locks timing, or corrupts later command writes.

SEQ-E pass:
  skipping $3FEC->$3FE4 causes loss of output, repeated fault/status behavior, stuck timing, or missed subsequent events.
```

## Partial Pass Criteria

```text
SEQ-A partial:
  $3FE8 alone controls measured EST timing while $3FE6 behaves as companion/dwell/state.

SEQ-B partial:
  $3FE6 alone controls measured EST timing while $3FE8 behaves as companion/dwell/state.
```

## Fail / Stop Conditions

Stop and preserve trace if:

- EST output does not correlate with either `$3FE8` or `$3FE6`.
- `$3FF6/$3FDC` can be frozen without any effect, contradicting static rolling-state interpretation.
- `$3FEC→$3FE4` mirror has no observable function but another untracked register behaves as handshake.
- LA906 writes appear observational only and another timer path controls EST.

## Next Step

If rolling state is confirmed, create:

```text
docs/contracts/SPARK_ROLLING_STATE_MODEL.md
maps/contracts/spark_rolling_state_model.csv
docs/tests/SPARK_ROLLING_STATE_MODEL_TEST.md
```

Only after the conversion equation, rolling state, and ASIC output sequence are classified should a minimal spark handoff stub be written.
