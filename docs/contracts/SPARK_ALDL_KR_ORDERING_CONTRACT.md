# Spark ALDL / Knock-Retard Ordering Contract

## Purpose

Lock down the stock `$31` relationship between:

- the main/final spark accumulator,
- normal knock retard,
- the spark value handed to the EST timing bridge, and
- the spark value exported through ALDL.

This exists so future tuning work does not have to re-derive whether logged `Spark Advance` is upstream or downstream of normal knock retard.

## Conclusion

For the normal running path, the `$31` ALDL spark value is **downstream of normal knock retard**.

Therefore:

```text
logged ALDL Spark Advance = post-KR commanded spark value
logged Knock Retard       = diagnostic amount removed by knock logic
```

Do **not** subtract logged KR from logged Spark Advance a second time.

Approximate pre-KR spark demand may be reconstructed as:

```text
pre-KR spark ~= logged Spark Advance + logged Knock Retard
```

subject to ALDL sampling skew and any other spark modifiers active between the compared samples.

## Static Proof

### 1. Main spark accumulator is copied into the signed spark/retard working value

Stock source:

```asm
AA1A:  LDD     L01FD       ; FINAL SPK ADV
AA1D:  SUBB    L4132       ; initial/reference spark offset, scale 256/90
AA20:  SBCA    #$00
AA22:  STD     L01EE       ; CURRENT RETARD (2's CMP)
```

So `L01FD` is upstream of the `L01EE` value used by the output-side spark path.

Burst-knock logic may also subtract from `L01EE` before the normal knock-retard section.

### 2. Normal knock retard is stored in `L020C` and explicitly subtracted from `L01EE`

Stock source:

```asm
AACB:  STAA    L020C       ; DEG, KNOCK RETARD
AACE:  LSRA
AACF:  PSHA
AAD0:  TSX

AAD1:  LDD     L01EE       ; CURRENT RETARD (2's CMP)
AAD4:  SUBB    0,X
AAD6:  SBCA    #$00
AAD8:  STD     L01EE       ; CURRENT RETARD (2's CMP)
```

This establishes ordering unambiguously:

```text
L01FD / main spark path
    -> L01EE
    -> normal KR subtraction
    -> updated L01EE
```

### 3. KR scaling is deliberately converted to the spark scale before subtraction

The ALDL/source comments define:

```text
L020C Knock Retard: DEG = 45N / 256
spark/SAREF scale:  DEG = N / (256/90)
```

Equivalently:

```text
KR storage      = 256/45 counts per degree
spark storage   = 256/90 counts per degree
```

`LSRA` at `AACE` halves the KR count before subtraction:

```text
(256/45) / 2 = 256/90
```

That exactly converts knock retard into the common spark representation used by `L01EE`.

### 4. The post-KR `L01EE` value is copied to `L01F0` before degree-to-time conversion

Later in the same spark-output path:

```asm
AB3E:  STD     L01EE       ; CURRENT RETARD (2's CMP)
AB41:  STD     L01F0
AB44:  BCLR    L004F,#$01  ; 1 = RETARD, 0 = ADVANCE
AB47:  LDD     L01EE
```

`L01F0` is therefore a shadow of the spark state **after** the normal KR subtraction, immediately upstream of the sign/magnitude and degree-to-time/EST bridge.

The downstream bridge then transforms this spark-domain value using RPM/DRP-period and latency terms before writing the ASIC timing registers (`$3FE8`, `$3FE6`).

## ALDL Address-Alias Proof

The stock ALDL pointer table exports spark as:

```asm
FDB $31F0   ; SAREFFNL FINAL VALUE OF SAREF (MSB)
FDB $31F1   ; SAREFFNL+1 FINAL VALUE OF SAREF (LSB)
             ; DEG = N / (256/90)
```

and exports knock retard separately as:

```asm
FDB $020C   ; NOCKRTD, KNOCK RETARD
             ; DEG = 45N/256
```

The apparent `$31F0` versus `L01F0` mismatch is resolved by the ALDL transmit routine.

For table pointers in the `$1000-$3FFF` range, the transmitter performs:

```asm
F8B0:  LDX     0,X

F8B8:  CPX     #$1000
F8BB:  BCS     LF8DC
F8BD:  CPX     #$3FFF
F8C0:  BHI     LF8DC
F8C2:  XGDX
F8C3:  BRSET   L0050,#$08,LF8C9
F8C7:  ANDA    #$00CF
F8C9:  XGDX
F8CA:  LDD     0,X
```

For the normal path where the mask at `F8C7` executes:

```text
$31 AND $CF = $01
```

so the ALDL pointer:

```text
$31F0 -> actual live RAM read $01F0
$31F1 -> actual live RAM read $01F1
```

Thus the ALDL `SAREFFNL` spark word is reading the same `L01F0` word populated at `AB41` from the post-KR `L01EE` state.

## Full Ordering

```text
spark table / idle spark / modifiers
    -> L01FD                 main/final spark accumulator
    -> subtract initial/reference offset
    -> L01EE                 signed spark/retard work value
    -> burst-knock adjustment if active
    -> normal knock calculation
    -> L020C                 KR diagnostic storage
    -> LSRA                  KR scale conversion 256/45 -> 256/90
    -> subtract KR from L01EE
    -> torque-management / later limiting paths as applicable
    -> L01EE
    -> optional ALDL/controller spark override path
    -> L01F0                 post-KR spark shadow
    -> sign/magnitude conversion
    -> DRP-period / latency degree-to-time conversion
    -> $3FE8 / $3FE6         EST timing hardware handoff
```

ALDL export path:

```text
ALDL table $31F0/$31F1
    -> transmitter address mask $31xx -> $01xx
    -> live RAM $01F0/$01F1
    -> post-KR spark value
```

## Tuning Interpretation Rule

When reviewing `$31` logs:

```text
ALDL Spark Advance = final/post-normal-KR commanded spark-domain value
Knock Retard       = amount normal knock logic removed
```

Example:

```text
ALDL Spark = 26.7 deg
KR         = 3.7 deg
```

Interpret as approximately:

```text
post-KR commanded spark = 26.7 deg
pre-KR demand           = 30.4 deg
```

Incorrect interpretation:

```text
26.7 - 3.7 = 23.0 deg actual spark
```

That would double-subtract KR.

## Current Log Consequence

In the previously observed low-RPM/high-load event, representative pairs were:

| Logged spark | KR | Reconstructed pre-KR demand |
|---:|---:|---:|
| 27.8 deg | 2.6 deg | 30.4 deg |
| 26.7 deg | 3.7 deg | 30.4 deg |
| 28.5 deg | 1.9 deg | 30.4 deg |
| 29.2 deg | 1.2 deg | 30.4 deg |

The near-constant ~30.4 degree pre-KR demand is therefore not an artifact of subtracting KR twice.

Do not assume the visible base-table cell itself equals ~30.4 degrees; interpolation and other spark modifiers can contribute before `L01FD` / `L01EE` reach the observed value.

## Timing-Light Evidence

A dial-back timing-light comparison at idle matched the ALDL spark display while knock retard was zero.

That observation validates the practical ALDL spark scaling/display against crank timing for that zero-KR condition.

It **does not by itself prove** upstream/downstream KR ordering because KR was inactive during the check. The ordering proof is the static code trace above.

## Sampling Caveat

ALDL fields are serialized rather than captured atomically at one CPU instruction. During a rapidly changing knock event, the logged Spark and KR fields can have small temporal skew relative to one another.

For sustained or slowly changing events, this does not alter the architectural conclusion that the ALDL spark channel is sourced downstream of normal KR.

## Classification

```text
ALDL-SPARK-KR-ORDERING: CONFIRMED STATIC
```

Confirmed by:

1. `L01FD -> L01EE` upstream spark transfer.
2. Explicit `L020C` KR subtraction from `L01EE` at `AAD1-AAD8`.
3. KR-to-spark scale conversion by `LSRA`.
4. Post-KR `L01EE -> L01F0` copy at `AB3E-AB41`.
5. ALDL pointer table exporting `$31F0/$31F1` as `SAREFFNL`.
6. ALDL transmitter masking `$31xx -> $01xx` before dereference.
7. Separate ALDL export of `L020C` as the KR diagnostic field.

## Source Anchors

Primary source file:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

Relevant addresses:

```text
AA1A-AA22  L01FD -> L01EE
AA51-AA59  burst-knock subtraction from L01EE
AACB-AAD8  L020C storage, scale conversion, normal KR subtraction
AB3E-AB47  post-correction L01EE -> L01F0 and output-side sign handling
F8B0-F8CA  ALDL pointer decode / $31xx-to-$01xx masking and dereference
```

ALDL table anchors:

```text
SAREFFNL  -> $31F0/$31F1, scale 256/90
NOCKRTD   -> $020C,       scale 45N/256
```
