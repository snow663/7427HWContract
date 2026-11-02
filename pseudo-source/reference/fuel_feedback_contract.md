# O2 feedback, BLM learning and pulse corrections

At introduction this batch added25 public routines, bringing the source to245:112 implemented
outlines,102 implemented algorithms and31 dependency boundaries. Every public
routine has its own file. These callable stages preserve the factory state and
integer operations; the full running-fuel root remains unfinished.

## Entries and stops

| Stock scope | C entry | Behavior |
| --- | --- | --- |
| 863D..8661 | `pcm_oxygen_activity` | Raw O2 activity, separate from direction |
| E477..E561 | `pcm_closed_loop_admit` | Warmup, closed-loop and learning permissions |
| 8662..86AF | `pcm_oxygen_thresholds` | Airflow proxy and four threshold/interval views |
| 86B0..86F1 | `pcm_oxygen_direction` | Threshold/trend direction and change/age counters |
| 877C..878F,8911..891D | `pcm_oxygen_neutral` | INT/P neutralization, retaining O2 fraction |
| 86F2..878F | `pcm_oxygen_admit` | Control admission or completed neutral return |
| 8790..886E | `pcm_oxygen_proportional` | Error, P, interval and temporary window output |
| 886F..88CC | `pcm_oxygen_integrator` | Sign agreement, delay and equality-bound INT update |
| 88CD..88E8 | `pcm_oxygen_window` | Strict P-window and warmup suppression |
| 88E9..891D | `pcm_oxygen_combine` | Saturated INT/P combination and signed encoding |
| 863D..891D | `pcm_oxygen_control` | Contiguous controller, including early neutral return |
| F280..F28D | `pcm_blm_reset` | Reset all21 retained cells to128 |
| F28E..F2A9 | `pcm_blm_boot_clamp` | Ordered boot bounds across all21 cells |
| 8C73..8D9D | `pcm_blm_select` | Phase9F speed history, hysteresis and selected-cell validation |
| 8D9E..8DEE | `pcm_blm_transition` | TPS crossing and wrapped BLM-change qualification |
| 8E1D..8EB3 | `pcm_blm_learn` | Counted cell update and return-time sample stores |
| 8C73..8EB3 | `pcm_blm_control` | Selection/transition, existing decel histories and learning |
| 891E..8EB3 | `pcm_fuel_afr_learning` | Existing AFR/PE followed by the complete BLM tail |
| 80FC..8105 | `pcm_fuel_pulse_scale` | Rounded word multiplier without pre-double |
| 80EE..8105 | `pcm_fuel_blm_scale` | Saturated pre-double, then rounded BLM multiplier |
| 8032..8057 | `pcm_fuel_egr_blm` | EGR subtraction and PE learned-lean safeguard |
| 82ED..8341 | `pcm_fuel_derivative_correction` | Raw derivative publication, factor bounds and PW gain |
| 8342..837F | `pcm_fuel_baro_battery` | BARO matrix/fourfold scale followed by battery scale |
| 8380..83B0 | `pcm_fuel_feedback_apply` | Signed INT/P, MAP AE and0254 publication |
| 82ED..83B0 | `pcm_fuel_post_corrections` | Contiguous post-decel correction body |

## Shared state and calibration views

The existing raw/filtered O2, INT, startup003F context, PE, short-PW latch,
closed/idle AFR, REF packet and IAC selected-BLM owners are reused. Named new
state includes O2 activity/age, warmup and learning flags, interval/thresholds,
P/error/delays, signed026F,21 retained cells, BLM counters and081A speed history.
The existing0065 RPM history is now explicitly mapped in the joined fixture;
the BLM return produces the sample that the next PE invocation consumes.
The high EGR-fraction byte remains the spark owner; the new low byte completes
its01B2/01B3 word. Bit fields preserve the other owners sharing their addresses.

Source defaults come from SHA256-checked BMHM bytes. The four O2 curves use ten
knots each: input128 reads the next nominal curve's first byte even at zero
weight. The base-delay view supports every byte coordinate, including reads
through the neighboring matrix header. Both matrices retain offset, byte-wrapped
stride and endpoint-neighbor semantics. Test-only expanded backing is independently
checked against the recorded ROM.

The byte evidence corrects two HAC defects:866F compares against128, and87AD
contains the positive-error `BSET` missing from the text. Both byte sequences are
asserted by the differential suite.

## Control and arithmetic

Raw activity, filtered O2, direction, closed-loop selection and permission to learn
are distinct. The E477 service gate can force closed-loop selection; the faster
86F2 gate uses the opposite service-value polarity to select neutralization.
Warmup elapsed time uses the low byte of the shifted runtime word, preserving
wrap. Activity expires on a call finding its age already at the limit.

Direction follows raw O2 trend inside the threshold band. A change wraps its
counter, sets the notification and clears age; a steady direction saturates age.
Neutralization replaces only the high O2-filter byte and retains its fraction.
Idle P can atomically XOR the low003F context with05; SEI/CLI are literal mask
assignments. Failures preserve the completed P/context/mask prefix. Both selected
bit pairs use all-selected-bit BRSET semantics.

The P-window remains a local C value corresponding to the ROM stack temporary.
Error multiplication truncates; nonidle P uses a separately rounded doubled
product. INT updates require sign/direction agreement. Its calibration stops are
equality checks, with byte wrapping outside those values. The P-clearing window
uses two strict comparisons. Encoded026F is a signed additive PW correction.

BLM selection retains normal cells through inclusive hysteresis bounds and can
select five special cells. An invalid cell resets all21 retained values. Boot
upper/lower bounds are separate and apply in that order, including contradictory
bounds. Runtime selection and learning use their own bounds. Learning counters
retain the factory127/255 behavior; small errors/direction disagreement preserve
counts. Every completed learning return clears the cell-change flag, saves RPM63
at0065 and raw O2 at01D4.

Direct `pcm_blm_learn` calls must use a selected index0..20 when a write is
admitted. An invalid index returns BAD_CONFIGURATION after completed counters;
it does not model arbitrary writes past the21-cell retained bank. Normal selection
always supplies a valid index. Configuration contracts cover this explicit bound.

BLM first doubles PW with saturation, then applies the rounded gain. Its neutral
128 therefore retains the factory saturation behavior. The decel multiplier entry
omits that double. EGR rounds its fraction word with16-bit wrap before deriving
its subtraction; PE suppresses a learned-lean BLM application. Derivative logic
publishes its raw value before factor bounds. BARO and battery gains remain
separate. Signed INT/P addition precedes MAP AE addition and the0254 packet store.

## Verification and remaining work

The suite contains927,344 compiled-C/ROM comparisons across all750 scoped
instruction starts, including377 selected failure prefixes and1,024 retained
history calls. It checks312 distinct source-profile bytes (334 overlapping
read-view entries) and1,054 expanded fixture bytes against stock.
It compares mapped state, all21 cells, typed bus order, literal masks,
completed frames, bounded configuration errors, callback prefixes and retained
histories against real ROM instructions. Coverage includes the O2 controller,
closed-loop admission, complete BLM tail, reset/boot helpers and the specified
correction ranges. Explicit joins cover AFR/PE/BLM, input/filter/control, startup
admission and selected correction/finalizer/REF calls.

Those joins are test compositions rather than a new broad fuel admission.
The cut/decel/reservoir and sync/async stages are now connected through852B by
the [delivery contract](fuel_delivery_contract.md). Ignition/STOP handling and
the852C tail still need resident C implementations.
Required EGR producers and broader fuel/slot1/4/D/F admissions stay explicit.
The optional1800 extension still stops the joined AFR/BLM body when absent or
failed. Physical mixture response, target ABI, interrupt timing and backend
hardware behavior remain separate validation.

At introduction both host routes contained48 checks:24 quick contracts/provenance checks and24
ROM suites. After local verification, publish the batch and report GitHub CI as
pending. Check its completed results before a later merge; do not wait for Actions
in the implementation turn.
