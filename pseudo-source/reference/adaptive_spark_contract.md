# Burst knock, adaptive learning and spark gains

Authority is the recorded stock BMHM image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
These are raw fixed-point source contracts, with compiled-C comparisons against
actual instructions. No target compiler ABI or physical spark scaling is implied.

## Routines and integration

| C routine | ROM scope | Integration |
|---|---|---|
| `pcm_knock_gains` | CAD5..CB14 | Low-octane RPM factor, event gain and PE/non-PE cap; callable suffix of CA6B |
| `pcm_burst_gain` | CA4C..CA6A → CB14 | Callable tail of the scheduled C9F7 producer |
| `pcm_low_octane_learn` | CE10..CE7B | Called directly after the input dependency in slot6 |
| `pcm_low_octane_retard` | A77A..A791 | Callable slice of the broader A466 spark controller |
| `pcm_knock_burst` | AA33..AA80 | Optional burst latch/countdown and command subtraction |
| `pcm_knock_corrections` | AA33..AADB | Burst followed by the previously implemented normal-KR consumer |
| `pcm_ac_switch_inputs` | CB15..CC34 | Explicit unported AC/diagnostic-switch input boundary |

Slot6 preserves the stock order at 7B14..7B1A: CB15 input work, then CE10 learning.
The former `PCM_SLOT_06` whole-slot binding is replaced by
`PCM_AC_SWITCH_INPUTS`, which owns only CB15. A missing or failed input binding
stops before learning. Learning tests the full phase after that callback; it
runs only at06, once per complete 160-phase cycle in ordinary dispatcher fixtures.

Slot7 still delegates its complete body. MAT/PE and knock gains at CA6B..CB14
now have an implemented callable wrapper; the other slot7 callees remain
unported. See the [spark terms contract](spark_terms_contract.md). The earlier C9F7 body also remains part
of its existing slot dependency. This step does not replace those boundaries
with partial gain calls or change their cadence. The broad A466 spark root
remains delegated. The [command wrapper](spark_command_contract.md) now retains
command preparation and the upper limit before AA33, followed by the lower
limit and service edits after AA81's normal-KR slice. Output conversion and
remaining root admission still need ports. Producer/consumer sequence tests make those handoffs
reviewable without claiming the test call order is a new factory schedule.

## Named state and calibration

| Factory location | C owner | Contract |
|---|---|---|
| 0841 | `knock.octane_rpm_factor` | Scheduled low-octane RPM multiplier |
| 0842,020E,006E.1 | `knock.burst_gain`, `burst_countdown`, `burst_active` | Burst amount, wrapping countdown and latch |
| 0843,0844 | Existing `knock.event_gain`, `retard_limit` | Now have implemented producers |
| 0209..020B | `knock.activity`, `scaled_activity`, `adaptive_retard` | Retained learning state and its two scaling stages |
| 0052.0,0052.1 | `knock.learning_high`, `learning_low` | Separate first-observation latches; arbitrary both-set inputs are retained on routes that do not clear them |
| 003D.5,0050.4 | `runtime.power_enrichment`, `diagnostic_switch` | Explicit inputs; diagnostic switch is produced by CB15 |
| 01C0,01C2,01C9 | `spark.load_coordinate`, `previous_load`, `vacuum` | Spark load/history/vacuum inputs; distinct from REF's0067 coordinate |
| 01D9,01DA | Existing `reference.throttle`, new `spark.previous_throttle` | Current and previous TPS samples |
| 006F | `spark.load_status` | Gain/cap producer tests mask48 |
| 400F | `calibration.mode_f` | Shared feature byte; stock10 leaves burst bit3 clear |
| 4585..4593 | `knock.pe_retard_cap[8]`, `cruise_retard_cap[7]` | Cap curves with bounded input coordinates |
| 4594..45A4 | `knock.event_gain_curve[17]` | Event gain over the full RPM-coordinate byte |
| 45B6..45BD | Eight `learn_*` calibration fields | Coolant/load/change gates, high/low thresholds, increment/decrement and scale |
| 45BE..45D7 | `knock.octane_rpm[9]`, `octane_load[17]` | RPM and load multipliers |
| 46DF..46E3 | Five `burst_*` scalar fields | Load/TPS/change gates, duration and curve input cap |
| 46E4..46EE | `knock.burst_curve[11]` | Enough source knots for every reachable transformed input, including cap variants |

The gain inputs are sampled at their own ROM positions. They are not replaced
by one shared snapshot. The learner's01C2 input is the older of two load-history
latches, distinct from immediate01C1; `pcm_spark_base` now implements the A700
history producer within the still-delegated broader spark root.
Named state is cleared by the existing reset outline;
remaining reset stages and retained-state behavior still need their own ports.

## Exact arithmetic and transitions

`pcm_knock_gains` samples RPM62 separately for the low-octane RPM factor and the
event gain. PE cap selection samples RPM again and uses
`max((RPM62>>1)-16,0)`. Non-PE selection starts with source=255; a clear006F
mask48 substitutes vacuum01C9. Its cap input is `max((source>>1)-32,0)`.
All three curves use the existing rounded16-segment interpolation.

The maximum lookup inputs determine storage:127 needs 9 knots for low-octane
RPM,111 needs 8 for PE cap, and95 needs 7 for non-PE cap. `pcm_lookup16` therefore
accepts a knot pointer with the explicit requirement of at least
`(input>>4)+2` bytes. Its arithmetic is unchanged. These call sites and the
earlier17-knot callers retain ROM differential coverage.

Burst gain starts with `t=max(coolant-153,0)`. Because t<=102, the original two
byte shifts and second-carry saturation equal `min(255,4*t)` in this specific
routine. Multiply by 153, round by 128 and take the high byte. This input is at
most 152; then clamp to46E3 and interpolate46E4. Eleven knots cover every
reachable value even if the cap is changed to 255. Stock cap 112 makes the later
bytes adjacent to the stock curve numerically unused; the source preserves
their recorded defaults for reachable calibration variants.

Burst's global gates require400F.3, diagnostic0050.4 clear, and coolant strictly
above45DA. A failed gate retains the latch/countdown and skips burst subtraction.
The normal-KR consumer still sees any retained burst latch afterward.

- With an old active latch, decrement020E as a byte; zero wraps to 255. Clear
  the latch only when the result is zero. Subtract0842 from01EE with word wrap
  even on the call that cleared the latch.
- Without that old latch, require load below46DF and TPS below46E0. A negative
  current-minus-previous TPS rejects arming; otherwise require delta>=46E1.
  Arm the latch and load46E2. The new arm does not subtract burst on that call.
- The ordered correction wrapper then runs normal KR. A newly armed latch
  zeros normal KR; an expiring latch can permit both the final burst subtraction
  and a normal-KR subtraction in the same call.

Learning at phase 06 reads old0209 first. A sensor fault subtracts45BC with a
zero floor, preserves the learning latches, then stores and rescales activity.
Without fault, require coolant>45B6, load>=45B7, and either decreasing load or a
nonnegative load increase<=45B8 relative to01C2. Qualification failure clears
both learning latches and retains activity and scaled activity.

| Retard classification, in source order | Latch/state transition |
|---|---|
| 020C<=45BA, low latch clear | Set low, clear high; retain activity on this first observation |
| 020C<=45BA, low latch set | Subtract45BC with zero floor |
| Otherwise020C<=45B9 | Clear both latches; retain activity and scaled activity |
| Otherwise high latch clear | Set high, clear low; retain activity on this first observation |
| Otherwise high latch set | Add45BB with saturation at255 |

An admitted store also computes `scaled_activity=R8(45BD,activity)`, including
first-observation routes that retained activity. Here
`R8(a,b)=hi(a*b+128)`. Threshold inversion follows this literal test order; it
does not trigger an invented calibration normalization.

The separate A77A slice computes `load_factor=L1(load01C0,45C7)`, then
`adaptive_retard=R8(R8(octane_rpm_factor,load_factor),scaled_activity)`.
Both roundings remain. This value later enters the earlier composite spark
sum; it is distinct from020C and burst subtraction.

## Verification and remaining work

The adaptive suite adds 480,560 C/stock-ROM comparisons: 132,096 gain/cap cases,
135,337 burst cases, 142,818 learning cases, 65,792 adaptive-retard cases,
2,048 calibration/state variants, 2,048 joined/slot6 witnesses, 31 failed
mask/dependency prefixes and 390 history calls. All 201 scoped instruction starts
execute and all 83 new calibration bytes match stock.

The corpus includes every RPM/vacuum pair, every coolant/curve-cap pair,
every TPS/previous-TPS pair, every countdown/burst-gain pair, every activity/scale
pair, every current/previous load pair and every RPM-factor/scaled-activity pair
with the supplied load multiplier. Other witnesses cover equality, carry,
borrow, wrap, inverted thresholds, first/repeated observations, faults, latch
expiry, disabled feature gates and input changes at the CB15 boundary.

CB15 is explicitly stubbed in slot6 comparisons: the stub records admission,
can fail or change selected inputs, and returns through a real ROM RTS with
register clobbers. Its body, ADC behavior and physical switch inputs are not
modeled. ROM-side local stack use and balanced returns are checked; target C
stack costs, interrupt interleavings and physical timing remain separate work.
The kernel regression confirms ten CB15 admissions and one learning update per
160 phases with the selected admitted inputs.

Both host verification routes retain these adaptive entries alongside the newer
spark-terms, modifiers and command suites, bringing CTest to 18 checks. The C inventory is 116 public
routines: 47 implemented outlines, 40 dependency boundaries and twenty-nine algorithms.
These counts describe source organization, not whole-firmware equivalence. Base/environmental composite
construction and idle/transient/decel corrections are now implemented.
Resident overrides and limits/service are also implemented; remaining admission,
optional 1812 and output handoff keep explicit boundaries.

See the [knock consumer contract](knock_control_contract.md),
[factory upstream spark derivation](../../docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md)
and [scheduler map](../../docs/analysis/FACTORY_SCHEDULER_MAP.md).
