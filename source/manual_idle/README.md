# Single manual-transmission idle controller

This is a new strategy for the **exact 0.3.12 spark/idle Rev A** image, SHA-256
`d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e`.
It replaces both transmission-dependent idle strategies in an **in-memory
simulation overlay**. No flashable BIN is produced. The truck's image and the
registers' image identity remain Rev A. The pending deceleration-spark and
cold-idle spark-table changes are separate and are not implemented here.

[The complete trace and integration notes](../../docs/investigations/MANUAL_IDLE_REPLACEMENT.md)
describe the original paths, shared consumers, removals and limits.

## Source

- [manual_idle.asm](manual_idle.asm): executable HC11 strategy, with symbolic
  calibration, replacement addresses and the existing routine-entry ABI.
- [manual_idle.c](manual_idle.c): independently written native-C reference using
  a CPU-memory view. It is not a compiler-generated HC11 binary or a new
  hardware abstraction layer.
- [manual_idle_layout.h](manual_idle_layout.h): generated addresses for the C
  comparison. The original OEM pseudo-source is preserved separately.

The controller has one temperature-based RPM target and one runtime learned
baseline. It uses bounded P/I correction, one startup-air fade, one TPS follower
and an optional A/C feedforward adder. All strategy state updates use the
existing main-IAC scheduling admission. The slot7 target publisher remains
for timing compatibility, and slot9 becomes a returning stub.

The runtime learned value starts from a fixed seed after boot, stopped/crank
initialization or homing completion. It **does not retain learned air across
key cycles**. No Park/Drive/A/C learning banks, cross-bank transfer, cold-bound
snapshot gate, derivative state or BLM-driven RPM target addition remain in
this strategy. A/C has a simple load adder, not another learned bank.

## Calibration proposal

The existing `$FF60` RPM curve is reused by both startup and running calculation.
New P/I gains, cold-air feedforward, follower decay and A/C air are **initial
development parameters, not values established by the truck's logs**. The
baseline seed (38 internal units) and starting-air amount (60 internal units)
match the current image's corresponding Drive defaults, but this does not make
the new combined controller behavior equivalent to the old one.

| Parameter | Proposed value | Meaning |
|---|---:|---|
| RPM target | Existing `$FF60` | Raw coolant-index lookup, 12.5 RPM per target count |
| Capture / release RPM margin | 100 / 200 RPM | Relative to the requested idle target |
| Capture / release normalized TPS | 2 / 3 | Raw normalized TPS counts, not percent or volts |
| Integral qualification | 16 main calls | Approximately 0.4 seconds at nominal admission |
| Error deadband | 25 RPM | Error removed before P/I multiplication |
| Proportional gain | 64/256 air units per error count | Capped at 24 internal air units |
| Integral gain, either sign | 4/256 air units per error count per main call | Baseline bounded to 0..180 air units |
| Starting baseline | 38 air units | One Q8.8 word, with fraction explicitly initialized |
| Startup air | 60 air units | Falls by 1 every 4 running main calls; nominally about 6 seconds |
| Follower | TPS above the closed-throttle band, capped at 40 air units | Immediate rise, decay 0.5 air unit per main call |
| Stall threshold / addition | Target minus 200 RPM / +12 air units | Shared stall flag is published independently of output saturation |
| A/C addition | 5 air units | Follows the existing request bit `$0052.5` |

Cold-air feedforward is a single monotonic 17-knot table. Its coordinate is
**RAM `$0283`**, not effective coolant byte `$0006` and not degrees Celsius.
The existing producer subtracts/limits its coordinate before publication.
The proposal reaches zero extra air at index160. It needs measurement against
actual cold-start airflow before a release. All air values above are internal
controller coordinates, **not IAC motor steps**.

Integral action freezes outside capture, before qualification, during startup
air or follower decay, during DFCO, and while the existing driver reports low
battery. Directional anti-windup also freezes it against a previously saturated
upper/lower air command. Opposite-direction correction remains allowed. The
physical step-position limit is not treated as a measured airflow limit.
Proportional overspeed correction also operates on the closed-throttle approach
before idle capture, so that path can shed air without learning a false baseline
while the engine may still be coupled to the wheels. Initial air calibration
must still put the engine within the proportional controller's capture ability.
The TPS follower is zero throughout the closed-throttle band; sensor counts
accepted as closed cannot hold integration off by maintaining follower air.
Each positive feedforward stage saturates before P is applied. An overspeed
P subtraction remains effective even when feedforward reaches the upper rail.
The default RPM/TPS hysteresis matches the retained Rev A fuel-idle classifier.
Any later calibration change to those thresholds must keep both consumers
aligned or explicitly unify their calibration source before release.

## Verification

From the repository root:

```sh
python tools/manual_idle_overlay.py
python tools/verify_manual_idle.py --check-recorded
python tools/trace_manual_idle.py /absolute/path/to/0.3.12_engine_only_spark_idle_revA.bin
python tools/verify_manual_idle_runtime.py /absolute/path/to/0.3.12_engine_only_spark_idle_revA.bin
```

The first two commands need no full image. They use recorded excerpts and a
native C compiler. The last two enforce the exact original-image hash, create
an overlay **only in memory**, and write reports rather than firmware files.
Longer hot/cold reset scenarios are recorded separately and can be repeated
with `--case hot_idle --main-calls 320 --budget 14000000` and the corresponding
`cold_idle` case, using `--output` to keep their reports separate.

This is a software implementation and integration candidate. The simulator
imposes RPM; it does not predict the engine's reaction to new air commands.
Passing tests therefore establishes neither stable warm-up nor the correct
mixture, gains, cold airflow, physical IAC behavior or worst-case interrupt
deadlines. The retained spark slope can still interact with the new controller.
