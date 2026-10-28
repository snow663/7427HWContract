# Factory diagnostics: detection, retention and reporting

This is a ROM-backed contract for the resident BMHM diagnostic monitors,
fault-reaction masks, retained log, flash reporting, clear paths and local
service selectors. It uses stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
CPU4000..FFFF equals full-file offsets. CPU0000 is RAM. Stock values do not
replace the truck's separately recorded 2.bin values.

The evidence includes actual opcodes/branches, all 72 bit-to-flash-code
mappings, clear masks and reaction descriptors. See
[factory_diagnostic_bits.csv](../../maps/structure/factory_diagnostic_bits.csv),
[factory_dte_branches.csv](../../maps/structure/factory_dte_branches.csv),
and [the closure ledger](FACTORY_DIAGNOSTICS_TRANSMISSION_EMISSIONS_CLOSURE.md).
The flash table gives an identity, not proof that each of its 72 positions
has an implemented monitor. No missing monitor is invented from its name.

## Three different kinds of fault state

For bank indexj=0..8:

| State | Address | Owner/effect |
|---|---|---|
| Live fault byte Dj | 0016+j | Local monitors and boot/hardware summary paths |
| Candidate bytePj | 0056+j | Central persistence/intersection at E132 |
| Retained byteHj | 000B+j | Qualified log union, explicit clear, age and boot validation |
| Log mask Ej | 5B00+j | Candidate admission and flash enumeration |
| Lamp maskLj | 5B09+j | Selects faults that request normal lamp latch 0071.0 |
| Reaction enableRj | 5B2B+j | Transmission fault reaction, independently of Ej |
| Reaction alternate Aj | 5B34+j | Changes which reaction filters see Dj |

Bits are scanned 80,40,20,10,08,04,02,01 in each byte. The first bank's codes
are 13,14,15,16,17,18,19,21. The next bank begins 22. The exact remaining
mapping is generated from ROM FE57..FE9E, rather than assuming eight
consecutive decimal code numbers per byte. Code 12 is the FE56 opening
report, not a fault bit. Live 16.4 is code 16; live 17.5 is code 24. The latter
has both an electronic-transmission monitor and a separate manual-option
path at DE07. Naming both merely “VSS fault” loses that distinction.

Most byte/word timers in 0100..029C and 0800..08FF start in unconditional
boot-cleared RAM.000B..0035 and 029D..034D are conditionally retained.
Setting a live fault need not immediately store a code, light the lamp,
or clear an already retained code when the condition disappears.

## Boot and retained-state rules

718A obtains the ADC inputs. Factory entry requires 082F in[40,100), TPSA6
and coolant ADC082D>=252, transmission-temperature ADCA5<=5. It sets 0044.0
and bypasses the ordinary validation path to 7459.

Otherwise 303F must equal 0B. Failure sets 003A.2. With that match, F2AA
sums bytes 4008..FFFF modulo 65536 intoY, servicing the watchdog as the
address wraps. A4008=31 image is accepted with matching word 4006;4008=AA
also bypasses the mismatch failure. Other failures set 003A.1. The common
failure path sets 0005.4, removes 3FFC bit 0008, sets live 001A.5 and retained
000F.5 (code 51), refreshes checksum 0015 and waits for the sampled diagnostic
ADC082F<100. This is separate from the later normal retained checksum.

F326 returns `u8(-sum(RAM000B..0014))`. At 720C compare it to 0015. Failure
clears 0000..000A,000B..0035 and 029D..034D; seedsTPS zero 02F6=C5B24:80,
resets BLM through F280 and sets 0046.6. Acceptance keeps those areas.
The checksum covers retained DTC bytes and age 0014, not every retained cell.

723F independently checks the 52 bytes 02F8..032B. It accumulates modulo 256
while walking backwards, and records whether **any intermediate cumulative
sum** was nonzero. Accept only final sum 0 with that observation set. An
all-zero block is rejected. Rejection fills all 52 bytes with 80 and sets 003A.6.
The three 17-byte transmission adaptive banks and checksum 032B use this
second validation scheme; they are not covered by 0015.

Boot 7272..7356 decrements each nonzero retained recovery counter only when
it is below its own calibration threshold. Counters 001F..0031 use thresholds
5B1E,21,42,52,58,5E,62,75,76,7A,8C,90,A3,A5,A7,A9,AB,C0,CA respectively.
Counter 0031 with live 001E.2 may then receive+2 and clear that live bit when
below 5BCA. Boot clears 0019 bits 06; manual 400F.7 also clears 0017.5.
At 7378,0032/33/34 values reaching 5BC7/C8/C9 receive B=0. CLRB726E
establishes that value on the shared boot path; the intervening recovery
bookkeeping preserves it. The stores are STAB, rather than immediate clears.

## Diagnostic admission and cadence

DC89 runs in slot D after AIR output and MAT. It sets 006F.7 only when
phase&F0=0; otherwise clears it. Thus many “one second” timer increments
actually mean once per 160-phase cycle, nominal 999.756 ms, while local
decision paths may execute every 16 ticks. Diagnostic timing is counted in
admissions, not wall time guaranteed under reentry or special scheduling.

0050.4 comes from diagnostic ADC CB15. DC89 mirrors it to 0071.7 and handles
diagnostic lamp cycling. Stopped operation skips most running monitors and
clears 0228,0219 and word 021A before entering reporting. Ordinary 0050.4 clear
also clears 003C/0216. Special 001A.5 with that ordinary switch state takes the
lamp-request exit early. The flash path is not simply “run every monitor,
then print all bits.”

Most transmission-family monitors begin `BRSET 003B,#04,return`, which
freezes their local timers and flags in that mode. A disabled individual
5B xx mask usually clears its timer but retains the old live fault. Some
central engine monitors instead clear their live bit on each admission.
Those differences are recorded below.

## Engine and shared monitors

| Routine / live bit | Exact qualification and timer behavior |
|---|---|
| DD40 /16.7 code 13 | Clears live bit first.006F&24 must be 0. Run-time qualification 0071.6 latches when low byte(word 00FD>>1)>=4E32. DFCO0046.3 counts 015F toward 4E33 and clears O2 timer 021C; outside DFCO decay 015F and require<4E34. RawO2 must be>4E35 and<=4E36. Old 021C>4E38 sets fault before current TPS/coolant update. On phase high nibble 0,00FE.0 clear,coolant>4E39, TPS>4E37 increments 021C, otherwise decrements it when nonzero. Earlier failed gates clear 021C |
| DDBA /16.4 code 16 | Clears live first. Any 006F&48 orVSS>4E3A clears 0817. Otherwise old 0817>4E3F sets fault before current qualification. RequireMAP01C6<4E3D,coolant>4E3E,RPM0062 in(4E3B,4E3C],TPS<4E40. Eligible 006F.7 increments 0817; failure clears it |
| DBFB /17.6,.4 codes 23/25 | Sample mux 4 ADC, invert into 0230. Tests start only after run timer>word 4E45. For code 23, if 5B01.6 enabled clear live first;0230<4E41 and old 021D>4E42 sets, else VSS<=4E47 increments 021D; other paths clear timer. Code 25, if 5B01.4 enabled clears live;0230>=4E49 and old 021E>4E4A sets, elseVSS>4E47 increments; other paths clear timer. Failed mask still clears its timer, retaining live. Convert via FE45 to 0855; if either live 17&50,022F uses 4E48 default, else 0855 |
| DE07 /17.5 code 24 | Only manual 400F.7 and 5B01.5. Nonzero word 0849 clears live and 081C. Otherwise old 081C>4E43 sets live; below that, VSS>4E44 increments 081C, with no low-speed clear |
| DE3A /18.7 code 31 | Clears live first. With 400F.0, old 006F.4 or high 0288>=4E4B sets live and 006F.4. The latter is sticky until explicit clear |
| DFCA /18.5 code 33 | Clear live and 006F.6 in candidate B first. Any 006F&24 clears 0228. Letlimit=min(4E61,hi 02F4). Require ADC082E>limit. Old 0228>4E62 sets live and 006F.6 before TPS/RPM qualification; otherwiseTPS<4E60 andRPM0061>=4E63 increment, failed gate clears 0228 |
| A4B3 /18.4 code 34 | Ordinary even conversion. Clear live and 006F.3 first.006F.2 or rawMAP082E>=4E64 clears 0229. Otherwise old 0229>4E66 sets live and 006F.3 before current gates. Else RPM0061<4E65 orTPS>4E67 increments 0229; failed gate clears it |
| E00D /0004.7 EST event | Skip for 0044.2,0050.3,phase.4 or 004F.6 clear. Sample 3FCA and compare old 0205. RPM0061>4E70 and unchanged sample increments 022C until old>4E73, then sets 0004.7. Other admitted conditions write 022C=0. Save sample 0205. ABCB connects this local event to live code 42 below |
| E041 /19.3 code 44 | Clear live. F ilteredO2 high 01D0<4E78. Without 0072.6, timer 0219>4E79 sets stage 0072.6 and clears timer; otherwise requireclosed-loop and 0071.2 clear to count. With stage set, old 0219>4E7A sets live; otherwise 00FE.0 must be clear to continue. Count only 006F.7. Failed O2/gates clear stage and timer |
| E084 /19.2 code 45 | Clear live only if 400E.5 clear. RequireO2 high>4E7D. Compare old word 021A toword 4E7E, orword 4E80 after high-MAT observation 0044.5.022F>4E7C sets that observation. Old timer>limitsets live. Otherwise requireclosed-loop,0071.2 clear, then literal TPS path: TPS>4E82 qualifies directly; else TPS>=4E83 fails. Count only 006F.7; failing gates zero 021A |
| E0F6 /19.1 code 46 | If 5B03.1,A7>=90 andVATS003D.1 clear,old 0856>4E84 sets live. Else increment 0856, suppress store if it wraps 0. No local clear of fault/timer on failed admission |
| E286 /1A.2 code 54 | If 5B04.2 enabled clear live.0072.0 sets live immediately. Else A7>=4E88 required. With 0072.1 set, run fuel 004F.4 and pump-feedback 0055<4E87 sets live. Without stage, increment 022A; new>4E85 sets 0072.0/live, else feedback>=4E86 sets 0072.1. Failed battery admission retains timer/stages |

AE5C VATS samples TIC2 word 3012 changes into 0851. It sets 003D.1 when option
400D.6 is absent, or a nonzero new delta lies in[word 518D,word 518B]. An
already set pass bit bypasses further tests. Its physical frequency scaling
is an interface, not proved by the register name.

785A counts missing CAM observations in 084E with saturation 255 when 5B03.6
is enabled; new/current count>4E6F sets 0019.6(code 41). The REF paths call
it at 75D1/774C and clear 084E on their observed-CAM routes 75FB/7733.
Boot and explicit clears are the other lifetime boundaries; a successful
sample does not locally clear code 41. CEBB's code 43 knock-input ADC window
and its 0207 timer are specified in the upstream spark contract. F25F's ADC
poll timeout and D14E's separate feedback timeout set 001A.1(code 55) and
003A.0; a subsequent admitted conversion clears 001A.1 before polling again.

### Post-handoff EST monitor ABCB

This runs after the integer spark hardware writes and closes the earlier
ABCB monitor boundary. With 0044.3 clear, skip to the ordinary board-request
tail. With it set but no fresh-conversion 0050.2, return through ACA3. With
a fresh conversion, sample 3FCA into D/X. If 5B03.5 is disabled, accept the
monitor immediately: set 004F.6,clear 022C,save 0205,clear 0044.3 andcopy
3FEC to 3FE4. An already enabled 004F.6 takes the clear/copy tail too.

Otherwise an existing 0044.7 lock sets live 0019.5(code 42). For a new test,
compute wrapped 3FCA-old 0205. High byte 0 andlow<=4E71 is a good event:
first good sets 0044.6 and saves sample; a second consecutive good accepts
the monitor as above. A bad event compares old 022C to 4E72; old>limitsets
0044.7 andlivecode 42. Otherwise increment 022C,clearfirst-good 0044.6 and
save 0205. The bad/first-good paths return without the acceptance copy.

The tail sets 004B.4. If 0004.7 setand 0044.2 clear, set livecode 42 andclear
004B.4. Otherwise service 003B.4 with 0391.3 sets 0044.2 andclears 004B.4.
Finally clear 0050.2. These are exact software monitor/output transitions;
the ASIC meaning of 3FCA/3FEC/3FE4 remains a hardware interface.

O2 lean/rich state can invoke F28E BLM reset when 400C.1 and either 0019.2
or 0072.6. Readiness/closed-loop admission at E477 onward remains in
[FACTORY_CLOSED_LOOP_AND_LEARNING.md](FACTORY_CLOSED_LOOP_AND_LEARNING.md).
The IAC local code 35 paths remain in
[FACTORY_IAC_LEARNING_AND_OUTPUT.md](FACTORY_IAC_LEARNING_AND_OUTPUT.md).

## EGR diagnostic state machine DE56..DFCA

5B02.6 controls code 32. Enabled entry clears live 0018.6; disabled or
0070.3 completed paths bypass the response test, retaining phase/timers.
Linear 400D.1 with 0070.0 also bypasses response qualification and mirrors fault.
Normal response test requires closed loop and no DFCO. Nonzero 021F decrements
only 006F.7 and clears stabilization/response timers and active 0070.2.

With cycle timer 0 require desired 01AE>=4E51; vacuum in(4E4D,4E4E];
TPS in(4E4F,4E50]; absolute TPS01D9-01DE<=4E54; VSS>=4E57.
Failure clears 0220/0221 and active 0070.2, retaining failure count 0223.
006E.0 reset is consumed and also clears this test phase. Before active
0070.2, requireabs(INT020F-128)<=48F7. Old 0220<=4E52 increments it;
old>limitsets active 0070.2,savesINT0222 and clears 0220. Active 0070.2 causes
the EGR duty controller to close the valve for this response test.

During active test, an INT increase>=4E56 passes (a borrow does not).
Until old 0221>=4E55, increment that timer. Timeout increments 0223; reaching
4E53 sets 0070.0 and decrements the candidate once before storing. Pass
decrements 0223; if the new/nonzero value remains, store it and rearm. Zero
clears 0070.0 and, with 400D.7,sets completed 0070.3. Rearm writes 021F=C4E4C,
clears 0220/0221 and 0070.2.0070.0 mirrors into live 0018.6.

The additional linear-position branch requires 400D.1 and 5B02.6. Existing
0070.0 sets live immediately. Raw 01B4<4E59 counts 0227 until old>=4E5F,
then sets 0072.5 and 0070.0. Otherwise 0227 clears. With completed 0070.3,
word 0225 increments towardword 4E5D; reaching it clears 0072.5 and resumes
position testing. No reset of 0225 is invented on that path. Position testing
requiresdesired 01AE<=4E5C anderror 01BA>4E5A;0224 increments until old>=4E5B.
Then set 0072.5. If 0070.3 was already set, also set 0070.0/live; otherwise
set 0070.3 and clear 0224. Nonqualifying position clears 0224.

## Transmission monitor families

For the following table, each routine has 003B.2 freeze and its own log-enable
mask unless stated otherwise. `t` is the listed timer. Common qualified
counting increments first, compares the **new** t against the byte threshold,
sets fault on>=, then clears t. Failed qualification clears t. This differs
from the engine monitors' old-timer comparisons.

| Entry / code / live | Test and important extra gates | Timer / threshold |
|---|---|---|
| E75F /14 /16.6 | ADC082D<5B13 sets;>=clears after qualification | 0160 /5B14 |
| E793 /15 /16.5 | ADC082D>5B15 sets;<=clears | 0161 /5B16 |
| E7C7 /21 /16.0 | TPSA6>5B1C | 0162 /5B1D |
| E808 /22 /17.7 | TPSA6<5B1F | 0163 /5B20 |
| E847 /24 /17.5 | NoMAP18&30,TPSfault 16.0/17.7;MAP01C0 in[5B45,5B46],TPSB2 in[5B47,5B48],word D1<word 5B3D, no 1C.0/17.1,word C2>word 5B3F,range A2&50=0 | 0164 /5B41 |
| E8C8 /28 /17.1 | Illegal decoded range A2.7 | 0165 /5B51 |
| EA40 /52 /1A.4 | Battery A7>5B63; wordtimer | 0169 /word 5B64 |
| EA7C /53 /1A.3 | Literal battery A7>5B66, despite misleading names | 016B /5B67 |
| EAB1 /58 /1B.6 | Transmission ADC A5<5B68 sets,>=clears | 016C /5B69 |
| EAE4 /59 /1B.5 | Transmission ADC A5>5B6B sets,<=clears | 016D /5B6C |
| EB19 /63 /1B.2 | BARO ADC02F3>5B6D sets,<=clears | 016E /5B6E |
| EB4D /64 /1B.1 | BARO ADC02F3<5B71 sets,>=clears | 016F /5B72 |
| EB81 /71 /1C.3 | Engine speedword B7<word 5B81; no 17.1 and A2&52=0. Recovered speed qualifiesclear | 0174 /5B83 |
| EBC0 /72 /1C.2 | N-basedabs(word D5-word CC)>word 5B86(A2&50 clear), elseword 5B88; requires 01AB=0,01AC>=word 5B8A,A1=255,no 17.1 | 0175 /5B8D |
| EC2D /73 /1C.1 | 008E.7 orabs8(014F)>5B8E; no 1D.7 and 0178=0 | 0176 /5B8F |
| EC79 /75 /1D.7 | 01AC>=word 5B9B; battery below temperature interpolation of 5B96/97 entering,5B98/99 staying | 0178 /5B9A |
| ECCC /77 /1D.5 | Pattern 009F.3 illegal request | 0179 /5B9D |
| ECFF /79 /1D.3 | Ifclear,temp B5>=5B9F and 1B.6 clear sets; ifset,temp B5<5B9E qualifiesclear; wordtimer | 017A /word 5BA0 |
| ED3F /81 /1D.2 | 009E.0 set and 009E.5 clear | 017C /5BA2 |
| ED80 /82 /1D.1 | 009E.0 set and 009E.4 clear | 017D /5BA4 |
| EDC1 /83 /1D.0 | 009E.0 set and **both**009E bits 30 set | 017E /5BA6 |

Codes 14/15/58/59/63/64/75 use symmetric time qualification on entry and
recovery. Codes 21/22/28/52/53/77/81/82/83 use first-good-observation flags
94/95/96/97. Where a retained recovery budget is tested, a permitted recovery
adds 2 to that counter and clears live. Already consumed observation flags
prevent repeated recovery in that boot. Hitting the recovery limit retains
the fault even with good input. Code 52 uses 97.0; code 53 uses 95.1; neither
uses a retained budget. Code 77 uses 95.6 without a budget. Exact counter
addresses/limits follow boot's list and the branch inventory.

E847's first 94.2 observation clears an existing eligible code 24 before normal
testing. Later readings use the table's full qualification. Similar first-call
handling exists for codes 39/68/69/85/86/87/89: these are not all symmetric
debouncers. Codes 66/67/70-equivalent reserved entries EB17,EB18,EE5F,EE60
are literal RTS stubs in this image. Their table positions do not supply a
missing implementation.

The remaining converter/ratio/shift monitors have longer admission chains:

- **Code 37 E905:** brake 009C.0 must stay set to test. With speed D7<=5B53,
  latch 94.4,clear 94.5 and 0182. Above it,94.4 is required. Count 0182 in the
  band below 5B54; at/above 5B54 set 94.5 andcount 0183. Require 0182>5B55 and
  0183>5B56, then increment 0166 toward 5B57. Brakeclear permits timed
  recovery usingbudget 0023<5B58, adding 2; clears 94 bits 30. Saturating
  age writes suppress wrapped 0. Some exits retain 0166.
- **Code 38 E99E:** converse brake episode. Brake-set prepares 94.6, clears
  .7 and times recovery 0167/budget 0024<5B5E. Brakeclear with D7>5B59 sets
  94.7 andcounts 0185; in(5B5A,5B59]sets 94.6 andcounts 0184. At D7<=5B5A,
  require 0184>5B5B and 0185>5B5C, then count 0167 toward 5B5D. Episode flags
  reset on both accepted and rejected completion. This is a speed-episode
  test, not one continuous “brake stuck” timer.
- **Code 39 EE02:** first 95.0 observation permits budget 0025<5B62 recovery.
  Thereafter signed word EB>=signed 5B5F, TCC0089.5 set, gear D9 ne 0,3,
  no 1C.3/1C.0/17.1 and any A2&0C. Count 0168 toward 5B61.
- **Code 68 EE61:** absolute slipword ED>word 5B77, gear 3,TCC0089.5 set,
  no 1C.3/1C.0/17.1 and any A2&0F. Count 0172 toward 5B79. Recovery uses
  first 95.2 observation andbudget 0028<5B7A.
- **Code 69 EEBC:** signed word EB is strictly betweenword 5B7D and word 5B7B,
  TPSB2>5B80, noTPSfaults,0089.5 clear, gearnot 0/3, no 1C.3/1C.0/17.1,
  word 01AC>word 5B84,any A2&0C. Count 0173 toward 5B7F. First 95.3
  observation can clear live without a retained recovery-budget test.
- **Code 74 EF2B:** turbineword BD<word 5B91,range A2&50=0,no 17.5/1C.2,
  outputword D3>word 5B93,no 1C.3/17.1,01AC>word 5B84. Count 0177 toward
  5B95; recovered turbine speed also qualifies timedclear.
- **Code 85 EF88:** ratio F9 must lie outside all open intervals
  (5BAF,5BB1),(5BB3,5BB5),(5BB7,5BB9),(5BBB,5BBD),andgearnot 3.
  Require noTPSfaults/1E.4/17.1, B2>5BAC,no 1C.3,01AC>word 5B84,
  no 17.5/1C.2/1C.0,D7>5BAD,any A2&2F. Count 017F toward 5BA8;
  recoveryfirst 96.3 andbudget 002E<5BA9.
- **Code 86 F02F:** gear<2,ratio F9<=word 5BB9; otherwise common code 85
  speed/TPS/input-fault gates,any A2&0F. Count 0180 toward 5BAA;
  recoveryfirst 96.4 andbudget 002F<5BAB.
- **Code 87 F0AD:** gear>=2,ratio F9>=word 5BB3,temperature B5>5BAE;
  same later gates andany A2&0F. Count 0181 toward 5BBF;
  recoveryfirst 96.5 andbudget 0030<5BC0.
- **Code 89 F131:** called after a completed shift observation, not every
  diagnostic slot. First 96.6 permitsbudget 0031<5BCA recovery. Test only if
  saturating 8*adaptive 0148 reaches the signed BC6B curve threshold.
  For gears 1/2/3, measured 0136/37/38 must exceed 5BC4/C5/C6. F1DD
  requires no 1B&60,temperature B5>=5BC1,noTPSfaults,TPSB2>=5BC2,
  no 17.5/1C.2/1C.0,and D7>=5BC3. Increment 0032/33/34; reaching
  5BC7/C8/C9 sets 001E.2 without storing the threshold-reaching counter.

These predicates preserve signed branch conditions and comparison order.
The raw branch map records their timer stores and exceptional early exits.

## Fault reactions used by the transmission

E6BC receives a nine-byte mask ending atX+9 and returns nonzero if any
`Dj & Rj & ~Aj & reaction_mask[j]` is nonzero. It preservesY/B; A/N/Z
describe the result. Wrappers E654,E664,E674,E69C,E6AC,E6E5 select masks
E720,E729,E732,E73B,E744,E756 respectively and update 0098.4/.5/.6,
0099.0/.1/.4. E684 sets 0098.7 for live 001D.7 immediately; otherwise it
only considers E74D mask when 0087.1 set. E62D uses the opposite alternate
polarity: any`Dj & Rj & Aj & maskE717[j]`sets 0098.3.

E5CF sets 0098.0 from TPS code 21/22 filtered byR&~A. E60B sets 0098.1
from 17.5 or 1C.2 with those masks. E6F5 sets 0098.2 from 17.1 or 1C.5.
E5F1 sets 0099.3 when`001A & 5B2F &18`nonzero, or when 0086.7 clear
and word 0100=0. E6E4 is a no-op. Reaction masks are not the log masks;
disabling lamp/logging does not prove the controller ignores a live fault.

## Central log E132 and age DD14

DD14 increments retained age 0014 once after 00FE>=10 usingone-shot 0043.1.
It increments 0014 and decrements 0015, preserving the
checksum. Age>5B12 clears 000B..0013 and 0014,003C and recomputes 0015.
No time-based clearing of all the other retained recovery counters is implied.

When 0043.2 is set, E11A skips the normal log/report tail. Diagnostic 0071.7
calls the flash routine instead; ignitionoff 0044.4 skips normal logging.
Otherwise:

1. If allPj=0, seed eachPj=`Dj & Ej`. A nonzero 022B decrements and exits;
   zero 022B clears lamp latch 0071.0. Seeding does not immediately log.
2. If somePjwas nonzero, replace eachPjwith`Pj & Dj & Ej` and OR the
   survivors into A. This is **intersection with an existing candidate set**;
   newly appearing faults do not enter that set until the next seeding pass.
   Increment 022B modulo 256.
3. Select timer threshold from 4E2E..4E31: baseindex 0/2 according to 0071.0,
   plus 1 when A!=0. If threshold>=new 022B, exit. Otherwise clamp 022B to
   threshold. With A=0 exit; with A!=0 write 022B=C4E30, ORPjintoHj, clearPj,
   clear 0014 and recompute 0015.
4. After that log commit, any`Dj & Lj`sets 0071.0. That latch affects later
   timing and normal lamp behavior; it is not assigned directly on each
   local fault update.

The following lamp tail has an engine-stopped/bad-shutdown delay 004F.1 and
0050.3 override.0071.0 or those exceptional conditions request 0072.7;
otherwise clear 0072.7. F3EE writes active-low 3FFC bit 0008 from 0072.7 in
the ordinary common fast group. The requested lamp state and actual hardware
flush occur at different points in the scheduler.

## Flash reporting E1EC

On entry without 003C.6, initialize 003C.1 repeat state and load FE56+cursor
into two digit bytes 0214/0215. Cursor 0 selects code 12. Set 0218=28,
003C.6 and clear 0071.0. While active, decrement 0218; nonzero retains
the current lamp state. On expiration, alternate four-count lamp-on/off
intervals using 0071.0 and decrement the selected digit. A digit is complete
when its decrement becomes negative;003C.5 switches digits, inserting 8 counts.
After both digits the low 003C bits provide repeated reports.

Then scan retainedHjmasked by Ej, shifting each byte left and testing carry.
0216 increments before indexing FE56+0216, producing the bit/code mapping
in the evidence CSV. Cursor>71 wraps to 0 and clears active 003C.6. The next
entry can restart code 12.0071.0 is copied to 0072.7 at the end. This routine
reports **retained masked faults**, not every current local bit.

## Explicit clear and service lifecycle

F333AND sHj,Dj,Pjwith nine keep masks F377..F37F. It clears 0004.7,
0044.7,0072.0,006F.4,0070.0,counters 001F/20,0817,021C,081C,
then refreshes 0015. F380AND sHj,Dj with F3DB..F3E3 but leavesPjunchanged.
It clears 0094 bits F0 and 008E.7 and the explicitly listed recovery counters
001F..24,26..2D,2F..34 plus 0182..0185; **0025 and 002E are not in its
clear list**. Refresh 0015 afterwards. These routines are masks, not blanket
clears of every live and retained diagnostic state.

F64E runs at the end of the transmission input pipeline and supplies the
local service owners needed by all three contracts. It first packs status
0130/0131. With 0042.1,selector 0399=04 and word 036A=0, set 003B.3;
039A/039B bits 18 select one-based gear 0103 via the solenoid table;
039E.7 admits 039F to TCC010A. Request 039A/039B selectors are masks, not
ordinary calibrated gear inputs. The adaptive selector is the literal
X+7=03A0:bits 40/80 update 011A.6/.7. At F6EF, **03A1 always writes
0111 on this path**; the branch operands preserve that unconditional tail.
When service is active and receive 0042.1 disappears or 036A!=0, clear 0399,
010A,0103,0111,0118 and 003B.3.

Engine-output selector 038E=04 with 0042.0 sets 003B.4.0391.4 rising resets
BLM via F280; general 003B.1 or engine 0391.6 rising invokes F333;003B.0
rising invokes F380.0045 bits 10/80/40 suppress repeated clears. When the
engine service loses receive ownership or 036A expires, clear 003B.4,038E
and 0044.2. These are local payload consumers; full SCI framing/command
authorization and the factory callback remain separate service documentation.

F781 supplies timeout: when 0042&03 nonzero, count 0367 without storing 0;
at>=200 or wrapped 0 clear selectors 038E/0399,0042&03,0045&D0,003B&43,
3FFC.2,SCI302D=26 and words 0360/0362. Separately, active 003B&18 counts
word 0368 toward 51BB then sets word 036A=1. In inactive mode,036A counts
toward 51BD then clears 036A and 0368. The literal masks and later F64E cleanup
explain why payload bytes can remain populated after active controls expire.

## Documentation boundary

The resident monitors, log/age/checksum, reaction masks, flash lamp, masked
clears and local service overrides above are documented. Raw acquisition
sampling is covered where it owns these decisions; the engine and IAC
contracts retain their linked local monitors. No code is assigned to the RTS
stubs or reserved flash positions. Full SCI/factory command framing, disconnected
code/reachability, opaque low-memory extensions, hardware electrical behavior
and interrupt interleavings remain separate work; they are not represented as
completed by the diagnostic-bit inventory.
