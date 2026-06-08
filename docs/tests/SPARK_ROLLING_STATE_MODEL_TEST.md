# Spark Rolling State Model Test

## Goal

Determine whether `$3FF6`, `$3FDC`, and `$01EC` are required persistent spark timing state, and how they affect EST output.

## Required Signals

- REF input
- EST output
- bypass line
- `$3FF6` read/write trace
- `$3FDC` read/write trace
- `L01EC` trace
- `$3FE8` write trace
- `$3FE6` write trace
- `$3FEC` read trace
- `$3FE4` write trace
- `D_AB97` if traceable
- crank/run transition marker

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| stock fixed RPM | baseline | rolling state repeats predictably |
| fixed RPM, fixed spark | hold command | `$3FF6/$3FDC` advance continuously event-to-event |
| fixed RPM, +5° spark step | spark step | command writes shift while rolling state remains continuous |
| freeze `$3FF6` | fixed RPM | timing jitter/lock/fault if rolling anchor required |
| freeze `$3FDC` | fixed RPM | paired edge/dwell behavior changes if required |
| force `L01EC` +N | fixed RPM | `$3FE6` shifts if correction/dwell term |
| skip `$3FEC->$3FE4` | fixed RPM | determine mirror/ack requirement |
| first spark after run transition | crank-to-run | determine init requirements |
| recompute-only experiment | overwrite rolling state from current period/spark each event | passes only if state does not need continuity/history |

## Classifications

```text
ROLL-A:
  $3FF6 is required rolling event anchor.

ROLL-B:
  $3FDC is required prior-edge or paired-edge state.

ROLL-C:
  L01EC is required timing/dwell/latency correction.

ROLL-D:
  $3FEC->$3FE4 is required feedback/ack.

ROLL-E:
  rolling state can be recomputed from current period/spark each event.

ROLL-F:
  static model incomplete.
```

## Procedure

1. Capture a stock fixed-RPM baseline with fixed spark command.
2. Record event-to-event progression of `$3FF6`, `$3FDC`, `L01EC`, `$3FE8`, and `$3FE6`.
3. Step commanded spark +5° and -5° while keeping RPM fixed.
4. Verify whether command writes shift while `$3FF6/$3FDC` remain continuous.
5. Freeze `$3FF6` for one or more events and observe EST timing, jitter, lockup, or faults.
6. Restore stock behavior, then freeze `$3FDC` and observe paired-edge/dwell behavior.
7. Force `L01EC +N` and determine whether `$3FE6` shifts as predicted.
8. Skip or block `$3FEC->$3FE4` mirror if practical and observe output/status behavior.
9. Capture the first run spark event after crank/run transition to identify initialization requirements.
10. If safe, try recomputing `$3FF6/$3FDC` from current period/spark only and compare against stock continuity.

## Data To Record

```csv
test_name,event_index,rpm_ref_hz,d_ab97,l01ec,l3ff6_before,l3fdc_before,l3fe8,l3fe6,l3fdc_after,l3ff6_after,l3fec,l3fe4,est_offset_deg,bypass_state,freeze_target,mirror_skipped,path_result,notes
```

## Pass Criteria

```text
ROLL-A pass:
  freezing $3FF6 breaks timing continuity, causes jitter/lock/fault, or corrupts following $3FE8/$3FE6 writes.

ROLL-B pass:
  freezing $3FDC changes paired-edge timing, dwell-like behavior, or following $3FE6 calculation.

ROLL-C pass:
  forcing L01EC shifts $3FE6 and/or paired-edge timing predictably.

ROLL-D pass:
  skipping $3FEC->$3FE4 causes output loss, fault/status repeat, stuck timing, or missed subsequent events.

ROLL-E pass:
  recomputed rolling state matches stock across steady state, spark steps, and RPM changes without continuity loss.
```

## Fail / Stop Conditions

Stop and preserve trace if:

- EST output becomes unsafe or uncontrolled after freezing rolling state.
- `$3FF6/$3FDC` do not affect output despite static read/update evidence.
- another untracked register clearly carries the true rolling state.
- first-event/run-transition behavior uses a separate init path not covered by this contract.

## First-Event / Init Items To Watch

During crank-to-run transition, capture:

```text
$3FF6 initial value
$3FDC initial value
L01EC initial value
first $3FE8 write
first $3FE6 write
first $3FEC->$3FE4 mirror
bypass/EST transition state
```

These determine the next contract:

```text
docs/contracts/SPARK_INIT_STATE.md
maps/contracts/spark_init_state.csv
docs/tests/SPARK_INIT_STATE_TEST.md
```

## Next Step

After rolling state and first-event behavior are classified, create the spark init-state contract. Do not create a spark handoff stub until init state is documented.
