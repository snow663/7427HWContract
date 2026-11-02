# Background IAC, desired RPM and queued learning work

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Actual instructions supply the desired-RPM producer at989C..99C4, its9250..925D
switch helper, kicker helpers at920E..923F and the complete9E99..A2AF background
body. Each public routine has its own file and declaration in `include/iac.h`.

| Order | Factory scope | C interface | Result |
|---|---|---|---|
| 1 | 989C..99C4,9250..925D | `pcm_iac_desired` | Desired RPM0857, base/offset/count state and stall threshold0868 |
| 2 | 9EA3..9EE9 | `pcm_iac_movement` | Movement cold-word gain and DFCO decay |
| 3 | 9EEA..9FDD | `pcm_iac_kicker` | Ordered qualification, phase-gated timer and helper admission |
| 3a | 920E..9225 | `pcm_iac_kicker_disable` | Clear active/qualification state and request kicker output |
| 3b | 9226..923F | `pcm_iac_kicker_enable` | Initialize TPS-zero high byte/timer when inactive and clear output request |
| 4 | 9FDE..A12C | `pcm_iac_cold` | Cold bounds/decay, queued cold transfer or warm snapshots |
| 5 | A12D..A153 | `pcm_iac_transition_decay` | AC-adder hold, clear and divider decay |
| 6 | A154..A287 | `pcm_iac_transfer` | Queued opposite-gear and opposite-AC integral words |
| 7 | A288..A2AF | `pcm_iac_publish` | Optional hold aging and selected snapshot086A |

`pcm_iac_background` preserves that order and stops at the first failed prefix.
The running qualification is existing004F.7, independent of fuel running. A
stopped entry jumps directly to publication atA29A: no desired-RPM update, decay,
learning or hold decrement, and no calibration requirement. Production slot7
calls the resident body directly. The old `PCM_IAC_BACKGROUND` enum remains
reserved without renumbering and has no production binding requirement.

## Named state and shared ownership

| Factory location | Source owner | Meaning in this scope |
|---|---|---|
| 0036 bitsDF | `iac.context` | AC/gear, qualification, transition and kicker context |
| 0036.5 | Existing `spark.override_request` | Separate spark owner, excluded from the IAC raw mask |
| 0037..0039,0009 | IAC flags | Kicker, queued transfer, learning and retained state |
| 029D..02A6 | `iac.bank[0]` | Park no-AC/AC integral words and snapshots, cold word and bound |
| 02A7..02B0 | `iac.bank[1]` | Drive equivalents |
| 02B1,02B2 | `baseline_on`, `baseline_off` | Kicker TPS baselines |
| 02F6,02F7 | `tps_zero_high`, `tps_zero_low` | Separate bytes; enable updates only02F6 |
| 088F,0891,0895,0897 | `proposed[bank][ac]` | Integral transfer work words |
| 0893,0899 | `cold_proposed[bank]` | Cold transfer work words |
| 0857 | Existing `spark.iac_desired_speed` | One shared producer/consumer field |
| 0866,0867,086A | `hold[]`, `selected_snapshot` | Running-only hold aging and selected publication |
| 3008.2 | Explicit PORTD read | Optional switch sample |

Existing coolant0006, TPS01D9, battery00A7, BARO02F4 and VSS0284 fields are
reused. New boolean fields represent only their assigned bits in003E,0018,004B
and038F. The ROM fixture merges these fields back into raw bytes and compares
213 distinct output bytes, including the preceding spark/slot7 state. Unrelated
bits must survive. The host reset outline clears the new IAC state; this does
not replace the unfinished target reset/retained-memory stages.

## Desired RPM and switch sample

The coolant coordinate is a byte. Values above160 transform with wrapped
`u8(2*(value-160)+160)` before the rounded lookup. AC/drive select one of four
curve views. Low battery and filtered roughness add truncated product-high
bytes with their separate limits; these products do not use rounded gain.

Invalid BLM cell/value or insufficient coolant clears085B. Otherwise a count
below its limit increments only when the phase high nibble is zero. The call
that increments into the limit still skips the BLM adder; a following call
whose old count meets the limit adds it. The startup term in park first wraps
the doubled byte, then uses rounded gain. Additions wrap as bytes. A decreasing
base slews by one per call before switch processing.

Option4E8F.4 admits the switch behavior. Threshold selection precedes PORTD
sampling. The helper preserves its register-held threshold, while later reads
of0857,085F, offset, delay and context remain fresh where the ROM reads them.
Directed callbacks change these fields during the read to distinguish those
cases. Switch delay expiry and offset changes preserve the original call order.
The final stall value is either the selected literal factor or the truncated
desired-speed product, selected by option4E8F.7.

Service override0038.6 returns before desired/stall publication, retaining both
values. Other running background work continues. A failed PORTD read preserves
the already-committed base/count prefix and retains the later outputs. It
returns NO_HARDWARE through the existing explicit transaction interface.

## Movement, kicker and decay

Movement gain is admitted only if0009.1 is clear and byte0284 is strictly above
4EC0. Stock4EC0=FF closes this gate for every byte input. Tests explicitly change
the profile to exercise both cold-word gains and the one-time latch. This stock
finding does not assert the value in the user's current tune.

DFCO decay uses byte DEC before checking zero. An old divider of zero wraps to
255. An expiring divider decays on that call. Exact subtraction to zero retains
0038.5; a subtraction borrow clears it. AC-adder decay instead checks the hold,
clears the adder when AC is off, and treats an already-zero divider as ready.

Kicker qualification retains the factory branch order across service, cold,
BARO, TPS, VSS, drive integral, error and context gates. Multi-bit0036 mask0C
requires both bits. Phase gating uses the high nibble, retaining the initial
phase07 timing strategy. An inactive disable retains the timer; an active
disable clears it. Enable initializes only an inactive kicker, writes02F6
without changing02F7, and clears the separate004B.7 request on every call.
The request is software state; this background body does not drive a motor.

## Cold bounds, snapshots and queued transfers

The cold route is selected by the bound high bytes. Nonzero fractions alone
do not select it. A nonzero cold delay decrements without decaying on that call;
old zero performs the gains and reload. A decayed bound whose high byte reaches
zero becomes a zero word. Each cold word is limited to its new bound. The
reload combines two lookup views and saturates the doubled product toFF.

Upper/lower cold comparisons can queue an opposite-bank word in0893/0899 and
change0038.4. High-zero or gain-zero routes can retain an earlier pending bit;
the explicit lower comparison can clear it. Stock4EEE..4EF1 are zero, so
modified profiles exercise these normally inactive transfer arms.

When both bound high bytes are zero, qualified coolant/error/context conditions
permit warm snapshots and clear0018.3. Park updates its selected snapshot
without setting the drive warm flags. Drive sets0009.4 or.5 according to AC.
The cold and warm branches remain distinct even for fractional-only bounds.

Integral transfer requires0036.3, clear0036.4 and no003E.2 low-battery flag.
The gear comparison uses high-byte differences and separate park/drive limits.
It queues the opposite gear's selected AC word and sets or clears that word's
pending bit. The AC comparison uses the complete word difference, selects its
lower/upper limit in order, and queues the current gear's opposite-AC word.
These flag mappings differ. Proposals normally have zero fractions; carry from
the AC-off addition storesFFFF, including itsFF fraction. Proposals never
directly overwrite the learned029D/02A0/02A7/02AA cells in this body.

Running publication ages nonzero0866/0867 holds, then selects a snapshot by gear
and AC. Stopped publication skips both decrements. Slow/main IAC consumers of
these words remain separate source work.

## Source calibration views

`PcmIacCalibration` and `calibration/idle_tables.c` retain137 distinct ROM bytes.
The four17-knot RPM views start at4F32,4F41,4F50 and4F5F. The17-knot cold-delay
view starts at4EDC; the runtime view has six backing bytes at4EE9 because the
lookup reads a neighboring knot even at the capped coordinate64. Views can
overlap in the stock image. Their explicit backing preserves raw-byte behavior
without making neighboring bytes independent calibration parameters or fixing
our eventual executable/calibration placement. Stock option4E8F=0E leaves the
switch behavior off; profile variants test it on.

Stopped publication and inactive helpers retain their actual early-return
configuration behavior. Paths needing profile data reject a missing root/IAC
profile with BAD_CONFIGURATION. The profile is an immutable source object,
not a serialized EEPROM layout.

## ROM oracle correction and verification

Partial-mask IAC witnesses exposed an error in the simulator: BRSET used an
any-selected-bit test. The official
[NXP M68HC11ERG, rev2.1, p12](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf)
specifies all selected bits set; BRCLR requires all selected bits clear. Both
direct and indexed BRSET implementations now follow that rule. Exhaustive tests
cover all256 values and256 masks, both branches, and direct/X/Y forms:
393,216 instruction vectors, including mask zero, retained CCR and operand.
This change does not establish instruction cycle accuracy.

All18 simulator tests pass locally, including actual BMHM boot and a100,000
instruction run, alongside all190 factory tests and the earlier C suites.
Historical factory replay guards keep their original zero/full-mask witness
domain; they are not broadened by silently changing an old proof's scope.

The new suite adds1,645,037 compiled-C/ROM comparisons:

| Corpus | Calls |
|---|---:|
| Calibration/state variants | 1,024 |
| Desired RPM, context, BLM expiry and switch | 393,216 |
| Movement words/gains and DFCO divider | 131,072 |
| Kicker flags/timer and enable/disable | 262,144 |
| Low-BARO, small integral and error qualification | 2,560 |
| Cold bounds, transfer and warm snapshots | 262,144 |
| Gear/AC integral transfers | 524,288 |
| AC amount/divider | 65,536 |
| Background, slot7, subsequent normal call and callbacks | 2,208 |
| Failed switch/probe/module/publication prefixes | 333 |
| Retained-state histories | 512 |

All559 instruction starts in the desired/helper/background scopes execute.
The suite compares mapped state, ordered transactions/hook/mask events, final
mask and missing-task identity, rejects unexpected RAM writes and checks ROM
frame balance on completed calls. Missing180C/180F/1812 and the unfinishedACA7
body retain explicit fixtures.9E99 is executed, not stubbed. A subsequent phase8
spark call is supplied explicitly; the intervening input pipeline is not inferred.

Only the earlier400,081-case slot7 suite links `tests/iac_background_boundary.c`
to preserve its narrow fixture contract. Production, the new suite and the
full160-phase kernel tests use the resident IAC body with its task binding absent.
Both host routes contain34 CTest entries. The inventory is172 public routines:
76 implemented outlines,40 dependency boundaries and56 algorithms.

The [slow IAC and9CFD follower](iac_slow_contract.md) now run in slot9.
The [main IAC controller](iac_main_contract.md) is now implemented; next is the step driver. ACA7, upstream acquisition and other scheduled producers remain explicit.
Target reset/interrupt assembly, compiler ABI, coherent shared-word access,
memory/stack fit and physical motor/timing validation are still required. This
source and its witness corpus do not constitute a flashable target BIN or a
whole-program equivalence proof.
