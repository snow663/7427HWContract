# Period/RPM preparation and adaptive timing terms

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The new normal precomputation covers A5E5..A6FF. A conditional wrapper joins
the earlier admission and A700..AB43 command bodies. Production AC51 now calls
the resident alternate implementation; optional 1812 remains an explicit dependency. The separate
[output body](spark_output_contract.md) now implements AB44 publication; SWI
handling remains outside the implemented normal path.

## Routine ownership

| Routine | ROM scope | Responsibility |
|---|---|---|
| `pcm_lag16` | F436..F458; F479..F498 | Rounded word-target lag with an optional intermediate result |
| `pcm_spark_period_sample` | A5E5..A629 | Fresh period, optional scaling and RPM coordinates |
| `pcm_spark_rpm_filters` | A62A..A686 | Monitor latch, load filter and filtered RPM |
| `pcm_spark_reference_term` | A6BE..A6D8 | Pure piecewise period transform |
| `pcm_spark_period_terms` | A687..A6FF | Adaptive/reference/battery terms and fresh limit |
| `pcm_spark_precompute` | A5E5..A6FF | Ordered sample→filters→timing terms |
| `pcm_spark_build` | Normal A466..AB43 | Admission→precompute→command, with an explicit completed-command result |

Each public routine has its own file. The existing REF common tail now uses
the shared word-lag helper while retaining its two 006A stores. The completed
[resident controller](spark_controller_contract.md) now joins these wrappers,
publication and the monitor in the dispatcher.

## State interfaces

| Factory location | C field | Use |
|---|---|---|
| 005F,01E8 | Existing `period_basis`, new `period` | Scaled basis and separately retained raw period |
| 083D | `spark.rpm_raw` | Raw fractional-division result |
| 0061,0062 | Existing `rpm_low_coordinate`, `reference.rpm_coordinate` | Piecewise low-range and ordinary rounded coordinates |
| 028E,028C,028D | `rpm_monitor_filtered`, `rpm_monitor_previous`, `rpm_monitor_delta` | Monitor filter and phase-latched change |
| 0067,0068 | Existing `reference.load_coordinate`, `load_filtered` | Produced byte target and filtered word |
| 0837 | Existing `spark.transient_target` | High byte of saturated doubled raw RPM |
| 0063,0064 | Existing `rpm_high`, `rpm_fraction` | One existing paired filtered-RPM word, not a second independent state |
| 01EA,01E6 | Existing `adaptive_period`, new `previous_period` | Adaptive state and period history |
| 083F,01EC | `reference_term`, `period_correction` | Reference transform and final capped timing term |
| 00A7 | `spark.battery_sample` | Raw battery input, distinct from the 0055 REF input |

Existing struct clears include the new fields. Addresses are provenance, not
a target RAM ABI. Named volatile fields preserve the specified samples/stores;
they do not prove compound atomicity, target word coherency or instruction time.

## Shared word filter

For target t, old word x and byte gain g:

```text
d = u16(t-x)
h = (d>>8) - (256 if t<x else 0)
intermediate = u16(x+h*g)
result = u16(intermediate + ((low(d)*g+128)>>8))
```

Borrow determines the signed 17-bit difference. An int16 cast of d would lose
the correct direction for large differences. The two word wraps and the MUL
carry's rounding are retained explicitly.

F436 stores the intermediate in its saved-X stack word, so its PULX returns
that intermediate in X; it does **not** preserve the input X value. F479 writes
the intermediate through its caller's destination pointer and retains X.
Both return the final result in D. The C helper returns the result and optionally
the intermediate; it does not impose that machine register/frame ABI.

The 0068 and 006A callers publish the intermediate before their final store.
The 0063 caller stores only the final word. Its original F436 temporary remains
a C local. A null intermediate pointer is valid.

## Period and RPM coordinates

Read 3FC0 and store the same unscaled sample at 005F and 01E8. Compute
`m=u8(32*cal4141)`. If m is nonzero, replace 005F with the existing rounded
word gain; if zero, retain the raw word. Stock 4141=08 makes m zero and skips
scaling. Doubling 005F to obtain the FDIV denominator wraps at 16 bits.
The numerator is 307; a zero denominator or numerator>=denominator yields FFFF.
Store the quotient R at 083D.

For R<6000 hex,0061 is the high byte of `max(2*R-1F80 hex,0)`.
Otherwise use the high byte of `R+4080 hex`, with 255 on word carry.
0062 is `min(255,(R+128)>>8)`. Its SBCA correction prevents a top-end byte
wrap; that correction is intentionally absent from the monitor rounding below.

The standalone A62A ROM fragment requires A to hold the just-published 0062
value. Its differential fixture supplies that precondition; the C filter
routine receives the coordinate through the existing named field.

## Filters and phase latch

Update 028E with `lag8(0062,old028E,cal50E4)`. Round its high byte using
`hi(u16(new028E+128))`, including wrap. Only when `(phase&1F hex)==04` store
the byte difference from old 028C to 028D, then store the rounded byte to 028C.
Other phases retain both latch bytes.

Store 0067=`min(255,(4*R+128)>>8)` and use 0067<<8 as the 0068 target.
A zero old 0068 seeds directly; otherwise use the word lag with 4517, publishing
its intermediate and final values. Next saturate 2*R to a word and publish its
high byte at 0837. A zero old 0063/0064 seeds directly; otherwise word-filter with
4153 and store the final paired word. Thus a zero gain holds an initialized
filter, but does not prevent the separate zero-state seeding route.

## Adaptive and battery/reference terms

Subtract the 01C2 load latch from current 01C0 as a byte. A non-borrowing delta
of at least 32 publishes `FF00 hex | delta` to 01EA. Otherwise form
`candidate=u16(2*(previous_period-period))` and adopt it only if the N bit of
`u16(candidate-old01EA)` is clear. This N-bit test is not a general signed
comparison. Cap the current 01EA down to `period>>3` using unsigned ordering.

Save the current period to 01E6 and compute the 083F reference term:

| Raw period p | Result |
|---|---|
| p<458 | (p>>1)+79 |
| 458<=p<1638 | ((p-458)>>4)+308 |
| p>=1638 | ((p-458)>>2)+87 |

Store 01EC=`u16(4*max(120-batteryA7,0)+reference_term+adaptive_period)`.
Then read 3FC0 **again** and form `limit=u16(fresh_period-39)`; below 39 this
subtraction wraps. Cap the current 01EC down to that unsigned limit. The RAM
value is sampled after the I/O callback, rather than retaining a cached sum
from before the read. Selected callback-time mutations verify this distinction.

## Completion and failure prefixes

`pcm_spark_build(pcm,&built)` clears built before work and sets it only after a
complete successful normal command through AB43. Alternate dependency success,
missing bindings, I/O failures, bad configuration and the pre-SWI trap boundary
all leave it false. A null result pointer returns BAD_CONFIGURATION before
state work. AB44 EST command publication remains outside the builder; the
earlier 3060/306F transactions remain part of admission.

The period-sample and filter routines require the immutable spark profile.
The literal timing-term routine needs no calibration but requires a 16-bit period
read. A failed first read leaves period/RPM state unchanged; a failed final read
retains the preceding adaptive/history/reference/correction writes. Wrappers
propagate the first failure without rollback. These error returns are C
development contracts, not new factory-ROM error instructions.

## Calibration and validation

| Address | Stock | Profile field |
|---|---|---|
| 4141 | 08 | `period_scale` |
| 4153 | F0 | `rpm_filter_gain` |
| 4517 | 00 | `load_filter_gain` |
| 50E4 | 00 | `monitor_filter_gain` |

These four bytes include three newly represented addresses and one previously
represented byte: 4517 is within the earlier altitude table's backing view.
The address-based ROM fixture updates both views consistently. Native source
profiles and the future serialized calibration layout need not preserve factory
overlapping placement. All 1,194 fixture bytes match the stock image.

The new differential suite exercises all 163 instruction starts in A5E5..A6FF,
F436..F458 and F479..F498. It checks return values and helper intermediates,
RAM state, I/O width/order, final mask, unresolved dependency and builder result.
Completed ROM local frames balance. The suite adds 699,057 C/ROM comparisons:
263,837 word-filter cases, 65,536 reference-term cases, 69,120 period/coordinate
cases, 83,968 RPM/filter cases, 211,968 adaptive/battery/limit cases, 3,712 joined
witnesses, 660 failure prefixes and 256 full-builder history calls. The corpus covers
every possible target-minus-old difference in -65535..65535 with selected gains,
every low-difference/gain pair at both word-filter entries, every period word,
all raw RPM words, phase/rounding boundaries, load-byte pairs, every adaptive
word, battery/limit boundaries, joined paths, selected failures and histories.

This earlier slice suite substitutes AC51 with a link-time return/state fixture;
production and the complete-controller suite use the real adapter. 1812 uses an explicit well-formed
fixture return with register clobbers. These are not implementations or ABI
proofs of those bodies. The first SWI and AB44 output conversion are not executed.
Selected callback-time state changes do not establish every IRQ interleaving.

Both host routes contain 32 CTest entries. The inventory is 161 public routines:
73 implemented outlines, 41 explicit boundaries and 47 algorithms. The
[output/alternate bodies](spark_output_contract.md) are also implemented.
The [monitor and resident controller](spark_controller_contract.md) are now implemented. Target compiler ABI, stack/memory fit, cycle timing and
physical
backend behavior remain separate work.

See the [admission contract](spark_admission_contract.md),
[command contract](spark_command_contract.md),
[upstream period/RPM derivation](../../docs/analysis/FACTORY_UPSTREAM_FUEL_CALCULATIONS.md)
and [integer handoff](../../docs/analysis/FACTORY_SPARK_INTEGER_HANDOFF.md).
