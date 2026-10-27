# Factory running-fuel calculation and delivery

This documents the factory running-fuel calculation from the normalized inputs at `$7FD8` through `$024E`, every intervening correction/mode branch, synchronous shaping, and the output boundary at `$852C`. It includes the asynchronous helper `$8548-$858A`, the INT/proportional combination `$88E9-$891D`, and the injector-offset producer `$E2FB-$E303`.

The raw integer behavior and ordered RAM/device writes are established for this scope. The completed [upstream fuel](FACTORY_UPSTREAM_FUEL_CALCULATIONS.md) and [O2/BLM](FACTORY_CLOSED_LOOP_AND_LEARNING.md) contracts now supply the resident VE, AFR, density/temperature, AE, learning and crank calculations. Physical injector/ASIC response retains its own boundary. This is a factory-code contract; replacement firmware and simulator features are outside its completion assessment.

## ROM authority and notation

The complete stock BMHM image is 65,536 bytes, SHA-256 `6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`. CPU `$4000-$FFFF` uses the same full-file offsets; CPU `$0000` is RAM. The raw HAC is retained unchanged. `maps/structure/bmhm_fuel_rom_evidence.json` captures the bytes, and `factory_fuel_rom_instructions.csv` lists 790 decoded instructions across the reviewed ranges.

Stock BMHM values in this document are distinct from the truck's separately identified `2.bin` tune. Raw words below are unsigned and big endian unless signedness is stated. `u8` and `u16` wrap modulo 256 and 65536; `sat16(x)=min(x,65535)` for nonnegative x.

```text
M(m,w) = floor((m*w + 128) / 256)          # $F550, rounded 8×16 multiply
Q(n,d) = floor(n*65536/d), if d>n         # FDIV
       = 65535, if d=0 or n>=d
```

Invalid fractional divides have a defined `$FFFF` quotient and an unspecified remainder. The equations here use only the defined quotient, or the remainder of a valid integer divide. With a zero repeated divisor, the later quotient/clamp is already determined without assigning a value to the unspecified remainder.

## 1. Base speed-density calculation: `$7FD8-$802F`

| Input | Meaning at this boundary | Width |
|---|---|---:|
| `$0257` | Already normalized MAP/density quantity | 16 |
| `$0236` | Already normalized charge-temperature denominator | 16 |
| `$0231` | Selected/interpolated VE result | 8 |
| ROM `$4D94` | Cylinder-volume/unit-conversion multiplier | 8 |
| `$01E8` | Reference-period word | 16 |
| `$024A` | Current commanded AFR representation | 8 |
| ROM `$4D92` | Injector-flow divisor | 16 |

The exact calculation is:

```text
density_fraction = Q(word0257, word0236)
word0238 = M(byteROM4D94, density_fraction)              # 7FE8
word0234 = M(byte0231, word0238)                        # 7FF4

word0232 = min(65535, 2*floor(word0234*256/word01E8))    # 800D
            or 65535 when word01E8=0

mixture = Q(word0234 >> 2, byte024A << 8)
word024E = min(65535, floor(mixture*256/wordROM4D92))    # 802F
            or 65535 when wordROM4D92=0
```

`$0232` is a separate period-normalized air quantity; the AFR division reloads `$0234`. It does not use `$0232` as the pulse-width numerator. The two right shifts before the AFR divide discard bits before the next division. Consequently, replacing this sequence with one floating-point speed-density equation loses its actual truncation and overflow behavior.

The integer/fractional quotient assembly at `$7FF7-$800D` and `$801C-$802F` saves X on the stack, takes the fractional high byte, and combines it with the integer low byte. `TSTA` tests the saved integer **high** byte; the subsequent PULA preserves that test for the branch. A nonzero high byte forces `$FFFF`. The air-rate path additionally doubles with saturation.

Stock BMHM has `$4D92=$1B60` (7008) and `$4D94=$CE` (206). These are verified stock bytes; this pass does not substitute them for the truck tune's values or assign new physical scaling to the entire fixed-point chain.

## 2. EGR correction and BLM: `$8032-$8058`

```text
egr_multiplier = high(u16(word01B2 + 128))
word0252 = M(egr_multiplier, word024E) >> 2             # 8040
word024E = u16(word024E - word0252)                    # 8049
```

BLM is byte `$0248`. Its application helper `$80EE` first doubles `$024E`, saturating at `$FFFF`, then applies `$F550`:

```text
word024E = M(BLM, min(2*old024E,65535))
```

BLM therefore remains a multiplicative correction around 128. At ordinary unsaturated widths, 128 is exactly neutral. At widths at or above `$8000`, the preceding saturated double limits the neutral result to `$8000`. That intermediate limit belongs in the documented implementation.

The caller always applies BLM when its bit7 is set. For BLM below 128, `$003D bit5` suppresses the call when set. This is the existing PE-associated learned-lean safeguard: the actual branch condition is recorded independently of the upstream PE state machine.

The decel calls at `$8235/$82E2` enter `$80FC` instead, applying `M(multiplier,word024E)` without the initial double.

## 3. Cut, transient, and decel state logic: `$8058-$82EC`

Execution uses the following priority order. A reduction branch skips the remaining gates in this section and rejoins at `$82ED`.

| Region | Qualification and action |
|---|---|
| `$8058-$8099` | `$0016 bit4` bypasses this qualification. Otherwise ROM `$400F bit7` selects whether to skip a countdown. When the countdown is used, `$0041 bit5` reloads `$084D` from `$5155`; otherwise a nonzero `$084D` decrements, and zero skips evaluation. Evaluation requires `$0812 <= ROM5156` and `$01D9 > ROM5159`. RPM byte `$0061` exceeding `$5157/$5158`, selected by `$0053 bit3`, sets that hysteresis bit and enters the reduction path. A qualifying evaluation below the threshold clears the bit. |
| `$809C-$80E0` | ROM `$400F bit0` with all masked `$006F bits $34` clear bypasses the hard-cut tests. Otherwise RPM threshold X starts at `$4967`, with +1 for existing `$0046 bit4`, and +2 when `$0016 bit4` or any `$0099 bits $03` are set. Vehicle threshold Y starts at `$496B`, with +1 for existing bit4. RPM `$0062 > ROM[X]` cuts immediately. The delayed route requires `$0284 > ROM[Y]` and `$0062 > ROM4966`; `$026A` increments until its comparison against `$4965` qualifies the cut. Other routes clear `$026A`. |
| `$80E2-$80EB` | Set `$0046 bit4`, store zero to `$024E`, then enter the reduction path. Later additive stages still execute; this local zero alone is not a whole-pipeline output guarantee for arbitrary supplied states. |
| `$8106-$8174` | Clear the hard-cut bit, update asynchronous enrichment and its activity/hold flags, then continue to decel qualification. |
| `$8175-$824A` | Apply the decel qualification, recovery, and countdown rules detailed below. These either select reduction or continue to ordinary decel enleanment. |
| `$824D-$82EC` | Restore the ordinary reduction factor to `$FF`; optionally calculate a load/TPS-derived enleanment multiplier and apply it to both `$023A` and `$024E`. |

The reduction path `$821D-$8238` sets `$0046 bit3`, loads `$0245` from `$4942`, sets `$003D bit4`, and stores `max(byte0244-byteROM4943,0)` to `$0244`. That byte multiplies `$024E` through `$80FC`. A factor that reaches zero stays zero until the ordinary path restores `$0244=$FF`.

### Asynchronous enrichment state

The `$810C` calculation starts with byte `$087F`. A pending `$003E bit0` is cleared and adds ROM `$48C6`. `$0041 bit4` and its cached bit3 detect another addition of ROM `$48C7`. Byte `$023F` then adds unless an earlier addition already overflowed. These byte additions saturate at 255.

For a nonzero result A:

```text
word023A = u16(old023A + ((A*byte023C) >> 3))           # 8149
```

This reservoir addition wraps as a word. Nonzero A, or `$0005 bit7`, activates `$003D bits $C0`, `$006E bit0`, and `$0044 bit1`, and reloads `$081D` from `$48CA`. Entry into activity also sets `$006E bit3` when `$003D bit6` was clear. Inactive calls clear bit6 and decrement a nonzero hold byte `$081D`; `$0044 bit1` clears on a call that finds the hold byte already zero.

### Decel qualification and recovery

The decision sequence at `$8175` is:

1. If byte `$0006 < ROM4944`, go directly to ordinary enleanment.
2. `$0041 bit5` selects recovery.
3. With `$006F & $24 == 0`, compare TPS `$01D9` against the `$4C94` header lookup of `$0062`, using an input subtraction of 32. TPS at or above the result resets `$0245` and reloads `$0246` from `$4941`; existing `$0046 bit3` also sets the transition flag `$003E bit0`.
4. A positive `$0065-$0063` greater than `$4945` selects recovery.
5. With `$006F & $48 == 0`, `$01CA > $4946` selects recovery. Otherwise select `$01CF` when ROM `$400E bit1` is set, or `$01C0` when clear. A selected load at or above `$493D` reloads `$0246` from `$4941` when the existing reduction bit is clear; when it is set, the second threshold is `$493E`.
6. Compare RPM `$0062` against byte `$0243`, adding `$493A` with byte saturation when reduction bit3 is clear. RPM at or below that threshold selects recovery.
7. Unless `$0016 bit4` bypasses the vehicle test, `$0284` must meet `$493B/$493C`, selected by existing reduction bit3. Failure selects recovery.
8. A zero `$0246` selects reduction. A nonzero one decrements only when `phase_byte0002 & $0E == 0`. Both the delay route and the load-reload route decrement a nonzero `$0245` before continuing; the load reload does not freeze that active timer.

Recovery adds word ROM `$493F` to `$023A` when `$0245` was nonzero. A word carry replaces that sum with `$7FFF`; otherwise the sum is retained. Recovery sets `$003D bit7`, clears `$0245`, reloads `$0246` from `$4941`, then continues to ordinary enleanment. The TPS reset route clears `$0245` without the reservoir addition.

### Ordinary enleanment

`round_byte(w)=min(255,(w+128)>>8)`. Compute `TPS_drop=round_byte(word01DE)-byte01D9`; a borrow exits with `$003D bit4` and `$0053 bit1` clear. Otherwise store the drop in `$082B`. The drop must exceed ROM `$4936`, except when ROM `$400B bit7` and the existing `$0053 bit1` latch jointly bypass that comparison. A newly qualifying drop sets the latch.

Next compute `load_drop=round_byte(word01C7)-byte01C0`. It must be nonnegative and exceed ROM `$4937`. Look up `min(load_drop,160)` at `$4B20` and `TPS_drop` at `$4B2B`, sum with byte saturation, and calculate:

```text
a = min(255, floor(lookup_sum*byte0242*8/256))
if byte0284 < byteROM4939:
    a = high(min(65535,2*(a*byteROM4938+64)))
multiplier = u8(-a)
```

A zero multiplier takes the inactive exit. Otherwise set `$003D bit4`, replace `$023A` with `M(multiplier,old023A)`, and apply the same multiplier to `$024E` through `$80FC`. The existing `$0053 bit1` latch remains set on this active route.

## 4. RPM, barometric, battery, INT, and MAP-AE corrections

### RPM-dependent factor: `$82ED-$8341`

This correction requires all four comparisons:

```text
byte0067 >= ROM4516
byte01D9 <= ROM48DB
byte0284 <= ROM48DC
byte0006 >= ROM48DD
```

Failure stores `$80` to `$006C` and leaves PW unchanged. Success computes:

```text
a = min(255,(Q(word006A >> 1, word0068)+128) >> 8)
byte006C = a
factor = upper451A, if a >= upper451A
       = lower4519, if a < lower4519
       = a, otherwise
word024E = min(65535,2*M(factor,old024E))
```

The raw `$006C` value is stored before the factor clamp. Stock `$4516=$FF` and both factor limits are `$80`; the enable qualification still matters.

### Lookup arithmetic

The `$F4C1` one-dimensional lookup uses `index=input>>4`, `fraction=(input&15)<<4`, and adjacent byte knots. It rounds `abs(second-first)*fraction/256`, then adds or subtracts that adjustment according to slope. `$F4BD` first subtracts an input offset with a lower clamp at zero. `$F49A` additionally caps the input to a table header.

`$F4DE` subtracts the two lower-axis offsets with zero clamps. Header byte 2 is the row stride. It performs two separately rounded column interpolations, then a rounded interpolation between those row results. It does not perform one unrounded four-cell weighted average, and it contains no general upper-axis clamp. Actual neighboring reads are retained in the byte evidence.

### Barometric and battery multipliers: `$8342-$837D`

```text
axisA = high(min(byte01C6,216)*151 + 145)
baro_factor = lookup2(axisA, byte01CC, table49AA)
word024E = min(65535,4*M(baro_factor,old024E))           # 836C

battery_factor = lookup1(byte0055, table4988)
word024E = M(battery_factor,old024E)                    # 837D
```

The two barometric doubles saturate; the battery multiply has no following double. The battery multiplier and the later byte offset are separate mechanisms.

### INT/proportional combination and application

The reviewed producer at `$88E9-$891A` combines integrator byte `$020F` and proportional byte `$027A`. With `$003E bit6` clear, it sums them with saturation at 255. With bit6 set, it subtracts proportional from integrator with a zero floor. On that subtracting route, ROM `$400B bit3` and `$0044 bit1` jointly enable a cap: proportional above ROM `$4912` is first replaced and stored back at `$027A`.

```text
byte026F = u8(combined - 128)
signed_correction = byte026F, if byte026F < 128
                  = byte026F - 256, otherwise
word024E = min(65535,max(0,old024E+signed_correction))   # 839C
```

Thus a change of one resulting signed INT/P count adds or subtracts one PW count. INT/P is an additive correction; BLM supplies the learned multiplicative correction.

Finally, byte `$023E` adds as MAP AE with a `$FFFF` ceiling. `$83AB` stores the corrected `$024E`; `$83AE` copies it into `$0254` before delivery routing.

## 5. Delivery routing: `$83B1-$84BB`

| Condition | Result |
|---|---|
| `$0044 bit4` set | Store zero in `$024E`, then enter the finalizer. An existing async-route bit can still bypass the final synchronous write. |
| ROM `$400B bit0` set | CPI/PFI alternative route. Existing `$0051 bit0` doubles PW with saturation. Otherwise `$082A` increments up to 255; `$0254 <= ROM492C` and the timer meeting `$4974` latch `$0051 bit0/$003F bit4`, then double PW. A pending `$003D bit7` can still service an async packet. |
| TBI, ROM `$400B bit2` and `$0050 bit7` both set | Select synchronous routing immediately. |
| Other TBI cases | Use the hysteresis thresholds below to choose synchronous or asynchronous delivery. |

For the threshold route, choose base `$492A` when the previous `$003E bit4` was set, or `$492C` when clear; then set bit4. `wordROM[base]` is the PW threshold. The high/low bytes of `wordROM[base+4]` are the load/RPM thresholds.

Select asynchronous routing when PW is at or below its threshold. Above the PW threshold, select synchronous when either threshold byte is at or above its corresponding `$01C0/$0062` input; otherwise select asynchronous.

Synchronous selection clears `$003E bit4` and clears word `$0259`. That word clear preserves fractional byte `$025B`. It services an async packet only when `$003D bit7` was set. The asynchronous route explicitly writes `$0000` to `$3FCE` at `$8426`, accumulates fuel, and evaluates a packet.

### Fixed-point asynchronous accumulation

Read the period at `$842C`; this is a coherent live sample supplied separately from RAM. Let:

```text
ratio = Q(word024E, min(65535,2*live_word3FC0))
integer,remainder = divmod(ratio,80)
fraction16 = floor(remainder*65536/80)
rounded_fraction = fraction16 + 128
```

The high byte of `rounded_fraction` is stored at `$025E`; a carry increments the integer before word `$025C` is stored. Word `$025D` then adds into `$025A`, with carry and byte `$025C` added to byte `$0259`. Together `$0259-$025B` form a wrapping 24-bit accumulator. Equivalently its increment is `floor((floor(ratio*65536/80)+128)/256)` in that representation.

### Packet selection and remaining reservoir

Form `total=u16(word0259+word023A)`. Word ROM `$4932` is the maximum packet, and `$4934` is the lower emission threshold.

- If `total <= minimum`, set `$0046 bit0`, clear `$003D bit7`, and emit no packet.
- If `minimum < total <= maximum`, clear `$023A` and word `$0259`, then emit `total`.
- Above `maximum`, subtract the maximum from `$0259`. When that subtraction borrows, add `$023A` back to the wrapped difference, store it as the remaining `$023A`, and store zero to `$0259`. Otherwise store the difference to `$0259`. Emit the maximum packet.

Successful emission sets `$003D bit7` and clears `$0046 bit0`. Comparisons use the wrapped `total`; the code does not promote the two-word sum to a wider saturating value. Stock maximum/minimum packet words are `$0312` (786) and `$005C` (92).

## 6. Final synchronous shaping: `$84BC-$852B`

If `$003E bit4` remains set, the async bypass stores the unshaped `$024E` at `$024C`, clears `$003F bit7`, and jumps to `$852C`. **It does not update `$0250` and does not issue another `$3FCE` write.** A BPW channel sourced from `$0250` can therefore retain its previous synchronous value while `$3FCE` has been cleared for async delivery.

Otherwise:

1. A zero PW stores zero to `$024C/$0250` and skips both minimum shaping and additive offset.
2. For nonzero PW below `$0100`, look up `max(PW-32,0)` at `$4979`; add the returned byte, then subtract word ROM `$4971`. A borrow selects the replacement word `$496F` and sets `$003F bit7`.
3. On the nonborrow route, clear `$003F bit7` and compare against the minimum `$496D`. A value below it selects `$496F` and sets the flag. PW at or above `$0100` enters this minimum comparison directly, skipping the short table and `$4971` subtraction.
4. Store the shaped value to `$024C`. If nonzero, add byte `$0256` with 16-bit wrapping, then cap that wrapped result at `$7FFF`. Store the final value to `$0250`.
5. TBI writes that word to `$3FCE` at `$8512`. The CPI/PFI branch instead computes `min(65535,4*M(byteROM4973,word005F))` and stores it to `$081F` at `$8529`; this slice does not issue the TBI hardware write on that branch.

The final synchronous equation is therefore:

```text
final = 0, if shaped=0
      = min(u16(shaped+byte0256),32767), otherwise
```

Wrapping precedes the limit. For example, a supplied shaped `$FFFF` and offset 4 produce `$0003`; replacing this with an unlimited-width addition followed by a clamp would produce a different value.

Stock minimum and replacement are both `$0020`; the short subtraction is `$0002`. With the stock zero short-table entries and a supplied offset of 4, input PW 255 shapes to 253 and writes 257, while input PW 256 skips the subtraction and writes 260. The zero-PW and table-boundary cases are part of the documented behavior.

## 7. Additive offset producer and asynchronous hardware sequence

The producer at `$E2FB` reads battery byte `$00A7`, applies the `$4B05` one-dimensional lookup, and stores one byte at `$0256` (`$E303`). This is separate from the `$0055/$4988` multiplicative battery path.

The async helper `$8548` receives a packet word in D. If ROM `$400E bit4` is set and the word is below 256, it applies the same short lookup and `$4971` subtraction, with a zero floor on borrow. It then adds `$0256` **even when the packet or shaped value is zero**. This addition wraps and has no `$7FFF` limit in this helper.

| PC | Software action |
|---|---|
| `$8571` | Write the resulting word to `$3FF2` |
| `$8577` | Read a coherent live word from `$3FFC` |
| `$857F` | Write that word with `$0400` clear |
| `$8587` | Write the same word with `$0400` set |

`$0400` is bit2 of the byte at CPU `$3FFC`, the high byte of the word. The RTS helper `$F3ED` occurs between accesses. These software values/order are established; the physical trigger response is a hardware dependency.

## 8. Initialization, cadence, and state ownership

Boot's `$7173 -> $F2FD` clears `$0100-$029C`, including `$023A`, `$0244-$025E`, `$026F`, the fuel accumulator, shaped/final PW, additive offset, counters, and fractional state. The `$715B` indexed ASIC loop attempts zero writes to `$3FCE/$3FF2` while clearing even words `$3FC0-$3FF8`. It does not clear `$3FFC`. A software zero write does not establish later hardware readback behavior.

The ordinary scheduler calls fuel root `$7D4B` on odd phases, with the main special-mode gate clear. Its nominal admission is every other TOC3 tick, approximately 12.496948 ms; busy/pending coalescing prevents treating that nominal interval as a physical execution guarantee. Earlier `$7D4B` code selects running versus crank/stop/zero paths before `$7FD8`. The following producers and consumers execute within the reviewed running slice:

| State | Current producer/update | Use/lifetime |
|---|---|---|
| `$024E` word | Base, EGR/BLM, control, RPM, baro/battery, INT/AE, route | Working running-PW accumulator |
| `$0252` word | `$8040` | Current EGR subtraction term |
| `$0254` word | `$83AE` | Snapshot before delivery routing |
| `$024C` word | `$84C3/$84F5` | Unshaped async-route value or shaped sync value |
| `$0250` word | `$8508` | Final sync value; retained on async bypass |
| `$0244` byte | Reduction decrement or ordinary `$FF` restore | Persistent reduction multiplier |
| `$0245/$0246` bytes | Decel reload/decrement/reset rules | Persistent hold/qualification counters |
| `$003E bit0` | Decel transition; consumed by enrichment | Deferred enrichment addition |
| `$003E bit4` | Delivery selection | Route latch plus threshold hysteresis |
| `$0259-$025B` | Ratio increment, packet subtraction, integer-word clears | Persistent 24-bit delivery accumulator |
| `$023A` word | Enrichment, recovery, enleanment, packet accounting | Persistent asynchronous reservoir |
| `$003D bit7` | Enrichment/recovery and packet result | Enables later async packet service |

The complete explicit read/write inventory is `factory_fuel_memory_accesses.csv`. Its indexed operands retain their addressing mode; call-specific helper aliases remain in the existing nested-flow maps rather than becoming invented global variables.

## 9. Checked examples and documentation status

One review fixture supplies density `$2F00`, temperature `$B000`, VE 180, AFR 145, period 2000, BLM 128, offset 4, and the stored stock calibrations. It selects ordinary synchronous delivery. These are chosen raw states, not a truck log:

| Change from fixture | Corrected `$024E` | Written `$3FCE` |
|---|---:|---:|
| Baseline | 160 | 162 |
| BLM 100 | 124 | 126 |
| BLM 100 with `$003D bit5` set | 160 | 162 |
| Signed INT/P +20 | 180 | 182 |
| Signed INT/P -20 | 140 | 142 |
| MAP AE +200 | 360 | 364 |

The different final deltas include the real short-PW threshold behavior. The separate async fixture writes `$3FCE=0`; when a packet is emitted it writes `$3FF2` and toggles the `$0400` word mask in the recorded order.

Supporting validation checks the equations against actual instruction execution, including every 16-bit final PW, every signed correction byte, base-division boundaries, BLM/EGR limits, 1D/2D rounding, producer branches, state initialization, 1,200 varied delivery fixtures, and 2,048 varied complete running fixtures. All explicit RAM/ASIC write values and ordering are compared. Some fixtures vary mode calibration bits or provide inconsistent raw states to exercise boundaries; they are not evidence those states occur in normal operation.

The underlying CPU pull/IDIV flag behavior needed correction to preserve the quotient-high-byte branch. ISA authority is the [NXP HC11 reference manual](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf), instruction details for FDIV/IDIV (pages 543–544) and PUL (page 567). The checked factory artifacts are:

- `bmhm_fuel_rom_evidence.json`: full-image identity and captured bytes.
- `factory_fuel_rom_instructions.csv`: exact instruction inventory.
- `factory_fuel_memory_accesses.csv`: explicit memory references.
- `factory_fuel_dependencies.csv`: state producers, initialization, and scope.
- `factory_fuel_handoff_vectors.csv`: raw inputs and predicted state/hardware values.

The documentation for this running-fuel integer slice is complete. Its upstream inputs remain the local boundary of this derivation, but their resident coordinate/charge/VE, AFR/PE/startup, AE and O2/BLM producers are now documented in the companion contracts, together with `$85B2` cranking and its local delivery. [FACTORY_ENGINE_CALCULATION_CLOSURE.md](FACTORY_ENGINE_CALCULATION_CLOSURE.md) supplies the combined checklist, cadence, initialization, and explicit raw/cross-controller interfaces. Full flag ownership across other controllers, opaque extensions, interrupt interleavings, physical unit normalization and delivered-fuel behavior retain their boundaries; this is not a whole-factory completion claim.
