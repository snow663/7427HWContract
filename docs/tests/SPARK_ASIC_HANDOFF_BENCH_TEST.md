# Spark ASIC Handoff Bench Test

## Goal

Determine which ASIC register(s) control commanded spark timing and what units/write sequence the new OS must reproduce.

This test intentionally comes before any minimal spark writer.

## Required Signals

- EST output / ignition control signal
- REF input simulator signal
- bypass line if accessible
- writes to candidate `$3Fxx` registers
- final spark RAM variable if available
- knock retard RAM variable if available
- timing light or scope-derived spark offset
- battery voltage
- crank/run mode marker

## Candidate Registers

```text
$3FDC  spark dwell/work-period candidate
$3FE4  possible $3FEC mirror/handshake
$3FE6  spark companion command candidate
$3FE8  spark/EST timing output candidate
$3FEC  ASIC status/source read
$3FF6  EST fall counter / scheduling basis
$3FFA  packed ASIC status read
$3FFC  global output latch / possible EST/bypass involvement
```

## Test Matrix

| Test | Condition | Expected |
|---|---|---|
| key-on/no-ref | no reference pulses | no run spark command / safe state |
| crank | fixed low RPM ref | crank/bypass behavior visible |
| run fixed spark | force known spark value | output offset changes predictably |
| spark step +5° | stable RPM | EST timing advances by 5° if final spark path active |
| spark step -5° | stable RPM | EST timing retards by 5° if final spark path active |
| knock retard forced | stable RPM | final output retards if knock path active |
| bypass transition | crank to run | mode/handshake registers change |
| invalid command | clamp/min/max | output remains safe |
| freeze `$3FE8` | stable RPM and spark command changes | if `$3FE8` is final delay output, EST timing stops tracking command |
| freeze `$3FE6` | stable RPM and spark command changes | identifies whether `$3FE6` is companion or final command |
| freeze `$3FF6` | stable RPM and spark command changes | identifies timing-basis/scheduler dependency |
| mirror test `$3FEC->$3FE4` | stable RPM | identifies whether `$3FE4` must mirror/status-ack `$3FEC` |

## Static Candidate Sequence To Watch

```text
0xAB97  ADDD L3FF6
0xABA4  SUBD L3FF6
0xABAA  STD  L3FE8
0xABB0  ADDD L3FDC
0xABBA  STD  L3FE6
0xABC0  STX  L3FDC
0xABC8  STD  L3FF6
0xAC28  LDX  L3FEC
0xAC2E  STX  L3FE4
```

## Classifications

```text
Path S-A:
  one register receives final spark/timing command directly.

Path S-B:
  final spark is converted into a delay/tick value and written to ASIC.

Path S-C:
  spark command requires companion mode/handshake writes.

Path S-D:
  HC11 timer hardware, not ASIC handoff, controls spark timing.
```

## Procedure

1. Run a stable REF simulator at a fixed RPM.
2. Capture the candidate `$3Fxx` writes/reads and EST output offset.
3. Force or patch final spark by a known step, preferably `+5°` and `-5°`.
4. Watch which candidate register values change proportionally.
5. Freeze or override one candidate at a time if the test setup allows it.
6. Repeat through crank/run transition.
7. Repeat with knock retard forced or simulated if possible.
8. Classify the handoff path.

## Data To Record

```csv
test_name,rpm_ref_hz,forced_spark_deg,knock_retard_deg,three_fdc,three_fe4,three_fe6,three_fe8,three_fec,three_ff6,three_ffa,est_offset_deg,bypass_state,path_result,notes
```

## Pass Criteria For A Spark Writer

Do not write a minimal spark writer until these are known:

```text
final handoff register(s)
unit scale
write order
refresh timing
required companion/handshake behavior
safe default/crank behavior
```

## Stop Conditions

- Stop and preserve the trace if EST output changes with `$3FE8` but not `$3FE6`.
- Stop and preserve the trace if `$3FE6` changes output only when `$3FE4/$3FEC` are mirrored correctly.
- Stop and preserve the trace if `$3FF6` is required as a timing basis rather than a passive status counter.
- Stop and preserve the trace if the bypass line changes independently of these ASIC writes.
