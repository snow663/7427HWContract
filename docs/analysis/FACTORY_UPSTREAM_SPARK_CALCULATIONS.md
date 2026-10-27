# Factory upstream spark calculations

This documents the resident spark-command construction through `$AB3E`, including all table/modifier branches, startup/run admission, knock-event production, low-octane learning and command limits. It connects to [the completed normal spark integer handoff](FACTORY_SPARK_INTEGER_HANDOFF.md). [The closure index](FACTORY_ENGINE_CALCULATION_CLOSURE.md) defines stock ROM authority, shared integer operations/lookups, cadence, initialization and external interfaces. `C/W` below mean ROM byte/word calibration reads. Raw counts take precedence over inherited engineering labels.

## Admission and inputs

The ordinary even group enters `$A466`, first producing the load coordinates documented in [upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md). `$A4B3-$A4EB` clears `$0018 bit4/$006F bit3`, then updates a MAP plausibility state: `$006F bit2` or raw MAP `$082E>=$4E64` clears `$0229`; otherwise an old counter `>$4E66` sets those two flags. Below that count, RPM61 `<$4E65` or TPS `>$4E67` increments the byte; other cases clear it. The flag-setting branch preserves the old counter. These updates occur before reference qualification and can affect later substituted loads.

Reference IRQ sets `$0050 bit5` when ignition-off `$0044 bit4` is clear. `$A4EC` consumes it, clears the **word** `$0260`, sets `$0050 bit2`, decays `$01EA` as documented in the handoff contract, and clears missing-reference counter `$0202`.

Two running qualifications are independent:

| State | Qualification |
|---|---|
| Fuel-running `$004F bit4` | `$A581`: period `$3FC0<W[$4135]` increments byte `$0211`; reaching `$4143` sets the bit and clears the counter. At/above the period threshold clear the counter. Called on qualified new-reference branches while the bit is clear |
| Spark-running `$004F bit7` | First reference sets `$0044 bit3` and bypasses conversion via `$AC51`. Later references require period `<W[$4133]`; reaching count `$4142` in `$0210` sets bit7, clears `$0210`, sets `$0004 bit3`, clears `$0051 bit6` and resets word `$01F2=0`. Period failure resets `$0210`; earlier calls use the alternate RPM path |

On an already spark-running new-reference path, `$004F bit6` **set** and `$0051 bit6` **clear** permit startup-gain update: `lag8(255,old01F2,C[$414E])` until the old word exceeds `$FEF0`, then set `$0051 bit6` to bypass gain in the output conversion. The same `$01F2` storage is later reused by decel recovery; it is not two independent variables.

Without a new REF, increment word `$0260` while below `$4962`; at/above the threshold write `$306F=0`. At `$0260>=$00A0`, cap `$02CE` down to `$4D96` if it was greater. When `$0202>=$17`, clear `$004F bits $90` and `$0044 bit3`, set `$005F=$FFFF`, clear `$3060 bit4` and enter the SWI loop. Otherwise a non-spark-running call uses `$AC51`; a running call increments `$0202` and continues to period/RPM/term conversion. These counters measure admitted calls, not independently established time units.

The alternate RPM path, normal period/RPM filters and their exact transforms are in the fuel producer document; the `$01EA/$083F/$01EC` period/battery/adaptive terms are already closed in the handoff contract. Together they remove the upstream period-input gap without duplicating that derivation.

## Base and environmental terms

### Base table and its actual header

At `$A700-$A709`, shift load latches `$01C1→$01C2`, `$01C0→$01C1`. The low-octane change comparison later uses the older latch `$01C2`.

Choose table `$4166` or `$428A` according to **entry** `$0050 bit6`: clear selects `$4166`, set selects `$428A`. Both headers are `00 00 11`; first data are `$4169/$428D`. Header byte0 is the **A/RPM lower offset**, byte1 the **B/load lower offset**, byte2 stride17. The older “MIN MAP then MIN RPM” header description is reversed relative to the actual helper, even though both stock offsets are zero.

Use B=load `$01C0`. A=`RPM61` when that byte<=64; otherwise `sat8(RPM62+16)`. `L2(A,B,header)` returns byte `$01F8`. There are17 rows ×17 columns. Raw row/column knots are0,16,…,256; the piecewise RPM coordinate gives conventional rows400,600,800,1000,1200,1600,…,6000 RPM, not a uniform400 sequence at the low end. The load labels20…100 kPa are conventional labels for the raw load coordinate, not proof of sensor electrical scaling.

The table choice occurs before this pass's idle controller writes `$0050 bit6`. Thus that selection uses retained state from an earlier admitted pass. It is not an instantaneous lookup selected by the later result.

### Coolant and altitude, `$A72D-$A779`

Mode byte `$43AE` chooses vacuum `$01C9` when zero, load `$01C0` otherwise; B is half that selected byte. Coolant row A is `$0006` through176; above176 it is `2*(min(coolant,208)-88)`. Header `$43AF`, first data `$43B2`, feed `L2`. With idle `$0050 bit7` and coolant `<$4140`, floor the raw result at `$413C`. Store `$01F9`.

Altitude spark is recalculated only when `$400D bit2` is set: `$01FB=L2(BARO01CC,vacuum01C9,$44D5)`. When disabled it **retains** `$01FB`; the later bias subtraction still occurs. The unconditional boot clear establishes zero at startup, rather than an implicit default equal to the altitude bias.

### Low-octane scaling and EGR

Slot7 produces `$0841=L1(RPM62>>1,$45BE)`. `$A77A` forms:

```text
load_factor = L1(load01C0,$45C7)
020B = R8(R8(byte0841,load_factor),byte020A)
```

The activity learner producing `$020A` is specified below. This retard is upstream of normal instantaneous KR.

EGR term starts as `C[$413E]<<8`. With `$006E bit7` clear, store that word directly at `$01F4`, resetting the filter to the bias. With the bit set, mode prefix `$485F=0` selects column `hi(192*byte01B2)`; that read is the **high byte** of word `$01B2`. Nonzero mode selects `V(u8(-01C9))`, where `V(x)=2*x` at/below64, otherwise `min(192,((x-64)>>1)+128)`. Row is `min(RPM62,160)>>1`; header `$4860`. Filter the lookup result with `lag8(result,old01F4,C[$485E])` and store the word. The EGR demand/fraction producer and enable qualification are in upstream fuel.

### MAT, PE and knock gains, `$CA6B-$CB14`

| Output | Production |
|---|---|
| `$01FA` MAT magnitude / `$0041 bit1` sign | `$400B bit6` clear or MAT `$022F<80` stores magnitude0, retaining the sign bit. Otherwise cap MAT at192. Prefix `$4439` nonzero selects B=`min(RPM62,176)`, zero B=`max(vacuum01C9-80,0)`. Look up `L2(MAT,B,$443A)`, subtract `$413F` with byte wrap; if result's N bit set, set sign bit and byte-negate the magnitude; otherwise clear sign bit |
| `$01FC` PE spark | Default0. Require coolant `>$45DA`, knock fault `$0019 bit4` clear and PE `$003D bit5` set. Then `R8(L1(RPM62,$44BF),byte0278)` |
| `$0841` low-octane RPM factor | `L1(RPM62>>1,$45BE)` |
| `$0843` knock event gain | `L1(RPM62,$4594)` |
| `$0844` normal KR cap | PE: `L1(max((RPM62>>1)-16,0),$4585)`; otherwise `L1(max((source>>1)-32,0),$458D)`, source255 when `$006F&$48` nonzero, vacuum `$01C9` otherwise |

MAT's N-bit classification after byte subtraction must not become a general signed comparison of unlimited values. Its later multiplier is also truncated rather than rounded.

Burst magnitude `$0842` is produced at `$CA4C`: `t=max(coolant-153,0)`, two byte left shifts, force255 if the second carry is set, then `H1(R8(transformed,153),$46E3,offset=0)`. Here t<=102 for a byte coolant, so the resulting transform equals a saturated multiply by4; the shift sequence elsewhere can have different behavior for larger inputs.

## Composite word and subsequent corrections

### Word sum, `$A7D7-$A81D`

`$01FD` is a **16-bit accumulator**, not a byte. The EGR byte rounds with word wrap: `e=hi(u16(word01F4+128))`. Then:

```text
01FD = u16(e + byte01FB + byte01F8 + byte01FC + byte01F9 + byte02CB
           - C[$413B] - C[$413C] - C[$413D] - C[$413E]
           - (C[$55F2] if (byte00A4 & $0F)!=0 else 0)
           - byte020B - byte015A)
```

Each subtraction propagates borrow to the high byte. `$02CB` is the startup spark adder, with seeds/decay specified in upstream fuel. `$015A` is a transmission-supplied retard input; subtraction and later limits are closed here, while transmission's production/state machine is separate. `$00A4` is also an explicit cross-controller input.

At `$A81E`, choose coefficient `$449D` when MAT sign `$0041 bit1` is set, `$44AE` otherwise. `effect=hi(L1(load01C0,table)*byte01FA)` with **no rounding**; store `$083C`. Subtract effect as a word when sign set, otherwise add, with word wrap.

### Idle spark, `$A84E-$A905`

Require runtime word `$00FD>=$415E`, VSS `<$415A`, coolant `>$415D` and TPS strictly below `$415B` (or `$415C` when entry `$0050 bit6` set). Failure clears bit6 and preserves the current `$01FD`.

Use IAC desired-speed byte `$0857` as target high byte, low byte0. When idle `$0050 bit7` is clear, add `$4160` to that high byte. A byte carry clears `$0053 bit0` and disables correction; the intervening subtraction on that branch is not committed as a correction.

For a valid target, subtract word `$0063`. Negative difference sets `$0053 bit0`, takes its word magnitude and selects table `$44F0`; nonnegative clears the bit and selects `$4502`. With magnitude d:

```text
index = d>>4                         if d<1024
      = min(255,(d>>7)+56)           otherwise
amplitude = hi(H1(index,table,0)*H1(load01C0,table+8,0))
signed_amplitude_byte = u8(-amplitude) if difference negative else amplitude
derivative = L1(4*clamp(byte006C-96,0,63),$451B)
b = u8(derivative + signed_amplitude_byte - C[$4514])
```

If b has bit7 set, sign-extend it to a word without an additional negative clamp. Otherwise cap it at `$4515` and zero-extend. Add that word to `$01FD` with wrap and set `$0050 bit6`. `$0857`, `$006C` and their full IAC controller are explicit interfaces; this closes their spark consumption.

### Transient spark, `$A906-$A979`

Require coolant in inclusive `[$46F2,$46F3]` and `$400F bit7` set. Otherwise preserve transient state and do not modify demand. At idle (`$0050 bit7`) store `$0838=byte0837<<8`, with no adder.

Off idle, save byte error `u8(byte0063-byte0838)` at `$083A` **before** updating the lag. Gain=`L1(TPS>>2,$46F4)`; `$0838=lag8(byte0837,old0838,gain)`. Select three-byte parameters `$46EC` for error N clear or `$46EF` for N set; use byte-negated error magnitude in the latter case. Compute `correction=min(param2,u8(hi(magnitude*param0)+param1))`, storing `$083B`. The offset addition wraps before the cap. N-set error adds the correction to `$01FD`; N-clear subtracts it, with word wrap.

### Decel and recovery, `$A97A-$A9DF`

DFCO `$0046 bit3` sets recovery latch `$0051 bit5` and clears word `$01F2`. Let `d=u8(byte01F9-C[$413C])`. Store `$0208=u8(C[$4152]+d)` when d's N bit is clear, otherwise `$0208=C[$4152]`. Subtract that byte from demand with borrow propagation.

Without DFCO, a clear recovery latch skips this correction. With it set, choose gain `$414F`, or `$4150` when TPS `>$4151`. If old `$01F2>$FEF0`, clear the latch; otherwise update it with `lag8(255,old,gain)`. **This call still applies recovery even if it just cleared the latch**: add `R8(hi(01F2),0208)-0208` to demand. Startup gain and decel recovery share `$01F2`; the mode and latch decisions must remain in a replay or reconstruction.

### Extension and special override, `$A9E0-$AA19`

`$0086 bit6` calls external `$1812`, whose implementation/effects are not supplied by the mapped ROM. The subsequent resident override runs only when `$4E90 bit1` is set. It requires `$0036 bit5`, coolant `>$4161` and TPS `<=$4164` (or `$4165` when old `$0053 bit4` set). Success replaces word `$01FD` with `W[$4162]` and sets `$0053 bit4`; an enabled-but-failing qualification clears it. A disabled calibration branch retains that flag.

## Reference subtraction, burst, normal KR and limits

At `$AA1A`, set `word01EE=u16(word01FD-C[$4132])`. `$AA25` imposes the upper bound using a true signed `BGT` after subtracting demand from `W[$4144]`: store the signed smaller word. This is not an unsigned cap, and occurs before the following knock terms.

### Burst, `$AA33-$AA80`

Require `$400F bit3`, `$0050 bit4` clear, and coolant `>$45DA`. With old `$006E bit1` set, decrement byte `$020E` (zero wraps), clear the latch if the result is zero, and subtract `$0842` from `$01EE` **on this call even if the latch cleared**.

Without that old latch, load `$01C0<$46DF`, TPS `<$46E0` and a nonnegative `TPS-byte01DA >= $46E1` arm the latch and load `$020E=$46E2`. The newly armed call does **not** subtract burst. If the global burst gate fails, the local timer/latch is retained while this subtraction is skipped.

### Normal knock, `$AA81-$AADB`

Atomically read pending events `$020D` into B and clear the byte, then reenable interrupts. Event consumption happens even on routes that subsequently skip or zero KR:

1. Active burst latch sets A0; or when `$0016&$60==0` and coolant `<$45DA`, set A0. Store `$020C=0` and subtract zero.
2. Otherwise, if VSS `<$45D8` and byte `$0063<$45D9`, skip both the normal-KR update and its subtraction. The old diagnostic `$020C` is retained but is not applied on this route.
3. Knock fault `$0019 bit4` chooses fixed `$4E77`.
4. Otherwise `candidate=sat8(old020C+hi(2*byte0843*events))`, with a doubling carry also forcing255; use `min(candidate,byte0844)`.

For updating routes store `$020C=A`, then subtract `A>>1` from `$01EE` through the saved stack byte. Normal KR's stored byte and spark-subtraction counts therefore have a factor-of-two relationship. The exact stack proof and subsequent output conversion are in the integer handoff contract.

### Signed lower bounds and service, `$AADC-$AB3D`

Select a signed lower bound:

| Condition | Bound |
|---|---|
| `$015A!=0` and `$00A4 bit3` set | `W[$414A]` |
| `$015A!=0`, bit3 clear, any `$00A4&$17` | `W[$414C]` |
| Otherwise recovery `$0051 bit5` and TPS `<=$48DA` | `W[$4148]` |
| Other | `W[$4146]` |

The actual `BLT` compares signed bound to demand; replace demand only when bound is at/above it. This supplies a signed lower limit after knock, independently of the earlier upper limit.

Service `$003B bit4` plus `$0395 bit3` edits D **after** these limits. With `$0395 bit4` clear, zero D first; otherwise retain it. `$0395 bit5` chooses subtract `$0398`; clear chooses add it, with word wrap. `$AB3E/$AB41` commit this post-service command to `$01EE/$01F0` before the established period/startup/rolling-state handoff. Service edits are not silently re-clamped.

## Knock-event and adaptive-state producers

### Knock IRQ, `$CE7C-$CEBA`

Acknowledge `$3023=$80`. Sample live word `$3FC8`, form wrapped difference from old `$0203`, and save the new baseline. Cap that event difference at255. Index both knock curves with `RPM62>>2`:

```text
excess = count - C[$45DB+index]
if excess <= 0: return from interrupt
increment = sat8(excess+C[$461C+index])
020D = sat8(old020D+increment)
```

If the first addition carries, the actual code directly writes255; the final result is the same cap. This accumulates pending events, while `$AA81` owns atomic consumption/reset. It does not prove each hardware count represents one physical knock.

### Normal KR decay and sensor fault, `$CEBB-$CF15`

On slot8 only when phase bit4 is clear, `step=max(1,R8(L1(RPM62,$45A5),old020C))`, then `$020C=max(old020C-step,0)`. The local implementation uses a negated byte plus carry to floor at zero. Other slot8 phases skip decay but still reach the diagnostic.

With `$5B03 bit4` enabled, read ADC channel0. An input outside inclusive `[$4E76,$4E75]` increments byte `$0207` while the old count `<=$4E74`; an old count `>$4E74` sets fault `$0019 bit4`. A valid input clears the fault and count. The increment is not universally saturating for arbitrary calibrations; a disabled diagnostic retains both. Its gates into PE spark, normal KR and low-octane learning are all explicit above/below.

### Low-octane learning, `$CE10-$CE7B`

Only full phase `$06` executes learning, nominally once per160 TOC3 ticks. Load old activity `$0209` into B. Fault `$0019 bit4` subtracts `$45BC` with zero floor, then stores/scales it. Otherwise require coolant `>$45B6`, load `$01C0>=$45B7` and no positive load increase above `$45B8` relative to `$01C2`. A negative load change passes that last check.

| Normal KR `$020C` | Activity update |
|---|---|
| `<= $45BA`, old `$0052 bit1` clear | Set bit1, clear bit0; retain activity this first low observation |
| `<= $45BA`, bit1 already set | Subtract `$45BC` with zero floor |
| `> $45BA` but `<= $45B9` | Clear `$0052 bits $03`; retain `$0209/$020A` |
| `> $45B9`, old bit0 clear | Set bit0, clear bit1; retain activity this first high observation |
| `> $45B9`, bit0 already set | Add `$45BB` with saturation |

A failed coolant/load/change qualification clears `$0052 bits $03` and retains activity and scaled retard. An admitted store writes `$0209=B`, then `$020A=R8(C[$45BD],B)`, including the first-observation routes that retained B. The scaled `$020B` subsequently enters the word sum, before burst and normal KR. This is a distinct adaptive retard, not a component automatically removed by adding logged normal KR back to logged spark.

### Companion reference word, `$CDF7-$CE0F`

The ordinary odd group writes `$3FD8=$F000|b`. Select b0 when `$0051 bit4`; otherwise use actual EGR-duty byte `$01AF` when spark-running `$004F bit7`; without that running bit, use255 when `$0071 bit7`, otherwise0. This software write is distinct from the period/EST conversion. Its hardware interpretation remains in the output-interface scope.

## Completion and interpretation

All resident upstream terms and local branches through the command handoff are documented here, together with their separate startup, gain, interrupt and learning producers. The older [modifier/tuning contract](../contracts/SPARK_UPSTREAM_MODIFIER_CONTRACT.md) retains its recorded `2.bin` calibration facts; this document supplies exact stock arithmetic and corrects the table-header interpretation and word width.

For log reconstruction, `logged Spark + logged normal KR` approximates a pre-normal-KR composite command. It already includes low-octane, coolant, PE, EGR, startup and applicable state corrections, and later signed limits/service paths can change it. Raw base-table recovery therefore requires these states and ALDL serialization timing. Completing this software derivation does not claim closure of IAC/transmission/governor controllers, unknown `$1812/$180F` extensions, post-handoff monitor `$ABCB`, physical spark angle/timebase or all interrupt interleavings.
