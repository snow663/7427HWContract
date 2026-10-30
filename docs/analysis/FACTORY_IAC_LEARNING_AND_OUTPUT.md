# Factory IAC: retained learning, reset, service and step output

This completes the state/output side of [the IAC controller](FACTORY_IAC_CONTROLLER.md) from actual BMHM bytes. The [closure index](FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md) defines provenance and verification. Integer helper notation is shared with the controller document; all table values here are stock software counts, independently of previously recorded truck `2.bin` facts.

## Retained state and boot

Low bytes `$0007-$000A` are not part of the unconditional `$0036-$00FF` clear. Boot `$720C` computes `u8(-sum(bytes000B..0014))` through `$F326`, comparing it with byte0015. A mismatch clears `$0000-$000A`, `$000B-$0035` and `$029D-$034D`, seeds word02F6 from `$5B24:$80`, resets BLM and sets `$0046 bit6`. A matching checksum preserves those retained areas. The checksum does **not** directly checksum the physical position or even bytes0007..000A; acceptance is a software retention condition, not proof the motor stayed in place.

Controller flags0036..0039 and working state0857..089A are unconditionally cleared by their normal boot ranges before later seeds. The retained cell bank is:

| Context | Integral word | Saved high-byte snapshot | Cold flow word | Cold bound word |
|---|---|---|---|---|
| Park, AC off | `$029D` | `$029F` | `$02A3` | `$02A5` |
| Park, AC on | `$02A0` | `$02A2` | Same park words | Same |
| Drive, AC off | `$02A7` | `$02A9` | `$02AD` | `$02AF` |
| Drive, AC on | `$02AA` | `$02AC` | Same drive words | Same |

`$02B1/$02B2` are separate kicker-on/off TPS baseline bytes. BLM starts at02B3, immediately after these IAC fields; they are not BLM cells.

### `$925E/$92A4` setup

Boot calls925E. Set0885=`u8(4*C[$4EF2])`. On NV-failure flag46.6, seed software position0007=`$4EB0` and call92A4. That seed routine writes **high bytes only**: drive no-AC02A7 and snapshot02A9=`$4EB2`; drive AC02AA/snapshot02AC=`sat8(base+addition)`; park equivalents029D/029F use `$4EB1`, AC02A0/02A2 use the same addition. Addition is `$4EB4` below coolant `$4EB5`, otherwise `$4EB3`. Fractions of the integral words are not overwritten by these byte stores. Seed02B1=`$50D4`.

Bad-shutdown0004.3 chooses93C5, preserving phase bits000A&0C and clearing its other bits unless reset0009.0 is already active. Normal shutdown instead calls92F1 below. With kicker option4E8F.2, low BARO high02F4<=50CE or coolant<50C7 sets kicker-active37.2; otherwise call920E to disable it. Copy software position0007 to target0008 and set output-shadow004C.4 through9240. A later boot write `$744D` replaces the entire shadow with `$40`, so setup's enable-bit write is not the final boot shadow value.

### `$92F1-$93C4` retained-cell adjustments

Warm-stable flags0009.4/5 qualify additions `$5098/$5099` to drive snapshots02A9/02AC. A byte carry substitutes `$50C3/$50C4`; it is not a general unconditional clamp. If the resulting snapshot exceeds its associated integral high byte, store snapshot<<8 to that word. Clear the warm flag after its update.

Config4E90.0 copies no-AC snapshots029F→029D and02A9→02A7 as **byte** writes. The following stock instruction at9343 is `95 08`, **`BITA $0008`**, after loading config4E8F. It tests `C[$4E8F] & byte0008`, not immediate config bit3. The branch must preserve this literal operand despite the likely intended calibration interpretation.

When that test is nonzero, recompute all four AC high-byte/snapshot values from their no-AC integral/snapshot high bytes plus the coolant-selected4EB3/4EB4 addition with255 cap. On the two integral-add overflow branches, the code additionally stores `$FF` into low byte02A1 or02AB before writing the high byte. Nonoverflow branches retain those fractions. When the test is zero and config4E90.0 is set, copy AC snapshots02A2→02A0 and02AC→02AA as bytes. With both gates clear, retain AC values.

## Background execution and cold decay

Slot7 root9E99 skips directly to snapshot publicationA29A when spark-running4F.7 is clear. Running calls989C for desired RPM, then background housekeeping/learning. Slot9 rootA2B0 similarly returns immediately when nonrunning, otherwise runs follower9CFD, slower adder decays, fault tests and reset qualification. These are separate from the every-four-tick main controller and per-tick phase service.

### First drive-away and DFCO terms

With0009.1 clear and VSS **strictly greater** than `$4EC0`, multiply park/drive cold words02A3/02AD by `M(C[$4EC1],old)` and set0009.1. Nonrunning initialization clears that bit, allowing a later qualifying event.

A nonzero DFCO magnitude0887 with DFCO46.3 clear decrements byte0888. Only a result0 reloads `$50BF` and reduces0887 by `$50BE` with zero floor. Borrow also clears sign38.5; an exact subtraction to zero does not take that clear branch. A zero old divider wraps to255 on DEC; it is not treated as an immediate expiration.

### Cold bounds and bank-transfer candidates, `$9FDE-$A12C`

Only high bytes of cold bounds02A5/02AF are tested for activity. With either nonzero, decrement nonzero delay0875; at delay0:

1. Replace each bound by `M(C[$4EBD],oldBound)`, forcing the whole word0 when its resulting high byte is0.
2. A zero new bound forces its associated cold word0. Otherwise reduce park cold with4EBE, drive cold with4EBF, and cap each result at its new bound.
3. If either bound high remains nonzero, reload0875=`hi(sat16(2*L1(ECTindex,$4EDC)*L1(min(hi(0232),64),$4EE9)))`; otherwise store0.

The cross-bank cold-transfer calculation also runs while waiting on a nonzero0875, retaining the old cold words for that calculation. For current bank high byte a and other-bank high b, use upper/lower multipliers4EF0/4EF1 in park or4EEE/4EEF in drive. Nonzero upper multiplier gives `upper=a+R8(a,k)`: if the addition does not carry and upper<b, propose upper<<8 for the other bank. Otherwise a nonzero lower multiplier gives `lower=a-R8(a,k)`; lower<b clears pending38.4, lower>=b proposes lower<<8. A proposal goes to0899 when park is current (future drive),0893 when drive is current (future park), and sets38.4. A zero current high byte or zero applicable multiplier can leave the pending flag/value unchanged. Main-controller gear transitions later consume these candidates.

When **both bound high bytes are already zero at entry**, skip this decay/transfer branch and consider warm snapshots instead. Require all bits36&0C set, coolant in inclusive4FBF..4FC0, absolute error0858<=4FBE and filtered error high0859<=4FBE. Then clear diagnostic18.3 and save the current cell high to its snapshot. Drive snapshots also set0009.4 or0009.5 for later boot adjustment; park snapshot writes do not set those warm flags. Bytes at A0FA..A113, absent from the inherited HAC rows, explicitly perform the park snapshot stores.

### AC transition-flow decay

If0876 nonzero and hold0877=0, AC-off context clears0876 immediately. In AC-on context count0878 down; on expiration reload `$4F22` and subtract `$4F21` from0876 with zero floor. A nonzero AC hold skips decay. This uses background admitted calls, independently of the fast main-controller hold decrement.

## Learned-cell transfer preparation, `$A154-$A287`

Prepare transfers only with integral-admitted36.3 set, stall36.4 clear and low-battery3E.2 clear. The destinations below are work words, not immediate learned-cell writes. Main context transitions consume their flags as documented in the controller contract.

First compare park/drive high bytes for the current AC context: p=`029D` or02A0, d=`02A7` or02AA. Park-minus-drive above4FC6, or drive-minus-park above4FC5, proposes the following opposite-gear value; proposals have fraction0.

| Current gear | p-d above4FC6 | d-p above4FC5 | Destination / flag (AC off,on) |
|---|---|---|---|
| Park | p-4FC6 | p+4FC5 | 0895/0897;38.2/38.3 |
| Drive | d+4FC6 | d-4FC5 | 088F/0891;38.0/38.1 |

Within the allowed range, clear the corresponding opposite-gear flag. Raw branches compare byte differences with borrow; the selected additions/subtractions do not receive an invented separate saturation step.

Next compare AC/no-AC word cells within the **current gear**. Select base029D/work088F with low/high bounds4FC1/4FC2 in park, base02A7/work0895 with4FC3/4FC4 in drive. Subtract ACword-noACword. A borrow/zero or high difference below the lower bound selects that lower bound for correction. A positive high difference above the upper bound selects the upper bound. A positive difference with high byte within the inclusive range clears the corresponding pending flag. Fractions influence borrow/zero, while the limit comparisons themselves use the high byte.

On correction, AC-off proposes future AC=`sat8(noAC_high+bound)<<8`, except addition carry stores `$FFFF` including fraction255; AC-on proposes future no-AC=`max(AC_high-bound,0)<<8`. Flags/destinations are park AC38.1/0891, park no-AC38.0/088F, drive AC38.3/0897, drive no-AC38.2/0895. Proposals are not direct commands to the motor.

Finally decrement nonzero entry holds0866/0867 and publish the selected context's snapshot at086A. The nonrunning root jump reaches publication without these decrements.

## Throttle-kicker state machine, `$9EEA-$9FDD`

The kicker has its own request bit `$004B bit7` and learned TPS-zero interaction; it is distinct from the IAC phase bits. Config4E8F.2 disabled, or service3B.4 plus038F.6, skips ordinary kicker handling while still allowing later background learning/decay.

Helper920E clears37 bits18. If active37.2, clear timer088D and active bit. Set disabled-once36.6 and set request4B.7. Helper9226, when not already active, writes high byte02F6=`u8(byte02B1+C[$50D5])`, retaining02F7, loads088D=`$50D3`, and sets37.2. Its common923C exit clears4B.7. These changes feed TPS normalization as well as output control; they must not be modeled as an isolated airflow adder.

Use this ordered branch procedure for the running background call:

1. **Active:** when both36&0C set, save high02F6 at kicker-on baseline02B1 and set39.0. Old underflow flag37.3 goes directly to timer/speed handling. Otherwise coolant<50C7 loads timer50CC and requests enable through9226. At warmer coolant, old37.4 goes to timer/speed handling; BARO<50CD instead follows the overspeed/small-integral checks: require36.7, drive no-AC integral high02A7<50CF and admitted36.3, then set37.4 when error0858 is below50D1 (drive) or50D2 (park). Failed checks can retain kicker state and jump directly to later housekeeping.
2. **Active timer/speed handling:** disabled-once36.6 with nonzero088D counts that timer down only at phase07 and requests enable. Otherwise TPS>50CB or VSS>50CA takes the BARO/flow decision below. Below both limits, disabled-once set requests enable; without it, nonzero timer counts down at phase07 and requests enable, zero timer takes the decision.
3. **Inactive:** timer<=15 goes to off-time increment. Above15, both36&0C set records high02F6 at02B2 and sets39.1. Timer equal to50D7 takes the BARO/flow decision; other values increment as bytes only at phase07, then call920E. These are equality/byte-wrap rules, not a universal saturating timer.
4. **BARO/flow decision:** BARO high<=50CE, or `hi(u16(word02A7+word02AD))>50D0`, takes the possible-enable branch. Other cases disable via920E. Possible-enable calls9226 when TPS>50CB or VSS>50CA; below both it leaves state unchanged.

The source labels imply an on/off throttle-kicker actuator, but electrical direction and full transmission/port ownership remain interfaces. The branch procedure above, saved baselines and output request polarity are the software contract.

## Slot9 decays, diagnostics and reset admission

After follower processing:

- Nonzero switch adder087B counts087C down. On expiration subtract4F31 with zero floor; reload hold4F30 only while the adder remains nonzero, otherwise store0.
- Nonzero startup flow086B clears immediately when003F.6 is set. Otherwise count divider086C down, reload4EB9 and decrement the adder on expiration.
- Startup RPM addition085C similarly clears on003F.6. Its initial hold085E decrements only at phase09; after the hold, divider085D counts slot9 calls, reloads4EBB and decrements085C.
- In drive with neither36.2 nor36.3 set, cap the selected drive integral high at snapshot+4FC7 (no AC) or+4FC8 (AC), but only when that addition has no byte carry and the existing high exceeds it. Store fraction0 on replacement.

Kicker/TPS-baseline diagnostic requires config4E8F.2, mask5B02.2, done39.2 clear, and **both** baseline flags39&03 set. A borrow in02B1-02B2, or a difference<50D6, sets09.6 on the first eligible failure and18.2 on a later eligible failure with09.6 already set. A passing comparison clears both. Set done39.2 after any evaluation. This is not a counter updated on every motor step; the nonrunning seed clears the baseline/done flags for a later assessment.

Phase bit5 set returns before the following diagnostic **and reset checks**. Otherwise, when5B02.3 enabled, require no VSS fault16.4, no16.0/17.7 input fault, no low-battery3E.2, integral admitted36.3,09.6 clear, both full cold words02A3/02AD zero and filtered error high0859>50C0. Increment byte088E while its old value<=50C1; an old value>50C1 sets18.3. Failure clears timer and fault. Disabled mask retains them on this path; warm-stabilityA0FA is a separate clear of18.3.

Reset qualification then requires reset09.0 clear and completed/valid09.2 clear. Ignition-off triggers reset; ignition-on requires VSS>=4EB7. The commonA3FA operation sets reset09.0, clears36 bits1C, writes target0008=0 and software position0007=255. It does not claim the motor was physically at255. Main93D0 continues commanding0 until the software count reaches0, sets09.2 and seeds default cells. An ignition-off pass with completed09.2 then requests park4EB0. The slow phase gate does not block the separate main-controller reset request on its ignition-off branch.

## Service commands and nonlocal exits, `$A407-$A465`

The main controller callsA407 only with service3B.4. Ignition-off or reset-in-work returns normally without changing the request. Otherwise:

| Service selection | Action / return |
|---|---|
| 0391.5 set | Pop the A407 return address, jumpA3FA; reset then RTS to the main controller's caller |
| Both0395.0 and038F.6 clear, or both set | Normal return; ordinary controller continues |
| Only0395.0, 0395.1 clear | Clear36 bits0C, pop the return address, set target0008=0396 through9899; skip the rest of this controller pass |
| Only0395.0, 0395.1 set | Write desired RPM0857=0396, set override38.6, normal return; later background989C honors the flag |
| Only038F.6 | Pop return address;0390.6 sets kicker-active37.2 and calls923C (request on), clear chooses9222 (request off) and clears37.2; RTS to controller caller |

The popped word is a return address, not a global data write. These escapes explain why assuming every A407 call returns to93E1 misrepresents service behavior. The original malformed HAC A40B destination is confirmed asA465 by actual bytes.

## Step service and output, `$91A3-$920D`

Load mode000A and raw battery00A7. Above169, clear enable bit4 and set low-battery3E.2, holding count/phases. At/below169, ignition-off44.4 or battery **strictly above**4EB6 admits movement, clears3E.2 and sets enable. Low battery sets3E.2 and holds count/phases but **retains the old enable bit**; it does not explicitly clear it. No volt scaling is inferred from these comparisons.

Equal position/target clears direction bit0 and holds phases. Otherwise reset09.0 suppresses stepping only when **all** old phase-counter bits02&03 are set. Normal stepping has no such phase gate. Direction0 means software position must increase; direction1 means decrease. A direction reversal updates direction only, with no count/phase transition on that invocation. On an already matching direction, change the byte count by exactly1 and advance the ring:

| Direction | Phase bits sequence |
|---|---|
| 0 / increasing count | `00 → 04 → 0C → 08 → 00` |
| 1 / decreasing count | `00 → 08 → 0C → 04 → 00` |

The `BRSET #$0C` ring test requires both bits, while `BRCLR #$0C` requires neither. Both-set/neither-set cases toggle bit2 for direction0 or bit3 for direction1; one-set cases do the opposite. Enable is a retained gate independent of the ring, not a step pulse.

Commit000A, then atomically set `004C=(old004C&$E3)+(000A&$1C)`. Ordinary stepping does not directly write the hardware latch. This closes the software A/B/enable field; physical pin polarity and airflow direction remain unassigned.

### Actual service order and cadence

TOC3 calls7B6D→91A3 **before** testing busy and before incrementing the main phase. Normal main work later calls7BA7→F3EE, which falls throughF400 and writes `byte004C→$3062`. Thus an ordinary fresh pass can issue the new shadow in the same timer entry, before the later93D0 target calculation. That newly calculated target normally waits for a later step-service admission.

Reset's phase test uses the **old** main phase byte. During uninterrupted160-phase operation it suppresses one of four step opportunities, allowing120 count-update opportunities per cycle versus160 without reset; direction-change and other gates can reduce them. The nominal normal tick is 6.248474 ms, but those counts are not guaranteed motor-step rates.

Busy reentry still executes91A3 and can change the count/phase shadow, then returns without the ordinary7BA7 latch service. Catch-up main passes repeat the latch/controller paths without repeating7B6D. Special fast-group mode001A.5 also bypasses the ordinary7BA7 call. Multiple software transitions can therefore precede one observed latch write. A one-for-one physical step cannot be inferred from software count deltas alone.

F400 additionally merges port state at3060/004B, samples3064→004D and writes004E→3067; it is a shared board service. Other shadow owners include boot744D, transmissionC522's `(old004C&FC)+C[B319+gear]`, C546/C54B controlling bit5 and CC79 clearing bit7. At gear-table indices0..3 the bytes are01,00,02,03 and an uninterrupted merge preserves the IAC field; outside that index domain the code has no local table clamp. Proving the complete gear-index lifetime belongs to transmission work. Factory-test code writes3062 directly, including phase patterns and clears. These co-owners are captured without declaring the entire factory-test/transmission subsystem complete.

A [complete-handler interrupt witness](FACTORY_STACK_AND_SHARED_OUTPUT_CONTRACT.md)
now establishes the preemption limit of that merge: C514 reads004C before its
unmasked whole-byte update. A busy TOC3 reentry afterC51C can advance the IAC
field, then C522 restores the older field from B. Pending catch-up reachesF411
without another step service, issuing31 where the sequential-arrival fixture
issues39; both end at the same software position. Physical incidence and coil
response are not inferred. Disjoint nominal bit fields alone do not make these
two read/modify/write transactions commute under preemption.

The software count is also directly seeded at926D, decremented at9B10, incremented at9BD6 and assigned255 atA404. Only91E6 accompanies a normal ring step. The resulting distinction between retained count, reconciliation, target and issued phase writes is part of the completed factory IAC documentation.
