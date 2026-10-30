# Factory upstream fuel calculations

This closes the resident producers of VE, density, charge temperature, commanded AFR, PE/startup and AE used by [the running-fuel contract](FACTORY_FUEL_INTEGER_HANDOFF.md), and documents the separate crank equation and its reference-event delivery. [The closure index](FACTORY_ENGINE_CALCULATION_CLOSURE.md) supplies ROM identity, shared integer/lookup definitions, cadence, initialization and external interfaces. Addresses below are CPU addresses; `C/W` denote ROM byte/word calibration reads. All constants and instruction decisions here were read from the hash-identified stock BMHM image, independently of the truck's recorded `2.bin` values.

## Input coordinates and normalization

### MAP filtering, `$7BA7-$7BF4`

The default target is raw MAP byte `$082E`. When `$006F & $48` is nonzero, the substitute is normally `C[$4E68]`. With `$004F bit4` set, the substitute can instead be built from `4*(TPS01D9*C[$4E69])`: either word-shift carry selects the default, otherwise add its high byte to `H1(RPM62>>1,$4E6A,offset=16)`. A byte carry or result greater than `$4E68` also selects the default.

Apply `lag8(target,word01C3,gain)` with gain `$4138` when `$0047 bit0` is set, otherwise `$4137`. Store the word at `$01C3`; store its rounded high byte at `$01C6`. This particular rounding is `u8(hi(word)+bit7(low(word)))`, **without** a saturation correction on byte overflow.

The gain-selection state is made at `$7DB6-$7DEF`. Let `mode=($0041&$10)+($0089&$20)` unless `$400F bit7` is set, in which case omit the second term. Stability requires `mode==($0047&$FE)`, `abs(byte0063-byte0065)<=C[$413A]`, `$0050 bit7` set and `$003E&$A0` nonzero. A failure reloads `$01C5` from `$4139`; a qualifying nonzero old counter decrements it. Both routes set bit0 in the stored mode. Only a qualifying call finding the old counter already zero stores mode with bit0 clear. Thus this is an admitted-call hold, not an independently timed physical delay.

### BARO, `$C583-$C667`

`$02F4` is a filtered word; its high byte supplies the BARO input. The source has two modes:

- `$5D02 bit2` set: read the selected ADC channel5 into raw byte `$02F3`; add11 with a 255 cap, then filter with gain `$4158`.
- Otherwise estimate BARO from MAP. Ignition-off `$0044 bit4`, or MAP `$01C6` greater than the old BARO high byte, admits MAP directly. These tests precede the diagnostic substitutions. On the remaining route, `$006F bit6`, or any `$006F&$0C` combined with MAP below `$4E68`, forces `$4E68<<8` and raw `$02F3=$4E68`.

For the remaining estimate to update, require `$4155<=RPM61<=$4154`, coolant `$0006 >= $4159`, TPS `$01D9 > $4156`, and `abs(TPS-byte01DE)<=$4157`. Compute an additional correction with `L2(min(128,R8(RPM62,171)),TPS>>1,$4558)`. Add MAP with saturation, store the target at `$02F3`, and filter with `$4158`. A failed estimate holds the old word if its high byte is nonzero; a zero high byte selects the default `$4E68<<8` instead. The direct MAP route also uses the filter.

Convert the resulting BARO high byte `b` to `$01CC`: return143 if `b<13`; otherwise `R8(151,b-13)`. Four offset lookups use this coordinate:

| Output | First-knot address | Input |
|---|---|---|
| `$01E4`, TPS AE factor | `$4B60` | `max(01CC-96,0)` |
| `$01E3`, rapid-TPS PE threshold | `$4C89` | Same |
| `$01CD`, PE low-RPM threshold | `$4975` | Same |
| `$01CE`, normalized-load divisor factor | `$49D1` | Same |

### TPS and coolant

`$B1CF-$B1EF` computes the effective TPS zero as `hi(u16(word02F6+128))`; subtract it from raw byte `$00A6`, flooring at zero. With delta `d`, the result is `hi(sat16(4*(d*C[$5B26]+32)))`. It stores `$01A6` and returns A. Fuel saves the old `$01D9` at `$01DA`, calls this helper, then stores the result at `$01D9`; `$0098 bit0` substitutes calibration `$5B23` instead. Raw acquisition and learned-zero ownership are explicit inputs.

`$C96A-$C9BF` indexes a 256-byte conversion table with raw coolant `$082D`: use `$FC45` when `$0043 bit7` or `$004E bit0` is set, `$FD45` when both are clear. Store converted byte `$00A8`. Above120 clear `$004E bit0`; at/below106 set it; between those thresholds retain it. If any `$0016&$60` is set, substitute `$5B1A` when runtime word `$00FD>$5B18`, otherwise `$5B1B`; store effective coolant at `$0006`. Clear first-conversion flag `$0043 bit7`, then produce `$0283=min(max(coolant-16,0),192)`.

The neighboring `$C9C0` filter/diagnostic of `$00A9` belongs to a separate temperature-monitor path; it does not replace `$0006` in the equations here. MAT `$022F/$0230`, battery `$0055/$00A7`, VSS `$0284` and switch/gear flags retain their stated input ownership.

### Load coordinates, `$A466-$A4B2`

```text
d = byte02F4 - MAP01C6
if d <= 0: d = 1
01C9 = u8(-K2R(151,d))
01C0 = K2R(151,max(MAP01C6-26,0))
q = Q(word0257, byte01CE<<8)
01CF = hi(sat16(2*max(q-8192,0)))
```

`$01C9` is the byte encoding of a negative vacuum-related coordinate; callers sometimes use it directly and sometimes negate it as a byte. It is not interchangeable with `$01C0` load or `$01CF` normalized load. These producers run in the even group, while density below runs in the odd group, so `$01CF` can consume the previous admitted density sample.

### Period and RPM, including the alternate path

At `$A5E5`, sample `$3FC0` into word `$01E8` and `$005F`. Set `m=u8(32*C[$4141])`. If nonzero, replace `$005F` with `M(m,period)`; otherwise retain it. Stock `$4141=8` makes m zero. Compute `R=Q(307,u16(2*word005F))` and store `$083D`. That divisor double wraps; it does not saturate.

| Output | Exact production |
|---|---|
| Byte `$0061` | For `hi(R)<96`, high byte of `max(2*R-8064,0)`; otherwise `hi(R+$4080)`, capped at255 on word carry |
| Byte `$0062` | `min(255,(R+128)>>8)`; `SBCA #0` after the add preserves255 at the top overflow boundary |
| Word `$028E` | `lag8(byte0062,old028E,C[$50E4])` |
| Byte `$028D` | When `(phase&$1F)==$04`, subtract old `$028C` from `hi(u16(028E+128))` with byte wrap; then update `$028C` to that rounded byte |
| Byte `$0067` | `min(255,(4*R+128)>>8)` |
| Word `$0068` | Target `0067<<8`; if old word zero store directly, otherwise `lag16(target,old,C[$4517])` through `$F479` |
| Byte `$0837` | `hi(sat16(2*R))` |
| Word `$0063` | Target `sat16(2*R)`; if old word zero store directly, otherwise `lag16(target,old,C[$4153])` |

Reference IRQ copies `$0068` to `$006A` on its non-fuel-running route. The separate ratio `$006C` is an input to idle/transient controllers, not an alias of these filter words.

Before normal spark admission, `$AC51-$ACA6` is a real alternate producer. With `$0044 bit3` set it samples/scales the period and calculates `$0061/$0062` using the same quotient and coordinate formulas, but does not update `$083D`, the normal RPM filters or the spark output. With bit3 clear it only sets `$005F=$FFFF`. Both exits clear `$004B bit4` and `$0050 bit2`. The source index candidate at `$B968` is lookup data, as proved in the closure index; it does not add a third RPM producer to this reviewed flow.

## Density, charge temperature and VE

At `$7E40-$7E4E`:

```text
word0257 = Q(byte01C6,694) + 2649
```

The byte numerator is zero extended. With produced MAP bytes this density word is at most26728.

At `$E2C8-$E2FA`, charge-temperature input is coolant unless `$400B bit6` enables MAT blending. When enabled:

```text
k = L1(hi(word0232),$4AE3)
d = max(coolant0006-MAT022F,0)
temperature_index = sat8(MAT022F + floor(2*k*d/256))
t = L1(temperature_index,$4AF4)
word0236 = (t<<7) + $7480
```

On the disabled branch, use coolant as `temperature_index`. The two possible overflow tests in the blend both force255. The denominator is in `[29824,62464]`, nonzero and greater than the maximum produced density numerator. This establishes validity of the first running-fuel FDIV for states from these producers; it does not assert validity for arbitrary corrupt RAM. `$0232` is the period-normalized air quantity produced downstream, so this is a stateful feedback input, not a fresh sensor.

### VE geometry and selection, `$7F86-$7FD7`

Transform load L=`$01C0` to B: `B=L` for `L<=64`, otherwise `B=ceil(L/2)+32`. Select open VE when TPS `>=C[$48DA]`, VSS `>=C[$48D8]` or RPM62 `>=72`; otherwise select idle VE.

| Table | Header / first data | A row coordinate | B column coordinate / shape |
|---|---|---|---|
| Open VE | `$49D5`: `10 00 0B`; data `$49D8` | RPM62; raw knots16,32,…,256 | Transformed load; 16 rows ×11 columns |
| Idle VE | `$4A88`: `20 00 0B`; data `$4A8B` | `min(byte0063,144)`; raw knots32,48,…,144 | Same load transform; 8 rows ×11 columns |

The 11 transformed-load knots are0,16,…,160, corresponding to original load coordinates0,16,32,48,64,96,128,160,192,224,256. The conventional calibration labels are20,25,30,35,40,50,60,70,80,90,100 kPa. Open RPM labels are400…6400 in400 steps; idle labels400…1800 in200 steps because its input is the high byte of the doubled/filtered RPM coordinate. Raw coordinates and bytes are the authoritative mapping.

At idle's maximum A=144 the interpolation reads an adjacent row beginning at `$4AE3`, with zero row fraction. Record the actual reads; do not infer an extra VE row or an implicit helper clamp. VE is stored at `$0231`.

Open selection sets `$004F bit3`. On returning to idle, if that old bit was set and INT `$020F<=$490F`, set `$004F bit5` to request an O2 reset, then clear bit3. Selection uses the input TPS/VSS/RPM thresholds, rather than simply reusing idle flag `$0050 bit7`.

The downstream contract continues from `$7FD8`: density/temperature quotient, cylinder factor `$4D94`, VE multiplication, air charge `$0234`, period-normalized `$0232`, AFR and injector-flow division, and all pulse-width corrections/output routes.

## Fuel-mode admission and histories

Fuel `$7D4B` runs on ordinary odd phases. It has stop/crank/running branches before the VE/air equation:

- With ignition-off `$0044 bit4`, word counter `$027E<8` skips the stop reset. At8 or above, clear `$0004&$83`, `$0019&$60`, runtime word `$00FD`, pulse word `$024C`, RPM62, `$02CD/$02CE/$0268`, running bits `$004F&$90` and related startup flags; set `$0051 bit3`. Once `$027E>=W[$4009]`, write `$3039=$08`, load CC from `$50`, and enter STOP. Otherwise increment/store the counter.
- On ignition returning, a previously set `$0051 bit3` clears that bit, `$0046 bit7`, `$0044 bit3`, `$003E bit3`, `$0223/$027D`; set `$0086 bit3` and restart `$027E` at zero via `$FFFF+1`.
- `$004F bit4` selects the running equation. It is qualified separately from spark's `$004F bit7`; see the spark admission contract. With fuel-running clear, seed histories `$01C7=load<<8`, `$01DE=$01DC=TPS<<8`, calculate crank `$02CF`, and route crank delivery below.

Both crank and running call `$AE5C`. This is a **fuel authorization latch**, not a flag for every new REF. With `$400D bit6` clear it sets `$003D bit1`. With the bit set and the latch not already set, compute the wrapped input-capture difference `read16($3012)-old0851`; a zero difference leaves the state unchanged. A nonzero difference saves the new capture baseline and sets the latch only when `W[$518D]<=difference<=W[$518B]`. The latch has no local clear, apart from initialization/other owners. On the running route, a clear latch commands zero by jumping to `$84F5` before AE/VE. The nonrunning route still calculates crank fuel after calling it.

When `$400F bit0` is set, `$7E3D` calls `$90D3` before density production. This is the separate governor/throttle-state interface named in the closure index.

## Acceleration enrichment

### MAP AE, `$7EB2-$7F20`

Compute `delta16=(load01C0<<8)-word01C7`. A borrow or zero clears `$01CA`, `$023E` and `$0005 bit7`. Otherwise `$01CA=hi(u16(delta16+128))`. Select threshold `$48C0` at idle (`$0050 bit7`), otherwise `$48BF`; TPS `<= $48C1` doubles that threshold with saturation. A delta byte at/below the effective threshold clears AE and its flag, retaining the measured `$01CA`.

For an active event:

```text
a = S1(delta_byte,$4B49)
if TPS > C[$48C2]: a = sat8(2*a)
a = K2(a,H1(RPM62,$4BA4,offset=16))
023E = min(255,floor(a*byte023D/32))
```

Set `$0005 bit7`. The downstream running-fuel path adds byte `$023E` directly to the synchronous pulse-width word; it is not another VE multiplier.

### TPS AE, `$7F21-$7F85`

Require a positive TPS difference from high byte `$01DC`. If fractional history byte `$01DD` has bit7 set, decrement that difference; zero then exits. A previously clear `$0005 bit6` requires difference `>$48C3`; an already active event bypasses that entry threshold. Double the difference with saturation and look up `$4B4F`:

```text
a = L1(sat8(2*d),$4B4F)
if VSS0284 < C[$48C5]: a = K2R(a,C[$48C4])
023F = K2R(a,byte01E4)
```

Set `$0005 bit6`. A failed entry stores zero `$023F` and clears the bit. Update the TPS AE history `$01DC=lag8(TPS,old01DC,byte01E5)` only when phase bit1 is set on this odd-group path. Fuel's downstream async reservoir separately consumes this contribution and its temperature gain.

### Environment gains and decel histories

| Producer | Result |
|---|---|
| `$E30B-$E339` | `$0242=S1(coolant,$4B16)`; `$023C=K2(L1(coolant,$4B71),L1(MAT022F,$4B82))`; `$023D=L1(coolant,$4B93)` |
| `$C9F7-$CA0F` | `$01E5=L1(0283,$4B64)`; `$0243=L1(0283>>1,$4C8D)` |
| `$CA10-$CA32` | `$0272=L1(min(coolant,192),$4BAD)`; subtract `$48E8` with zero floor unless `$003F bit6` set or coolant `>$48E3` |
| `$CA33-$CA4B` | `$01CB=L1(0283,$4B3C)`; `$01BB=H1(coolant,$475F,offset=80)` |
| `$8DEF-$8E1C` | If `$0240` nonzero decrement it. Otherwise reload `$48C8`, update `$01DE=lag8(TPS,old01DE,$48C9)` and `$01C7=lag8(load,old01C7,$01CB)` |

These are distinct histories: fast TPS AE `$01DC`, slower decel TPS `$01DE` and load `$01C7`. Their rates and retained fractional bytes determine thresholds.

## Startup and additional AFR/spark states

`$E33C-$E476` runs only on slot F with phase bit4 clear; `$E306` returns earlier on the other half. With fuel-running `$004F bit4` clear, and `$0004 bit3` clear, reseed:

| State | Seed |
|---|---|
| `$02C8`, startup AFR subtraction | `L1(coolant,$4C33)` |
| `$02CB`, startup spark adder | `S1(coolant,$452C)` |
| `$02CC`, spark hold count | `S1(coolant,$4536)` |
| `$02C9`, additional AFR magnitude | `L1(coolant,$4C9D)` |
| `$02CA`, startup AFR hold count | `C[$4929]` |

Even if `$0004 bit3` suppresses those five seeds, the nonrunning route refreshes `$0267=L1(coolant,$4CAE)` and `$01FF=S1(coolant,$4540)`, then skips decay.

With fuel-running set, update the low nibble of `$003F` atomically, preserving the upper nibble: bit0 indicates borrow in `old0066-byte0063`, bit1 indicates its absolute magnitude `>=$4954`, bit3 indicates IAC effort `$0858>$4FBE`, and bit2 copies `$0036 bit7`. Save byte0063 at0066. O2's idle P selection consumes these bits and may XOR bits0/2 later.

Startup AFR decay follows this priority:

1. If `$02CA` nonzero, decrement it and skip AFR decay.
2. If `$02C8` zero, skip it. A nonzero `$027D` hold decrements unless it equals `$4959`, coolant `<=$4957`, and `$0041 bit5` is set; that combination holds it unchanged. If decrement reaches zero, set `$003E bit3`; if it remains nonzero, skip reduction.
3. If `$0270` nonzero, decrement it. Otherwise reload it with `K2(L1(coolant,$4C44),L1(min(hi(0232),64),$4C55))`, and replace `$02C8` by `hi(old02C8*C[$4928])`, **without rounding**. If `$003E bit3` is clear, this new value `<=$4958` and coolant `<=$4957`, also load `$027D=$4959`.

Startup spark decay then executes separately. A nonzero `$02CC` decrements only at full phase `$0F` and prevents adder decay for that call. With `$02CC=0` and `$02CB!=0`, decrement nonzero `$0200`; otherwise reload `$0200=L1(min(hi(0232),64),$44D0)` and set `$02CB=hi(old02CB*byte01FF)`, again truncated.

Additional AFR magnitude `$02C9` decays on REF events at `$7650`, only while it is nonzero and fuel-running is set. Increment `$0268` up to255. Form `a=L1(coolant,$4CBF)` and `b=L1(transformed02CE,$4CD0)`; `transformed02CE` is two byte left shifts, forcing255 only if the **second** shift carries. Original bit7 is discarded; original bit6 forces255. If `hi(a*b)<$0268`, increment byte `$081E`; when it reaches `$4964`, clear it and set `$02C9=max(old02C9-$0267,0)`.

Boot `$7393-$73FE` copies raw MAP to `$01C6` and high `$01C3`, then uses `K2R(151,u8(rawMAP-26))` for `$01C0` and high `$01C7`. Unlike the running load conversion, that boot subtraction has no zero-floor branch. `$C614` supplies the held/default BARO path. Boot calls the coolant/gain producers, records starting coolant at `$0282`, seeds O2 bytes `$01D5/$01D0/$01D2` from `$48BE`, and seeds TPS-history high bytes. Hot-restart flag `$0004 bit4` is cleared then conditionally set when the saved old coolant is `>=$495A` and new coolant `>=$495B`. A conditional boot route at `$744F` loads `$02CE=$4D96` when `$0004 bit3` is set. Full word initialization follows the retained-memory rules in the closure index.

## Commanded AFR, `$891E-$8A8A`

Start with stoichiometric byte `$48E7`. If any `$003E&$A0` is set, store it immediately; `$400D bit0` clear bypasses startup subtraction/filtering. With that bit set, coolant `>$48D1` uses stoich through the startup path; otherwise use the open-loop table. With `$003E&$A0` zero, use the table directly.

The open-loop mode byte is `$4BBA`; zero selects vacuum `$01C9`, nonzero load `$01C0`. Use `L2(min(coolant,192),selected>>1,$4BBB)`, first data `$4BBE`. Subtract `$02C8` with zero floor. Entry idle flag `$0050 bit7` caps AFR at `$0272`, reloads `$0266=60` and stores `$0264=AFR<<8`. Otherwise decrement a nonzero `$0266`; while it was nonzero, a requested AFR above high `$0264` is filtered with `$48EC`, storing the word and a saturated rounded high result. Requests at/below the old high byte, or an expired hold, store the new target directly at `$0264`. Store this base at `$024A`.

Re-evaluate idle with inclusive `VSS<=$48D9` and `TPS<=$48DA`. On leaving idle, runtime `$00FD>=$48E0` sets `$003F bit6`; clear `$0050 bits $82` and `$0271`, then reload base AFR. At idle set bit7. If idle target `$0272` is greater than base AFR, keep the already richer base and reset warm-idle bit1/timer. Otherwise:

- Coolant `<=$48E2`: set `$0050 bit1` and use `$0272` immediately.
- Warm, `$48DE!=0`: unless `$400B bit1` is set, `$0041 bit5` blocks qualification and resets bit1/timer. If bit1 was already set, use idle target only after `$0271>$48DF`; until then retain base and increment the timer only at full phase `$27`. If bit1 was clear, require `$0271>$48DE` before evaluating INT stability.
- `$48DE=0`, or that entry delay passed: require `abs(INT020F-128)<=$48F8` to set bit1 and clear the timer. This call keeps base AFR; later calls apply the selected idle target. An unstable INT increments the timer only at phase `$27`. Timer INC is byte wrap, not saturation.

Next, when `$003E bit7` is clear, hot-restart `$0004 bit4` subtracts `$495C` with zero floor. In the strict coolant interval `($48E4,$48E5)`, `$0041 bit5` subtracts `$48EB`; otherwise, while `$082C<=$48E6`, increment `$082C` with saturation and subtract `$48EA`. Apply upper cap `$4913`, or `$4E7B` when `$0072 bit6` set. **After this cap**, if REF count `$0268>=$495F`, apply `$02C9`: subtract with zero floor when coolant `<=$4961`, add with saturation above it. Store `$024A`.

If fuel-running is clear, skip PE and the running final overrides, copying `$024A→$024B` before BLM selection. It is incorrect to model all these paths as a single stoich/PE switch.

## Power enrichment, `$8A92-$8C37`

Permission `$003D bit0` is set and `$0263` cleared when VSS `<$4921` and TPS `<=$4922`. Otherwise, if `$0263<$4923`, increment it and set permission. Reaching the limit does not clear permission at this point; the exit below clears it.

Three RPM curves use `H1(RPM62,header,offset=32)`: `$4C5A→$01E0` upper TPS shape, `$4C7F→$01E1` exit-count decrement, `$4C64→$01E2` entry threshold. If PE `$003D bit5` is already set, lower the entry threshold by `$4917` with zero floor. TPS must be **greater** than that effective threshold or take ordinary exit.

Above threshold, take full gain255 when the existing `$003F bit5` is set; when positive `byte0063-byte0065>$4914` (also latch that bit); when coolant is outside `($4915,$4916]`; or RPM62 `>=$4918`. A nonnegative `TPS-byte01DB >= byte01E3` also latches `$003F bit5` and takes full gain.

On the remaining gradual route, RPM62 below `$01CD` rejects a new entry, but does not reject an already active PE. A clear permission bit selects the vehicle-change exit below. Otherwise compare old `$0277` with `$491A`, increment a byte candidate, and only when the old value reached the threshold add `$491B` to gain `$0278` with saturation and clear `$0277`. Full-gain routes also clear `$0277`. Set PE `$003D bit5`.

Target starts at `L1(RPM62,$4C6E)`. When `$0269<=$491D`, increment `$0269` only at full phase `$07`. During this hold, if RPM `<$4918`, coolant in `($4915,$491E]`, and TPS `<=$01E0`, add a TPS-shaped target offset:

```text
n = max(TPS-01E2,0)<<8
d = max(01E0-01E2,0)<<8
r = hi(Q(n,d))
target = sat8(target + max(C[$4925]-R8(r,C[$4925]),0))
```

Invalid or equal fractional divides use the defined `$FFFF` quotient, not a made-up remainder. Cold addition then subtracts `$4924` with zero floor if coolant `<=$491C`, RPM `<$491F` and VSS `<$4920`. If current `$024A` is already at/below target, retain it; otherwise store `AFR-R8(0278,AFR-target)`. This same `$0278` is the PE spark gain.

Ordinary exit compares old `$0276` to `$4919`; when old count reached it, clear gain `$0278` and PE hold `$0269`, without storing the increment candidate. Before that threshold, save the increment only at full phase `$17`. Clear `$003D bits $21` and `$003F bit5`.

The vehicle-change exit instead compares word `$0818` with `$4926`. Below it, use ordinary exit. At/above it, `$0276=0` sets permission and rejoins PE entry, clearing `$0277` while retaining gain. Otherwise decrement `$0276` by1 when TPS `<=$01E0`, or by `$01E1` with zero floor above that TPS threshold; store only at phase `$17`, then clear the exit flags. `$0818=abs16(word0284-old081A)` is sampled only at phase `$9F`, updating baseline `$081A` then.

At `$8C38`, save TPS to `$01DB`. `$0052 bit6` caps AFR at `L1(hi(0232),$4999)` when that is richer. Service `$003B bit4` plus `$0395 bit2` replaces AFR with `$0397` and skips the extension. Otherwise `$0086 bit6` calls unknown `$1800`. Copy the resulting `$024A` to `$024B`. [BLM selection/learning](FACTORY_CLOSED_LOOP_AND_LEARNING.md) follows on both running and nonrunning AFR-task routes.

## Crank equation and delivery

### Main-task equation, `$858B-$8612`

The dedicated period coordinate samples live `$3FC0`, applies the same optional multiplier `u8(32*$4141)`, then returns zero if the resulting period is zero; otherwise `r=min(127,hi(Q(614,period)))`.

```text
pw = M(L1(coolant,$4D9C),W[$4D9A])
if byte02CE > C[$4D95]:
    table = $4DB6 if hot_restart_0004_bit4 else $4DAD
    pw = M(L1(r,table),pw)
pw = M(L1(max(BARO01CC-96,0),$4DBF),pw)
pw = sat16(2*pw)
if that double overflowed: return $FFFF immediately
pw = M(S1(TPS,$4DC3),pw)
return sat16(4*pw)
```

At `$7E66`, the caller doubles this result with saturation into `$02CF`, refreshes battery through `$C56F`, and replaces `$02CF` with `M(L1(byte0055,$4988),02CF)`. It has not used VE, running AFR or injector-flow division.

### Event gain, `$7827-$7859`

If reference count `$02CE>23`, use index `02CE&7` in `$4E26`. Otherwise use index02CE in `$4E0E` for hot restart; without that flag, select `$4DF6` when coolant `>=$4D99`, otherwise `$4DDE`. For table byte g and input pulse p, return `sat16(2*M(g,p))`.

`$400C bit2` chooses where crank delivery happens. Clear: main task admits when `02CD>=L1(coolant,$4DCD)`, applies event gain to `$02CF` and enters `$84F5`, bypassing running short-PW shaping but using the existing final offset/output route. Set: main task jumps to its scheduled tail without that delivery; REF handles it instead.

### REF delivery and counters, `$750F-$764F`

REF sets `$0050 bit5` unless ignition-off `$0044 bit4`; with `$0050 bit0` it samples MAP into `$082E`. Fuel-running jumps to the additional-AFR event routine instead. Nonrunning copies `$0068→$006A`, then increments `$02CD` up to255 unless ignition-off. REF requires `02CD>L1(coolant,$4DCD)`, a **strict** comparison differing from the main task. Rejected events clear the relevant capture flag and jump to shared IRQ continuation `$77C6` without the following delivery/count update.

With `$400C bit2` set, apply event gain to `$02CF` and store `$024C`. `$400B bit4` clear calls the async helper `$8548` with that packet. With bit4 set and `$0019 bit6` set, halve `$024C` then call async. Otherwise add byte `$0256` with word wrap, force `$7FFF` only when the result has bit15 set, and store `$0250` for the alternate timer route.

Stock `$400C=$B7` has bit2 set, and `$400B=$04` has bit4 clear: **stock crank fuel uses REF-triggered async delivery**, not the ordinary running `$3FCE` write.

The optional timer route is also resident and decoded. With `$3023 bit0` clear, count02CD=1 sets `$0053 bit5`; later calls with that latch scale `$0250` by `sat16(2*M(C[$4960],0250))` and decrement `$02CE` with zero floor. Set `$3020&$03` and `$300B bit3`, then call bank/output helper `$785A`. Compute `candidate=u16(sat16(2*0250)+read16($300E))`, save `$0825`, clear `$3020 bit0`, and write `$301E`: choose `u16(fresh300E+2)` when its subtraction from candidate has N clear, otherwise candidate. This is an N-only test.

With `$3023 bit0` set, acknowledge `$3023=1`, clear `$084E`, set `$3020&$0C` and `$300B bit4`, clear `$0053 bit5`, calculate the same candidate into `$0827`, clear `$3020 bit2`, and write the corresponding selected value to `$301C`. The bank helper and timer electrical behavior remain hardware interfaces; the candidate arithmetic and local write choices are recorded.

After either delivered route, or with `$400C bit2` clear, increment byte `$02CE`; a wrap to zero is replaced by `$F0`. If battery `$0055<=$4D98`, cap it at `$4D97`. This counter is not an unlimited reference-event total. Shared IRQ continuation and run-side REF handling beyond the documented event routine retain their own scope.

## EGR terms feeding fuel and spark

`$CF16-$D03D` calculates desired command `$01AE`. Qualification uses the block at `$46F9` (offsets below); failure supplies zero to the final command checks.

| Check | Qualification / state |
|---|---|
| MAT mode `$400B bit6` | Require `$0230` greater than offset3, or offset4 when `$006E bit7` was set |
| Coolant | Starting coolant `$0282>offset0` selects minimum offset2, otherwise offset1; effective coolant must reach it |
| Diagnostics | Any `$0018&$30` inhibits |
| Load | `$01C0>offset10`, or offset11 with old `$006E bit4`; success sets bit4, failure clears it |
| TPS lower bound | Unless `$006F&$24` nonzero, TPS `>offset8`, or offset9 with old `$006E bit5`; success sets bit5, failure clears it |
| RPM | RPM62 `<=offset6`, or offset7 with old `$006E bit6`; success sets bit6, failure clears it |
| VSS | Require VSS `>=$46FE` unless `$0016 bit4` set |
| Vacuum | `$01C9<=offset13`, or offset12 with old `$006E bit2`; success sets bit2, failure clears it |
| Final checks | TPS `<=offset14`, AFR `>=offset15`, DFCO `$0046 bit3` clear; `$400D bit3` optionally also requires `$003E bit7` |

Mode prefix `$470A` chooses B:2→normalized load `$01CF`,0→vacuum `$01C9`, other→load `$01C0`. Base `L2(min(RPM62,160),B>>1,$470B)` is multiplied with `K2` first by coolant factor `$01BB`, then by `L2(load>>1,BARO01CC,$4767)`. Below `$4709`, or with `$0051 bit4` or `$0072 bit5` set, force0. Store `$01AE`. Extension `$1815` is called when `$0086 bit6` set; afterward service `$003B bit4` plus `$0393 bit1` can override `$01AE=$0394`.

`$D03E-$D14D` produces filtered EGR fraction word `$01B2`. Define `V(x)=2*x` for `x<=64`, otherwise `min(192,((x-64)>>1)+128)`, with x=`u8(-01C9)`.

- `$400D bit5` or bit2: clear `$006E bit7`; `$0070 bit0` supplies target0. Otherwise bit2 of `$0070` bypasses the actual-duty test; without it require actual duty `$01AF!=0`, setting `$006E bit7` on success. Target is `L2(min(RPM62,160)>>1,V(x),$478A)`.
- Other calibration mode: clear `$006E bit7`; `$0070 bit0` or `$0072 bit5` supplies zero `$01B1`. `$0070 bit2` bypasses duty qualification and uses desired `$01AE` directly. Otherwise, `$400D bit1` selects position `$01B9` with minimum `$485A` and runtime minimum word `$485B`, optionally inhibited by `$400D bit4` plus idle flag; without bit1 require actual `$01AF>=$485D`. Passing qualification sets `$006E bit7` and selects `$01B9` for bit1 mode or `$01AE` otherwise.

For the latter mode, scale selected base by `R8(160,base)`. Let `d=sat8(L1(hi(0232),$47D3)+x)` and store `$01B0`. Column coordinate is d below64, otherwise `min(144,((d-64)>>1)+64)`. Store `$01B1=L2(scaled_base,column,$47E5)`. Divide `ceil(byte01B1*C[$47E4]/2)` by word0232 with `Q`, then take its saturated rounded high byte to obtain target. A zero denominator yields the defined `$FFFF` quotient, even when a disabling branch supplied a zero numerator.

For both modes, replace target with `R8(target,L1(max(BARO01CC-96,0),$4856))`, then `lag8` with old `$01B2` and gain `L1(min(hi(0232),64),$47CE)`; store the word. Thus a disabled command does not imply immediate zero fraction. Fuel's exact consumer uses the fraction for fresh-air displacement; spark uses its separate term and enable flag, as documented in the handoff/spark contracts.

## Battery-dependent scheduling state

The fuel-tail helper `$8613-$863C` uses raw battery `$00A7`: below40 sets ignition-off `$0044 bit4` and clears REF/MAP-sampling `$0050 bit0`;40 through89 holds these states. At90 or above, a previously set ignition-off bit seeds capture baseline `$0205` from `$3FCA`, then clears ignition-off; `$400C bit0` optionally sets the sampling bit. This helper's raw battery counts do not establish volts.

The slot-F prelude `$E286-$E2C7` is separate from the charge calculation: when `$5B04 bit2` is enabled it clears `$001A bit2`, immediately sets it again if `$0072 bit0` is latched, and otherwise only qualifies the later battery tests when `$00A7>=$4E88`. With `$0072 bit1` set it requires fuel-running and `$0055<$4E87` before setting `$001A bit2`. Without bit1 it increments byte `$022A`; new count `>$4E85` latches `$0072 bit0` and sets `$001A bit2`, otherwise `$0055>=$4E86` latches `$0072 bit1`. Failed tests leave the bit cleared by this invocation; the disabled calibration route retains it. These are local scheduling/qualification state effects, not a proof of the full electrical diagnostic or of all consumers of `$001A bit2`.

## Review boundary

The resident upstream calculation and local state behavior above are documented. O2/BLM producers are completed in their companion contract. Raw acquisition, full IAC/governor/transmission/diagnostic state machines, low-memory extensions, complete IRQ/output-service behavior and physical-unit interpretation remain explicit interfaces in the closure index. No simulator feature or new bench result is required to mark these bounded documentation rows complete.
