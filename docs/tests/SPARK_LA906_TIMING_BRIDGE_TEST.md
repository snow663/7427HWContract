# Spark LA906 Timing Bridge Bench Test

## Goal

Determine which `LA906`-written ASIC values actually move EST timing and which values are rolling state, monitor state, or handshake/mirror state.

## Required Signals

- REF input simulator signal
- EST output / ignition control signal
- bypass line if accessible
- writes to `$3FE6`
- writes to `$3FE8`
- reads/writes to `$3FDC`
- reads/writes to `$3FF6`
- `$3FEC` read values
- `$3FE4` mirror writes
- final spark RAM value if known
- knock retard RAM value if available
- timing light or scope-derived spark offset

## Candidate Values To Log

```text
$3FE8  first computed timing command candidate
$3FE6  second computed timing command candidate
$3FDC  rolling work-period / correction state candidate
$3FF6  EST fall counter / rolling timing anchor candidate
$3FEC  ASIC status/source/capture candidate
$3FE4  mirror/ack/handshake target candidate
$3FC0  hardware DRP/ref period basis
L01EE  current retard / final spark-offset accumulator candidate
L01EC  latency/reference correction candidate
L0201  spark latency table result
L020C  knock retard
```

## Test Matrix

| Test | Condition | Expected observation |
|---|---|---|
| stock idle/run trace | fixed RPM/ref, stable operating state | repeatable `$3FE8/$3FE6/$3FDC/$3FF6` sequence per spark update |
| fixed-RPM spark step +5° | stable RPM, force final spark +5° | one or both `$3FE6/$3FE8` values shift and EST output advances |
| fixed-RPM spark step -5° | stable RPM, force final spark -5° | one or both `$3FE6/$3FE8` values shift and EST output retards |
| fixed spark, vary RPM | hold software spark constant, vary ref period | timing-domain values scale with `$3FC0`/ref period |
| force `$3FE6` only | hold other writes stock if possible | classify whether `$3FE6` directly moves EST timing |
| force `$3FE8` only | hold other writes stock if possible | classify whether `$3FE8` directly moves EST timing |
| force paired `$3FE6/$3FE8` | apply coherent pair if derived | classify whether pair is required |
| freeze `$3FF6` | hold rolling anchor constant | observe timing break/jitter/lock if rolling state required |
| freeze `$3FDC` | hold work-period state constant | observe whether second command or dwell/timing breaks |
| block `$3FEC→$3FE4` mirror | prevent or freeze mirror/ack write | observe whether EST output fails, drifts, faults, or continues |
| knock retard forced | stable RPM, force knock retard | final output retards if knock path is active upstream |
| bypass transition | crank to run | identify mode/handshake/status changes and first valid LA906 sequence |

## Static Sequence To Watch

```text
0xAB97  ADDD L3FF6
0xABA4  SUBD L3FF6
0xABAA  STD  L3FE8
0xABB0  ADDD L3FDC
0xABB3  SUBD L01EC
0xABBA  STD  L3FE6
0xABC0  STX  L3FDC
0xABC8  STD  L3FF6
0xAC28  LDX  L3FEC
0xAC2E  STX  L3FE4
```

## Classifications

```text
S-B1:
  $3FE6 is final timing command.

S-B2:
  $3FE8 is final timing command.

S-B3:
  $3FE6/$3FE8 are paired timing commands.

S-C1:
  $3FEC→$3FE4 mirror is required handshake.

S-C2:
  $3FF6/$3FDC rolling state must be maintained.

S-D:
  ASIC writes are monitoring/handshake only and another timer path controls EST.
```

## Data To Record

```csv
test_name,rpm_ref_hz,forced_spark_delta_deg,l01ee,l01ec,l0201,l020c,l3fc0,l3fdc_before,l3ff6_before,l3fe8_write,l3fe6_write,l3fdc_after,l3ff6_after,l3fec_read,l3fe4_write,est_offset_us,est_offset_deg,path_result,notes
```

## Pass Criteria For Timing-Bridge Identification

A register or register pair is promoted from candidate to required spark handoff only if controlled changes produce predictable EST timing movement while other variables are held fixed or logged well enough to explain the movement.

## Fail Criteria For A Candidate

A candidate is not the direct timing command if forced changes to it do not move EST timing, or if EST timing follows another value while that candidate is frozen.

## Stop Conditions

- Stop and preserve the trace if freezing `$3FF6` causes unstable/jittered EST output.
- Stop and preserve the trace if blocking `$3FEC→$3FE4` causes loss of EST output or error 42/43 behavior.
- Stop and preserve the trace if `$3FE6` and `$3FE8` must be updated as a coherent pair.
- Stop and preserve the trace if spark timing follows HC11 timer activity instead of ASIC writes.

## Next Step After This Bench Test

If `$3FE6/$3FE8` or a pair is confirmed as the spark command handoff, create a separate contract for:

```text
SPARK_DEGREE_TO_TICK_DEPENDENCY
```

Do not write `source/minimal_os/spark/spark_write.asm` until the command register(s), units, rolling state, and mirror/ack requirements are known.
