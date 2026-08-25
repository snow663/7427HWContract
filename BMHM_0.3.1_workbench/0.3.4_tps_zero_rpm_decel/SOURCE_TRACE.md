# Source trace — TPS A/D to learned zero and the 0.3.4 decel-source change

Source authority: stock `$31_HAC.SRC` / `31_HAC_from_ORG_7100_to_end_NOWRAP.html`.

## TPS signal path

The stock TPS path is intentionally adaptive rather than an absolute-voltage idle switch.

```text
TPS sensor
  -> raw A/D L00A6
  -> learned/filtered zero L02F6
  -> raw minus learned zero
  -> TPS gain $5B26
  -> engine TPS L01A6
  -> final TPS L01D9
```

### Raw TPS acquisition

At `$F245-$F24E` the PCM reads the TPS A/D channel and stores the result in `$00A6`.

### Downward zero tracking

At `$B116-$B129`:

```asm
B116  LDAA  L00A6      ; raw TPS A/D
B118  CMPA  L02F6      ; learned/filtered TPS zero
B11B  BHI   LB12C      ; raw above learned zero -> upward/event path

B11D  LDAB  #$80
B11F  LDX   L02F6
B122  LDY   #$5B25
B126  JSR   LF436      ; lag filter
B129  STD   L02F6
```

So if the raw closed-throttle A/D moves downward, the learned baseline can follow it through the stock filter.

## Stock upward TPS-zero learner

The stock upward-learning event is `$B12C-$B15D`.

Relevant stock code:

```asm
B12C  LDAA  L00F7
B12E  SUBA  L00D7
B130  BCC   LB137
B132  BCLR  L009A,#$04
B135  BRA   LB160

B137  BRSET L009A,#$04,LB160
B13B  BRSET L0018,#$02,LB160
B13F  BRSET L0018,#$01,LB160
B143  BRCLR L009C,#$01,LB160
B147  CMPA  L5B2A
B14A  BLS   LB164

B14C  LDAA  L02F6
B14F  ADDA  L5B29
B152  CMPA  L5B24
B155  BLS   LB15A
B157  LDAA  L5B24
B15A  STAA  L02F6
B15D  BSET  L009A,#$04

B160  LDAA  L00D7
B162  STAA  L00F7
```

### What `$00D7` is

At `$B2A3-$B2AF` the source explicitly identifies `$00D7` as the filtered VSS quantity:

```asm
B2A3  STD   L0814

; FILTER Vss
B2A6  LDX   L00D7
B2A8  LDY   #$5D20
B2AC  JSR   LF436
B2AF  STD   L00D7
```

Therefore the stock learner is comparing a retained prior filtered-VSS reference `$00F7` with current filtered VSS `$00D7`.

### Stock event semantics

- If current speed rises above the retained reference, subtraction underflows and `$B132` clears `L009A.b2`, re-arming the learner.
- During deceleration, while the drop is below `$5B2A`, `$B14A` branches to `$B164` **without updating `$00F7`**. The decrease therefore accumulates relative to the retained reference.
- Once the decrease exceeds `$5B2A` and the other stock qualifiers pass, the learned TPS zero `$02F6` is incremented by `$5B29`.
- `$5B24` clamps the learned zero.
- `L009A.b2` is then set so only one upward correction is made during that deceleration event.

This is a carefully bounded one-step-per-event learner, not a continuously chasing zero.

## BMHM 0.3.4 substitution

0.3.4 leaves all of the event/latch structure above intact and changes only the source quantity.

### `$B12E`

```asm
stock:  SUBA L00D7      ; current filtered VSS
0.3.4:  SUBA L0062      ; current engine RPM/25
```

Byte change:

```text
$B12F: D7 -> 62
```

### `$B160`

```asm
stock:  LDAA L00D7      ; update retained VSS reference
0.3.4:  LDAA L0062      ; update retained RPM reference
```

Byte change:

```text
$B161: D7 -> 62
```

`$00F7` is only referenced by this TPS-zero event logic in the traced stock source, so within this function it can safely become the retained RPM reference without allocating new RAM.

## Threshold reinterpretation

`$0062` is the stock RPM/25 quantity. `$5B2A` remains raw `10`.

Thus the same comparator now represents:

```text
10 counts * 25 RPM/count = 250 RPM cumulative drop
```

This is close to the original intent: one upward TPS-zero correction after a meaningful deceleration event, with re-arm after RPM rises again.

## Why not force VSS to zero

A fixed VSS value would create false engine-state semantics elsewhere and would also destroy the event meaning here. 0.3.4 instead changes this consumer to use the engine-domain signal it actually needs: deceleration.

## Remaining caution

This trace proves and removes the known direct filtered-VSS dependency in the runtime upward TPS-zero learner. It does not assert that every speed-derived RAM item in the entire ROM has been eliminated. Future traces should continue to treat VSS consumer-by-consumer.