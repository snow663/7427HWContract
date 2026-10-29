# Factory transmission control

This documents the resident BMHM transmission input, shift, pressure,
adaptive-learning, TCC, spark-request and output code from actual stock ROM
bytes. The image SHA-256 is
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
CPU4000..FFFF equals offsets in the full 65,536-byte image; CPU0000 remains
RAM. No stock value is substituted for the separately recorded truck 2.bin.

[factory_dte_instructions.csv](../../maps/structure/factory_dte_instructions.csv)
and the branch/call/state maps contain the instruction evidence.
[factory_transmission_descriptors.csv](../../maps/structure/factory_transmission_descriptors.csv)
decodes the priority tables, including RAM override targets. The
[diagnostics contract](FACTORY_DIAGNOSTICS.md) owns fault detection,
reaction-mask formulas, retained clear/age and local service lifetimes.
The [emissions contract](FACTORY_EMISSIONS_CONTROL.md) owns shared output
and AC selectors.

## Conventions, gear encoding and execution context

All words are big endian. `u8/u16` wrap; `sat8/sat16` saturate unsigned;
`s8/s16` interpret the corresponding two's-complement value. `SS8/SS16`
saturate a mathematical signed result. `R8(a,b)=floor((a*b+128)/256)`.
`L1` is F4C1; `S1` is F4B6; `L2` is F4DE, with the exact lookup geometries
and lag/FDIV rules in
[the engine calculation contract](FACTORY_ENGINE_CALCULATION_CLOSURE.md).
`Q(n,d)` is the fractional divide quotient:floor(65536*n/d) when d>n,
otherwise FFFF. IDIV is the integer quotient, not Q. Helper calls preserve
registers only as specified by their actual implementation.

Gear D9 is **zero based**:0 first,1 second,2 third,3 fourth. The one-based
service field 0103 uses 1..4. Pattern 009F bits 1/2 request performance/manual;
bit 3 marks an illegal selector. Range 00A2 is a decoded bit field, not D9.
BRSET requires all selected bits; BRCLR requires all clear. BMI/BPL uses N;
signed relational branches use N xor V. PUL/XGDX preserve arithmetic flags.

| Operation | Scheduler admission |
|---|---|
| Current sample 7B6D and feedback 7C13 | Every nonfactory timer entry before phase advance/busy check; no second step in a tail catch-up pass |
| Switch/capture/fault/input pipeline AE85 | Ordinary phase&3=0 |
| Shift selection D4EB | Slots 3 and B, nominal 8 ticks between opportunities |
| Board solenoid/TCC service C514 | Slots 3,7,B,F; after D4EB in 3/B |
| Shift progress B32D | Ordinary phase&3=1 |
| Pressure/TCC progress B56B | Ordinary phase&3=2; exact order B587,BE5C,BA38,BF62,BEBC,C00B |
| TPS and transmission spark C4E5 | Ordinary phase&3=3; after main IAC |
| TCC qualification C6BB | Slot 5 only when 400F.6 clear |
| Temperature/BARO environment | Slots 1 and 4; slot 4 alternates bit 4 groups |
| Central local DTC wrappers C8B1/C4F5 | Slots 4/F respectively |

Tick 6.248474 ms and phase 00..9F give nominal opportunities, not guaranteed
wall-time periods. The nonelectronic 400F.6 option changes C6BB admission,
C514's output branch and ADAA, but there is no single top-level option
branch that skips every other transmission task. Do not infer one.

## Switches, pattern and input pipeline AE85

AE85's order is AEA4,B018,B089,C483,B1F0,B23C,B2C9,B2ED,F781,F64E.
Consequently a local service update occurs after that pass's earlier input
calculations. Fault reactions may affect following calculations immediately
or the next task depending on this order.

AEA4 samples 3000.6 into 0076.7. It builds 009E from
`(~3002)&0F` plus`((3060 xor3062)&03)<<4`. Save 009C to 009D, mirror PE003D.5
into 009C.2, and set 009C.7 only for 0050.4 with 0086.7 clear. Capture 004D into
009B;5D03 bits 02/04/08/10 can hold range/bit 0/bit 7/0076.7-derived states
on a detected input change. Without their hold,009C.1 mirrors 004D.0,
009C.5 is inverse 004D.7 and 009C.6 inverse 0076.7.004D.7 changes reload 01AB
from 5D2F;01AB decrements in that same admission.

The range lookup uses `(004D&1C)>>2` to select ROM B010:

| Raw index | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|---|
| A2 decode | 88 | 08 | 88 | 04 | 20 | 40 | 01 | 02 |

Save old A2 to A3 before comparing; a change clears stability age A1, otherwise
A1 increments without storing wrapped 0. B018 filters ADC01A1 toward 01A2
with 5D2A, classifies its high byte using 5D2B..2E, and selects
B084=`09,01,02,04,09`. Candidate changes clear 01A5; unchanged candidates
count toward 5D29 before replacing 009F. Option 5D02.5 with A2.1 and 0098.2 clear
directly requests manual 04. B089 runs range/pattern/TPS/speed diagnostics;
0098.2 forces A2=88. Qualified illegal-pattern fault can replace 009F low
nibble with 09; unsupported manual requests toggle 05. These are literal
mask operations, not a new inferred gear selector.

C483 constructs one-hot priority selectors:

| Selector | Priority, first match |
|---|---|
| 0080 shift | manual→01,performance→02,otherwise 04 |
| 0082 cold gain | manual→01,otherwise 02 |
| 007FTCC | transmission hot 0087.1→01,manual→02,performance→04,otherwise 08 |
| 0081 kickdown | coolant-hot 0087.2→01,transmission-hot 0087.1→02,manual→04,performance→08,otherwise 10 |

## Capture records, speed selection and slip

AEA4 first derives engine speed B7=`Q(120,word005F)`, replacing results<=120
with 0. It then atomically obtains pulse count 3027 and capture 3010, repeating
the capture and incrementing the count if the count changed across the read.
Write record B9's+8/+6. The turbine estimator E58C uses Y=B9, gain word 5D12,
reload byte 5D11, returning D into BD. Gear>=3 adjusts C4=`Q(BD>>1,word5D15)`;
lower gears copy BD.

Output capture uses 3FE0/3FC2 when 5D02.4 clear, otherwise 3FC6/3FF8.
It rereads the capture/count pair on detected change and writes record C8's
+8/+6. E58C usesword 5D19 andreload 5D18.009C.5 then applies F5A2 multiply
byword 5D1C andtwo saturating doublings before storing CC.

E58C's nine-byte record and literal returns matter:

| Offset | Meaning |
|---|---|
| +0 | Previous byte count |
| +1 | Previous capture word |
| +3 | Timeout byte |
| +4 | Saved speed word |
| +6 | Current capture word |
| +8 | Current byte count |

For nonzero wrapped count deltan, if old timeout is nonzero calculate
`saved_speed=Q(Q(8*n,calibration_word),u16(current_capture-old_capture))`.
If old timeout 0, skip that calculation and retain the saved speed for this
first batch. Save current count/capture, reload timeout from the caller's B,
and return the saved speed word.

For **unchanged count**, decrement nonzero timeout. If it remains nonzero,
return D=`0:remaining_timeout`; the routine does **not** reload the saved
speed on that exit. At timeout 0, zero record+4 andreturn 0. Thus the caller's
BD/CC store can receive a small timeout value while record+4 still holds an
older speed. This distinction is preserved from bytes E59D→E5CE and checked
by bounded execution; it is not silently changed to a conventional hold-last.

B1F0 filters B7→word 01AC with 5D10,BD→C2 with 5D14,C4→C6 with 5D17.
It forms `SS16(B7-C4)`, filters that signed word through F420/5D0D into EB,
and writes its absolute representation into ED. These slip values therefore
use different histories from the selected output-speed path.

B23C selects output D1:

- With 0098.1 fault, obtain a gear-ratio word through B2B2 and use
  `Q(BD>>2,ratio)`. Reverse 009C.5 additionally applies 5D1C/F5A2 and×4 sat.
- Otherwise, when 0164 or 0175 timer is nonzero, retain old accepted D5 as D1.
  With both 0 use CC; copy old D3 to D5 only when 0086.3 set, otherwise write D5=0.
- Filter selected D1 toward D3 with 5D1B. Divide D3 byword 5D1E, signed-saturate
  its high byte around bias 128 using 0102, add 128 with FFFF overflow cap,
  save 0814, then lag toward D7 using 5D20.

B2B2 usesword 5B43 for A2.5; otherwise words 5B49+2*D9, forcing index 1
if 0098.2. B2C9 uses C2/D3 normally; gear>=3 and 0089.5 uses 01AC/C2,
while gear>=3 withoutthatbitsets 009A.1 anduses C2/D3. Halve numerator twice;
if zero, XGDX swaps in denominator before FDIV. Store quotient F9.
Do not remove that zero-path swap or assume ratio F9 is always a physical ratio.

## TPS, temperature, BARO and gain owners

B0E4 uses 0098.0 for defaultTPS=C5B22:00. With pending enabled TPS-fault
timers it uses the TPS history 01AA when 5D02.0, otherwise retains B0.
Normal operation filters raw A6 down toward retained 02F6:80 with 5B25;
qualified brake/deceleration episodes can increment its **high byte only**
by 5B29 up to 5B24, retaining its fraction. It shifts overlapping byte histories
01A6..01AA andlags the admitted value towardword B0 using 5B28.
Bias 0101 is applied around 128 with signed saturation to produce B2.
Kickdown 009C.4 is set forTPSB0 strictly above 5D21 entering/5D22 staying,
unless manual 009F.2. B1AC is the boot upward TPS-zero filter 5B27, capped at
5B24:00. B1CF subtracts rounded 02F6 fromraw A6 withfloor 0, multiplies 5B26,
adds 32 and doubles twice with saturation; it stores high 01A6 forengine use.

C8D6/C96A use direct 256-byte conversion tables FC45/FD45 selected by 0043.7
or channel hysteresis 004E.1/.0. Converted values<=106 set the hysteresis,
>120 clear it, the middle band holds. C8D6 writes B4; C96A writes A8 andnormal
engine coolant 0006, with fault/default behavior linked in the engine contract.
C8FD substitutes 5B6A for enabled live 58/59, filters B4:80 toward B5 with 5D0B,
sets transmission-hot 0087.1 using 6ABA entering/6ABB staying, and builds
cold weight AB from A9 and 5D36/37:FF below/equal lower,0 at/aboveupper,
otherwise`~hi(Q((A9-lower)<<8,(upper-lower)<<8))`.0087.0 has separate
5D34/35 hysteresis. C9C0 filters A8:80 with 5D0C into A9, using 5B17 if enabled
coolant faults; >5D04 sets 0087.2,<5D05 clears it.

C668 uses reaction masks to substitute word 5B6F for high BARO/MAP faults,
word 5B73 for low faults, respecting 5D02.2 separate-BARO option. Otherwise
`wordAC=lag16(02F3*C5D07+word5D08,oldAC,C5D0A)`. AC is a word;
the descriptor gains use its high byte. B2ED classifies8*temperature B5 with
its -1/+17 hysteresis into 0152 andloads 0153/0154 from B31D and B325.
These gain bytes feed the fast force-current controller.

## Priority descriptor D8FE

The descriptor has stop-maskbyteh 0, stridebyteh 1, then word pointers.
Input A is a selector mask, B is a gear column, X is descriptor base. For
bitpositionsk=0..7 in increasing order:

```text
row_address = base+2+2*B+k*stride
if A & (1<<k):
    X = word[row_address]
    return C=0 if X!=0 else C=1
if stop_mask & (1<<k): return C=1
```

Selection is tested **before** the stop mask. A null selected pointer fails
immediately; it does not try a later set selector bit. On a stop/no-bit
failure, X retains the current row address; it is not automatically 0.
A/B are restored. The pointers are complete big-endian words, not halves
combined with a stored routine byte. Dynamic selection and conditional
priority are real; these particular tables supply data/curve addresses.

| Tables | Use |
|---|---|
| D6BD/D6D7 | Normal up/down speed curves, selector 80,3 gear columns |
| D6D1/D6EB | Three direct cold-offset curve pointers; **no descriptor header** |
| D6F7/D71D | Kickdown up/down speed scalars,selector 81 |
| D717/D73D | Three direct cold-offset scalar pointers; **no descriptor header** |
| D743 | Kickdown upshift RPM-word scalar,selector 81 |
| D6F1 | Three direct cold RPM-offset word pointers |
| D763/D775 | Nine direct range-override pointers indexed by 3*(range_low>>1)+gear |
| D787/D79B | Fault override descriptors pointing to RAM0104..0106/0107..0109 |
| D7AF/D7C1/D7D3 | Temperature gains for speed, kickdown floor and RPM |
| C2D6/C2F8/C31A/C33C | TCC release/apply normal/kickdown speed |
| C35E/C380/C3A2/C3C4 | TCC apply/release base and rate curves |
| C3E6/C3F8 | TCC normal/kickdown cold gains |

The originally apparent C3A2 dispatchers and writes fall inside these
descriptors. This semantic contract extends their previous byte/data proof;
it does not generalize that conclusion to unrelated dynamic dispatch sites.

### Threshold helpers and arithmetic

D980 adds a signed 16-bit offset scaled by cold AB to an unsigned base inX,
preserving X and clamping the mixed-sign sum at 0/FFFF. It takes the offset's
magnitude, applies F550 rounding, restores its sign, and uses carry plus operand
signs for saturation. For -32768 the magnitude is8000; it is not discarded.

D94B forms a gain from calibration byte g:
`o=s8(u8(g-128)); D=u16(2*hi(AC)*o-(o<<8)+8000)`.
Its returned A is the gain high byte. D92E selects a gain pointer via 0082 and D9;
if present, multiply saved input word by A with F550 and double/saturate. If absent,
restore the original input word. This multiplier is distinct from D980's
additive cold correction.

D969's other pressure factor uses `o=hi(AC)-128`, scalarf=byte[X].
Form the signed producto*f, add 4000 to its word representation. If the signed
high-byte addition is not greater than 0, use 0; otherwise double the word
with ordinary 16-bit wrap. This is the actual BGT-after-ADDA rule; it has no
general unsigned FFFF cap. B587 rounds it before taking the high multiplier.

D7E5 normal threshold uses descriptorY+6 andselector 80. It obtains
`v=L1(B2,selectedcurve)` and firstknotb. IfY+8'sper-gear cold curve exists,
its values and firstknot supply signed offsets about 128; otherwise offsets 0.
Apply D980 to(v<<8), then D92E usingY+10; separately cold-correct(b<<8).
Return the larger high byte of corrected result and corrected firstknot,
carryclear. Missing main descriptor returnscarryset.

D840 kickdown uses Y+0 withselector 81 and scalar first byte, cold scalar from
the direct per-gear pointerY+2; Y+4 gives gain. It also obtains the normal
Y+6 firstknot/coldY+8 firstknot floor. Return the larger high byte; missing
kickdown main descriptor returnscarryset. D8A7 uses the D6B7 triple for the
additional upshift RPM-word threshold: load direct cold offset word, select
main RPM pointer with 81, add cold correction and apply gain. Its failed
D8FE path retainsXas returned by that helper; no nonexistent zeroing is
assumed. D8CE range override only admits A2 low 3 nonzeroand 0098.2 clear,
then the nonzero direct pointer; D8F0 reads a selected overridebyteor 0 onfailure.

## Shift selector D4EB

Rebuild reaction flags through E684,E6AC,E69C; clear source 0084. For gear<3,
try upshift sources in strict priority: nonzero RAM-fault descriptor D787,
range override D763, admitted kickdown D840(D69F), normal D7E5(D69F).
0084 bits 08/04/02/01 record that source. Threshold FF prevents upshift;
otherwise threshold<=speed D7 and optional RPM thresholdX<=word 01AC admits
+1.0099.5 bypasses the RPM threshold by settingX=0.

If no upshift, gear>0 tries downshift equivalents D79B,D775,D840(D6AB),
D7E5(D6AB), recording 0084 bits80/40/20/10. Threshold 0 prevents downshift;
otherwise threshold>speed D7 admits-1. A changed tentative gear saves the
threshold into 0187. Then apply overrides in this order:

1.0087.0 or 0098.7 caps gear at 2.
2.0099.3 forces 1.
3.0099.0 blocks an upshift to>1 or a downshift to<1; if resultinggear 1
  andspeed D7>=5D39, change to 3.
4.0098.3 or 0099.1 forces 1, overriding the preceding rules.

Clear 0083 bits 24 andset.2 forhigher/.5 forlower tentative gear. A downshift
from gear 2 latches 0083.6,clears.7 onentry. Outside that case clear.6 and
increment 0135 without storingwrap 0. Downshift from gear 3 clears 0135. During
the specialgear 2 window, if 0135 in(5D32,5D33),0118=0 and 0134<5D31,
holdoldgear. Otherwise downshift also waits forTCC offage 0125>=5D30.
0085.5 marks the range A2.2,gearcandidate 3,0197 nonzero case.

E562 caps candidate using E57C's four rows indexed by(A2&7)>>1, substituting
lowbits 6 when 0. Rows are[0,1,1,1],[0,1,1,1],[0,1,2,2],[0,1,2,3].
After that cap, clear 0083 bits 09. Nonzero service 0103 is decremented,
clamped to 0..3 andwritten directly to D9 with 0187=FF; it does **not** set
the normal up/down event bits. Without service, set 0083.0 for up/.3 for down
andupdate D9 onlyon change. Request, event and observing bits have different
lifetimes.

## Shift observation B334/B367 and learning qualifications

B334 sets movement/runflag 0086.7 andclears 00FF if anyword 01AC/D3/C6
reaches 5D23/25/27. Below all three, only an already-setflagcounts 00FF;
new 00FF>5D0E clearsflag. The byteincrement itself wraps.

B367 increments DB with saturation 255.0083 combinations 11 or 0A clear
snapshotbits 12 andactive 0085.1. On a new event(any 83&09)wheninactive,
set active 0085.1,clear 0085.4/.7,snapshot up.0→.1/down.3→.4,record range
instability 008E.3,saveold DB→0188,clear DA/DB/019A,set DF/E0=127,
initialize qualification 90 frompatternchange,clear 91/92,saveTPSB2→0195.
Absence of a current event clears active. An already complete 0085.7 returns.

For a normal upshift, compare ratioword F9 to 68A9+2*(D9-1). At/above it,
clear accumulation 019A and 0085.4,reset origin DA=DB andsave 0189[gear-1].
Below it but not belowword[X+6], add F9>>5 to 019A with FFFF capandset 0085.4.
Each admitted stage runs B4B2. When the ratio falls below the lower bound,
or DB=255, finalize mean=`sat16(32*IDIV(019A,u8(DB-DA)))`, preserving
FFFF as a sentinel. Store its high byte 019C[gear-1]. A short observation
sets 0091.6 using 68CB[gear-1]. Then BA65 learnsand F131 tests long shift;
mark 0085.7,clear activeand 83 snapshotbits 12. Gear 0 or downshift snapshots
complete on DB>=68B5[D9]without that upshift-learning calculation.
009A.1 takes the documented alternative completion path and sets 91.4/9A.4.

B4B2 accumulates reasons in 90/91 rather than resetting them each call:

| Field | Disqualifying observations |
|---|---|
| 90 | Pattern/change bit 0; temperature outside the open window; TPS outside(lower,upper]; large TPS change from 0195; range A2&03; excessive elapsed DC; old-pressure-limit 008E.2; calibrated exact time/origin case |
| 91 | Insufficient previous shift age 0188; insufficient range stability A1; speed change from 0187; reaction 0098.4; special ratio/short window/long origin conditions |
| 92 | Reverse 009C.5 and transmission hot 0087.1 |

Every test's calibration address is in B4B2's ROM branch map. These flags
are inputs to BA65 and F64E status 0131, not direct proof of mechanical shift time.

## Adaptive cells and checksum

Three 17-byte banks start 02F8,0309,031A. Their raw values are biased 128;
032B is a modulo 256 checksum adjusted atomically whenever a byte changes.
BC65 contains their pointers. B91D selects gear/pattern context and reads
`L1(B2,bank)-128` into 0148 and coordinate`(B2+8)>>4`into 0149. An ongoing
qualified upshift can retain the old 0148 rather than reselect it. Negative
offsets remain signed; pressure later uses arithmetic>>3.

BA65 records measured DC=u8(DB-DA)in 0136..38 and signed-saturates
desired time minus measured time into DD and 0139..3B. Desired curves are BC41/47
normal versus cold  BARO hysteresis 93.1,or BC4D/53 performance;0114 overrides
the desired time. With 68A8.1, short mean 019C can choose a special step.
Otherwise long origin/TPS/temperature gates choose a long-shift step, negative
DD a short-shift step, or the BC3B per-gear 17-entry lookup at clamp(DD+8,0,16).
Store selected step E1 with its 93 classification. Learning is admitted by the
long origin branch, or any 93&38 with all 90/91/92 zero. Set 93.0 when admitted.

For offsets j=0..4 about 0149-2, skip indices<0 or>16. Each step is the
rounded magnitude of`(E1-128)*ROM[6A16+j]`, with sign restored. Existing
cell raw value supplies low-bit phase DE=`((u8(cell-128) xor09)&07)`.
DF/E0 headroom can cap the negative/positive step; zero headroom forces 0.
The literal negative cap is`u8(-8*DF+DE-5)`with its borrow test, positive
cap`u8(8*E0+DE)`. Add the step with signed saturation, then constrain it using
the BC6B/BC71 per-gear TPS curves about 128. Only 0113=0 and 0086.3 set commit:
write the biased new cell and checksum 032B=`u8(oldchecksum+oldcell-newcell)`
inside SEI/CLI. Five neighbors can be updated; this is not one global trim.

B99F consumes 011A.7 and restores 17 bytes per bank from 6A81/6A92/6AA3,
adjusting 032B per byte. B9EE consumes 011A.6 and writes80 to all 51 cells,
likewise adjusting the checksum. Scheduler order is B9EE then B99F,so restore wins
when both are requested. BA38 counts an eligible 93 event at RAM032C/033D
(BA5F words)plus 0149; its 93.6 latch prevents repeated counts for the same
93.5 classification. These count bytes are separate from learned bank cells.

## Pressure command B587 and current reference BE5C

Nonzero service 0111 directly becomes pressure E2. Normal calculation preserves
this order; signed offsets and late limits cannot be commuted:

| Stage | Source and exact behavior |
|---|---|
| Base | L2(TPSB2,u8(2*D7),pointer B961+patternbits 06). Reverse A2.5 uses speed 0. Carry from doubling speed selects B967's pointer family without replacing the wrapped coordinate |
| Shift correction | Gear context is D9-1, or D9 during downshift snapshot 83.4. A nonzero 0115..17 supplies a signed correction; otherwise B96D selects normal/performance/manual curves and subtracts 128. Add with SS8 |
| Adaptive correction | Read 0148 through B91D, arithmetic-shift it right 3, then SS8-add |
| Temperature/TPS surface | B991 selects a surface by gear. Temperature coordinate ishi(B5*160). TPS coordinate is 0 at/below 5F28,48 at/above 5F2B, otherwise piecewise interpolation across 5F28..2B. Subtract 128 from the surface result and SS8-add |
| Shift shape | SS8-add BCC6's signed high byte 013E, then apply BC77's temporary reduction |
| Downshift correction | Snapshot 83.4 selects B97F's normal/performance/manual curve using F4A4 at speed D7. Subtract 128 and SS8-add |
| Environment | B88D applies the qualified kickdown/coolant 5F16 addition, PE5F30 curve, zero floor, normal-knock reduction outside gear 3, then MAT5F41 about 128 with a 0..127 clamp |
| BARO factor | Read B999's gear curve at TPS; pass it through D969 using high AC. Round the word by+128 before taking the high multiplier. Multiply pressure and double; N/V overflow clamps 127. Save 0142 |
| Speed floor | Unless slip hold E8 is active, range/fault/gear selects 5F85/96/A7 at D7. Save the floor 0143; it can raise pressure and set 008E.2. Save slip EB into EF and pressure into 0145 |
| Engagement shaping | Range entry, speed 5F11/12 and 008E bits 02/10/20 control 0140 deadband,0141 hold,0146 offset and 0144 candidate. Use 5FB8/6043 with rounded 4*C2 and capped temperature, then 60CE at TPS/speed<=32. Hold additions 5F0E/10 wrap as bytes; signed comparison and deadband select 0144 or 0145 |
| Switch correction | Input 009C.1 subtracts 5F21[D9], with signed saturation and a zero floor |
| Final limit | Update signed headrooms DF/E0. Fault 0098.3 or E664 reaction 0098.5 forces C5F2C; otherwise limit the candidate to C5F2C. SS8-add 0112 and floor 0 into E2 |

BC77 selects reduction 0199 and timer 0198 from 5F06..0B using ratio F9 and
upshift bits83&03. At the BEQ following PULA, flags still come from the
**timer store**: timer 0 skips the reduction even when restored pressure A is
nonzero. BCC6's signed word 013E has an up-event seed, per-gear ratio/delay/
duration curves BE37..BE55 and separate 3-4 time branches. Its rate update is
`SS16(old013E+8*(lookup-128))`. Return to a steady shape uses 6754 plus
17*(D9-1), with fraction 0. “Torque signal pressure” is an inherited label;
no new physical pressure scale is inferred here.

Headroom is accumulated during observation:
`DF=min_signed(DF,candidate)` and
`E0=min_signed(E0,SS8(C5F2C-candidate))`. These limits constrain later
adaptive-cell steps, so their state age matters.

BE5C turns pressure E2 into current reference 014D. Fault 0099.3 forces 0.
Otherwise the 70A1 curve at`sat8(3*B5)` provides change hysteresis around
previous pressure 0147. Two comparisons around that old pressure and flag
008E.6 select surface 6E59 or 6F7D. Coordinates are A=B5 and
`B=sat8(2*E2+hi(170*E2))`. Save the lookup into 014D and E2 into 0147.
The reference is calculated after the fast task's current sample, so they
are not guaranteed to describe the same admission.

## Fast force-current feedback and output

7B6D selects ADC7 and waits for ready without a local timeout. Average four
samples 3031..3034 with nearest-quarter rounding into 014E; obtain TPS/MAP/O2
through F245. After CLI, call 7C13 and write 3068=`0600|014C`. This runs even
on busy timer reentry; the ordinary slower controller tasks do not.

With 004C.5 clear, zero 0150,014C and 014F. Otherwise:

```text
old_error = s8(014F)
e = SS8(min(014D,57)-014E)
if e in {-1,+1}: e=0
014F = e
delta = SS16(e*0153-old_error*0154)
increment = floor((delta+2)/4)
0150 = clamp(old0150+increment,0,0E00)
014C = rounded high byte of Q(0150,0E00), capped255 on round overflow
```

The two ASR/ROR pairs and carry addition implement the stated signed
quarter rounding. These multipliers update one accumulator; they do not
produce a separately stored integral and proportional output sum.

This calculation is unmasked and runs before the scheduler's busy test.
The [complete busy-handler ordering witness](FACTORY_INTERRUPT_ADMISSION_AND_CURRENT_OUTPUT.md)
shows a nestedTOC3 entry between the0150 read and store can lose an accumulator
update. Reentry after that store can preserve0150 while the interrupted
calculation later publishes an older014C and3068 command. Treating the formula
as atomic, or comparing only its final accumulator, omits these conditional
instruction-order effects. Actual timer-arrival feasibility remains open.

With accumulator 0150=0E00 and neither 008E.7 nor 0086.0 set, count FC until
new FC>C6E54. Then compare battery A7 against
`u8(C6E55+R8(B5,u8(C6E56-C6E55)))`: below it sets 0086.0; otherwise set
008E.7. Clear FC on either decision. With neither flag and accumulator below
0E00, clear FC. Recovery of 0086.0 requires battery strictly above the analogous
6E57/58 threshold until new FC>C6E54; then clear FC and 0086.0. Other recovery
failures retain FC. Fault 008E.7 has a separate explicit clear.

C514 sets current-enable shadow 004C.5 unless 0099.3, live 001C.1/001D.7,
0086.0 or 008E.7 inhibits it. Raw service 039A.6 selects 039B.6 instead,
without a 003B test at that particular selector. F411 later latches 004C to
3062: the current calculation can see a changed shadow before that latch.

## Electronic TCC qualification C6BB

Clear word 008C/008D and build the inhibit reasons below. Names describe
software inputs, not an independently measured transmission state.

| Bit | Qualifying inhibit |
|---|---|
| 8C.0 | 6AB4.3, any range A2&03, and transmission-hot 0087.1 clear |
| 8C.1 | 6AB4.5 and temperature below 6AB8 entering/6AB9 staying 008B.0 |
| 8C.2 | 6AB4.6 and coolant A9 below 6AB6/6AB7 |
| 8C.3 | Debounced brake 009C.0 |
| 8C.4 | 6AB4.1 and TPS delay 018D nonzero; an applying state can latch 008B.5 |
| 8C.5 | 6AB4.0 and downshift lock delay 018C nonzero |
| 8C.6 | 6AB5.1, transmission-hot clear, switch 009C.1, gear>0 and speed below the gear 6ABB/6ABE row, selected by 008B.0 |
| 8C.7 | 6AB5.0 and negative-slip hysteresis 0089.7 |
| 8D.0 | 6AB5.4 and upshift delay 0124 nonzero |
| 8D.1 | 6AB5.2 and one-shot 008B.3; consume that one-shot |
| 8D.2 | 6AB5.2, reaction E674 and temperature below 6AC2/6AC3;0089.2 holds comparison hysteresis |
| 8D.3 | 6AB5.2, fault 0099.2 and gear not 3 |
| 8D.4/.5 | 6AB5.5/.6 and range A2.2/.3 |

The brake owner 7D21 runs in the common fast group. It compares input 004D.1
with the inverse of stored 009C.0. Agreement clears FB; disagreement counts
FB until its old value>=5D06, then replaces 009C.0 with inverse 004D.1.
This input is distinct from 009C.1, the separately decoded 004D.0 switch.

Compute upper word 0129 from 6D5E and lower 012B from 6D6F using
`sat8(2*E2)`. Service 010A in 1..100 writes 0126=652*selector and sets 008A
bits 14, then returns. Values 101..200 force an apply request; values>200
force release. Fault 0099.3 zeros the command and clears requests. Normal
control clears 008A bits 14 after absolute service expires. The special
brake/downshift/fault case can force apply for range A2.2 with gear 3.
Any remaining inhibit clears 008B bits 06. TPS-rise hold 018E forces release.

MAP must reach 6AEC with 0089.6 clear, or 6AED with it set. Bypass that MAP
test only when **both** live MAP bits 18&30 and both corresponding reaction
mask bits are present. These are two all-bit tests, not either-fault tests.

Select C2D6 while releasing or C31A while applying, adding 22 for kickdown.
Kickdown reads the first scalar; otherwise evaluate L1 at TPS. Save the
first knot 0128. Apply cold gain C3E6/C3F8 and floor the result at 0128.
Speed D7>=threshold clears 008B.1 and sets 008B.2 (apply); lower speed sets
.1 and clears.2 (release). No valid descriptor clears both requests.

## TCC transition preparation BEBC/BF62

BF62 increments word ages 011B/011D and bytes 012D/012E without storing a
wrapped 0. When neither applying nor releasing, similarly increment off-age
0125. At 011D>=word 6AE5, clear 011D and reduce word 0121 byword 6AE9 with
zero floor; then enforce minimumword 6AE1. Bit 008B.5 has its own 0123 timeout
6AEB. Shift event 0083.3 reloads 018C from 6AD2[D9]; event 0083.0 reloads
0124 from 6AD5[D9-1]. Nonzero delay bytes decrement before possible reload.

BEBC decrements 018E and compares current TPSB2 against previous B3, then
updates B3. A positive change>=6ACF reloads 018E=6AD0. A negative wrapped
change<=6ACE reloads 018D=6AD1; other paths decrement nonzero 018D.
Signed slip EB<word 6AC4 sets 0089.7; EB>word 6AC6 clears it. Speed hysteresis
0089.3 uses 6AC8/6AC9 and selects TPS thresholds 6ACA/6ACB below the window,
6ACC/6ACD above it, according to apply/release context.

With 6AB4.2 and TPS below the selected value, set 008B.3. If applying 0089.6
or the 008B.5 hold is active and arming 008B.4 is set, set 008B.7 and clear
.4. If word 011B<=word 6AE3, increase 0121 byword 6AE7 with FFFF saturation.
Clear 011B. These separate ages and flags prepare the later command task;
none is a universal TCC-enable bit.

## TCC base curve C271

InputX is the curve; Y points to an override pair. A nonzero byte[Y]
provides D=byte*257 directly. Otherwise:

```text
g = L1(sat8(2*E2),6E2A)
v = L1(TPSB2,X)
b = byte[X]
p = 2*g*(v-b)+(b<<8)             # extended signed intermediate
```

Clamp negativep to 0 andp>65535 to FFFF. For an in-range value, addhi(p),
plus one only whenlo(p)+hi(p) carries; cap a final overflow at FFFF. Then
apply signed byte[Y+1] to the high byte around 128. Signed overflow replaces
**the entire word** with 0000 or FFFF; an in-range adjustment preserves the
fraction. Restore the 128 bias and save F1. The extended sign 0192 and byte
carry behavior are covered by execution cases, including both saturation
ends and the direct override. This is not one floating-point blend.

## TCC apply and release C00B

Absolute service 008A.4 returns unchanged. Otherwise apply request 008B.2
has priority over release 008B.1. Neither request clears 011F,0089 bits 70,
008A.6 and command word 0126.

Apply may be held while 008B.7 is set, transmission-hot 0087.1 is clear and
word 011F<0121. Set 008B.6 and increment 011F with saturation. Clear the
transition state/command while retaining that counter. Once hold ends,
clear 008B.7/.6 and 011F.

New apply sets 008B.4 and 0089.6, clears 0089.4, zeroes 0125/012D/012E and
seeds E7=C6ADD. Before convergence 0089.5:

1. Select base C35E using 7F/D9, falling back to 6DB3. C271 uses override
   pair 010B/010C.
2. Select increment C3A2, falling back to 6E08, evaluated at TPS;0110
   overrides that rate. Form D=8*rate; add its high byte into its low byte.
   Add command 0126's low byte. On low carry, INCB once, then ADCA the old
   command high byte with that carry. Cap a high carry at FFFF.
3. Enforce floor F1 and save candidate F3. Slip ED>word 6AD9 sets E7=1;
   ED<word 6ADB decrements E7, and a new 0 converges. Candidate>=upper 0129
   also converges. Set 0089.5, save age E6, run C271 at 6E3B with override
   pair 010F/0110, clear F6/012D and seed EA/F5 from that record.

Converged apply uses 6E3B/C271 and its rate/slip adjustments. EA counts down;
on expiration addbyte[X+12] to E9 withSS8 and reload[X+11]. F5 counts down;
when ED>word[X+13], addbyte[X+15] to E9 and reload[X+16]. F6 increments and
resets 0 when ED<word[X+17]. Candidate construction loads **A=F1 high,B=F6**,
halves D, applies E9 around 128 with signed saturation, doubles, then restores
**B=F2**. Doubling carry caps FFFF. Certain new-shift events instead write
upper 0129 directly. F6 participates in the arithmetic; it is not unused.

New release sets 0089.4, clears 0089 bits 60 and 008A.6, and zeroes 011F/012D/
012E. Select base C380 with fallback 6CC5 and override 010C/010D. Rate uses
0110 if nonzero, otherwise 6ADE during TPS-rise hold 018E, otherwise C3C4
with fallback 6D1A at TPS. Multiply by 8 and add its high byte into the low
byte; subtract the old command low byte. On borrow DECB once, then SBCA
the old command high byte. A nonnegative result completes release and
clears state/command. Otherwise NEG16 produces the decreasing command;
cap it to F1 and enforce lower 012B. Slip/age gates 6ADF,6D3C,6D4D can end
release early;008A.6 latches one phase and E5 captures its age.

The common tail clamps the candidate between 012B/0129, saves 0126 and
forms E9 from command-F1 through the literal RORA/ADCA/V correction.
C514 sets 008B.0 only when command>012B and 008A.2, then writes
306A=`7F00|hi(0126)`. It does not send the whole software command word.

## Solenoids, nonelectronic TCC and shift lamp

C514 replaces shadow 004C's low 2 bits with B319[D9]=01,00,02,03. This
proves the software pattern; physical solenoid polarity remains separate.
Shared IAC bits are preserved. F411 later latches 004C to 3062. With 400F.6,
C514 skips 306A; CCC1 instead writes 7FFF/7F00 from 0089.5.

ADAA runs its nonelectronic TCC decision only with 400F.6. The 5168 load
curve uses`u8(2*hi(205*VSS0284))`. With 0089.5 set, subtract 515B with
zero floor and select the second 5160 threshold. TPS below the load
threshold reloads 0853=515F and clears 0089.5. Otherwise VSS>=selected 5160
sets 0089.5 immediately. Below that upper window require coolant>=515A,
absolute TPS change from 0854<=515C falling/515D rising, and VSS strictly
greater than the selected 5164..67 pair (004D.0 and 0089.5 select it).

Use 517E while unlocked or 5171 while locked. Curve coordinate is wrapped
4*hi(205*VSS), with offset 64. Curve>=TPS andRPM0063>=selected 5162/63
qualify the 0853 countdown; zero locks. Failure reloads 515E and unlocks.
Save TPS into 0854 after the decision. These hysteresis windows and delays
are distinct from the electronic TCC pressure-command task.

ACA7's shift lamp requires 400E.2. A stopped diagnostic mode or local service
can force 0053.2. Normal operation samples the 3FE0 change into 0849 and saves
0847; require coolant>511F,TPS>=5120/21,VSS>=5,RPM>=40. RPM>5122 turns
the lamp on immediately. Otherwise classify 0845 from the low quotient of
`IDIV(Q(15,005F),u16(0849+(0849>>1)))`, using 5113's thresholds; save the
low quotient into 084B. Require RPM above the per-class limit. Compare the
doubled rounded TPS gain against 5125/513B curves corrected by BARO5151.
A passing decision counts down 0846; zero turns on the lamp. Failure reloads
0846 from 5123/24 and turns it off. CCC1 writes 306C=1FFF/1F00 from 0053.2
when 400E.2; the governor is a separate 306C owner.

## Transmission spark requests

C4E5 orders B0E4 TPS, D9B7 mode, DA6F range spark, DAE2 shift spark and
C40A limiting. D9B7 starts A4.0 at a qualifying range entry below 70D3, with
70D4.0 controlling its additional branch. High word 01AC>70B8 orTPS>70BA
moves it to A4.1. When turbine C2<word 70BB orage 015D>70BD, clear A4 bits 03.
Leaving A4.1 sets A4.4 and 015E=70D2. Separate A4.2 range hysteresis uses
70BE..C5 and requires A2&50 clear.

DA6F's priority is fault 0099.4→0; active shift A4.3→retain; A4.0→55F5
surface; A4.1→55F3; A4.4→55F3 scaled byQ(015E<<8,70D2<<8);
A4.2→55F4; otherwise 0. During decay, A4.2 floors the result at 55F4.
Decrement 015E and clear A4.4 on expiry or floor. Save 015A.

DAE2 will not start a shift shape while any A4&17 is set. Require range A2&70
clear and fault 0099.4 clear. Up-event 83.0 sets A4.3 and zeroes 015B/C;
down-event 83.3 ends it. The DBE3 per-gear surface supplies maximum 015B.
Gears 1/2 use ratio F9 high and DBEB's four pointer pairs for rising/falling
ratio fractions; gears 0/3 use age 015C and 70CE..D1. Form the integer
fraction withIDIV, apply it to maximum 015B with+128 rounding, and use A4.7
for the rise/fall saturated endpoints. Exit clears A4.3 and 015A.

C40A uses nonzero 0119 to overwrite 015A directly. Otherwise, A4.3 and
coolant A9 outside 70B2..B3 reduce 015A using 70B7 and a fraction of the
coolant boundary. Any A4&17 permits a second 70B4..B5/70B6 reduction.
Each stage usesQ and two rounded byte products. These producers close the
previously open 015A/A4 engine-spark interface; physical retard units remain
with the existing engine calibration evidence.

## Closure and interfaces

This resident software scope includes optional/manual/nonelectronic paths,
table priorities, retained learning, current feedback, faults, local service
and hardware command owners. The full SCI/factory command machines,
low-memory extensions, global pointer/reachability integration and physical
capture/driver/mechanical behavior remain separate scopes.
