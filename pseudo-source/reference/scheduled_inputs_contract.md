# MAP, VSS, AC, shift-lamp and environmental input batch

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
This batch implements six related groups in one PR while retaining one public
routine per source file. The current inventory is 180 routines: 82 implemented
outlines, 64 algorithms and 34 explicit dependency boundaries.

| Stock scope | C routine | Admission |
|---|---|---|
| 7DB6..7DF0 | `pcm_map_transient` | Callable fuel-group slice; stops before TPS acquisition |
| D4A3..D4D9 | `pcm_vss_calculate` | Callable raw VSS quotient/age producer |
| D4DA..D4EA | `pcm_vss_filter` | Resident slot9 tail after slow IAC |
| CB15..CC34 | `pcm_ac_switch_inputs` | Resident slot6 prefix before octane learning |
| ACA7..ADA9 | `pcm_shift_lamp` | Resident slot7 tail |
| C9F7..CA6A →CB14 | `pcm_environment_inputs` | Callable environmental producer including existing burst-gain tail |

The broader fuel and slot4 wrappers remain unfinished. These callable slices do
not silently skip their other scheduled producers or establish complete caller
cadence. Slot6, slot7 and slot9 preserve their existing call order. EGR demand at
CF16 and unsupplied optional modules retain explicit interfaces.

## MAP transient selection

The new context is the existing AC mirror0041.4 plus0089.5 when400F.7 is clear.
Compare that with old0047&FE. A changed context, an absolute byte RPM-high change
above413A, an inactive0050.7 or **no selected bit set in003E&A0** reloads01C5 from
4139. The actual BRCLR permits either selected bit; it does not require both.

Otherwise a nonzero countdown decrements. A call decrementing1 to0 still sets
0047.0; the next stable call finding0 clears it. Always replace context bitsFE
with the newly calculated context. The existing `io.map_transient` remains the
canonical bit0 consumed by the common MAP filter. The0065 producer remains
separate; this helper does not invent a previous-RPM update.

## VSS observation, quotient and filtering

Common I/O already increments080C when the observed3FC4 timestamp differs from
080D. Raw conversion uses080C,080D,080F and0811. With no new observations,
decrement a nonzero age and clear0812 only at zero. With observations and a zero
old age, retain the old quotient and seed the previous timestamp. With a nonzero
age, form `(460*count)&FFFF`, divide its unsigned fraction by the wrapped timestamp
difference, and store the quotient. FDIV overflow or zero denominator produces
FFFF. Clear the observation count, save the timestamp and reload age27 hex.

The numerator wraps before the division; replacing it with an unlimited-width
product changes high-count behavior. These are observed timestamp changes, not
a guarantee that polling captures every physical edge. VSS scaling, clock and
physical device behavior retain the existing hardware contracts.

Slot9 applies F436 word lag with gain4E8E to0812 and the prior0284/85 word. Its high
byte remains `spark.vehicle_speed_high`, shared with the existing spark/IAC
consumers. The new fraction owns0285 only. Slow IAC precedes this filter in the
same slot, so it sees the earlier speed sample rather than a reordered update.

## Diagnostic and AC qualification

CB15 assigns the mask true, clears0050 bits18, then publishes diagnostics from
082F: below40 sets bit10;40 through99 sets bit08 only with0044.0;100 and above
sets neither. Literal CLI follows this publication. Only then inspect400F.2.
With that feature clear the AC states are retained. A failed backend call retains
its completed prefix, and a missing optional AC profile fails after the diagnostic
prefix when the feature admits it.

With the feature set, retain the runtime/input gate, entry/exit holds, TPS word
count, IAC context, coolant and speed thresholds, throttle-release delay, RPM
qualification and running-RPM inhibition in their actual order. Threshold tests
use the old count. The throttle word increments with wrapping; the byte increment
paths retain the instruction's zero-result store guard. The context0036.4 route
clears only0041.4 and can retain0052.5. Other rejection routes clear both as the
stock body does. The delay publication calls and RPM-release qualification are
admitted-call counts, not a new millisecond conversion.

The AC request0052.5 and mirror0041.4 are the same owners used by housekeeping and
IAC. There is no duplicate flag. Housekeeping's alternate feature route and CB15's
AC route therefore interact through the existing shared state.

## Shift-lamp counter, ratio and lookup views

The shared400E.2 feature gate precedes all state changes. With it clear, retain
lamp, timers, counters and gear estimate. Diagnostic and service overrides have
their original priority and can publish the lamp without a peripheral read.

The normal route reads word3FE0, subtracts the current0847 baseline, stores0849,
and saves the returned counter before the coolant/TPS/speed gates. A callback
changing0847 after the read participates in the subtraction; a callback changing
the peripheral word does not replace the latched sample. Failed reads retain the
old baseline and delta. The hardware constant names the recorded address only.

Gear estimation uses FDIV(15,period005F), wrapped `delta+(delta>>1)`, IDIV and the
low quotient byte. Four successive threshold comparisons can leave0845 equal5;
there is no added fourth-gear clamp. Source counts and wrap are preserved even
when they are outside the normal admitted vehicle state.

The four RPM views begin5125,5130,513B and5146. Each has an11-byte stride, and an
endpoint lookup still reads its neighboring byte. The flat55-byte source view
5125..515B preserves those shared neighbors plus the barometric view at5151.
RPM is capped at200 before subtracting40; barometric input subtracts96 with a
zero floor. The TPS product rounds and saturates, while the later doubled
RPM/baro product uses its actual carry saturation without an invented rounding.

Threshold failure reloads0846 according to the retained/current gear group and
clears0053.2. Qualified calls decrement a nonzero hold while keeping the lamp
clear; a later call finding0 sets it. Early high-RPM and override paths retain
their shorter prefixes. The lamp bit shares0053 with existing IAC/spark state.

## Environmental publication and profiles

C9F7 successively publishes01E5,0243,0272,01CB and01BB, then runs the existing
burst-gain tail to0842. Retain the separate coolant index0283, index/2 factor,
192 coolant cap, conditional saturating subtraction and density cap-before-80
lookup. Failure of the bounded density view preserves the earlier four stores
and retains the old density and burst gain.

The suite checks185 source-profile bytes, including shared earlier knock bytes.
Read views include neighboring stock data where actual indexing reaches it;
that does not declare each byte an independent calibration parameter. Production
density has eight reachable knots. Twelve verified fixture knots admit modified
cap profiles through255 without silently reading outside native backing.

## Verification and remaining work

Local evidence covers1,603,654 compiled-C/ROM comparisons across all384 scoped
instruction starts, including678 selected failure prefixes and1,024 retained
history calls. The new suite links all six resident bodies and compares state, ordered typed
transactions, literal mask assignments and completed frame balance with actual
instructions. Sweeps include byte/word wrap, quotient overflow, partial masks,
old-count expiry, option/service gates, overlapping table views, callbacks,
selected failures and retained producer/consumer histories.

Earlier scoped suites explicitly link historical AC, shift-lamp or VSS boundary
fixtures where their original oracle stops at those entries. The current kernel
and this new combined suite link the resident implementations with those task
bindings absent. This preserves earlier slice domains while checking the newly
connected behavior directly. Historical fixtures do not describe current firmware
completion.

Both host routes have40 CTest-equivalent entries. The Python `--contracts-only`
route and CI first run all20 quick contracts/provenance checks. Then all20 ROM
suites run, with two independent comparisons at a time and the longest scheduled
first. No comparison is omitted to shorten the gate.

Next batch: remaining ADC acquisition and the EGR producer/controller chain.
Broader fuel/transmission work, target reset/interrupt entry, memory/ABI/linker fit,
actual peripheral response and physical timing remain separate. No target BIN
or actuator authority follows from host comparison results.
