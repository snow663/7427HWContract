# $31 Fuel Calculation / Injector-Command Trace Contract

## Purpose

Reconstruct the stock `$31` fueling algorithm backward from the proven TBI injector command boundary so road-log behavior can be interpreted as an actual control pipeline rather than as loosely related channels.

This document is intentionally written as a runtime-analysis contract for the calibration currently used in the truck. Where the executable establishes ordering or dataflow directly, the finding is marked static proof. Where a scale or physical meaning is still being normalized, that is kept distinct.

Primary executable source:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

Current tune reference used for byte-specific statements:

```text
454_bin_versions_1-4.zip / 2.bin
SHA-256: 2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

## Classification

```text
TBI-SYNC-HARDWARE-HANDOFF:          CONFIRMED STATIC
RUNNING-SYNC-FUEL-DATAFLOW:         CONFIRMED STATIC
VE-TO-AIR-CHARGE-PATH:              CONFIRMED STATIC
COMMANDED-AFR-DIVISOR-PATH:         CONFIRMED STATIC
INJECTOR-FLOW-DIVISOR-PATH:         CONFIRMED STATIC + BIN-2 BYTE VERIFIED
BLM-MULTIPLICATIVE-CORRECTION:       CONFIRMED STATIC
CLOSED-LOOP-INT/P-CORRECTION:        CONFIRMED STATIC
MAP-AE-SYNC-ADDER:                   CONFIRMED STATIC
TPS-AE/ASYNC-PATH:                   CONFIRMED STATIC
SYNC/ASYNC-TBI-ARBITRATION:          CONFIRMED STATIC
INJECTOR-DEADTIME/OFFSET-PATH:       CONFIRMED STATIC
CRANK-FUEL-SEPARATE-PATH:            CONFIRMED STATIC
FIXED-POINT-ENGINEERING-NORMALIZATION: PARTIALLY RESOLVED / REPLAY VALIDATION PENDING
```

---

## 1. Final synchronous TBI hardware boundary

BMHM TBI mode has `$400B bit0 = 0`, so the production synchronous path uses the direct TBI branch:

```text
L0250 final BPW
    -> $3FCE
```

Relevant region:

```asm
850B-8515  TBI/CPI-PFI mode selection and final synchronous write
```

Stock no-fuel behavior also explicitly zeros `$3FCE`.

This is the final hardware-facing synchronous injector ABI:

```text
input:  16-bit final injector pulse-width count
zero:   no synchronous fuel intent
output: $3FCE
```

Authority also exists in:

```text
docs/contracts/PRESERVED_OUTPUT_DRIVER_ISLANDS.md
```

---

## 2. High-level running fuel pipeline

The normal running path is not one monolithic equation. `$31` builds a base synchronous pulse width and then repeatedly modifies it before the hardware write.

```text
MAP / load
  -> filtered MAP / density term
  -> charge-temperature denominator
  -> cylinder-displacement scaling
  -> interpolated VE
  -> cylinder air charge
  -> divide by commanded AFR
  -> divide by injector-flow calibration
  -> L024E base synchronous PW
  -> EGR displacement correction
  -> BLM correction
  -> fuel-cut / DFCO / decel-state logic
  -> RPM-derivative / transient corrections as applicable
  -> altitude / barometric correction
  -> battery-voltage PW multiplier
  -> closed-loop INT/proportional O2 correction
  -> + delta-MAP acceleration enrichment
  -> L024E corrected synchronous PW
  -> TBI synchronous/asynchronous arbitration
  -> short-PW/minimum-PW shaping
  -> + injector voltage/deadtime offset L0256
  -> L0250 final synchronous PW
  -> $3FCE
```

A separate transient path can simultaneously create asynchronous fuel:

```text
delta TPS / delta MAP / transition logic
  -> AE state / async reservoir
  -> short-PW/deadtime shaping
  -> final async count
  -> $3FF2
  -> $3FFC bit2 trigger sequence
```

Therefore logged synchronous BPW is not necessarily the entire delivered-fuel event during a transient.

---

## 3. VE selection and interpolation

The running algorithm selects the appropriate VE table and stores the interpolated result in `L0231`.

Open-/normal-throttle path:

```asm
7FA8: LDAA  L0062
7FAA: LDX   #$49D5
7FB0: JSR   LF4DE
```

Idle/closed-throttle path:

```asm
7FB5: LDAA  L0063
7FBD: LDX   #$4A88
7FC0: JSR   LF4DE
```

Convergence:

```asm
7FD5: STAA  L0231
```

Interpretation:

```text
L0231 = interpolated VE selected by the current throttle/idle state
```

Future replay work should record the exact four source cells and interpolation fractions, not merely the nearest XDF cell.

---

## 4. MAP / charge-temperature / displacement air model

The air-charge side is recognizable as a speed-density model.

MAP-related density term is generated into `L0257` in the `$7E40` region.

Charge-temperature denominator is generated into `L0236` in the `$E2C8` region.

The code begins from coolant and optionally enters a MAT blend according to `$400B bit6`.

For literal `2.bin`:

```text
$400B = $0C = 0000 1100b
bit6 = 0
```

so the MAT-blend branch is not enabled in this calibration path.

The temperature conversion uses the `$4AF4` table and adds `$7480` after scaling:

```asm
E2ED: LDX   #$4AF4
E2F0: JSR   LF4C1
E2F3: CLRB
E2F4: LSRD
E2F5: ADDD  #$7480
E2F8: STD   L0236
```

The resulting representation is consistent with an absolute-temperature denominator. The exact engineering-scale normalization should be validated by replay before being treated as a final external-unit contract.

Cylinder-volume scaling is then applied using `$4D94`:

```asm
7FD8: LDD   L0257
7FDB: LDX   L0236
7FDE: FDIV
7FE1: LDAA  L4D94
7FE4: JSR   LF550
7FE8: STD   L0238
```

For literal `2.bin`:

```text
$4D94 = 206
```

The stock comments identify this as the application-specific cylinder-volume/unit-conversion term for the 7.4 L engine.

---

## 5. VE produces cylinder air charge

The interpolated VE is multiplied into the density/displacement term:

```asm
7FEB: LDAA  L0231
7FEE: LDX   #$0238
7FF1: JSR   LF550
7FF4: STD   L0234
```

Conceptually:

```text
L0234 proportional to:

    MAP * cylinder displacement * VE
    --------------------------------
           absolute charge temperature
```

`L0234` is therefore the central cylinder-air-charge quantity used by the running fuel equation.

This establishes the physical structure of the stock speed-density model directly from executable dataflow.

---

## 6. Commanded AFR is an active divisor, not a simple PW multiplier

The fuel path next divides the air-charge quantity by commanded AFR:

```asm
8010: LDX   L0234
8013: LDAA  L024A
...
801A: FDIV
```

`L024A` is the commanded-AFR state.

Its producer path includes, depending on mode/state:

```text
stoichiometric calibration
or open-loop AFR table
  -> startup enrichment
  -> hot-restart / cold-idle / crank-to-run effects
  -> AFR limits
  -> PE qualification
  -> PE AFR target
  -> PE slew/ramp
  -> cold PE correction
  -> special overrides
  -> L024A
```

Representative anchors:

```asm
891E: LDAA  L48E7       ; stoich reference path
8938: LDX   #$4BBA      ; open-loop AFR table
8998: STAA  L024A

8B5D: LDX   #$4C6E      ; PE/WOT AFR table
8BE3: LDAB  L0278       ; PE slew multiplier
8BEE: STAA  L024A
```

For literal `2.bin`, the PE AFR table contains `120` across the applicable region, corresponding to the calibration's 12.0-AFR representation.

Practical consequence:

```text
PE enriches the physical fuel equation by changing the AFR divisor.
```

It is not merely an arbitrary final-PW percentage adder.

---

## 7. Injector-flow calibration is the second main divisor

Immediately after the AFR division, the code divides by injector-flow calibration `$4D92/$4D93` and stores the result in `L024E`:

```asm
801C: LDX   L4D92
801F: IDIV
...
8021: LDX   L4D92
8024: FDIV
...
802F: STD   L024E
```

Literal `2.bin` contains:

```text
$4D92/$4D93 = $1A9C = 6812
```

Using the scaling documented in the stock source for the TBI injector-flow constant:

```text
6812 / 819.2 = 8.3154 g/s
approximately 66.0 lb/hr
```

Conceptually the base running equation is therefore:

```text
fuel mass = cylinder air mass / commanded AFR

base injector time proportional to:

    MAP * displacement * VE
    -------------------------------------------------
    charge temperature * AFR * injector flow capacity
```

and the stock implementation stores the fixed-point result in:

```text
L024E = base synchronous pulse-width accumulator
```

---

## 8. EGR displacement correction

The code subtracts an EGR-related fresh-air displacement correction from `L024E` immediately after the base calculation:

```asm
8032: LDD   L01B2
8035: ADDD  #128
8038: LDX   #$024E
803B: JSR   LF550
803E: LSRD
803F: LSRD
8040: STD   L0252

8043: LDD   L024E
8046: SUBD  L0252
8049: STD   L024E
```

For an EGR-disabled calibration this path should normally collapse toward no effective displacement correction, but the executable ordering remains part of the fuel pipeline.

---

## 9. BLM is a multiplicative learned-fuel correction

BLM enters through `L0248` and is applied to the synchronous PW accumulator:

```asm
804C: LDAA  L0248
...
8055: JSR   L80EE
```

The helper around `L80EE` multiplies `L024E` using the BLM value with the normal 128-centered convention.

Practical interpretation:

```text
BLM = 128 -> approximately 1.000 multiplier
BLM > 128 -> learned fuel addition
BLM < 128 -> learned fuel removal
```

The PE path contains a safeguard preventing an inappropriate learned-lean correction from defeating enrichment when PE is active.

This establishes BLM as a true learned multiplicative correction, distinct from the short-term O2/INT path.

---

## 10. Fuel-cut / DFCO / decel logic can override the calculated fuel

After the base equation and learned correction, state logic can modify or completely zero the synchronous PW.

Representative hard-zero behavior:

```asm
80E2: BSET  L0046,#$10
80E5: LDD   #$0000
80E8: STD   L024E
```

DFCO/decel logic occupies its own stateful region and includes qualification, hysteresis, and transitions.

Road-analysis consequence:

```text
VE and AFR alone do not guarantee a corresponding delivered PW if a downstream fuel-state machine has modified or zeroed L024E.
```

---

## 11. Barometric / altitude correction

The stock code applies an additional load/barometric correction after the main speed-density equation:

```asm
8342: LDAA  L01C6
...
8351: LDAB  L01CC
8354: LDX   #$49AA
8357: JSR   LF4DE

835A: LDX   #$024E
835D: JSR   LF550
...
836C: STD   L024E
```

The executable order is confirmed. Exact external-unit normalization of the `$49AA` table should be validated in the replay model before assigning a final engineering-percent label.

---

## 12. Battery-voltage multiplicative PW correction

Battery voltage also enters as a multiplicative correction:

```asm
836F: LDAA  L0055
8371: LDX   #$4988
8374: JSR   LF4C1
8377: LDX   #$024E
837A: JSR   LF550
837D: STD   L024E
```

This is separate from the later additive injector opening/deadtime offset.

Therefore the stock injector-voltage model has at least two distinct layers:

```text
1. battery-dependent multiplicative PW correction
2. additive injector opening/deadtime offset before final output
```

---

## 13. Closed-loop INT / proportional correction

The O2 controller builds a short-term correction using the integrator and proportional terms.

Relevant states include:

```text
L020F  integrator-like state
L027A  proportional component
L026F  combined signed correction
```

Combination region:

```asm
88E9: LDAA  L027A
...
8906: LDAA  L020F
...
8918: SUBA  #128
891A: STAA  L026F
```

Application to synchronous PW occurs around `$8380-$839C` as a signed correction to `L024E`.

Practical distinction:

```text
BLM      = learned, longer-term multiplicative correction
INT/P O2 = immediate closed-loop signed correction
```

They are separate stages and should not be treated as redundant displays of one factor.

---

## 14. MAP acceleration enrichment is added directly to synchronous PW

Delta-MAP acceleration enrichment is computed into `L023E`:

```asm
7EB2-7F1E  MAP-AE calculation
7F1E:      STAA L023E
```

It is later added directly to `L024E`:

```asm
839F: CLRA
83A0: LDAB  L023E
83A3: ADDD  L024E
83AB: STD   L024E
```

Therefore:

```text
corrected synchronous PW
+ MAP acceleration enrichment
= new synchronous PW
```

This is an additive transient-fuel term downstream of the steady-state speed-density calculation.

---

## 15. TPS acceleration enrichment feeds the asynchronous-fuel system

Delta-TPS acceleration enrichment follows a separate path:

```asm
7F21: LDAA  L01D9
7F24: SUBA  L01DC
...
7F3F: LDX   #$4B4F
...
7F70: STAA  L023F
```

Temperature-corrected transient fuel is accumulated into the async-fuel machinery, including the `L023A` reservoir/state.

This establishes the practical road-debugging rule:

```text
a throttle transient can contain simultaneous synchronous BPW and asynchronous AE fuel.
```

The synchronous ALDL BPW channel alone may therefore under-report total transient fuel delivery.

---

## 16. TBI synchronous/asynchronous arbitration

TBI delivery strategy is selected around `$83FB` onward.

Literal `2.bin` has `$400B bit2` set, corresponding to the stock TBI synchronous-fuel-at-idle configuration.

Off-idle logic evaluates current pulse width, load/RPM state, previous async state, and calibration thresholds and can explicitly zero the synchronous command:

```asm
8424: CLRA
8425: CLRB
8426: STD   L3FCE
```

while routing fuel through the asynchronous path.

Final async hardware sequence uses:

```text
async pulse count -> $3FF2
$3FFC bit2 clear/write -> set/write trigger sequence
```

Representative region:

```asm
8571: STD   L3FF2
8577+: manipulate $3FFC bit2 with stock short access delays
```

This path is already part of the preserved fuel-output island contract.

---

## 17. Short-PW / minimum-PW shaping

Before final synchronous output, the code handles very short pulse widths and minimum-delivery behavior.

Representative region:

```asm
84BC: LDD   L024E
...
84E9: CPD   L496D
...
84F2: LDD   L496F
```

Literal `2.bin` has a simplified short-PW setup compared with the stock nonlinear machinery, including the current minimum/replacement values and a largely zeroed short-PW correction table.

Exact `2.bin` byte-to-engineering documentation for all short-PW entries should remain tied to direct byte verification and replay rather than assumed from stock comments alone.

---

## 18. Injector opening/deadtime offset is the final additive correction

Battery voltage produces an injector offset/deadtime term in `L0256`:

```asm
E2FB: LDAA  L00A7
E2FD: LDX   #$4B05
E300: JSR   LF4C1
E303: STAA  L0256
```

Immediately before the final output:

```asm
84F5: STD   L024C
84F8: BEQ   L8508
84FA: ADDB  L0256
84FD: ADCA  #$00
84FF: CPD   #32767
...
8508: STD   L0250
```

So the final synchronous-output behavior is approximately:

```text
if shaped commanded fuel == 0:
    L0250 = 0
else:
    L0250 = clamp(shaped PW + injector voltage/deadtime offset,
                  0,
                  32767)
```

Then:

```text
L0250 -> $3FCE
```

This is the last confirmed algorithmic correction before the TBI ASIC command.

---

## 19. Cranking uses a separate fueling equation

Crank fueling does not simply reuse the normal VE/AFR running equation.

The cranking path around `$85B2` uses dedicated coolant, RPM/DRP, barometric, TPS, hot-restart, and voltage-dependent terms.

Representative anchors:

```text
$4D9C  crank PW vs coolant
$4D9A  crank scaling constant
$4DAD  normal crank RPM/DRP multiplier
$4DB6  hot-restart alternative
$4DBF  crank BARO correction
$4DC3  crank TPS correction
```

This means first-start / second-start / hot-restart behavior should eventually be reconstructed as its own replay path instead of being forced into the running speed-density model.

---

## 20. Runtime interpretation model

For road analysis, think of `$31` fueling as the following named layers:

```text
1. AIR MODEL
   MAP
   charge temperature
   displacement
   VE

2. MIXTURE TARGET
   open-loop / stoich
   startup
   PE
   special AFR modifiers

3. INJECTOR FLOW MODEL
   injector-flow calibration

4. LEARNED CORRECTION
   BLM

5. STATE OVERRIDES
   fuel cut
   DFCO
   decel enlean

6. ENVIRONMENTAL CORRECTION
   barometric / altitude
   battery multiplier

7. CLOSED-LOOP CORRECTION
   integrator
   proportional O2 term

8. TRANSIENT FUEL
   MAP AE -> synchronous adder
   TPS AE -> largely asynchronous path

9. DELIVERY STRATEGY
   synchronous vs asynchronous TBI

10. INJECTOR NONLINEARITY
    short/minimum PW
    battery/deadtime offset

11. HARDWARE
    L0250 -> $3FCE
    async -> $3FF2/$3FFC
```

---

## 21. Replay-model target

The next useful validation artifact is a code-exact `$31` fuel replay for literal `2.bin`.

For each road-log sample it should be able to report, where the required inputs exist:

```text
RPM / MAP / TPS / ECT / BARO / battery
selected VE table
source cells + interpolation fractions
interpolated VE
charge-temperature term
cylinder-air-charge quantity
commanded AFR and active AFR mode
injector-flow constant
raw speed-density PW
BLM contribution
short-term O2 contribution
baro correction
battery correction
MAP AE
TPS async AE state
sync/async selection
short-PW shaping
deadtime offset
predicted L0250 / $3FCE
logged BPW
prediction error
```

A mismatch between predicted and logged BPW becomes a diagnostic tool: it identifies an unresolved branch, scale, or state rather than being hand-waved as generic fueling behavior.

---

## Source anchors

```text
7E40...     MAP/density-side term -> L0257
7EB2-7F1E  MAP acceleration enrichment -> L023E
7F21-7F70  TPS acceleration enrichment -> L023F / async machinery
7FA8-7FD5  VE selection/interpolation -> L0231
7FD8-7FF4  charge-density/displacement/VE -> L0234
8010-802F  AFR + injector-flow divisions -> L024E
8032-8049  EGR displacement correction
804C-8058  BLM correction entry
80EE...     BLM fixed-point multiply helper
80E2...     representative hard fuel cut
8342-836C  barometric/altitude PW correction
836F-837D  battery PW multiplier
8380-839C  closed-loop short-term correction
839F-83AB  MAP-AE synchronous addition
83FB...     TBI sync/async arbitration
8424-8426  explicit synchronous-command zero
84BC-8508  short-PW/minimum/deadtime shaping -> L0250
850B-8515  TBI final synchronous write -> $3FCE
8571...     asynchronous pulse -> $3FF2 / $3FFC trigger
85B2...     separate crank-fuel path
88E9-891A  O2 proportional + integrator combination -> L026F
891E...     commanded-AFR generation
8B5D...     PE AFR target/slew path
E2C8-E2F8  charge-temperature denominator -> L0236
E2FB-E303  injector voltage/deadtime offset -> L0256
```

## Standing interpretation rule

Do not explain a road fueling event from VE alone.

At minimum, reconstruct:

```text
VE -> air charge -> AFR target -> injector-flow conversion
-> BLM / state corrections -> baro/battery -> closed-loop correction
-> transient fuel -> sync/async strategy -> deadtime -> ASIC command
```

and classify each conclusion as static proof, calibration-byte verified, replay-validated, bench-validated, or inference.
