# Idle, transient and decel spark modifiers

Authority is the recorded stock BMHM image, SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The new callable body ends at A9DF, before external1812, the resident special
override and subsequent limits. It does not implement the complete A466 root.

| Routine | ROM scope | Responsibility |
|---|---|---|
| `pcm_spark_idle` | A84E..A905 | Idle admission, unsigned RPM difference, lookup products and signed-byte correction |
| `pcm_spark_transient` | A906..A979 | Optional transient error, word lag, wrapped offset/cap and command correction |
| `pcm_spark_decel` | A97A..A9DF | DFCO retard, shared gain-word reset and recovery |
| `pcm_spark_modifiers` | A84E..A9DF | Ordered idle→transient→decel composition |
| `pcm_spark_composite` | A700..A9DF | Earlier base/environmental terms followed by these modifiers |
| `pcm_lookup_capped` | F499..F4A3 → F4BD..F4DD | Capped input, zero offset and existing rounded interpolation |

Each public routine has its own file. IAC, filtered RPM, transient-target,
fuel-cut and startup producers remain separate interfaces. The larger wrapper
preserves the original order: base selection samples retained0050.6 before
this pass's idle correction clears or sets it. Tests cover retained state over
successive calls, not an invented new dispatcher cadence.

## State interfaces

| Factory location | C field | Ownership in this step |
|---|---|---|
| 00FD | Existing `scheduler.run_counter` | Runtime admission word, with no new time-unit inference |
| 0063,0064 | `spark.rpm_high`, `rpm_fraction` | Shared high byte plus new low byte of filtered RPM |
| 0857,006C | `spark.iac_desired_speed`, `idle_derivative` | Explicit IAC inputs |
| 0050.6,0050.7 | Existing `idle_feedback`, `idle_state` | Separate table/admission state and idle-mode input |
| 0053.0 | `spark.idle_negative` | Unsigned target-minus-RPM borrow, not the word's N bit |
| 0837..083B | `transient_target`, `transient_filtered`, `transient_error`, `transient_correction` | Byte target, word lag, byte error and byte amount |
| 0046.3 | `runtime.deceleration_fuel_cut` | Explicit DFCO input |
| 0051.5,0208 | `spark.recovery_active`, `decel_retard` | Recovery latch and saved retard byte |
| 01F2 | `spark.startup_recovery_gain` | One shared startup/decel word, not a second independent lag state |
| 01FD | Existing `spark.composite` | Wrapped composite word; no physical output conversion yet |

The C RPM representation joins0063/0064 for the idle word comparison; transient
error reads only0063. The source addresses are provenance, not a target RAM ABI.
All new named state is covered by the existing reset-struct clears; the later
factory reset stages and startup-gain producer remain unfinished.

## Idle arithmetic and transitions

Admission requires runtime>=415E, VSS high<415A, TPS strictly below415B or415C
according to entry0050.6, and coolant>415D. Failure clears0050.6, retains the
composite, and normally retains0053.0.

Use0857 as a target high byte with low byte0. With0050.7 clear, add4160 to that
byte. A carry clears0053.0 and disables correction; it does not saturate the
target or commit the intervening assembly subtraction to the composite.

For a valid target, SUBD compares the target and RPM as unsigned words. Borrow
sets0053.0 and selects44F0; no borrow clears it and selects4502. Take the magnitude
of the mathematical difference in0..65535. An `int16_t` sign classification
would disagree on large errors and is deliberately not used.

```text
coordinate = difference >> 4                     if difference < 1024
           = min(255, (difference >> 7) + 56)     otherwise
speed      = H1(coordinate, direction_table)
load       = H1(load01C0, direction_table+8)
amplitude  = high(speed*load)                      # truncates
signed_byte = u8(-amplitude) if0053.0 else amplitude
derivative = L1(4*clamp(byte006C-96,0,63),451B)
b = u8(derivative + signed_byte -4514)
```

Classify b's N bit after byte wrapping. N-set b sign-extends without an extra
negative clamp; otherwise cap at4515 and zero-extend. Add the resulting word
to01FD with wrap, then set0050.6. This flag also feeds a later call's base-table
selection. Existing IAC target/derivative production is not silently replaced.

## Transient behavior

Require coolant within inclusive46F2..46F3 and400F.7. Disabled or disqualified
calls retain every transient field and do not change the composite. At idle,
write0838=0837<<8 and retain the old error/correction bytes, with no adder.

Off idle, first store `u8(byte0063-high(old0838))` at083A. Then look up gain from
TPS>>2 at46F4 and update0838 using the existing signed-floor byte-target filter.
The old error is not recomputed against the new baseline.

N-clear error uses46EC's three bytes; N-set error uses46EF and byte-negates the
error magnitude. Multiply magnitude by parameter0, truncate to the high byte,
add parameter1 **with byte wrap**, then cap at parameter2. Publish083B. A fresh
error-sign sample chooses add for N-set or subtract for N-clear, wrapping01FD.

Stock400F=10 leaves this feature disabled; stock coolant bounds are both0.
The optional enabled routes are verified with explicit calibration variants,
without changing the source defaults or the truck image.

## DFCO and recovery

DFCO sets the recovery latch and clears the shared01F2 word. Subtract413C from
coolant term01F9 as a byte. N-clear difference adds to4152 with byte wrap;
N-set difference leaves4152 unchanged. Save0208 and subtract it from01FD.

Without DFCO, a clear latch retains the word, saved retard and composite. With
the latch set, TPS>4151 selects4150; other TPS values select414F. If old01F2 is
greater thanFEF0, clear the latch; otherwise update it with `lag8(255,old,gain)`.
**The same call still applies recovery after clearing the latch**:
add `R8(high(current01F2),0208)-0208` to01FD. The next inactive call skips it.
The shared startup owner must use this same01F2 field when it is ported.

## Calibration views and failure prefixes

| Source | Profile fields |
|---|---|
| 415A..4160 | VSS/TPS/coolant/runtime idle gates and target-byte adder |
| 44F0,44F8,4502,450A | Four `PcmCappedCurve` views: limits96/128/96/128; backing lengths8/10/8/10 |
| 4514,4515,451B..452B | Idle bias, positive cap and17 derivative knots |
| 46EC..46F1 | Positive/negative transient gain, offset and cap |
| 46F2..46F8 | Inclusive coolant gates and five TPS-gain knots |
| 414F..4152 | Normal/fast recovery gains, TPS threshold and decel base |
| 413C,400F | Existing coolant bias and shared option byte |

Capped views retain zero-weight neighboring reads, including neighboring headers
and the4514 bias byte. Shared-address fixture changes update all affected views,
including the earlier altitude view. The native source profile does not require
factory overlapping placement in our future serialized calibration format.
The TPS gain input is at most63, so five knots are sufficient.

Missing calibration/profile or invalid accessed curve storage returns
`PCM_BAD_CONFIGURATION`. An idle lookup failure retains the already committed
direction flag and earlier composite-body results; it does not invent rollback
or clear the retained feedback flag. A failed admission can skip invalid unused
curves normally. Invalid-storage checks are C development contracts, not ROM
error-return behavior. Larger backing arrays can support changed curve limits.

## Verification and remaining work

The new suite compares 225,622 compiled-C cases against actual ROM instructions:
3,834 capped-curve cases, 73,703 idle cases, 3,067 expanded-curve index witnesses,
71,936 transient cases, 69,626 recovery
cases, 2,048 bounded variants, 1,024 auxiliary→full-composite witnesses and 384
history calls. All 234 scoped instruction starts execute. All 81 calibration bytes
match stock: 38 newly introduced to C calibration and 43 prior/shared.

The corpus covers every unsigned RPM word on the negative-error route, selected
positive/large-error boundaries, carry-disabling targets, byte correction sign
and cap behavior, every RPM-high/old-filter-high pair, every error/offset pair,
every recovery word, gate equality, wrapped DFCO subtraction and retained-state
histories. Expanded 17-knot backings with nonflat data expose large-error index
and saturation differences hidden by the stock 96 curve caps. The expansion is
a supplied test profile; factory defaults retain their 8/10-knot views.
ROM local frames balance and these scopes make no hardware I/O.
These witnesses do not establish all interleavings or target C stack/timing.

Both host routes retain these modifier contracts/differential checks and the
newer command suite, bringing CTest to 18 entries. The C inventory is 116 public routines:
47 implemented outlines, 40 explicit dependency boundaries and twenty-nine algorithms.
The [command path](spark_command_contract.md) now implements resident override,
signed limits and service edits under an explicit optional 1812 dependency.
Remaining source work includes admission and physical command/output handoff.

See the [earlier spark terms](spark_terms_contract.md),
[factory spark derivation](../../docs/analysis/FACTORY_UPSTREAM_SPARK_CALCULATIONS.md)
and [integer handoff](../../docs/analysis/FACTORY_SPARK_INTEGER_HANDOFF.md).
