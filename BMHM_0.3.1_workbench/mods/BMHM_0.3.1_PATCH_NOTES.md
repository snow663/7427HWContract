# BMHM 0.3.1 patch notes

## 1. Closed-loop DAMP1

Purpose: reduce closed-loop pulse-width authority/rate without changing O2 thresholds, slow-O2 filtering, VE, PE, spark, injector constants, or transient-fuel calibration.

Calibration edits:

- `$48ED: $0C -> $12` — BLM base update period approximately 50% longer.
- `$48F7: $02 -> $04` — non-idle BLM INT learning window widened from ±2 to ±4 counts.
- `$4D49-$4D4E: $20 -> $18` — P gain at 1200 RPM / 50-100 kPa.
- `$4D52-$4D57: $24 -> $1B` — P gain at 1600 RPM / 50-100 kPa.
- `$4D5B-$4D60: $24 -> $1B` — P gain at 2000 RPM / 50-100 kPa.
- `$4D64-$4D69: $30 -> $24` — P gain at 2400 RPM / 50-100 kPa.
- `$4D6D-$4D72: $30 -> $24` — P gain at 2800 RPM / 50-100 kPa.
- `$4D76-$4D7B: $30 -> $24` — P gain at 3200 RPM / 50-100 kPa.
- `$4D89: $A0 -> $C0`
- `$4D8A: $80 -> $A0`
- `$4D8B-$4D8D: $60 -> $80`
- `$4D8E: $80 -> $A0`

The P-gain changes remove about 25% proportional authority in the targeted load region. The `$4D89-$4D8E` changes slow INT ratcheting at moderate/large slow-O2 error.

## 2. Open-loop-idle patch repair and option byte

The earlier patch had executable code at `$FD45-$FD57`. Stock source proves `$FD45-$FE44` is a 256-byte coolant A/D lookup table. 0.3.1 restores the damaged table bytes to stock and relocates executable code into source-confirmed zero filler `$FE9F-$FF8F`.

Hook:

- `$E4FC -> JMP $FEA0`
- `$E4FF` stock `BSET $003E,#$A0` restored.

Option byte:

- `$FE9F bit0 / $01` — Force Open Loop At Idle.
- `$FE9F bit1 / $02` — Disable Closed Loop Fueling globally.

Default `$FE9F = $01`.

When bit0 is set and stock idle flag `$0050.b7` is active, the patch clears `$003E` mask `$A2` and exits via `$E561`, blocking closed-loop state and BLM learning at idle.

When bit1 is set, the patch additionally:

- blocks/clears closed-loop + BLM-enable state,
- substitutes BLM=128 into the fuel multiplier path at `$804C`,
- forces signed INT/P correction `$026F=0` at the `$8918` path.

PE, AE, VE, injector model, battery/baro correction and fuel-cut logic remain active.

## 3. Consumer-level VSS authority removal

The rejected VSS experiment that forced `$0812/$0284=0` is not used.

0.3.1 leaves the VSS capture/calculation/filter code untouched and patches consumers so the observed phantom VSS cannot alter engine behavior.

Main consumer patches:

| Address | New branch | Result |
|---|---|---|
| `$7F45` | `JMP $7F5A` | remove low-speed AE multiplier |
| `$7F9A` | `JMP $7FA2` | idle fuel selection ignores VSS |
| `$8073` | `JMP $809C` | disable VSS-based transmission-abuse path |
| `$80C5` | `JMP $8106` | remove MPH overspeed cut; RPM cut retained |
| `$8213` | `JMP $8218` | DFCO ignores VSS qualifier |
| `$82BC` | `JMP $82D1` | decel-enlean ignores low-speed VSS multiplier |
| `$82FC` | `JMP $830B` | disable VSS/stopped derivative-RPM special mode |
| `$8765` | `JMP $8790` | remove VSS-dependent CL lean-decel reset |
| `$899B` | `JMP $89A3` | idle classifier ignores VSS |
| `$8A92` | `JMP $8AAA` | remove VSS-dependent PE-delay bypass |
| `$8BCF` | `JMP $8BDD` | remove low-speed cold-PE adder |
| `$8BF3` | `JMP $8C0D` | remove delta-MPH PE-delay authority |
| `$8CA0` | `JMP $8CA8` | BLM idle-cell selection ignores VSS |
| `$99F2` | replaced again by true-idle gate | IAC VSS qualifier removed |
| `$9C4D` | `JMP $9C5F` | IAC proportional authority uses non-speed-limited path |
| `$9D15` | `CLRA; NOP; NOP` | local 0-mph index for IAC TPS-delay table; VSS RAM untouched |
| `$9D47` | `CLRA; NOP; NOP` | local 0-mph index for IAC TPS coefficient table |
| `$9EA7` | `JMP $9ECA` | remove IAC cold-offset VSS threshold |
| `$9F6C` | `JMP $9F74` | throttle kicker ignores VSS max-speed |
| `$9FD3` | `JMP $9FDE` | throttle-kicker release ignores VSS |
| `$A3F2` | `JMP $A406` | remove vehicle-speed-triggered IAC motor reset |
| `$A85A` | replaced again by true-idle gate | idle-spark VSS qualifier removed |
| `$AA9D` | `JMP $AAA5` | knock update ignores VSS; 800-RPM minimum retained |
| `$ACFC` | `JMP $AD38` | disable VSS gear inference for shift-light path |
| `$CBD6` | `JMP $CBDB` | A/C logic ignores VSS qualifier |
| `$CF94` | `JMP $CF9C` | EGR enable ignores VSS qualifier |
| `$D2EC` | `JMP $D307` | purge primary VSS qualifier removed |
| `$D2F9` | `JMP $D304` | purge-off secondary VSS qualifier removed |
| `$DDC3` | `JMP $DDEE` | prevent VSS-derived ERR16/buffer failure state |

VSS DTC enables:

- `$5B01: $A2 -> $82` — ERR24 output/transmission-speed-low test disabled.
- `$5B2B: $F1 -> $E1` — ERR16 VSS-failure test disabled.

Known remaining VSS references are documented in the source trace. Of particular importance, TPS self-zero still contains a VSS/deceleration-derived offset-learning qualifier.

## 4. True-idle state split

Fuel-side closed-throttle simplification remains. True idle *control* is separately gated so closed-loop IAC and idle spark are not active simply because TPS is closed during high-RPM decel.

New scalars:

- `$FF88 = $2C` — True Idle Control Enter RPM = 1100 RPM (`X*25`).
- `$FF89 = $30` — True Idle Control Exit RPM = 1200 RPM (`X*25`).

Implementation:

- `$99F2 -> JMP $FEF8` — IAC qualification gate in code cave.
- `$A85A -> JMP $FF20` — idle-spark gate in code cave.
- `$0036.b2` (stock IAC qualification state) is reused as hysteresis state.
- `$4E8F: $0A -> $0B` — manual-transmission IAC behavior selected so the automatic-trans fallback cannot re-enable idle control outside the new gate.

State intent:

- TPS not in stock idle state -> drive.
- TPS closed, RPM >1200 -> closed-throttle decel/dashpot region.
- TPS closed, RPM <=1100 -> true-idle control may enter.
- 1100-1200 -> hysteresis.

The stock `$0050.b7` idle flag is currently used as the TPS-side prerequisite. Subsequent TPS tracing showed that this is not an absolute-voltage gate; it is based on the self-zeroed engine TPS value. The exact threshold and TPS learner behavior are documented separately.

## 5. Current binary identity

`BMHM_0.3.1.bin`

- SHA-256: `da9898b1f1342fe4b23f379ed7057916b141f5550c4b5b0f80a11771b4aa34a1`
- checksum `$4006-$4007`: `$216C`
- `$FE9F=$01`
- `$FF88=44` -> 1100 RPM
- `$FF89=48` -> 1200 RPM
- `$4E8F=$0B`
