# Slot9 throttle follower, slow decay, diagnostics and reset admission

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Actual ROM instructions supply the following C routines. Each public routine
has its own file; `include/iac.h` declares the IAC functions.

| Scope | C interface | Responsibility |
|---|---|---|
| 7B2F..7B38 | `pcm_slot_09` | Ordered EGR demand, slow IAC, VSS filter |
| A2B0..A406 | `pcm_iac_slow` | Running admission, ordered work and late phase gate |
| 9CFD..9E98 | `pcm_iac_follower` | Filtered throttle follower, retained latches and airflow word |
| A2BA..A329 | `pcm_iac_slow_decays` | Switch, startup-flow and startup-RPM decays |
| A32A..A35B | `pcm_iac_drive_limit` | Selected drive cell cap from its snapshot |
| A35C..A397 | `pcm_iac_kicker_diagnostic` | Paired TPS baselines and retained two-observation fault |
| A39C..A3E5 | `pcm_iac_learning_diagnostic` | Ordered qualification and byte counter/fault |
| A3E6..A3F9 | `pcm_iac_reset_admit` | Reset request/validity, current0044.4 and VSS gates |
| A3FA..A406 | `pcm_iac_reset_request` | Software homing state, target0 and position255 |
| F4B6..F4BB → F4C5..F4DD | `pcm_lookup_scaled` | Scaled coordinate and rounded interpolation |

Slot9 now calls the real slow IAC between named `PCM_EGR_DEMAND` and
`PCM_VSS_FILTER` dependencies. Their CF16..D03D and D4DA..D4EA implementations
remain unfinished. The former whole-slot9 task ID is reserved and unused.
Missing bindings return UNIMPLEMENTED with the dependency identity; a failure
retains the completed prefix and stops the later calls. These are the actual
three factory admissions, not partial work injected into an otherwise opaque slot.

The root returns immediately when004F.7 is clear, requiring no profile and
changing no IAC state. Running work preserves follower → decays → drive cap →
kicker diagnostic. Phase bit5 then skips both the learning diagnostic and reset
admission. Earlier changes remain committed on that phase-gated return.

## State and ownership

| Factory location | C owner | Use |
|---|---|---|
| 0880 | `iac.follower` | Retained follower airflow word |
| 0882..0886 | `follower_filtered`, `follower_hold`, `follower_closed_threshold`, `follower_age` | Word filter, hold, threshold and age |
| 0282 | `starting_coolant` | Starting coolant, separate from current/indexed coolant |
| 087B,087C | `switch_adder`, `switch_hold` | Slow switch decay |
| 086B,086C | `startup_flow`, `startup_flow_divider` | Startup flow decay |
| 085C..085E | Existing `startup_rpm_adder`, new divider/hold | Shared desired-RPM startup term |
| 088E | `learning_count` | Byte count with explicit wrap |
| 003F.6,0018.2,0017.7 | `startup_cancel`, `kicker_fault`, `input_fault` | Separate flag owners |
| 0044.4 | Existing `reference.latch_inhibited` | Actual reset gate in this path |
| 0016 | Existing `runtime.primary_faults` | Independent10/01 diagnostic tests |
| 0007,0008 | `position`, `target` | Software count and target; no position sensor is established |

The earlier background state, cells, snapshots, pending flags, baseline values
and spark inputs are reused.0036.5 remains the existing spark override owner;
the IAC raw context continues to exclude it.0044.4 is not0051.3, represented by
`runtime.ignition_off`. Tests exercise the flags independently. The host reset
outline already clears the enlarged IAC group; target retained/reset stages
remain unfinished.

## Follower and extended cracker

Scale TPS to `min(255,4*TPS)`. Above the old filtered high byte, replace the
working word with the selected capped byte and zero fraction; drive also
reloads0884 from the VSS curve. At/below it, a nonzero hold retains the whole
old word. Otherwise use the park gain or a VSS lookup. Low load replaces the
gain with the truncated product high; force zero gain to1 before the existing
signed-floor byte lag. Both VSS lookups cap speed at80 and double it.

The working word remains local until9DEE. While0037.0 is clear, starting coolant
outside `[509A,509B)` or runtime00FD strictly above word509C sets that bit.
It remains set until another owner clears it. Stock509A=509B=49 gives an empty
window, so a clear bit is set on the first follower admission. Modified source
profiles exercise the temporary clear-bit multipliers; this is not a statement
about the user's current tune.

TPS-open0039.7, a follower hold or closed qualification0036.2 skips minimum
insertion. Closed qualification sets age255; the other skip routes clear age
and0037.1. On the eligible route, DFCO with option4E8F.1 clear sets0039.6 and
retains the age. Otherwise insert the coolant minimum, with its temporary
four-times-product multiplier while0037.0 is clear. Compare age before increment:
an old age at its limit sets0037.1; incrementing into the limit does not.

Commit the filtered word, clearing a low-only fraction below40. Subtract0885
from its high byte while retaining its fraction. A borrow writes follower0
directly, bypassing later hysteresis/DFCO-release publication logic. Otherwise:

1. Apply the selected rounded word gain when0037.1 is set.
2. Apply the scaled RPM lookup's rounded gain and multiply by4 with saturation.
3. Only if the RPM multiplication did not overflow, apply the coolant gain and
   another saturating multiply by4.
4. While0037.0 is clear, apply its final rounded gain and saturating multiply by4.

The overflow exit after step2 skips the coolant multiplier. Directed word
sweeps set that multiplier to zero to distinguish the exit from a generic clamp.
With TPS open, publish only when the high byte of absolute change meets5087.
With TPS closed, leaving a DFCO-suppressed condition clears0039.6 and publishes
once; otherwise retain a nonzero follower against an equal or rising proposal.
This is not a symmetric instantaneous throttle lookup.

## Decay, caps and fault state

The switch divider decays on old zero or on decrement-to-zero, floors the
subtraction, and reloads only if the adder remains nonzero. Startup flow uses
the same divider admission, decrementing its nonzero adder by1.003F.6 clears
the startup adder directly while retaining its divider.

Startup RPM has a separate initial hold that decrements only with phase high
nibble zero. The hold's expiry call still skips divider decay. Later calls use
the RPM divider and reload.003F.6 clears the adder without aging hold/divider.
The desired-RPM producer observes the resulting shared085C on its next admission.

Drive limiting requires0036.1 and both0036 bits0C clear. Add the selected AC/no-AC
snapshot and its limit as bytes; carry skips the cap. Replace only a strictly
larger high byte, storing fraction0. This direct cell cap is separate from the
background routine's queued transfer proposals.

The kicker diagnostic requires both enable bits, clear done0039.2 and both
baseline bits0039&03 set. Baseline subtraction borrow or a too-small difference
sets0009.6 on a first eligible failure; a later eligible failure with that bit
already set sets0018.2. A pass clears both flags. Every evaluation sets done;
the retained error is not automatically cleared on a first failure or skipped call.

The later learning diagnostic is admitted after the root's phase-bit5 gate.
Disabled5B02.3 retains its count/fault. Enabled qualification rejects the VSS/input
faults, low battery, absent integral admission, kicker failure, either nonzero
full cold word, or insufficient filtered error. Rejection clears count/fault.
An old count strictly above its limit sets0018.3; other counts increment as bytes.
Old countFF with limitFF wraps to0 and retains the fault's prior state. The
background warm-snapshot route remains a separate0018.3 clear.

## Reset request and remaining motor work

Existing reset0009.0 or valid0009.2 skips reset admission. Otherwise0044.4 takes
the reset directly, without a calibration read; its clear route requires VSS
at/above4EB7. The common helper sets0009.0, clears0036 bits1C, writes0008=0,
then0007=255. It retains unrelated IAC bits and the separate spark override.
Direct helper admission needs no profile.

Those are software homing requests. The [resident main93D0 controller](iac_main_contract.md) now consumes the
target/reset process and establishes software completion.91A3 phase/count
service is now implemented in the [step port](iac_step_contract.md). The software value255 does not establish a physical pintle position.
The main port preserves the service controller's nonlocal exits.

## Source profiles and verification

The new profile adds86 distinct source bytes. The scaled RPM descriptor uses
scale08 at5064 and nine reachable knots5065..506D. It checks backing length
before reading either knot and retains the output on BAD_CONFIGURATION. Other
views include17 coolant/minimum knots and12 VSS hold/gain knots, including their
reachable neighboring reads. Overlapping stock views do not fix our future
executable/calibration layout. The descriptor pointer is not a serialized format.

ROM comparisons extend the RPM backing to256 test-only bytes to exercise every
input/scale byte pair without reading absent native storage. Every fixture byte
is checked against stock. These neighboring bytes are not256 newly declared
production calibration parameters; production keeps the nine-knot stock view.
Default checks inspect every new source view, including overlapping bytes.

The new suite checks mapped state, ordered transactions/dependencies, final mask,
missing-task identity and completed local ROM frame balance across230 output
bytes. It rejects unexpected RAM writes. All348 instruction starts in the
follower, slow root, slot9 wrapper and scaled-lookup scopes execute. The complete suite adds749,466 comparisons.

The corpus includes all65,536 scaled input/scale pairs;149,504 follower/TPS/overflow
cases;131,072 decay cases;131,072 snapshot/current/AC cases;131,072 baseline/fault
cases;65,536 learning count/limit pairs;65,536 reset speed/limit pairs;2,560 reset
flag/gate witnesses;2,048 profile/state variants;4,346 joined/callback witnesses;
320 failed prefixes and512 retained-state calls.

Joined calls explicitly supply background/slow admissions and subsequent normal
spark calls. History inputs supply intervening hold changes. They do not infer
the acquisition pipeline, intervening main-IAC admissions or physical cadence.
The [main IAC suite](iac_main_contract.md) separately checks hold aging.
EGR/VSS and any enabled180F/1812 modules retain explicit return fixtures. The
full160-phase kernel regression uses the real slow body and verifies ten EGR/VSS
admissions and the absence of a whole-slot9 binding; the main port now also
updates shared qualification/error state during the full cycle.

Both host routes now have36 CTest entries. CI runs independent suites two at a
time; they do not share mutable fixture state or generated artifacts. The source
inventory is172 public routines:76 implemented outlines,39 dependency boundaries
and57 algorithms. Target ABI, interrupt entry, coherent word access, linker/RAM/
stack fit and physical peripheral/motor timing remain separate validation.

The main93D0 IAC controller and service/reset/learning consumers are now
implemented, and the91A3 step service is now checked separately. Other scheduled producers remain explicit.
