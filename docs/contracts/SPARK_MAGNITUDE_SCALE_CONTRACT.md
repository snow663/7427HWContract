# Spark Magnitude / Degree Scale Contract

## Purpose

Classify the degree-domain spark variables that become the unsigned magnitude input `A` to `LF550`.

This contract defines the angle side of the spark conversion. It does **not** define a spark writer.

## Known Downstream Math

```text
LF550(A, L005F) = round((A * L005F) / 256)
```

Therefore `A` is the spark angle/magnitude scalar used for degree-to-time conversion.

## Known Sink

```text
0xAB76  LDX #$005F
0xAB79  JSR LF550
```

At this call:

```text
A = spark_mag_u8
X = #L005F
```

## Strongest Static Scale Candidate

The source contains repeated calibration comments that directly identify spark-table and bias units as `SPK ADV 256/90`.

```text
A8xx idle spark correction: TBL = SPK ADV 256/90
CAxx WOT spark correction: TBL = (256/90) * SPK ADV DEG
AA1D initial spark subtract: 3.8 Deg, INITIAL SPK (256/90)
```

Leading candidate:

```text
A_count = round(degrees * 256 / 90)
degrees = A_count * 90 / 256
degree_per_count = 0.3515625°
```

This matches the expected hardware-friendly interpretation where `A=256` would represent one 90° reference window. Bench proof is still required.

## Variables

| Symbol | Candidate role | Candidate unit | Confidence |
|---|---|---|---|
| `L01FD` | final spark advance accumulator | 256/90 degree scale | high static |
| `L01FC` | working/table spark adder predecessor | 256/90 degree scale | medium-high static |
| `L01EE` | signed spark offset into conversion | 256/90 degree scale, two's-complement signed | high static |
| `L01F2` | startup spark override/filter value | 256/90 degree scale candidate | medium static |
| `L004F bit0` | sign flag for conversion | 1=retard, 0=advance | high static |
| `L020B` | low-octane spark retard | 256/90 degree scale candidate | medium-high static |
| `L020C` | knock retard | likely 256/45 stored, halved before subtract into 256/90 path | medium static |

## Required Chain

```text
base spark table / WOT spark table / idle correction tables
→ spark modifiers and bias subtraction
→ L01FD final spark advance
→ subtract initial spark bias L4132 (256/90)
→ L01EE signed offset / current retard
→ burst knock / knock / torque management clamps
→ serial override adjustment if active
→ sign/magnitude handling using L004F bit0
→ A before LF550
→ LF550(A, L005F)
```

## Critical Static Evidence

### Final spark scale and bias

```text
0xA7E7  LDAB L01FC        ; FROM TABLE L44BF
0xA811  SUBB L020B        ; LOW OCTAINE SPK RETARD
0xA81B  STD  L01FD        ; FINAL SPK ADV
0xAA1A  LDD  L01FD        ; FINAL SPK ADV
0xAA1D  SUBB L4132        ; 3.8 Deg, INITIAL SPK (256/90)
0xAA22  STD  L01EE        ; CURRENT RETARD (2's CMP)
```

This says `L01FD` and `L01EE` are in the same degree-domain scale as the initial spark scalar, with `L01EE = L01FD - initial_spark_bias` before later retard/clamp logic.

### Sign and magnitude handling

```text
0xAB44  BCLR L004F,#$01    ; clear sign, 1=retard, 0=advance
0xAB47  LDD  L01EE
0xAB4A  BPL  LAB50         ; positive path
0xAB4C  BSET L004F,#$01    ; negative offset means retard
0xAB4F  NEGB                ; magnitude from low byte
0xAB50  TBA                 ; A = unsigned magnitude
```

So `LF550` receives an unsigned 8-bit magnitude in `A`. `L004F bit0` carries the sign convention into the later add/subtract path.

### Startup override path

```text
0xAB55  LDAB L01F2         ; START UP SPARK
0xAB60  MUL
0xAB61  INCA
```

If the startup-path flag is active, startup spark modifies/replaces the normal magnitude before latency lookup and `LF550`.

### Knock and low-octane retard

```text
0xA78F  STAA L020B         ; LOW OCTAINE SPK RETARD
0xA811  SUBB L020B         ; LOW OCTAINE SPK RETARD
0xAACB  STAA L020C         ; DEG, KNOCK RETARD
0xAACE  LSRA               ; halve knock-retard value
0xAAD1  LDD  L01EE
0xAAD4  SUBB 0,X           ; subtract halved knock amount from L01EE
0xAAD8  STD  L01EE
```

The WOT/knock table comments mention `SPK ADV * (256/45)`; the `LSRA` before subtracting from `L01EE` is consistent with converting a 256/45 stored value into the 256/90 path.

## Current Candidate Scale

```text
MAG-A leading candidate:
  A uses 90°/256 scale = 0.3515625°/count.

candidate mapping:
  5°  → A ≈ 14
  10° → A ≈ 28
  20° → A ≈ 57
  30° → A ≈ 85
  40° → A ≈ 114
```

## Current Sign Convention

```text
L004F bit0 = 0 → advance/non-retard sign path
L004F bit0 = 1 → retard sign path
A entering LF550 = unsigned magnitude of L01EE low byte after sign handling
```

## Trace Row Summary

The machine-readable trace is in:

```text
maps/contracts/spark_magnitude_scale_contract.csv
```

It preserves rows for:

```text
L01FC table/predecessor writes and reads
L020B low-octane retard
L01FD final spark writes and reads
L01EE signed offset writes and reads
L020C knock retard and LSRA scaling
L004F bit0 sign flag
L01F2 startup spark override
A-before-LF550 sign/magnitude path
```

## Current Classification

```text
MAG-A:
  strongly supported statically. A appears to use 90°/256 scale = 0.3515625°/count.

MAG-B:
  less likely for A itself, but related 256/45 scale appears in knock/max-retard storage before LSRA conversion.

MAG-C:
  not supported for the final A path; table-native values appear converted/biased into the common 256/90 path before LF550.

MAG-D:
  not supported by static evidence, but bench proof remains required.
```

## Open Questions

- Is `L01FD` always 256/90 scale after every modifier, or do some paths add already-biased 16-bit values?
- Does the `L01EE` negative path using `NEGB` rely on all practical values fitting in signed 8-bit low byte?
- Does startup mode replace the normal magnitude or multiply/clamp it through `L01F2` only under a flag?
- Are knock and low-octane retard always converted into the same 256/90 scale before reaching `L01EE`?
- Does bench-measured `A` match `round(degrees * 256 / 90)` at 5°, 10°, 20°, and 30°?

## Stop Condition

Do not write spark output code until bench testing confirms the magnitude scale and sign convention. The next combined equation contract may use this candidate, but it must remain provisional until the `A` value before `LF550` is measured.
