# $31 ALDL Live-Serialization Timing Contract

## Purpose

Document the fact that `$31` 8192-baud ALDL engine data is **not an atomic snapshot**. Each output byte is dereferenced from live RAM at the time that byte is transmitted. This matters whenever causality is inferred from adjacent ALDL columns or rows during fast events such as knock, transient fuel, BLM-cell changes, VSS glitches, DFCO, or RPM/load transitions.

## Classification

```text
ALDL-LIVE-DEREFERENCE:       CONFIRMED STATIC
ALDL-FIELD-ORDER:            CONFIRMED STATIC/CALIBRATION
8192-BYTE-TIME:              PROTOCOL/ARITHMETIC
ROW-ORDER-CAUSALITY LIMIT:   CONFIRMED CONSEQUENCE
```

Primary source:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

## 1. Transmitter reads live RAM while sending

The SCI transmit ISR enters `LF822` and advances through the selected ALDL message definition.

For table-driven live-RAM entries, the transmitter resolves the pointer and then dereferences RAM during transmission:

```asm
F822: LDX   L0362       ; current 8192 data/message control block
F825: LDAB  L0360       ; message-length counter
...
F886: ASLB
F887: ABX
F888: LDX   $0009,X     ; pointer-table base
...
F8B0: LDX   0,X         ; selected live-data pointer
...
F8B8: CPX   #$1000
F8BB: BCS   LF8DC
F8BD: CPX   #$3FFF
F8C0: BHI   LF8DC
F8C2: XGDX
F8C3: BRSET L0050,#$08,LF8C9
F8C7: ANDA  #$00CF      ; normal $31xx -> $01xx alias handling
F8C9: XGDX
F8CA: LDD   0,X         ; LIVE RAM READ OCCURS HERE
F8CC: STAB  L0366       ; save companion byte for two-byte item
...
F8D4: BCLR  L003B,#$80
F8D7: LDAA  L0366       ; transmit companion byte on next byte slot
...
F8DC: LDAA  0,X         ; direct live byte read for other address ranges
```

There is no preceding operation that copies all 64 data fields into a coherent snapshot buffer before transmission.

Therefore:

```text
ALDL row != one instantaneous PCM state
```

Instead:

```text
ALDL row = sequence of live RAM observations spread across serial transmission time
```

## 2. Relevant engine-message field order

The mode-1/0 engine message definition begins at `$51EF` and specifies 64 output data bytes.

Relevant entries are:

```text
31  FILTMPH     -> $0284   filtered vehicle speed
34  NTRPMX      -> $0062   RPM/25
45  SAREFFNL    -> $31F0   final spark MSB
46  SAREFFNL+1  -> $31F1   final spark LSB
49  INT         -> $020F   closed-loop integrator
54  BLMCELL     -> $0247   active BLM cell
55  BLM         -> $0248   active BLM multiplier
56  NOCKRTD     -> $020C   normal knock retard
57  BPW MSB     -> $324C   base/synchronous PW display word
58  BPW LSB     -> $324D
```

The `$32xx` BPW alias follows the same ALDL address-remap mechanism used by `$31xx` aliases before live RAM dereference.

## 3. Intra-message timing skew at 8192 baud

With normal asynchronous serial framing of one start bit, eight data bits, and one stop bit:

```text
10 serial bits / byte
```

At 8192 bit/s:

```text
one transmitted byte ~= 10 / 8192 s
                     ~= 1.2207 ms
```

Approximate age difference between selected fields in the same engine message:

```text
VSS byte 31 -> INT byte 49:       18 bytes ~= 22.0 ms
VSS byte 31 -> BLM cell byte 54:  23 bytes ~= 28.1 ms
VSS byte 31 -> BLM byte 55:       24 bytes ~= 29.3 ms
VSS byte 31 -> BPW byte 57:       26 bytes ~= 31.7 ms
```

The exact host-log timestamp convention may add further ambiguity because software may timestamp at message start, completion, or after combining message pages. The static conclusion does not depend on host timestamp behavior: **the PCM itself reads these fields at different times.**

## 4. Consequence for VSS/BPW causality

Suppose the PCM transmits byte 31 while filtered VSS is still 9 mph:

```text
t0: byte 31 reads L0284 = 9 mph
```

If a VSS glitch occurs immediately afterward:

```text
t0 + 5 ms: L0284 becomes 255 mph
```

engine-control code can react to the new `L0284` during the following scheduler activity.

When the ALDL transmitter later reaches BPW:

```text
t0 + ~32 ms: byte 57 reads the now-modified BPW state
```

The resulting host row can therefore contain:

```text
VSS = old value
BPW = value calculated after the new VSS state
```

On the next message, VSS may finally appear as 255 mph.

Thus this apparent log ordering:

```text
row N:     VSS normal, BPW drops
row N+1:   VSS spikes
```

**does not prove that BPW changed before the VSS event internally.**

## 5. Filtered VSS is an actual engine-control state

The logged vehicle-speed field is not merely a scanner-side calculation.

Raw/new VSS is held in:

```text
L0812
```

and the stock VSS filter explicitly produces:

```asm
D4DA: LDD  L0812       ; new MPH
D4DD: LDX  L0284       ; old filtered MPH
D4E0: LDY  #$4E8E      ; VSS lag-filter coefficient
D4E4: JSR  LF436       ; lag filter
D4E7: STD  L0284       ; save filtered MPH
```

`L0284` is then used directly by engine-control code, including:

```text
7F45   low-speed TPS acceleration-enrichment modifier
7F9A   closed-throttle VE / idle-logic qualification
80C5   MPH overspeed/fuel-cut logic
8213   DFCO speed qualification
82BC   decel-enlean speed modifier
899B   AFR/startup/mixture-related logic
8A92   PE delay/bypass logic
8BCF   cold-PE logic
8C79   PE speed-delta bookkeeping
8CA0   idle BLM-cell speed qualification
...    additional spark/governor/diagnostic paths
```

Therefore a nonsensical logged `L0284` value such as 255 mph is evidence that the PCM's own filtered vehicle-speed control variable is nonsensical at the instant it was transmitted.

The separate low-speed abuse path at `8073` uses raw `L0812`, so both raw and filtered VSS can affect engine behavior through different branches.

## 6. Interpretation rule for road-log reconstruction

For slowly changing steady-state periods, treating columns in one row as approximately simultaneous is usually acceptable.

For fast transitions, do not infer exact cause/effect ordering from column position or row number alone.

Preferred evidence order:

```text
1. static executable dependency/order proof
2. calibration thresholds and state-machine requirements
3. sustained multi-sample log behavior
4. field-order-corrected timing correlation
5. single-row apparent ordering only as weak evidence
```

Where useful, a future replay/analyzer should assign each ALDL channel an approximate **within-message acquisition offset** rather than a single shared row timestamp.

## Source anchors

```text
D4DA-D4E7   raw VSS -> filtered L0284
F822-F8E6   live ALDL transmit/dereference engine
$51EF       mode-1/0 engine-message control block
$5234       field 31 FILTMPH -> $0284
$5258       field 49 INT -> $020F
$5262       field 54 BLMCELL -> $0247
$5264       field 55 BLM -> $0248
$5266       field 56 NOCKRTD -> $020C
$5268/$526A fields 57/58 BPW
```
