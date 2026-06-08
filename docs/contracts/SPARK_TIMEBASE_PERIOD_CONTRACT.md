# Spark Timebase / Period Contract

## Purpose

Classify the timebase variables used between final spark degrees and the `LA906` timing bridge.

## Known Math

`LF550` is confirmed:

```text
LF550(A, M16) = round((A * M16) / 256)
```

Spark path:

```text
A = spark_mag_u8
M16 = [L005F:L0060]
mult = round((spark_mag_u8 * L005F) / 256)
```

## Variables

| Symbol | Static role | Candidate unit | Confidence |
|---|---|---|---|
| `L005F/L0060` | software period basis used as `LF550` multiplicand | timer ticks or scaled REF/DRP period | medium/static |
| `L3FC0/L3FC1` | ASIC timing/period source; comments call it last REF/DRP period counter | DRP/REF period or event anchor | medium/static |
| `L0201` | RPM-indexed latency correction | latency ticks or scaled latency | medium/static |
| `L01EC` | timing correction/work-period state used after LA906 command candidates | time/tick-domain work term | medium/static |
| `L01EE` | current retard / signed spark offset before conversion | degree-domain signed offset | medium/static |

## Required Equation

Provisional:

```text
mult = round((spark_mag_u8 * period_basis) / 256)
D_AB97 ≈ ((mult - latency - period_anchor) >> 4) with sign/high-nibble tagging
```

Expanded current candidate:

```text
period_basis = L005F/L0060
latency = L0201
period_anchor = L3FC0/L3FC1
timing_work = L01EC
spark_mag_u8 = magnitude/sign-transformed L01EE or startup L01F2 path
```

## Static Findings

### 1. `L005F` is the direct spark-path period multiplicand

The spark conversion path loads `X` with `#$005F` immediately before the confirmed `LF550` helper call:

```text
0xAB76  LDX #$005F
0xAB79  JSR LF550
```

Since `LF550(A, [X]) = round((A * M16) / 256)`, this means `L005F/L0060` is the 16-bit multiplicand for converting spark magnitude into a time-domain product.

### 2. `L005F` is written from period/RPM support code

Static rows show:

```text
0xA5CF  STD L005F   ; LAST DRP PERIOD
0xA5E8  STD L005F   ; LAST DRP PERIOD VAL
0xA5FC  STD L005F   ; SAVE 16 BIT RPM VALUE
0xA5FE  LDD L005F   ; LAST DRP PERIOD VAL
```

This supports `L005F` as a software period/work basis, but does not yet prove whether it is raw period, filtered period, reciprocal/RPM-derived period, or scaled period.

### 3. `L3FC0` is the hardware period/event-anchor candidate

Static rows show `$3FC0` being read in RPM/period contexts:

```text
0x858B  LDX L3FC0   ; LAST REF PERIOD CNT'R
0xA581  LDD L3FC0   ; RPM = ((65536 * 120)/8)/CAL
0xA5E5  LDD L3FC0   ; LAST DRP PERIOD CNTR
```

The same hardware source is then subtracted immediately before the LA906 sink:

```text
0xAB8E  SUBD L3FC0
```

That makes `$3FC0` a strong candidate for hardware period/event anchor in the spark conversion path.

### 4. `L0201` is latency correction in the conversion path

`L0201` is produced by the RPM-indexed latency lookup documented in the degree-to-tick dependency contract. This timebase pass captures the actual store/read pair:

```text
0xAB72  STAA L0201
0xAB84  SUBB L0201
```

It is probably in the same pre-shift timing-domain family as the `LF550` product, but bench/emulator verification is still required because only `B` is subtracted and later packing/shift operations follow.

### 5. `L01EC` is time-domain work state, not raw spark degrees

`L01EC` is written and adjusted in the period-support area, then used after LA906 command candidate math:

```text
0xA6EC  STD L01EC
0xA6F5  SUBD L01EC
0xA6FA  ADDD L01EC
0xA6FD  STD L01EC
0xABB3  SUBD L01EC
0xABB7  LDX L01EC
```

That pattern makes it a timing correction/work-period term rather than a degree-domain spark command.

### 6. `L01EE` remains the degree-domain signed offset before conversion

`L01EE` is repeatedly labeled `CURRENT RETARD (2's CMP)` and is loaded at `0xAB1A`, then sign/magnitude handled before the latency lookup and `LF550` period multiply. It is the last clearly degree-domain variable before the bridge into time/tick domain.

## Current Classification

```text
TB-A:
  supported statically. L005F behaves like a raw or scaled REF/DRP period basis.

TB-B:
  possible. L005F also appears in RPM/work-value code, so it may be filtered or derived rather than a direct hardware copy.

TB-C:
  not currently supported; L005F clearly functions as the period multiplicand for LF550.

LAT-A:
  likely. L0201 is subtracted directly from the LF550 output path before LA906.

LAT-B:
  still possible because the later >>4/high-nibble packing step may mean L0201 is pre-shift or scaled.

ANCHOR-A:
  supported. L3FC0 is used as a hardware period/event anchor in the conversion path.

ANCHOR-B:
  not supported by static rows, but bench testing should still verify whether the L3FC0 subtraction affects EST output.
```

## Bench Sanity Targets

Assuming a 1/65536-second timebase only as a test hypothesis:

```text
1000 rpm:
  90°  = 15 ms  = 983 counts
  180° = 30 ms  = 1966 counts
  360° = 60 ms  = 3932 counts
  720° = 120 ms = 7864 counts

2000 rpm:
  90°  = 7.5 ms = 491.5 counts
  180° = 15 ms  = 983 counts
  360° = 30 ms  = 1966 counts
  720° = 60 ms  = 3932 counts
```

If observed `L005F` at 1000 rpm is near one of these values or a consistent 16× / 1/16× version, that will identify the period basis and explain the later `>>4`.

## Required Next Proof

The next bench/static gate is to capture `L005F`, `$3FC0`, `L0201`, and D at `0xAB97` while varying RPM and spark independently:

```text
fixed spark + doubled RPM:
  L005F should roughly halve if period-based

fixed RPM + spark step:
  L005F should stay constant while D_AB97 changes

fixed RPM/spark + latency change:
  L0201 should change and D_AB97 should shift
```

## Stop Condition

Do not write `SPARK_WRITE` until this contract can answer:

```text
For X degrees at Y RPM/ref period, what LA906 input value should be produced?
```
