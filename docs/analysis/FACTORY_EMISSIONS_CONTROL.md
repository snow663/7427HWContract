# Factory emissions controllers and shared outputs

This contract completes the resident BMHM EGR feedback/controller, purge,
AIR, catalyst model and associated shared output paths. Authority is the full
stock image SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
Addresses are CPU addresses, equal to offsets in this 65,536-byte file above
4000. The first 4000 file bytes do not make CPU RAM into ROM. Values here are
stock software quantities; the truck's separately recorded 2.bin calibration
is not substituted.

The instruction, branch and call evidence is in
[factory_dte_blocks.csv](../../maps/structure/factory_dte_blocks.csv) and its
companion maps. The already completed desired-EGR/fuel/spark equations remain
in [FACTORY_UPSTREAM_FUEL_CALCULATIONS.md](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md)
and [FACTORY_UPSTREAM_SPARK_CALCULATIONS.md](FACTORY_UPSTREAM_SPARK_CALCULATIONS.md).
EGR diagnostic phases are documented in
[FACTORY_DIAGNOSTICS.md](FACTORY_DIAGNOSTICS.md).

## Integer and lifetime conventions

`u8/u16` wrap to the stated width, `hi/lo` select bytes, and `sat8/sat16`
clamp an unsigned result. `R8(a,b)=floor((a*b+128)/256)`; `M(a,w)` is the
existing F550 rounded 8-by-16 multiplication. `L1(x,T)` denotes the actual
F4C1 curve lookup on raw knots spaced 16 axis counts apart; `L2(a,b,T)` denotes F4DE. These
helpers' geometries are specified in the engine contracts. An ASLD followed
by a carry clamp is not freely interchangeable with multiplication of an
already truncated high byte. A store of A preserves the adjacent fraction.

BRSET requires **all** mask bits set; BRCLR requires all clear. A BITA/BITB
followed by BNE accepts any selected bit. BMI/BPL test N, not N xor V.

Normal phase runs 00..9F with a nominal tick of 6.248474 ms. These are
software admission opportunities, subject to scheduler mode, reentry and
catch-up; they do not establish physical output periods.

| Path | Admission and ordering |
|---|---|
| D14E feedback; D1F6 position controller | Ordinary even fast pass, after range inputs and spark conversion |
| D03E EGR fraction | Ordinary low two phase bits 00, after the even feedback/controller calls |
| CDF7 hardware EGR command | Ordinary odd fast pass, after 7D4B fuel work |
| CF16 desired EGR | Slot 9; before slow IAC and VSS filter |
| D2B2 purge | Slot A, but returns unchanged when phase bit 4 is set; alternating slot-A admissions |
| CCC1 AIR/shared outputs | Slot D; before MAT and central diagnostics |
| D3B0 catalyst | Slot 5, but calculates only at full phase 05, engine-running and option 400F.4 |
| D472 manifold | Slot 5, every slot admission; local option 400E.3 |
| CB15 AC and diagnostic-switch inputs | Slot 6 |

## EGR state and option meanings

| State | Meaning and width |
|---|---|
| 01AE / 01AF | Desired position/duty byte / commanded duty byte |
| 01B0 / 01B1 / 01B2 | Pressure sum byte / flow byte / filtered fraction word |
| 01B4 | Raw feedback ADC byte |
| 01B5 / 01B7 / 01B9 | Closed reference word / filtered position word / rounded position byte |
| 01BA / 01BB | Absolute position error byte / coolant gain byte |
| 01BC / 01BE / 084F | Integral word / proportional word / integral increment word |
| 006D.3 | Actual feedback above desired position |
| 006E.7 | EGR flow admitted; produced by D03E, not a direct feedback switch |
| 0070.0/.2/.3 | Persistent failure / active response-test phase / completed-test stage |
| 0072.5 | Position/feedback EGR inhibition |

400D.1 is the **linear feedback option**. 400D.2 selects backpressure-style
fraction handling; 400D.5 also selects that fraction path. Several inherited
comments call bit 1 backpressure: the actual branch destinations distinguish
these options. They must not be merged. 400D.7 selects single-pass diagnostic
behavior; .4 suppresses linear flow at idle; .3 requires closed-loop fuel.

## Desired EGR CF16

The table below records admission before the two lookup gains. Failure enters
D010 with A=0. Later threshold/output inhibits still execute. Hysteresis bits
not reached before an earlier failure retain their old state.

| Gate | Exact admitting condition |
|---|---|
| MAT, if 400B.6 | Inverted ADC0230 strictly greater than 46FC when 006E.7 clear, otherwise 46FD |
| Coolant | If startup 0282<=46F9, current 0006>=46FA; otherwise 0006>=46FB |
| MAP faults | Both 0018 bits 30 clear |
| MAP | Current 01C0 strictly greater than 4703 entering,4704 staying;006E.4 records admission |
| TPS low | Unless 006F has any 24 fault,01D9 strictly greater than 4701 entering or 4702 staying;006E.5 records admission |
| RPM | 0062>=46FF entering or 4700 staying;006E.6 records admission |
| VSS | If 0016.4 clear,0284>=46FE; otherwise this VSS test is bypassed |
| Vacuum | 01C9<=4706 when 006E.2 clear, or<=4705 when set;006E.2 records admission |
| TPS high / AFR | 01D9<=4707 and 024A>=4708 |
| DFCO / open loop | 0046.3 clear; if 400D.3 set,003E.7 must be set |

470A selects the load coordinate:2 uses 01CF,0 uses 01C9, other values use 01C0.
Load is halved; RPM0062 is capped at 160. Desired A is the 470B surface result
multiplied by coolant gain 01BB and doubled with saturation, then multiplied
by the 4767 BARO/MAP surface and doubled with saturation. The second surface
coordinates are A=01C0>>1 and B=01CC. Desired values below 4709 become 0;
0051.4 or 0072.5 also forces 0. Store 01AE precedes optional opaque 1815
when 0086.6 set. Finally, service 003B.4 with 0393.1 writes 0394 to 01AE,
overriding the preceding result, including its inhibits.

## Feedback D14E and closed-reference learning

Without 400D.1, D14E writes 01B9=0 and returns; it retains the other feedback
words. With the option, it selects external mux 3, clears 001A.1, starts ADC1
and waits at most 12 polls for ready. Timeout sets 003A.0 and 001A.1, then the
routine still reads 3034 into 01B4. This is a software timeout indication,
not proof the returned ADC value is fresh.

If raw ADC01B4 is below the high byte of 01B5, filter it toward
`01B4:80` using 48A7. Enforce high-byte floor 48A6, setting the fraction 0
when the floor is used; write the resulting word 01B5. Then:

```text
delta = u16((01B4<<8)+128 - word01B5)
if subtraction borrowed: use delta's high byte0
product = min(hi(delta)*C48A4, 0x3FC0)
position_word = lag16(4*product, old01B7, C48A8)
01B7 = position_word
01B9 = hi(u16(position_word+128))
```

The final +128 is an ordinary word add, not a separate saturating round.
01B9>128 sets 0041.0. When 01B9<=128, desired 01AE=0 and 0041.0 was set,
clear that bit and write only the high reference byte
`01B5=min(u8(old_hi+2),C48A5)`. The old fraction remains. This is the second,
opposite-direction reference-learning path.

## Position/duty D1F6

Active response test 0070.2 forces 01BA,01BC,01BE and duty 01AF to 0 before
checking the linear option. Nonlinear mode otherwise copies 01AE to 01AF
without clearing the old controller words. Linear mode with service 0393.1
and 003B.4 bypasses the 0070.0/0072.5 inhibit; without that service, either
fault forces controller/error/duty 0.

Compute byte error `e=abs(01AE-01B9)` and 006D.3 for feedback>desired.
Store 01BA even when desired 0; desired 0 clears integral/proportional/duty,
but retains that computed error. On desired nonzero:

```text
if integral01BC == 0: integral = F4B6(01AE,48A9)<<8
increment = e * F4B6(e,48AF)             # full, unrounded product
084F = increment
integral = sat16(integral +/- increment) # subtract when006D.3set
01BC = integral
P = 2 * e * F4B6(e,48B5)
if doubling overflows: P = FF00          # not FFFF
01BE = P
output = sat16(integral +/- P)
01AF = hi(output)                        # no final rounding
```

## Flow fraction D03E and hardware CDF7

The 400D bits 20/04 branch clears 006E.7, returns fraction target 0 on 0070.0,
and otherwise uses the 478A surface when test 0070.2 set or previous 01AF!=0.
Nonzero normal duty also sets 006E.7. Its vacuum coordinate starts with
`v=u8(-01C9)`: use 2 v forv<=64; otherwise `min(192,128+((v-64)>>1))`.
RPM coordinate is `min(0062,160)>>1`.

The alternate branch also clears 006E.7 first. Fault 0070.0/0072.5 gives 0;
test 0070.2 uses desired 01AE. Normal linear flow requires idle admission if
400D.4, position 01B9>=485A and word run timer 00FD>=485B. Nonlinear flow
requires duty 01AF>=485D. Success sets 006E.7 and uses linear actual position,
or desired for the other mode. The position coordinate isR8(position,160).
The other coordinate uses the 47D3 airflow curve plus`u8(-01C9)`, saturating
the addition and compressing values>=64 to`min(144,64+((v-64)>>1))`.
The 47E5 surface gives 01B1. Multiply it by 47E4, halve **with carry rounding**,
FDIV by word 0232, then round the quotient's high byte using its low sign
bit, unless the high byte is already 255. There is no zero-denominator bypass:
word 0232=0 produces the FDIV overflow quotient FFFF, even with 01B1=0.

Both fraction branches then apply the 4856 offset lookup using BARO01CC
and offset 96, round the 8-by-8 product, and lag toward that byte using
`L1(min(hi0232,64),47CE)`. Word 01B2 is the stored filtered result. This is
the flow/fuel/spark interface, separate from duty and measured position.

CDF7 writes word 3FD8=`F000|duty`. Its duty selection is:

| Condition in order | Written low byte |
|---|---|
| 0051.4 set | 0 |
| Engine 004F.7 set | 01AF |
| Stopped and diagnostic 0071.7 set | 255 |
| Other stopped | 0 |

Thus the controller's 01AF is not the only hardware command source.

## Purge D2B2

Phase bit 4 set returns without touching any purge state. Otherwise 400C.7
must be set. A hot-start shortcut precedes DFCO and the normal qualifications:
if 0006>402C and word 00FD<=word 402D, set 01D6=255 and rebuild 0041.7.
It leaves multiplier 01D7 and timer 01D8 unchanged.

Normal admission requires 0046.3 clear, coolant>402B, VSS0284>=row[0],
TPS01D9>=row[2], high byte 0257>=row[1], and a nonzero byte
`ROM[4058+0247]` for the selected BLM cell. Row 4030 is used when 0041.7 clear,
4033 when set. Failure clears 01D6 and 01D8, and clears multiplier 01D7
only when VSS<402F.0041.7 is then cleared/rebuilt from nonzero 01D6.

In closed loop, update the multiplier only when vacuum 01C9<=4024 and
0005&C0=0. Otherwise clear 01D8 and calculate duty with the retained
multiplier. If timer 01D8<4025, increment and retain the multiplier. When
the old timer has reached 4025:

| Integrator 020F | Multiplier update |
|---|---|
| >=4026 | Saturating +4029 |
| <4026 and <4027 | Subtract 402A with floor 0 |
| Remaining window | Retain |

An attempted update clears 01D8. Closed-loop duty is
`max(R8(L1(hi0232,4036),01D7), L1(hi0232,4047))`.
Open-loop duty uses `p=u16(L1(hi0232,4047)*C4028+64)`, then doubles p;
carry from that doubling clamps FFFF. Store the high byte to 01D6. The add
itself is not separately saturated. Open-loop calculation leaves multiplier
and delay unchanged. The controller has no new purge-flow sensor inference.

## AIR and shared output service CCC1

First filter raw O2 byte 01D5 toward word 01D0 using 4E89. Without 400B.1,
skip the AIR decision and retain its old request/timer until common overrides.
With the option, B starts 0. Service 003B.4,038F.1 selects 0390.1 directly.
Normal AIR admission requires coolant>=4E8C and 0071.0 clear. In PE003D.5,
old timer 0279>4E8D turns AIR off; otherwise increment Band turn it on.
Outside PE require RPM0061<=4E8A, MAP01C6>=4E8B, and either 0050.1 set
or closed-loop 003E.7 clear. AIR request is 0046.2; store B into 0279 at the
shared decision exit. The local software polarity is recorded without
guessing valve plumbing.

Common overrides run even when the option was absent:

- Battery 00A7>=171 sets 0051.4 on the first observation. A subsequent high
  observation with that bit already set takes the clear-output route. A low
  observation clears 0051.4 and continues. This is a two-observation path,
  not an unconditional immediate off at 171.
- Stopped engine with diagnostic 0071.7 set requests purge 255, AIR on,
  AC0041.4 set and manifold 0052.3 set. Other stopped paths clear purge,
  AIR, shift lamp 0053.2, AC and manifold. The repeated high-voltage clear
  uses the same path even while running.
- Write AIR3FDA=DFFF if 0046.2 set, else D000.
- Write purge 3FD6=`B000|(selected_byte<<3)`; normal byte 01D6 is overridden
  by 0394 when 003B.4 and 0393.2 are set. This does not overwrite 01D6.
- For 3FD4, **any**0393 bit 38 enters a 0394 override, with no 003B.4 test
  at this selector: write`7000|(0394<<4)`. Otherwise start 7FFF.
  Governor option 400F.0 keeps 7FFF whenRPM0062>=50DC, otherwise 7000.
  Without that option, manifold 0052.3 keeps 7FFF; else option 400F.2
  and AC0041.4 clear keep 7FFF; remaining cases 7000.
- The shift-lamp 306C and nonelectronic-TCC306A co-writes follow these
  outputs; see the transmission contract. They are not aliases of EGR duty.

## Catalyst estimate and manifold tuning

D3B0 only calculates at phase 05 with 400F.4 and engine 004F.7. Other entries
retain the entire estimate and enrichment request. TPS<=4074 clears age 007E;
otherwise RPM0062<4075 increments that age without storing a wrapped 0.
Age>=4076 exits unchanged. Therefore high TPS may suspend the estimator.

```text
gain007C = L1(hi0232,4077)
base007B = L2(RPM0062>>1, hi0232,408F)
AFR_coordinate = 2*max(0,min(024A,155)-107)
reaction007D = L1(AFR_coordinate,4088)
target007A = sat8(base007B + (reaction007D-128))
word0078 = lag8(target007A, old0078, gain007C)
```

Signed target handling follows the actual post-SUBA N branch and byte carry.
In closed loop, estimate high 0078>406D increments 084C with saturation 255;
if the new timer>=4073, set 0052.6. At<=406E, or outside closed loop, clear
084C and 0052.6. The middle band retains the timer and proceeds to the second
pair: >406F sets 0052.6; >4070 retains it; otherwise clears it. This request
feeds the previously documented AFR path; it is a modeled temperature,
not an exhaust thermocouple reading.

D472 clears 0052.3 unless 400E.3 and its manifold window qualify. X starts 412B;
on entry with 0052.3 clear, require raw-temperature A8>=4131, then increment
X once. On entry with it set, X remains 412B and that coolant check is
bypassed. RequireRPM0062>byte[X],<=byte[X+2], TPS01D9>byte[X+4]. Set 0052.3
on success. The seemingly reversed row order is retained from ROM.

## AC/switch owner CB15 and the remaining speed reader

CB15 atomically clears 0050 bits 18, then ADC082F<40 sets diagnostic 0050.4;
40<=ADC<100 with factory-entered 0044.0 sets 0050.3. Other values leave both
clear. Without 400F.2 the AC portion returns, preserving its previous state.
With the option:

| Decision stage | State rule |
|---|---|
| Run/request | If run timer<word 4022 or 004D.0 clear, reload 0830=4012 and 0831=4013, then use the RPM-disable path |
| Start delay | Nonzero 0830 decrements and uses the same disable path |
| TPS cutoff | Compare TPS against 4010 when AC off,4011 when on. A qualifying low/equal TPS clears 0834; TPS above starts/increments 0834 until old word>4020. Either low/equal TPS or expired window continues only if IAC-enable 0036.4 clear |
| Coolant | AC off uses 401A; on uses 401B. Coolant>selected threshold reloads 0831 and uses the disable path |
| VSS/TPS delay | AC off selects 401D, on 401C.0016.4 or VSS>=threshold bypasses this delay. Below threshold, compare TPS to 401E(off)/401F(on); on also reloads 0836=4014. TPS above selected value with 0836 nonzero decrements it and reloads 0831 |
| Low RPM | AC off selects 4018,on 4017. RPM<=selected clears 0832; greater RPM counts 0832 toward 4015 and eventually uses disable path |
| Successful request | If high-RPM flag 0052.4 clear, set 0052.5; decrement 0831 until 0, then set 0041.4 |
| Disable path | Running RPM>4019 sets 0052.4, clears 0833 and reloads 0831. Otherwise count 0833 toward 4016, then clear 0052.4. Clear 0052.5 and 0041.4 |

The VSS comparison at CBD6 is now connected to this owner rather than left as
an unnamed peripheral reader. See the exact branch map for the tail jumps
back into the delay and disable stages.

## Interfaces and closure

The EGR/purge/catalyst working states above begin in unconditionally boot-cleared
RAM. Other shared states follow their named owners. Boot seeds the high byte
01B5 from 48A5 and preserves its later byte/word alias behavior. Service
payload framing and the 1815 extension remain separate implementation boundaries.
The ROM documents command words and sample handling; physical ADC scaling,
vacuum-sign conventions beyond the integer representation, driver polarity,
valve response and mechanical flow require their own evidence.

The named resident emissions software paths are documented through their
output selectors and diagnostics. This status does not imply complete serial,
factory-test, extension or whole-ROM reachability understanding.
