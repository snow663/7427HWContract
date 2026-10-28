# Factory RPM, VSS and governor calculations

This closes the stock resident speed calculation, RPM-ratio input, electronic governor and their local fuel-limit/fault/output interactions. [The IAC controller](FACTORY_IAC_CONTROLLER.md) and [its learning/output contract](FACTORY_IAC_LEARNING_AND_OUTPUT.md) document the IAC speed consumers. [The closure index](FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md) records byte authority and the remaining cross-subsystem interfaces. No truck calibration or VSS-elimination patch is made by this documentation.

Use `u8/u16`, `hi`, `sat8/sat16`, `Q`, `M`, `L1/S1/H1` from [the engine calculation index](FACTORY_ENGINE_CALCULATION_CLOSURE.md). Comparisons are unsigned unless explicitly called signed. `C/W` mean ROM byte/word values. A high-coordinate byte addition/subtraction operates on the high byte of a fixed-point word, preserving its fraction unless a floor/cap replaces the whole word.

## RPM coordinates and state age

The complete period/RPM conversion at `$A5E5-$A686` and alternate `$AC51-$ACA6` are documented in [upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md). They produce RPM61, RPM62, high-rate67, filtered words63/68, governor filter028E and sampled byte change028D. This document closes their remaining IAC/governor consumers rather than substituting source engineering labels for the raw transforms.

`$028E=lag8(RPM62,old028E,C[$50E4])` updates on admitted normal even-group conversion. Only phase `(02&$1F)==$04` saves the rounded filter high at028C and stores wrapped change028D from its previous sample. Its rounding is `hi(u16(028E+128))`, without an added saturation correction. Governor can consume one028D sample over multiple invocations.

REF has **two** writers of RPM history006A. The non-fuel-running route7535 copies word0068 directly. On the running continuation7765, OR high byte of live3FFA with saved status0073, clear saved0073.6 and require the combined bit40 (word mask4000). With that event, RPM67>=4516 and TPS<=48DA selects `lag16(word0068,old006A,C[$4518])` through F479; otherwise copy0068 directly. Store at7790. The indexed helper's partial intermediate write is followed by this final store. Without the status event, retain history006A. These different admission/filter rules establish the numerator's state age in the ratio below; history is not a permanently frozen crank sample.

## VSS sampling, raw calculation, filter and timeout

### Sample changes, `$7BF5-$7C0E`

In the ordinary common fast group, atomically sample word `$3FFA→$0073`, then reenable interrupts. Test high-byte bit04 (word mask `$0400`). When set, read word `$3FC4`; if different from previous timestamp080D, increment byte080C with wrap and store the new080D. Unchanged timestamp or clear status bit leaves them unchanged.

Thus080C counts **observed timestamp changes**, not a proved count of every physical VSS edge. Polling, timestamp wrap and hardware semantics remain distinct from this software operation. The producer is a scheduled poll, not an invented separate VSS ISR.

### Raw VSS, `$D4A3-$D4D9`

Fuel-tail phase bit1 clear callsD4A3 after its O2 task, nominally every 4 ordinary ticks. Let n=byte080C and age=byte0811:

- n=0: with age0, write raw word0812=0. With age>0 decrement it; a result0 also writes raw0. Otherwise retain the prior raw word. Store the new age.
- n!=0 and old age=0: skip a speed quotient on this first/restarted batch, retaining raw0812. Clear080C, copy080D→080F, reload age39.
- n!=0 and old age!=0: `numerator=u16(460*n)`, `interval=u16(word080D-word080F)`, `raw0812=Q(numerator,interval)`. Then clear080C, save080F and reload age39.

The 460*n numerator is formed by230*n and a wrapping word double, **not** a saturating multiply. Invalid fractional divides have the defined `$FFFF` quotient. At nominal uninterrupted admission,39 no-event calculation opportunities are about974.762 ms; this is not a hardware edge-time guarantee. Each new observed batch restarts the timeout.

### Filter, `$D4DA-$D4EA`

Slot9 calls `word0284=lag16(raw0812,old0284,C[$4E8E])`, separately from the faster raw calculation. Stock gain4E8E is255. `$0284` high and `$0285` fraction form one filtered word; a byte consumer sees its high coordinate, while PE's speed-change sampler and governor use the whole word.

Working timestamps, counters and raw0812 are unconditionally cleared by boot's0800..08FF clear; filtered0284 by the0100..029C clear. This establishes software initial zero, not a calibrated physical speed measurement. The exact raw formula is closed without asserting an independently measured mph/Hz electrical scale.

## RPM ratio feeding IAC and spark, `$82ED-$8341`

The running-fuel path refreshes ratio006C only when execution reaches this region. Require RPM67>=`$4516`, TPS<=`$48DB`, VSS high<=`$48DC` and coolant>=`$48DD`. A failed gate stores128 and skips the following derivative PW multiply.

On qualification:

```text
q = Q(word006A>>1,word0068)
006C = min(255,(q+128)>>8)
```

The defined divide quotient and rounding/carry are preserved. If both nonzero words are equal, the result is128. The stored ratio is subsequently clamped to the ordered upper/lower factors4518/4519 for the fuel-PW multiplier; **the raw006C store happens before that clamp**. The exact fuel word multiply is already in the running-fuel contract.

IAC9CA6 and idle sparkA8D3 have their own ratio transforms and therefore consume the raw006C, including its default128. Fuel states bypassing this region retain the older ratio. Boot clears006C to0; that initial0 is not equivalent to an already executed neutral/default128 update.

## Separate fuel-cut limiter and abuse protection

The optional electronic governor and the hard fuel-cut limiter are different paths. At809C, config400F.0 **set** with no006F&34 fault bypasses the ordinary RPM/VSS cut checks. Config clear, or an enabled governor with those faults, takes the fuel-cut path.

Select RPM threshold pointer4967 and speed pointer496B. Existing fuel-cut latch0046.4 adds1 to **both** pointers for hysteresis. VSS fault0016.4, or any0099&03, adds another2 to the RPM pointer only. RPM62 strictly above its selected threshold immediately sets the cut latch, writes024E=0 and joins the existing decel/cut correction route821D.

Otherwise, speed high0284 must be strictly above its selected speed threshold **and** RPM62 strictly above4966. Only then count026A toward4965: an old counter>=limit cuts immediately; a smaller old count increments and continues fuel with the cut latch clear. Other ordinary exits clear026A and the cut latch at8106/8109. These are byte-counter admissions, not a newly inferred time unit.

The preceding abuse path8058 uses **raw VSS high0812**, not filtered0284. VSS fault16.4 bypasses it. With400F.7 set, test it directly. Without that manual-mode bit, P/N41.5 reloads084D from5155; leaving P/N counts it down and skips abuse after it expires. Qualification is raw speed<=5156, TPS>5159, and RPM61 greater than5157 (or5158 when abuse latch53.3 was set). Success sets53.3 and joins the documented fuel reduction821D; RPM failure clears that latch. Other failed gates can leave its prior value retained.

The rest of cut/decel/PW arithmetic is completed in [running fuel](FACTORY_FUEL_INTEGER_HANDOFF.md). Disabling electronic-governor400F.0 does not erase these limiter, raw-speed abuse or other VSS-qualified paths.

## Electronic governor target, `$8EB4-$90D2`

The target routine runs in the fuel tail at phase low3=3, nominally every 8 ordinary ticks. It produces target byte0299 and retains a fractional target accumulator0286. The actuator routine below runs more often.

| Governor flag0075 | Local role |
|---|---|
| bit0 | RPM governing active |
| bit1 | Anticipation stage active |
| bit2 | Filtered RPM above reference50D8 |
| bit4 | Anticipation recovery stage |
| bit6 | VSS at/above reference50DA |
| bit7 | VSS governing active |

Require config400F.0, spark-running4F.7 and006F&34==0. Failure writes0299=255 and returns, retaining the other governor state. On admission, clear75.2 and subtract filtered RPM high028E from50D8; borrow sets75.2 and byte-negates the error. Store magnitude0293. Optional0086.6 calls unknown1809. A returned carry jumps directly to the0299 store with **returned A**, bypassing local target logic; it does not necessarily store255.

### VSS state

With50DA=0, clear75.7 and skip fresh speed-error calculation, retaining75.6/0294. Otherwise subtract50DA from the **high byte** of filtered word0284, retaining its fraction. At/above reference, store0294=`hi(sat16(4*difference))`, set75.6, and, on a new75.7 entry, seed only the high byte of0286 to `min(C[$50E1],TPS01D9)`, retaining its fraction. Set75.7 and clear75 bits13 (bit0/bit1/bit4).

Below reference, take the full word magnitude, then0294=`hi(sat16(4*magnitude))` and clear75.6. Keep an existing75.7 only while this magnitude byte is **below**50DB; keeping it also clears75 bits13. Otherwise clear75.7. No local blanket clear normalizes all mode bits, so older retained bits can matter if calibration/state is changed in flight.

### RPM state and active control

When RPM-excess75.2 is set, and neither75.7 nor75.0 was active, lower high0286 to current TPS if TPS<=that old high byte. Set75.0 and clear75 bits12 (bit1/bit4). Existing active state bypasses that entry seed.

If either75.0 or75.7 is now set, form:

```text
gain = H1(old0299>>1,$50E8,offset=0)
error = 0293 if RPM-active75.0 else 0294
k = C[$50E0] if RPM-active75.0 else C[$50DF]
step = M(k,sat16(8*gain*error))
lead = sat16(4*C[$50DD]*0293)
speed_correction = 0
if VSS-active75.7:
    speed_lead = sat16(16*C[$50DE]*0294)
    speed_correction = hi(speed_lead)
    if RPM-excess75.2 clear: lead = speed_lead
```

Store intermediate and final step at028A, lead at0290 and speed correction at0292 in the actual order. If any75&44 (VSS-above bit6 or RPM-excess bit2) is set, subtract step from0286. Borrow or high result below50E2 replaces the **stored accumulator** with50E2<<8, and skips its lead subtraction. Otherwise store the candidate0286 and calculate a transient output high byte from accumulator-lead, floored at50E2. On the other branch, add step to0286 with word saturation, then form output high from accumulator+lead with255 cap. The lead result does not become the stored integral accumulator.

At the common output stage, any75&84 (VSS-active or RPM-excess) admits the speed-correction byte:75.6 clear adds it with255 cap; set subtracts it with floor50E2. Store target0299. Keep the distinction between the word accumulator0286, lead-adjusted candidate and final target byte.

### Anticipation when neither RPM nor VSS mode is active

Clear0292. With75.1 clear, a negative-N byte028D immediately chooses255<<8 as0286 and target255. Otherwise compare `S1(min(028D,32),$50EE)` to filtered RPM high028E: at/above it choose the same255 target; below it set75.1 and seed0286=`max(C[$50E3],min(C[$50E1],TPS))<<8`.

With75.1 already set, old recovery75.4 bypasses the following sign decision. Otherwise compute byte `0-028D` and use the actual signed `BLT`: signed-positive derivative selects the reducing branch; zero/negative derivative selects recovery. This uses N xor V, not merely the N bit of a wrapped negate.

- **Reducing:** `r=hi(sat16(4*L1(min(coolant,128)>>1,$50FA)*raw028D))`. Subtract r from high0286, retaining the fraction when it stays at/above50E3. Borrow or a lower result sets50E3<<8. Use the resulting high byte as output.
- **Recovery:** set75.4. Select gain50E7 when old0299<50E5, otherwise50E6; add unshifted word `0293*gain` to0286. A word carry writes255<<8 and target255; otherwise retain/store the whole sum and output its high byte.

All branches join the common speed-correction/output store above. After storing0299, any75&11 (RPM mode or recovery) can clear75 bits13 only when actuator integral **high byte0288=0**, and either RPM mode is clear or filtered RPM high028E<50D9. This is a byte-high release test, not a whole-word-zero requirement.

## Actuator I/P and hardware command, `$90D3-$9166`

Fuel calls90D3 on ordinary odd phases when config400F.0 is set, nominally every 2 ticks, before the density calculation. Its state is independent of the slower target admission:

```text
e = abs(byte0299-TPS01D9)
029A = e
P = sat16(4*e*S1(e,$50FF)); store0295
Istep = e*S1(e,$5109); store0297
```

If target<TPS, add Istep to old word0288; a carry stores **FF00**, notFFFF. Store the integral, then form integral+P, round by adding128 and use its high byte; either carry caps that output at255. If target>=TPS, subtract Istep from0288 with zero floor and store; subtract P with zero floor, then round the nonnegative result by128 and use its high byte, again checking carry.

Target0299=255 clears the integral0288 **after** the output candidate is calculated. It does not unconditionally force that same call's output candidate to0. With option400F.0 clear the caller skips90D3 entirely, so this routine issues no fresh command on that route.

Mode0051.4 forces output byte0. Otherwise service003B.4 plus0393.0 substitutes0394. Write the command word `$1F00|output` to `$306C/$306D` at9163. The `$1F` command header is fixed in this resident path; the electrical polarity and mechanical throttle direction are not established solely by the math.

### Shared output owners

306C is also written by the non-electronic TCC path: config400E.2 selects1FFF when0053.2 set,1F00 otherwise, atCDDF. That scheduled writer can overwrite a governor command if both configurations admit their paths; there is no local mutual-exclusion check in90D3. Factory-test stores atFB8D/FBBF are further owners. Their write instructions are captured, while the full factory-test sequence and transmission logic remain separate scopes. Normal software output ownership is therefore broader than the single9163 store.

## Local speed/governor diagnostics

The broader diagnostic root can bypass these local entries, so their stated clears/updates apply on admission rather than on every tick.

- **VSS plausibility at DDBA:** clear16.4. Any006F&48 or VSS>4E3A clears timer0817 and exits this check. Otherwise an old0817>4E3F sets16.4 immediately, before testing current MAP/coolant/RPM/TPS. With the old count at/below its limit, require MAP<4E3D, coolant>4E3E, RPM62 in strict-low/inclusive-high `(4E3B,4E3C]` and TPS<4E40; failure clears the timer. On a fully qualifying route increment0817 only when006F.7 is set; otherwise retain it. The count increments as a byte.
- **Manual/output-speed diagnostic atDE07:** with400F.7 and mask5B01.5, a nonzero word0849 clears17.5 and081C. A zero0849 with old081C>4E43 sets17.5; otherwise VSS>4E44 increments081C, lower/equal speed retains it. Disabled mode/mask retains these states here. This diagnostic uses the separate0849 input; it is not identical to VSS-buffer16.4.
- **Governor diagnostic atDE3A:** clear18.7. With400F.0, either existing006F.4 or integral high0288>=4E4B sets18.7 and006F.4. No local clear of006F.4 exists in this block. That bit contributes to the governor-inhibit mask34 and the fuel-limit fallback. Other diagnostic/service writers of shared006F remain explicit owners.

Slot4 mirrors selected TPS faults into006F bits24: clear them, set bit2 from0016.0 and bit5 from0017.7. These gates and governor's own bit4 explain the inhibit mask without inventing independent runtime-pointer behavior. Full DTC latching/history/reporting and every raw sensor fault producer remain separate diagnostic work.

## VSS consumer coverage and truck interpretation

`maps/structure/factory_rpm_vss_consumers.csv` checks each direct listing-seeded reader of0284 or0812 against actual instruction bytes. It links completed fuel, spark, O2, IAC and governor consumers to their contracts and leaves transmission/TCC, shift/gear estimation, AC, purge and remaining diagnostic consumers explicitly separate. This is a direct-reader audit, not proof that no indexed alias exists anywhere in the program.

VSS affects IAC closed qualification, proportional authority, follower delay/gain, first-drive-away decay, kicker enable and reset triggers; it also affects fuel/VE/AE/BLM, idle spark and knock gates in the completed engine contracts. There is no single speed byte that reproduces every branch's neutral behavior.

Stock400F is10 (electronic-governor bit0 clear),50DA is0, and4E8E isFF. Optional branches are nevertheless documented from their resident bytes. The old [literal2.bin authority audit](../investigations/BIN2_VSS_AUTHORITY_AUDIT_2026-08-20.md) retains its separate recorded tune values and proposed consumer-by-consumer changes. This pass does not re-read that tune or enact those proposals. Software calculation/command closure is distinct from electrical speed calibration, actuator mechanics and the separate factory controller scopes listed in the index.
