# Factory closed-loop fuel and learning

The resident O2 controller, closed-loop/learning admission, BLM cell selection and BLM updates are documented here from stock BMHM bytes. They complete the `$020F/$027A/$026F/$0248` producer boundaries of [running fuel](FACTORY_FUEL_INTEGER_HANDOFF.md). [The closure index](FACTORY_ENGINE_CALCULATION_CLOSURE.md) defines the shared math, evidence, cadence, initialization and raw-input interfaces; [upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md) supplies the AFR/PE/idle/startup producers.

These are state machines at different cadences. O2 direction, O2 activity, closed-loop selection, permission to learn and a selected BLM value are different states. A nonneutral BLM can still be consumed when learning is disabled.

## State and execution order

| State | Width | Role / owner |
|---|---|---|
| `$01D5`, `$01D4` | Bytes | Current raw O2 coordinate; previous sample saved by the AFR task |
| `$01D2` | Word | Filtered O2 coordinate; controller uses its high byte |
| `$003E bit6` | Bit | O2 direction, updated by threshold/trend logic |
| `$0004 bit0`, `$0241` | Bit, byte | O2 activity admission and age counter |
| `$003E bits7/5` | Bits | Closed-loop/stoich-selection state used by AFR and O2 gates |
| `$0052 bit7` | Bit | Warmup/open-loop short-term-control mode |
| `$003E bit1` | Bit | BLM learning permission |
| `$026B/$026C/$026D/$026E` | Bytes | Integrator interval base, O2 center, upper/lower thresholds |
| `$020F/$027A/$026F` | Bytes | Integrator, proportional magnitude, encoded signed combined correction |
| `$0275/$027C/$025F` | Bytes | Direction-change count, direction age, integrator delay counter |
| `$0247/$0248/$0249` | Bytes | Selected BLM index, current BLM, previous BLM |
| `$02B3-$02C7` | 21 bytes | Retained BLM cells |
| `$0274/$0273` | Bytes | Learning cadence counters |

The odd fuel group first updates the O2 filter. Its tail admits the O2 controller every fourth ordinary tick, or AFR/PE/BLM every eighth tick on a different phase. The slot-F admission routine runs every32 ticks, after its bit4 gate. The exact scheduler order is preserved in the existing scheduler contract; a newly set permission or PE flag need not be consumed on the same pass.

## O2 filtering and activity

At `$7E09-$7E35`, gain is `$48BD` at entry idle (`$0050 bit7`), otherwise `L1(byte027B,$4D05)`. Clamp raw `$01D5` to `[$48BB,$48BC]` using the ordered comparisons, then set `word01D2=lag8(clamped,old01D2,gain)`. Raw O2 is still available for direction/activity checks; its electrical conversion and ADC sampling are explicit sensor interfaces.

At `$863D`, if fuel-running `$004F bit4` is set, choose activity threshold pair `$48FF` (nonidle) or `$4903` (idle). Add2 to the address when closed-loop bit `$003E bit7` is clear. Raw O2 strictly above the first byte or below the second clears `$0241` and sets `$0004 bit0`. In-band samples retain both. The slower admission routine increments `$0241` to `$48D2`, then clears bit0 on a later call finding the age already at/above the threshold. It does not clear bit0 on the same call that merely increments to the limit.

## Closed-loop and BLM admission, `$E477-$E561`

Apply the checks in order:

1. Fuel-running clear, any `$0019&$0C`, `$0072 bit6`, or any `$0018&$30` together with idle `$0050 bit7`: reset age `$0241` for the latter fault/mode cases and take the disabled route. The nonrunning route itself does not clear age. Disable clears `$0052 bit7` and `$003E bits $A2`.
2. Service `$003B bit4` plus `$0391 bit0` bypasses normal admission. `$0392 bit0` clear takes disabled; set jumps directly to setting `$0046 bit7` and `$003E bits $A0`. The subsequent idle/learning checks still apply. This local bit use must not be conflated with the separate I/P service gate below.
3. Otherwise increment/age `$0241` as above. If activity bit `$0004 bit0` is clear, disable. If `$0050 bit4` or warmed latch `$0004 bit1` is set, bypass the time qualification. Otherwise use `elapsed=low(word00FD>>1)`: choose threshold `$48CF` for starting coolant `$0282>$48CC`, `$48CE` at/below `$48CB`, otherwise `$48CD`. These are raw byte comparisons, not a newly inferred time unit.
4. At/above that threshold set warmed latch `$0004 bit1` and clear `$0052 bit7`. Below it set `$0052 bit7`; if AFR `$024A>=$48E9`, clear `$003E bits $A2` while retaining bit7 of `$0052`. A richer AFR instead takes the ordinary disabled route, also clearing `$0052 bit7`.
5. On the warmed/qualified route, require effective coolant `>$48D0`. With `$0086 bit6` set, `$0801&3` must also be zero. A failure clears `$003E bits $A2`. Success sets `$0046 bit7` and `$003E bits $A0`. Idle warm-target flag `$0050 bit1` then clears `$003E bits $82` and returns, retaining bit5.

If that idle exception did not return, enable BLM learning `$003E bit1` only with **all** of:

- `$006F&$48==0`;
- coolant `>$48D6`;
- commanded AFR exactly equal to `$48E7`;
- vacuum coordinate `$01C9<=$48D3`;
- selected load in inclusive `[$48D4,$48D5]`: `$01CF` when `$400E bit0` set, otherwise filtered MAP `$01C6`;
- RPM62 `<$48D7`.

A failure of these learning-only checks clears bit1 without clearing the already established `$A0` state. Earlier closed-loop failures clear `$A2`. This explains why learning permission cannot be inferred from just the closed-loop display bit.

## O2 threshold preparation and direction, `$8662-$86F1`

Form airflow proxy `$027B=min(128,hi(4*hi(word0232)*C[$4949]))`, forcing128 on either shift carry. Nonidle uses four curves `$4CE1+9*j`, with `j=3,2,1,0`, indexed by this proxy. Store them at `$026B+j`, yielding lower threshold `$026E`, upper `$026D`, center `$026C`, then interval `$026B`. Idle instead loads word `$026D/$026E` from `$494A/$494B`, center from `$494C`, and only looks up the interval curve j=0. `$0070 bit2` substitutes `$4E58` for that interval.

Update direction `$003E bit6` using raw O2:

- If center plus `$4947` has no byte carry and O2 is strictly above it, set direction.
- Otherwise if center minus `$4947` has no borrow and O2 is strictly below it, clear direction.
- Otherwise set direction if current O2 is greater than previous `$01D4`, clear it otherwise. In-band direction therefore follows trend, not a simple retained Schmitt state.

A changed direction increments byte `$0275` with wrap, sets `$0043 bit4` and clears `$027C`. An unchanged direction increments `$027C` up to255.

## I/P admission and neutralization, `$86F2-$878F`

The local service gate `$003B bit4` plus `$0391 bit0` has first priority: `$0392 bit0` **set** selects reset at `$8779`; **clear** jumps directly to control `$8790`. This is the actual opposite selection from the admission routine's use of the same bit; do not replace the two code paths with one assumed “force closed loop” action.

Otherwise, `$003E bit7` or `$0052 bit7` must be set. Both clear jumps directly to neutral. Once admitted, use this priority:

| Condition | Local result |
|---|---|
| DFCO `$0046 bit3`, PE `$003D bit5` or `$0052 bit6` | Set `$0071 bit2`, then `$006E bit0`, then reset |
| `$400C bit5` plus `$006E bit3` | Clear `$006E bit3`, set `$006E bit0`, reset this pass |
| Either `$400C bit4` or bit6, together with `$003D bit2` | Set `$006E bit0`, reset |
| `$004F bit5` | Clear it, set `$006E bit0`, reset |
| Decel/enlean `$003D bit4` | Control if direction set or INT<128; otherwise set `$006E bit0` and reset |
| Other admitted state | Control if load `$01C0>$490B`, RPM62 `<=$490C`, RPM62 `>$490D`, VSS `<$490E`, direction set or INT<128; otherwise set `$0071 bit2/$006E bit0` and reset |

Reset/neutral stores INT128, high byte `$01D2=$66`, `$025F=0`, `$027A=0`, then combines to `$026F=0`. The low fraction `$01D3` is retained. Direct neutral does not necessarily set the notification flags associated with an inhibited/reset route.

## Error, proportional term and delays, `$8790-$886E`

Use `f=hi(word01D2)`:

```text
if f > byte026D:
    a = hi((f-026D)*C[$4955]); set 0046 bit1
elif f < byte026E:
    a = 026E-f; clear 0046 bit1
else:
    a = 0; retain 0046 bit1
if idle: a = hi(a*C[$4956])
a = min(a,96); store 0280
p0 = L1(2*a,$4D0E)
```

Idle P selection saves base delay `$494D`. If direction is clear, atomically XOR `$003F` with `$05`; this is a persistent bit update, not merely a local temporary. If **both** bits `$03` are set, or **both** bits `$0C` are set, load `$0262=$4952`; P coefficient is `$494F` with direction set or `$4950` clear. Otherwise load `$0262=$4953` and coefficient `$4951`. Set P=`hi(sat16(4*p0*coefficient))`.

Nonidle saves base delay `L1(027B,$4D28)` and sets P=`K2R(p0,L2(min(RPM62,144),load01C0>>1,$4D31))`. Store P at `$027A`.

Then:

```text
window = sat8(saved_base_delay + L1(2*a,$4D1B))
interval = hi(L1(2*a,$4D85)*old026B)
if idle: interval = sat8(interval+byte0262)
store interval at 026B and 0281
```

The old interval here is the freshly prepared value from this controller invocation, before the error-dependent multiply. BLM later consumes the resulting `$026B` at its own task phase.

## Integrator, proportional window and combination

Integrator may update only when error sign `$0046 bit1` and O2 direction `$003E bit6` agree: the combined mask must be0 or `$42`. A disagreement skips I delay/update while retaining P processing. When `2*a<=$4948`, clear delay `$025F` and skip I. Otherwise, if old delay is below interval, increment it as a byte; at/above interval replace it with zero. Only a resulting zero updates INT.

- Error-sign clear: increment INT unless it equals `$4911`. With `$0052 bit7` set, additionally stop at128 or above.
- Error-sign set: `$400B bit3` plus `$0044 bit1` inhibits the decrement. Otherwise decrement unless INT equals `$4910` or short-fuel floor latch `$003F bit7` is set.

These calibration bounds are **equality** stops; corrupt/out-of-range initial values are not silently clamped. Increment/decrement are byte arithmetic.

Clear P only in the strict window `window < age027C < sat8(window+C[$494E])`. `$0052 bit7` always clears P. The direction-combination at `$88E9-$891A` then produces:

```text
if direction clear:
    combined = sat8(INT+P)
else:
    if 400B bit3 and 0044 bit1: P=min(P,C[$4912]); store P
    combined = max(INT-P,0)
026F = u8(combined-128)
```

The running-fuel consumer sign-extends this encoded byte into an additive PW correction. It is not an extra multiplicative BLM-like factor. The existing handoff contract gives the exact subsequent word arithmetic.

## BLM selection, `$8C73-$8D9D`

After AFR calculation/shadowing, full phase `$9F` samples `abs16(word0284-old081A)` into `$0818` and updates `$081A`. This is the vehicle-change input used by PE. Cell selection itself executes on every admitted AFR task and begins by clearing `$003D bit2`.

Normal BLM has four RPM bins and four load bins, index `rpm_bin+4*load_bin`. RPM boundaries are `$48EE/$48EF/$48F0`; load boundaries `$48F1/$48F2/$48F3`. Equality belongs to the upper bin. Selected load is `$01CF` when `$400E bit0` set, otherwise `$01C0` (different from the MAP selection in the learning-admission routine).

If old index<16, retain it while both coordinates stay inside its expanded bounds. For a nonfirst bin, lower bound is its preceding boundary minus margin (`$48F4` RPM, `$48F5` load); subtraction borrow removes that lower test. For a nonlast bin, upper bound is the next boundary plus margin; addition carry removes that upper test. Otherwise lower/upper equality is retained. A failed bound or an old special cell recalculates the normal bins.

Special idle cells are enabled by `$48F6 bit0` and strict TPS `<$48DA`, VSS `<$48D9`. Start at16, add1 when config bit1 and `$0041 bit4` are set, add2 when config bit2 and `$0041 bit5` are set. **Within this special-cell branch**, `$0051 bit0` selects cell20. An unchanged special index can be retained directly.

A new/recalculated selection sets `$003D bits $0C` and `$006E bit0`; the normal hysteresis-retained route does not. Read cell `$02B3+index`. Runtime-valid values are at/below `$48FC` and at/above `$48F9` for indices<16, or `$48FA` for special indices. Failure sets `$0046 bit6` and invokes `$F280` to reset **all21** cells to128, returning A128 while preserving the selected B. Store `$0248` and index `$0247`.

## BLM transitions and learning, `$8D9E-$8EB3`

When `$400C bit4` is set, skip transition bookkeeping entirely, including the `$0249` update. Otherwise TPS crossing `$48DA` toggles `$0052 bit2` and immediately updates previous BLM `$0249`. Without such a crossing, form byte `d=u8(old0249-new0248)`:

- d=0 clears `$003D bit2`.
- d with N clear: retain that bit only when `d>=$4909` and INT `<=$4907`; otherwise clear it.
- d with N set: use byte-negated magnitude and retain the bit only when magnitude `>=$490A` and INT `>=$4908`; otherwise clear it.

These are N-bit byte classifications, not unlimited signed differences. Then store new `$0248` at `$0249`. The bit was set by cell selection; this logic can keep or remove it, rather than unconditionally setting it on a numerical difference. The decel-history filters at `$8DEF` follow before learning.

Learning requires `$003E bit1` set, cell-change `$003D bit3` clear and INT not128. Ineligible calls clear `$0274/$0273`. On an eligible call:

1. Increment `$0274` as a byte. If its result has bit7 clear, store it and require twice that result `>=$026B` to proceed. A result with bit7 set bypasses that compare/store, so valid retained counts stop growing at127. Until admitted, preserve both counters.
2. Increment `$0273`; a wrap to zero is not stored and proceeds with the retained255. Otherwise store it and require `>=$48ED`.
3. Require `abs(INT-128)>$48F7` for normal cells, `$48F8` for special cells. INT>128 also requires direction clear; INT<128 requires direction set. Small error/direction disagreement returns without resetting counters.
4. Add step `$48FB` to the selected cell with cap `$48FC` for INT>128. For INT<128 subtract the same step with zero/bound floor `$48F9` normal or `$48FA` special. Store through `$02B3+index` and at `$0248`; clear `$0274/$0273`.

Every return clears cell-change `$003D bit3`, copies byte `$0063→$0065` for PE's RPM comparison, and current raw O2 `$01D5→$01D4` for direction trend. The latter is an AFR-task sample, not the previous invocation of the faster O2 task.

## Reset, persistence and downstream meaning

BLM cells lie in the conditional retained-memory clear `$029D-$034D`, not the unconditional `$0100-$029C` clear. `$F280-$F28D` explicitly fills all21 cells with128 on reset/bad-cell paths. Boot `$F28E-$F2A9` instead applies upper bound `$48FD` then lower bound `$48FE` to all21 cells. Those boot bounds differ from runtime validity/learning bounds `$48F9/$48FA/$48FC`. Boot also seeds selected `$0248=128`; the next cell selection chooses the actual cell value.

Working INT/P/filter/counter states below `$029D` are cleared by the unconditional boot clear, then specific seeds apply. Boot seeds O2/filter high bytes from `$48BE`; neutralization sets INT128 and filter high byte `$66` on its own schedule. Zero at boot is therefore not interchangeable with a fully initialized running controller.

Running fuel applies `$0248` as its multiplicative 128-centered correction, preserving the documented intermediate saturation and PE learned-lean safeguard. `$026F` is a separate signed additive correction. A calculation using BLM, INT and proportional as three independent percentages will not reproduce the factory instructions.

The sensor acquisition, service payload source, every diagnostic-bit lifetime and physical mixture response are separate interfaces. All resident arithmetic, selected-cell writes, local qualification/reset paths and return-time sample updates described here are included in the upstream ROM evidence and documentation closure.
