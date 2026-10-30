# Factory IAC controller: target RPM, airflow and position

This is the stock BMHM ROM derivation of the idle controller, including its optional calibration branches. [Learning, reset and output service](FACTORY_IAC_LEARNING_AND_OUTPUT.md) closes the companion state/driver paths. [RPM/VSS/governor](FACTORY_RPM_VSS_GOVERNOR.md) supplies speed and RPM-ratio inputs. The [closure index](FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md) defines byte authority, evidence, execution context and remaining physical/external interfaces.

The controller calculates airflow, converts it to a target position byte `$0008`, and leaves stepping to `$91A3`. Position `$0007` is a software count, without a position sensor in this path. The arithmetic therefore does not establish physical pintle position.

## Notation, state and scheduling

Use the integer helpers in [the engine calculation index](FACTORY_ENGINE_CALCULATION_CLOSURE.md): `u8/u16` wrap, `sat8/sat16` cap at255/65535, `hi` selects the high byte, `M(a,w)` is the rounded byte-times-word product, `R8` the rounded byte product, `L1/S1/H1` the exact lookup entries. `A4(input,header)` below means `$F4A4`'s lower-offset/cap/multiplier lookup. `addH(w,b)` adds `b<<8` to a word, returning `$FFFF` on carry; `subH(w,b)` subtracts it with a zero floor. These helpers preserve the fractional low byte unless a cap/floor replaces the word. `C/W` identify ROM byte/word values; an address in a condition denotes its stored value, not the address as a literal integer.

The main `$93D0` controller runs on ordinary phase `phase&3=3`, nominally every 4 ticks. Desired-RPM/background `$9E99` runs in slot7; follower/decay/diagnostics `$A2B0` in slot9, nominally every 16 ticks each. The desired RPM and filtered follower can therefore be older than the fast controller's error calculation. Startup takes a separate main-controller path. Busy/pending coalescing and mode gates remain relevant; no wall-time frequency is guaranteed merely by these divisors.

| State | Meaning |
|---|---|
| `$0036 bit0/bit1` | AC context / drive context |
| `$0036 bit2/bit3` | TPS/VSS closed qualification / admitted integral control |
| `$0036 bit4/bit7` | Stall-recovery mode / RPM at-or-above target |
| `$0037 bit7` | Derivative term adds when set, subtracts when clear |
| `$0038 bit6` | Service desired-RPM override |
| `$0857/$0858/$0859` | Desired RPM byte / absolute error byte / error-filter word |
| `$0862/$0871/$0873` | Selected integral flow / cold flow / cold-flow bound |
| `$086D/$086E/$0870` | P-flow magnitude / derivative-filter word / D-flow magnitude |
| `$087D/$0880/$0889/$088B` | Base composite / follower / pre-BARO composite / final flow words |
| `$087F` | IAC-change acceleration-enrichment byte consumed by fuel |

All RPM/flow values here are raw software coordinates. Conventional source RPM labels do not independently prove electrical/timebase scaling.

## Entry, reset and nonrunning initialization, `$93D0-$9536`

`$0086 bit6` calls unknown low-memory `$1803` first. Clear service override `$0038 bit6`, then service mode `$003B bit4` calls `$A407`. That callee can pop its return address and leave the controller early; the companion contract documents each escape.

Reset-in-work `$0009 bit0` commands target0 until software position `$0007=0`; then clear reset, set `$0009 bit2`, and seed learned/default cells through `$92A4`. With ignition-off `$0044 bit4`, bit2 set requests park target `C[$4EB0]`; bit2 clear starts the reset routine `$A3FA`. With ignition on, spark-running `$004F bit7` selects the running controller. Otherwise initialize:

| State | Nonrunning seed |
|---|---|
| `$0866/$0867` | `L1(ECTindex0283,$4EF5/$4F02)` |
| `$086B/$086C` | `$4EB8/$4EB9` startup flow and divider |
| Temperature coordinate t | `ECTindex` through160; above it `2*(ECTindex-160)+160` |
| Base RPM | `L1(t,$4F32)`, or `$4F50` when `$4E8F bit0` set |
| `$085C` | `L1(t,$4F6E)` startup RPM addition |
| `$0857` | Byte-wrapped base plus085C; when config bit0 clear, first replace the addition by `hi(sat16(2*085C*C[$4EBC]))` |
| `$085D/$085E` | `$4EBB/$4EBA` RPM decay divider/hold |
| Zero seeds | `$086D/$0879/$087A/$0876/$0877/$0887/$087B/$0864=0` |
| `$086E` | **High byte only** set128; the low byte is retained |
| `$0859` | **High byte only** set `$4FBE` |
| Flags cleared | `$0036&$BD`, `$0037&$9B`, `$0038&$7F`, `$0039&$C7`, `$0009 bit1` |
| Park cold/current bound | Both words `$02A3/$02A5=L1(ECTindex,$4EC2)<<8` |
| Drive cold/current bound | Both words `$02AD/$02AF=L1(ECTindex,$4ECF)<<8` |
| `$0875` | `L1(ECTindex,$4EDC)` cold-decay delay |

Choose base integral `$0862` and cold `$0871` from park cells when config `$4E8F bit0` clear, drive cells when set. Config bit5 uses the fixed integral byte `$4EB1/$4EB2` with fraction0 instead of the retained cell word; cold still comes from the corresponding cold cell. Store `$087D=$FFFF`.

If effective coolant `$0006<$4E91`, directly request park target `$4EB0`. Otherwise form `addH(baseIntegral,086B)`, add cold with saturation and enter the common BARO/position conversion at `$983D`. The running P/D/follower sum is bypassed on this route.

## Gear and AC transitions, `$9537-$969D`

Input housekeeping9167 runs in the ordinary even group. When config400F.2 is clear, sampled port004D bit0 is mirrored to AC request0052.5 and0041.4; with the option set, those states belong to the separate AC-control path. Always clear P/N0041.5, then set it for `(004D&1C)==14` when400F.6 clear, or004D.4 clear when that config bit is set. The port sample itself comes from board service3064→004D. Transmission context00A2 remains an explicit separate input owner.

Save the old `$0036` context. Drive is clear when `$400F bit6` and P/N `$0041 bit5` are both set; without that configuration bit, either `$00A2 bit6` or bit4 selects non-drive. Other cases set drive `$0036 bit1`.

On a gear-context change, load these byte parameters. All offset/delay additions in this table are **byte wrapping**, without carry saturation:

| Transition | Flow `$0879` | Hold base `$087A` | Qualification part |
|---|---|---|---|
| Enter drive | `$4F23` | `$4F24` | `$4F25` |
| Leave drive | `$4F26` | `$4F27` | `$4F28` |

Below coolant `$4F29`, entering drive adds `$4F2B` to hold and `$4F2A` to qualification part; leaving adds `$4F2D/$4F2C`. Store the hold and flow, then raise `$0864` to the byte-wrapped sum of hold+qualification if that sum exceeds its old value.

For the current gear context, compute the **byte-wrapped** difference of AC/no-AC cell high bytes: `$02A0-$029D` in park or `$02AA-$02A7` in drive. `$0052 bit5` becomes AC context `$0036 bit0`. On AC-off transition, if old AC was set and `$0877=0`, form `hi(difference*C[$4F0F])`, clamp in the ordered comparisons to `$4F10..$4F11`, then load hold `$4F12` and qualification part `$4F13`. On AC-on transition, seed divider `$0878=$4F22`; use `A4(MAT022F,$4F14)` when `$4E8F bit6`, otherwise `hi(difference*C[$4F1C])` clamped to `$4F1D..$4F1E`; load hold `$4F1F` and qualification part `$4F20`. Store magnitude `$0876` and hold `$0877`; raise `$0864` from their two delay parts as for gear. AC-off with a nonzero old hold skips reloading the transition.

If either context changed, apply pending cell transfers whose `$0038 bits0..3` qualify the **new** context: park/no-AC→word088F, park/AC→0891, drive/no-AC→0895, drive/AC→0897. These words replace the selected retained integral cells. A pending cold transfer bit4 can, on a gear change while a cold-bound high byte remains nonzero, copy `$0893→$02A3` when entering park or `$0899→$02AD` when entering drive. Clear the consumed cold-transfer flag and all four integral-transfer flags on the recorded exits. Pending transfers are not unconditionally committed on every pass.

## Switch adder, timers and RPM error, `$969E-$9748`

With `$4E90 bit1`, helper `$9247` returns carry set when `$004D bit7` is clear. That branch seeds `$087B=$4F2E`, `$087C=$4F30`, `$0864=$4F2F` and transiently sets `$0036 bit5`. The common `$96BF` then clears bit5, including on the just-seeded route. Treat the stored timer/adder as the persistent result; do not invent a retained steering-active flag.

If `$087A=0`, clear gear adder0879; otherwise decrement087A. Decrement nonzero AC hold0877, stall hold0869 and follower delay0884. The stall bit36.4 clears only on a call finding old0869 already zero.

Form byte RPM error `byte0063-byte0857`: set `$0036 bit7` on no borrow; on borrow byte-negate and clear the bit. Store absolute error0858. Build a forced error-filter target from the maximum applicable transition deadbands: `$4F80` if087A nonzero, `$4F81` if0877 nonzero, `$4F82` if087C nonzero, and `$4F7F` if filtered TPS high0882>0885. A nonzero maximum directly stores that byte<<8 in0859; otherwise `0859=lag8(error,old0859,C[$4F7E])`.

Then call integral `$99C5`, proportional `$9C20`, and derivative `$9CA6` in that order before composing airflow.

## Desired idle RPM, `$989C-$99C4`

This runs from slot7 before background learning. Service flag `$0038 bit6` retains the supplied0857 and returns immediately, also skipping stall-threshold refresh. Otherwise transform ECTindex as above and choose the base curve:

| Drive / AC | Curve |
|---|---|
| 0 / 0 | `$4F32` |
| 0 / 1 | `$4F41` |
| 1 / 0 | `$4F50` |
| 1 / 1 | `$4F5F` |

If battery byte00A7 is below `$4F84`, add `min(C[$4F86],hi((C[$4F84]-battery)*C[$4F85]))`. Add rough-idle term `min(C[$4F83],hi(byte0859*C[$4F7D]))`. These additions wrap as bytes.

An idle BLM cell index0247>=16, BLM0248 below `$4F87` and coolant above `$4F89` admits timer085B. Increment it only when the full phase high nibble is zero (slot7 phase07); at/above `$4F88` add `$4F8A/B/C/D` selected by drive/AC. A failed gate clears the timer. Before expiry no such adder applies.

Add startup085C. In park, a nonzero085C first becomes `R8(u8(2*085C),C[$4EBC])`; the byte shift can wrap. If the requested base is below old085F, store old085F-1 instead; rising/equal requests store directly. This downward slew precedes the optional switch correction.

When `$4E8F bit4` is clear, write that base directly to0857, retaining0860/0861. When enabled, select threshold `$4F8E` park or `$4F8F` drive:

- Base at/above threshold clears switch offset0860, reloads0861 from `$4F90`, and uses base.
- Below threshold, helper9250 returns carry from physical `$3008 bit2`, preserving A and the branch flags across PULA. Input clear counts nonzero0861 down; at zero, reduce nonzero0860 by1 and reload `$4F91`. Offset0 also reloads that delay. Store byte-wrapped base+offset.
- Input set and selected threshold<=old0857 writes the threshold directly, retaining offset/delay. Otherwise count0861 down; at zero increment byte offset0860 and reload `$4F90`, then use base+offset with wrap.

Finally refresh stall threshold0868: table byte at `$504D+(0036&3)` is used directly when `$4E8F bit7`, otherwise use `hi(desired0857*table_byte)`. The skipped service-override route leaves this threshold older than0857.

## Integral controller, `$99C5-$9C1F`

Choose cell base X=`$029D` park or `$02A7` drive. The local six-byte frame contains increment at Y+0, cold flow at Y+2 and integral at Y+4. Initialize integral from `[X]` or `[X+3]` according to AC; cold from `[X+6]`; increment0. These are stack-frame aliases, not global RAM at an old X/Y value.

### Qualification

TPS>=`$4EF2` sets `$0039 bit7`; otherwise clear it. That TPS failure or VSS>=`$4EF3` reloads0864 from `$4EF4` and clears closed-qualification36.2. Below both thresholds set36.2. Filtered TPS high0882 must also be<=0885 before counting0864 down; a call decrementing it to zero still takes the fallback that pass.

With full qualification and old delay0, underspeed requires0866=0; overspeed requires0867=0. The fallback permits an underspeed exception when0866,087A and0877 are all zero, and either36.2 is set or config4E8F bit0 is clear. Overspeed fallback is inhibited. All admitted routes also require low-battery3E.2 clear. An active kicker37.2, previous final flow088B=0 and overspeed together inhibit control. Set admitted flag36.3 only after these checks; other exits clear it and retain the selected cells.

### Stall and ordinary increments

An active stall flag36.4 with overspeed reloads stall timer0869=0 and commits unchanged integral. Active stall with underspeed uses the ordinary path. With the stall flag clear, RPM63 below threshold0868 sets it and adds a whole-byte flow increment from `$5051+(0036&3)` to the integral high coordinate, saturating the word; hold0869 is `$5055` park or `$5056` drive.

For ordinary error e=0858, define the shared table coordinate:

```text
E(e) = 16*e        for 0..4
     = 4*e+48      for 5..16
     = 2*e+80      for 17..40
     = 160         above40
```

Integral curves are `$4F92/$4FA8` for underspeed park/drive and `$4F9D/$4FB3` for overspeed park/drive. The word increment is `L1(E(e),curve)*e`, **unrounded and unshifted**, stored in the local frame.

For underspeed:

1. Coolant>`$50C2`, integral high>`$50C3` (no AC) or `$50C4` (AC), service3B.4 clear and mode50.4 clear select a position-reconciliation route: clear09.2; when phase<`$50C6`, decrement software position0007 without advancing phases. Skip the ordinary integral/cold update.
2. Otherwise previous final flow088B=`$FFFF` inhibits further positive integration. If not saturated, integral high at/above its snapshot `[X+2/+5]` and cold word below bound `[X+8]` directs the increment into cold with a word cap. This compares the **old** cold to its bound; the new sum is not additionally clamped to that bound here.
3. Other underspeed calls add the increment to integral with word saturation.

For overspeed, consume adders first. Reduce nonzero087B by the increment high byte, floor0, and force at least a decrement of1 when unchanged; otherwise do the same for startup flow086B. Either route skips integral/cold reduction. With both zero, subtract the increment from integral with zero floor. If VSS fault16.4 is clear, cold is nonzero and the candidate integral high is below its snapshot, reduce cold instead and retain integral. Otherwise commit the integral candidate.

If this candidate is zero,09.6 clear, error>`$50C5`, and service/mode gates clear, clear09.2 and, when phase<`$50C6`, increment software position0007 without a phase step. The increment/decrement position reconciliations are byte arithmetic; they are not position-sensor measurements.

On committing integral with VSS fault16.4 set, impose a high-byte floor: `$4EB1` park or `$4EB2` drive, plus `$4EB3` with byte wrap for AC. A candidate below that floor becomes floor<<8. Store integral through `[X]` or `[X+3]`. Every exit writes cold to `[X+6]` and0871, bound `[X+8]` to0873, integral to0862, then releases exactly the six-byte frame.

## Proportional and derivative terms

`$9C20`: park uses `$4FCC` underspeed or `$4FD7` overspeed. Drive reads one of eight words at `$9C96 + (8*AC + 4*admitted36.3 + 2*overspeed36.7)`. Their actual destinations are `$4FE2,$4FED,$4FF8,$5003,$500E,$5019,$5024,$502F`. These16 bytes are pointer data, not code.

Drive overspeed additionally has VSS authority hysteresis: VSS>=`$4FC9` sets37.6, VSS<`$4FCA` clears it, intermediate speed retains it. While set, cap error at `$4FCB`. Other routes retain the flag but do not apply that cap. Store `$086D=L1(E(effective_error),selected_curve)`.

`$9CA6`: transform ratio006C by `r=max(ratio-96,0)`, then input0 for a subtraction borrow,255 for r>=64, otherwise4*r. Look up `$503C`. Equal target/old086E high exits without updating086E, sign or magnitude0870. On a change, choose the following filter behavior using old derivative sign37.7 and RPM error sign36.7:

| Old D sign / RPM sign | Target movement | Operation |
|---|---|---|
| 0 / 0 | Either | `lag8(target,old086E,$503B)` |
| 0 / 1 | Rising | Same slow gain503B |
| 0 / 1 | Falling | Direct target<<8 |
| 1 / 0 | Falling | `lag8(target,old086E,$503A)` |
| 1 / 0 | Rising | Direct target<<8 |
| 1 / 1 | Either | Fast gain503A |

Store086E. Subtract128 from its high byte; a borrow clears37.7 and byte-negates the magnitude, otherwise set it. Store0870=`floor((magnitude+2)/4)`, preserving the actual two-shift rounding. Ratio production and default128 are documented in the speed contract.

## Composite flow and final step target, `$9752-$989B`

Apply each stage in the following order; saturation/floor occurs at each stage, not just at the end:

1. Integral0862+cold0871 with word cap. Add high-coordinate P086D for underspeed, subtract for overspeed.
2. Add high-coordinate D0870 when37.7 set, subtract when clear.
3. Add startup086B and switch087B, checking each high-byte carry. Add AC-transition0876 in AC context, subtract it otherwise; add gear-transition0879. Use word cap/zero floor at each guarded operation.
4. Save old087D and store the new base composite087D. With TPS<`$50A9`, a nonnegative word increase whose high byte>=`$50A8` produces AE087F=`S1(hi(sat16(4*increase)),$50A2)`; otherwise087F=0. This compares composites **before** follower/DFCO/BARO, not target step counts.
5. Add follower high byte0880 to the base word. A carry forcesFFFF and skips directly to the PE cap, bypassing DFCO correction refresh/application on this pass.
6. With DFCO46.3, refresh correction from `L1(RPM62,$50AD)-C[$50AC]`: unsigned borrow sets38.5 and byte-negates; otherwise clear38.5. Save magnitude0887 and divider0888=`$50BF`. Apply saved magnitude as a high-coordinate subtraction when38.5, addition otherwise. This application also runs after DFCO ends until background decay removes it.
7. PE3D.5 caps the flow at `W[$50AA]`. Store pre-BARO0889.
8. `F=sat16(2*M(A4(BARO01CC,$4EA3),0889))`.
9. With kicker option4E8F.2, an active kicker37.2 subtracts `$50C8` from F's high byte. Borrow sets37.3 and forces0, skipping the following gain; a successful subtraction retains the low fraction. The enabled nonborrow/inactive route then uses `sat16(F+M(C[$50C9],F))`. Disabled option uses F unchanged. Store final088B.

The position conversion is a special increasing-table interpolator, **not** the general signed-slope `$F4C1` helper:

```text
q = floor((F+8)/16)          # 0..4096; carries propagated by ADCB/ADCA
i = q>>8; f = q&255
first = C[$4E92+i]; second = C[$4E93+i]
target0008 = u8(first + R8(u8(second-first),f))
```

It always byte-negates the first-minus-second difference; falling tables therefore follow wrapped delta behavior rather than general descending interpolation. Stock `$4E92-$4EA2` contains17 knots. At the upper endpoint the code reads the next byte at `$4EA3` with zero fraction. Direct park/reset/service targets bypass this airflow conversion. The fast stepping routine receives the resulting0008 on its next admitted invocation.

## Throttle follower and extended cracker, `$9CFD-$9E98`

This routine runs from slot9, only when spark-running, before the other slow decays/diagnostics. Set requested scaled TPS=`sat8(4*TPS01D9)`:

- Above filtered TPS high0882, set the word directly to the capped requested byte<<8; cap is `$506E` park or `$506F` drive. Drive also reloads0884=`L1(2*min(VSS,80),$5071)`.
- At/below it, a nonzero0884 holds the whole filtered word. Otherwise select lag gain `$5070` park or `L1(2*min(VSS,80),$507C)` drive. Load below `$5088` replaces gain by `hi(gain*C[$5089])`; force gain1 if zero. Filter with `lag8(requested,old0882,gain)`.

While hot-start flag37.0 is clear, starting coolant outside `[$509A,$509B)` or runtime word00FD>`W[$509C]` sets it permanently until nonrunning initialization. If those gates pass it stays clear. This flag selects temporary multipliers below; it is not inferred from current coolant alone.

If TPS-open39.7, follower hold0884, or closed qualification36.2 is set, skip minimum-cracker insertion. Set age0886=255 when36.2; otherwise clear age and37.1. On the eligible off-idle route, DFCO with option4E8F.1 clear sets39.6 and skips insertion/age update. Otherwise form minimum from `L1(ECTindex,$508A)<<8`, or `sat16(4*table_byte*C[$50A0])` while37.0 clear. Raise the filtered TPS frame to that minimum if necessary. Increment age0886 toward `$5097`; finding old age>=limit sets37.1 instead.

Commit the filtered word's high byte0882; for high0 and low<40, clear its low byte0883. Subtract closed threshold0885 from the high byte, preserving the fraction. Borrow stores follower0880=0. Otherwise:

```text
excess = ((hi(filtered)-0885)<<8) | low(filtered)
if 37.1: excess = M(C[$509E] if 37.0 clear else C[$509F],excess)
F = sat16(4*M(S1(RPM63,$5064),excess))
if the RPM product's doubles did not overflow:
    F = sat16(4*M(L1(ECTindex,$5057),F))
if 37.0 clear: F = sat16(4*M(C[$50A1],F))
```

The overflow exit after the RPM gain skips the coolant multiplier. With TPS-open39.7, update0880 only when the high byte of the absolute word change reaches `$5087`. With TPS closed, leaving a DFCO-suppressed cracker condition clears39.6 and accepts the new value once. Otherwise accept F only when old0880=0 or F<old0880; keep a nonzero old follower against a rise. Thus follower state is neither an instantaneous TPS table nor a universally symmetric lag.

The companion document supplies the background cell transfers, reset triggers, fault checks, step sequencing and actual latch cadence. Those paths complete the software controller rather than leaving its selected cells or output shadow as unexplained inputs.
