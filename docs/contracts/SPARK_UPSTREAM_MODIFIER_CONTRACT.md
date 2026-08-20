# $31 Spark Upstream Modifier / Table-Geometry Contract

## Purpose

Lock down the stock `$31` spark terms that exist **upstream of normal knock retard**, and correct the open-throttle spark-table RPM geometry used when interpreting calibration addresses.

This complements `SPARK_ALDL_KR_ORDERING_CONTRACT.md`.

The practical reason is that:

```text
ALDL Spark + ALDL KR
```

reconstructs the spark state immediately before **normal KR**, but it is not automatically the raw base-table value. Several adders/subtractors have already acted by that point, including the low-octane adaptive-retard path.

## Classification

```text
OPEN-THROTTLE-SPARK-GEOMETRY:       CONFIRMED STATIC/CALIBRATION
UPSTREAM-SPARK-SUMMATION:           CONFIRMED STATIC
COOLANT-BIAS CONTRIBUTION:          CONFIRMED STATIC + BIN-2 BYTE VERIFIED
PE/WOT-SPARK-ADDER:                 CONFIRMED STATIC + BIN-2 BYTE VERIFIED
LOW-OCTANE-BEFORE-NORMAL-KR:         CONFIRMED STATIC
BIN-2 CURRENT-CAL FACTS:             BYTE VERIFIED
```

Primary executable source:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

Current numbered tune archive reference:

```text
454_bin_versions_1-4.zip / 2.bin
SHA-256: 2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

---

## 1. Correct open-throttle spark-table geometry

The open-throttle spark table is declared at `$4166`:

```text
$4166  MIN MAP value
$4167  MIN RPM value
$4168  17 lines/block
$4169  first actual spark data byte
```

The table is 17 MAP columns x 17 RPM rows.

MAP columns are:

```text
20, 25, 30, 35, 40, 45, 50, 55, 60,
65, 70, 75, 80, 85, 90, 95, 100 kPa
```

The RPM rows are **not** a uniform 400-RPM sequence at the low end:

```text
400
600
800
1000
1200
1600
2000
2400
2800
3200
3600
4000
4400
4800
5200
5600
6000 RPM
```

The lookup code confirms special low-RPM handling:

```asm
A719:  LDAA  L0061
A71B:  CMPA  #64          ; 1600 RPM
A71D:  BLS   LA727
A71F:  LDAA  L0062
A721:  ADDA  #16          ; 400-RPM table offset
A727:  JSR   LF4DE        ; 3-D lookup
A72A:  STAA  L01F8        ; base/open-throttle spark result
```

For direct address interpretation, after the three-byte header:

```text
address = $4169 + (RPM-row-index * 17) + MAP-column-index
```

Two correction-history examples that exposed the earlier mapping error:

```text
$41A5 = actual 1000 RPM / 65 kPa
         previously labeled 1600 RPM / 65 kPa

$41DA = actual 2000 RPM / 75 kPa
         previously labeled 2800 RPM / 75 kPa
```

Therefore any historical spark-change CSV produced with the assumed regular low-RPM grid must be interpreted by **physical address against this corrected geometry**, not by its old RPM label.

This correction applies to the open-throttle **spark** table. The open-throttle VE table uses different geometry and is not automatically subject to this same error.

---

## 2. Main upstream spark summation

The open-/closed-throttle base spark lookup is stored in `L01F8`.

At `A7D7-A81B`, `$31` forms the main/final spark accumulator by adding several terms and then subtracting their associated biases/retards.

Relevant sequence:

```asm
A7D7:  ADDD  #128
A7DA:  TAB
A7DB:  LDX   #$0000
A7DE:  ABX
A7DF:  LDAB  L01FB       ; altitude spark correction
A7E2:  ABX
A7E3:  LDAB  L01F8       ; base open/closed-throttle spark
A7E6:  ABX
A7E7:  LDAB  L01FC       ; PE/WOT spark adder
A7EA:  ABX
A7EB:  LDAB  L01F9       ; coolant spark correction raw value
A7EE:  ABX
A7EF:  LDAB  L02CB       ; startup spark advance
A7F2:  ABX
A7F3:  XGDX

A7F4:  SUBB  L413B       ; main spark bias
A7F9:  SUBB  L413C       ; coolant spark bias
A7FE:  SUBB  L413D       ; altitude correction bias
A803:  SUBB  L413E       ; EGR correction bias
...
A811:  SUBB  L020B       ; low-octane adaptive spark retard
A816:  SUBB  L015A       ; additional runtime retard/correction term
A81B:  STD   L01FD       ; FINAL SPK ADV
```

Thus `L01FD` is already a **composite spark demand**, not a raw table cell.

A compact representation is:

```text
L01FD ~=
    base spark L01F8
  + coolant term L01F9
  + altitude term L01FB
  + PE/WOT term L01FC
  + startup term L02CB
  + EGR/filter contribution
  - calibration biases
  - low-octane adaptive retard L020B
  - L015A runtime correction
  + applicable state-specific terms
```

Do not infer an exact base-table value from `L01FD`, ALDL Spark, or `ALDL Spark + KR` without accounting for the active terms.

---

## 3. Coolant spark correction and the `$413C` bias

The coolant spark lookup stores its raw table result in `L01F9`:

```asm
A72D:  LDX   #$43AE / coolant-table path
...
A74B:  JSR   LF4DE
...
A761:  STAA  L01F9
```

Later the summation adds `L01F9` and explicitly subtracts `$413C`:

```asm
A7EB:  LDAB  L01F9
A7EE:  ABX
...
A7F9:  SUBB  L413C
```

Therefore the effective coolant spark contribution is:

```text
coolant contribution counts = L01F9 - $413C
```

Spark scale is:

```text
90 deg / 256 counts = 0.3515625 deg/count
```

The stock BMHM source defines:

```text
$413C = 57
```

and the coolant table uses raw `57` for nominal `0.0 deg` through much of its warm operating region.

The numbered current calibration lineage (`1.bin` through `4.bin`) instead contains:

```text
$413C = 51
```

including literal `2.bin`.

Consequently, whenever the coolant lookup returns the nominal-zero raw value `57`, the effective correction is:

```text
57 - 51 = +6 counts
+6 * 90/256 = +2.109375 deg
```

So in `2.bin`, a coolant-table cell that still represents nominal zero under the stock 57-count bias actually contributes approximately:

```text
+2.11 deg spark
```

This is a **bias mismatch effect**, not a claim that every coolant operating point is +2.11 degrees. Cells above or below 57 produce correspondingly different effective corrections.

---

## 4. PE/WOT spark adder

The WOT/PE spark correction path is explicitly gated by PE-active state and knock-system status:

```asm
CABC:  BRSET L0019,#$10,LCAD2   ; skip if knock-sensor error
CAC0:  BRCLR L003D,#$20,LCAD2   ; skip unless PE active

CAC4:  LDX   #$44BF             ; WOT spark advance correction vs RPM
CAC7:  LDAA  L0062              ; RPM/25
CAC9:  JSR   LF4C1

CACC:  LDAB  L0278              ; PE AFR slew multiplier
CACF:  MUL
CAD0:  ADCA  #$00
CAD2:  STAA  L01FC              ; SPARK ADDER
```

`L01FC` is then added directly into the main spark accumulator at `A7E7-A7EA`.

For literal `2.bin`, the 17 bytes at `$44BF-$44CF` are all:

```text
6
```

At the spark scale:

```text
6 * 90/256 = 2.109375 deg
```

Because the table result is multiplied by `L0278`, the contribution is slewed with PE rather than necessarily appearing instantaneously at full value.

For `2.bin` the PE/WOT spark term therefore ranges approximately:

```text
0 -> +2.11 deg
```

as the PE slew multiplier progresses from zero to full authority.

Important consequence: changing PE qualification/entry behavior can change commanded spark even when the main `$4166` spark table itself is untouched.

---

## 5. Low-octane adaptive retard is upstream of normal KR

The low-octane learner uses normal knock activity to update a separate adaptive state.

At `CE19-CE73`, `$31` evaluates coolant/MAP/knock conditions, maintains the low-octane activity counter `L0209`, and computes base low-octane retard `L020A`.

Relevant terminal sequence:

```asm
CE6A:  STAB  L0209
CE6D:  LDAA  L45BD       ; 8-deg low-octane base-retard maximum
CE70:  MUL
CE71:  ADCA  #$00
CE73:  STAA  L020A       ; low-octane base spark retard
```

That base adaptive retard is then multiplied by RPM and MAP factors before entering the main spark sum:

```asm
A77A:  LDAB  L0841       ; low-octane RPM multiplier
A77D:  LDAA  L01C0       ; MAP
A780:  LDX   #$45C7      ; low-octane MAP multiplier
A783:  JSR   LF4C1
A786:  MUL
...
A789:  LDAB  L020A
A78C:  MUL
A78D:  ADCA  #$00
A78F:  STAA  L020B       ; final low-octane adaptive retard
```

Then:

```asm
A811:  SUBB  L020B
A81B:  STD   L01FD
```

Normal instantaneous KR is applied later, after `L01FD` has entered the output-side spark path.

Therefore the ordering is:

```text
base table + upstream adders/corrections
        - low-octane adaptive retard L020B
        -> L01FD
        -> output-side spark work value
        - normal instantaneous KR L020C
        -> post-normal-KR spark
        -> L01F0
        -> ALDL Spark / EST handoff
```

This refines the ALDL reconstruction rule:

```text
ALDL Spark + logged KR
```

is approximately the spark demand **before normal instantaneous KR**, but **after low-octane adaptive retard**.

It must not be called the raw base-table value.

---

## 6. Correct interpretation of the ~30.4-degree reconstruction

Representative observed pairs from the previously analyzed event were:

```text
27.8 + 2.6 = 30.4 deg
26.7 + 3.7 = 30.4 deg
28.5 + 1.9 = 30.4 deg
29.2 + 1.2 = 30.4 deg
```

The static ordering proof means these sums are meaningful estimates of the state entering **normal KR**.

They do **not** prove that the interpolated base spark-table value itself was 30.4 degrees.

A base-table reconciliation must consider, as applicable:

```text
+ coolant contribution
+ PE/WOT spark adder
+ altitude correction
+ EGR/filter correction
+ startup/timeout correction
- low-octane adaptive retard
- other runtime retard/correction terms
```

For the current `2.bin` calibration in particular, two concrete upstream-positive possibilities are now byte-verified:

```text
nominal-zero coolant cell with $413C=51:  +2.11 deg
full PE/WOT spark adder:                    +2.11 deg
```

The PE term exists only when its qualification path is active; the coolant term depends on the actual coolant-table lookup result.

---

## 7. Tuning rules going forward

1. Map open-throttle spark edits by **physical address** using the corrected 17x17 geometry.
2. Do not reuse the earlier regular-low-RPM row assumption.
3. Treat logged ALDL Spark as post-normal-KR.
4. Treat `logged Spark + logged KR` as pre-**normal-KR**, not pre-all-knock and not raw base spark.
5. Account for low-octane adaptive retard separately when reconstructing upstream demand.
6. Account for the `$413C` coolant-bias mismatch in `2.bin` when a coolant cell resolves to stock nominal-zero raw value 57.
7. Account for `$44BF-$44CF` PE/WOT spark addition whenever PE is active.
8. Do not move historical mis-mapped spark corrections mechanically to another row; re-evaluate current logs against the corrected geometry first.

## Source anchors

```text
A70C-A72A  open/closed-throttle spark lookup and special low-RPM coordinate path
A72D-A761  coolant spark lookup -> L01F9
A77A-A78F  low-octane RPM/MAP scaling -> L020B
A7D7-A81B  upstream spark summation -> L01FD
AACB-AAD8  normal KR storage/scale/subtraction
AB3E-AB41  post-normal-KR spark shadow -> L01F0
CAC4-CAD2  PE/WOT spark table and slew -> L01FC
CE19-CE73  low-octane activity/adaptive-retard state -> L020A
```

Calibration anchors:

```text
$413C       coolant spark bias
$4166       open-throttle spark table header
$4169       first open-throttle spark data byte
$43AF       coolant compensation spark table
$44BF-$44CF WOT/PE spark advance correction vs RPM
$45BD       low-octane base spark-retard maximum
$45BE-$45C6 low-octane retard multiplier vs RPM
$45C7-$45DA low-octane retard multiplier vs MAP
```
