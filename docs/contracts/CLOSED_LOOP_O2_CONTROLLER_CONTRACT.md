# $31 Closed-Loop O2 / INT / BLM Controller Contract

## Purpose

Capture the stock BMHM `$31` closed-loop fuel controller as executable dataflow rather than treating ALDL `INT`, `BLM`, `O2`, and `Slow Rich/Lean` as generic OBD-style trims.

This contract is truck-first: it exists so road-log pulse-width movement can be traced back through the actual controller and so calibration changes can target the correct layer.

Primary executable authority:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

Stock calibration authority used for literal byte/table values in this document:

```text
BMHM stock BIN
SHA-256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
```

Current-truck warning:

```text
The running tune derived from 2.bin was changed again on 2026-08-22.
The exact post-change BIN has not yet been archived.
Therefore executable ordering below is authoritative, but any literal calibration
value must be rechecked against the newly uploaded running BIN before building
an exact binary patch.
```

## Classification

```text
RAW-O2 INPUT PATH:                    CONFIRMED STATIC
FAST RICH/LEAN DETECTOR:              CONFIRMED STATIC
SLOW O2 FILTER:                       CONFIRMED STATIC
SLOW RICH/LEAN + ERROR:               CONFIRMED STATIC
PROPORTIONAL CORRECTION:              CONFIRMED STATIC
INTEGRATOR DIRECTION/RATE:            CONFIRMED STATIC
FINAL INT/P SIGNED CORRECTION:        CONFIRMED STATIC
BLM LEARNING DIRECTION/RATE:          CONFIRMED STATIC
BLM MULTIPLICATIVE PW APPLICATION:    CONFIRMED STATIC
CURRENT POST-2026-08-22 CAL BYTES:     PENDING BIN CAPTURE
DAMPED CLOSED-LOOP PATCH:             DESIGN TARGET / NOT YET BYTE-VERIFIED
```

---

## 1. High-level controller topology

The stock controller is not a simple `O2 -> INT -> PW` loop.

```text
raw O2 A/D  L01D5
      |
      +---- FAST rich/lean detector --------------------+
      |                                                  |
      |                                                  v
      |                                      proportional correction sign
      |
      +-> clamp for slow filter
          -> airflow-dependent lag filter
          -> L01D2 filtered O2
               |
               +-> slow rich/lean hysteresis
               +-> slow O2 error magnitude
               +-> proportional magnitude/duration
               +-> integrator timing/direction
                         |
                         v
                     INT L020F
                         |
                         +-> BLM learning state

fuel calculation
  -> BLM multiplicative correction
  -> downstream fuel-state/baro/battery stages
  -> signed INT +/- proportional correction
  -> MAP AE
  -> injector shaping/deadtime
  -> final injector command
```

This means three distinct closed-loop effects can move delivered fuel:

```text
1. proportional correction P     immediate/timed additive PW correction
2. INT                            slower additive PW correction
3. BLM                            learned multiplicative correction applied earlier
```

They must not be interpreted as three displays of the same percentage trim.

---

## 2. Raw O2 and slow-filter input clamp

The raw narrowband value is `L01D5`.

Before the slow controller filters it, stock `$31` clamps the input using:

```text
$48BB = 36  -> about 156 mV low slow-filter limit
$48BC = 184 -> about 799 mV high slow-filter limit
```

Executable region:

```text
$7E09-$7E33
```

Therefore a logged instantaneous O2 value of 44 mV does **not** mean the slow filter is being driven with 44 mV. The slow path sees approximately the 156 mV floor. Likewise, values above about 799 mV are clipped for the slow path.

Practical consequence:

```text
raw sensor extremes can occur long before the filtered slow state crosses its
rich/lean threshold.
```

That lag is partly intentional, not automatically proof of a failed sensor or software error.

---

## 3. Airflow-dependent slow O2 filter

At idle, the stock fixed slow-filter coefficient is:

```text
$48BD = 2 -> about 0.008
```

Off idle, `$4D05-$4D0D` selects the lag coefficient versus airflow:

```text
airflow bin:     0    16    32    48    64    80    96   112   128
raw coefficient: 8    10    12    16    19    22    25    29    33
approx factor:  .031  .039  .047  .063  .075  .086  .098  .114  .129
```

So the controller intentionally filters O2 heavily, especially at lower airflow.

---

## 4. Three rich/lean threshold families

Off idle, `$31` builds airflow-dependent mean, rich, and lean thresholds:

```text
mean: $4CEA-$4CF2
rich: $4CF3-$4CFB
lean: $4CFC-$4D04
```

Stock approximate ranges:

```text
mean: 451-460 mV
rich: 473-486 mV
lean: 434-469 mV
```

At idle these are replaced by fixed values:

```text
$494A = 129 -> about 560 mV rich threshold
$494B = 110 -> about 477 mV lean threshold
$494C = 119 -> about 516 mV mean threshold
```

These values define a real hysteresis/error structure. There is not one universal 450 mV switch point.

---

## 5. Fast rich/lean detector

The fast detector is built around the mean threshold plus/minus `$4947`:

```text
$4947 = 36 -> about 156 mV fast rich/lean window
```

Executable region:

```text
$86B2-$86F0
```

Outside that wide window the raw O2 voltage directly establishes rich or lean.

Inside the window, the code compares the current raw O2 value `L01D5` with the prior raw O2 value `L01D4`. In other words, the controller can use **O2 slope/direction** inside the central voltage band rather than waiting for a single absolute threshold crossing.

The fast rich/lean state is stored in `$003E bit6` and is later used to select the sign of the proportional correction.

---

## 6. Slow rich/lean and slow O2 error

The filtered O2 value `L01D2` is compared against the separate slow rich and lean thresholds around:

```text
$8790-$87BE
```

Behavior:

```text
filtered O2 > rich threshold:
    slow state = rich
    error = amount above rich threshold

filtered O2 < lean threshold:
    slow state = lean
    error = amount below lean threshold

between thresholds:
    slow error = 0
```

Slow O2 error is stored in `L0280` and limited to 96 counts.

The rich-side error is additionally scaled by:

```text
$4955 = 232 -> about 0.906 rich-error multiplier
```

Idle additionally applies:

```text
$4956 = 192 -> 0.750 idle error multiplier
```

---

## 7. Proportional correction magnitude

Slow O2 error first indexes `$4D0E-$4D1A`:

```text
slow error:  0   8  16  24  32  40  48  56  64  72  80  88  96
base P:     16  16  16  16  16  24  28  32  36  40  48  64  64 counts
```

Off idle, this correction is then multiplied by the MAP/RPM gain surface `$4D31-$4D84`.

The stock gain rises in the same general operating region where the truck has shown loaded knock and strong PW motion:

```text
1200 rpm, 70-80 kPa: about 0.250
1600 rpm, 70-80 kPa: about 0.281
2000 rpm, 70-80 kPa: about 0.281
2400 rpm, 70-80 kPa: about 0.375
2800 rpm, 70-80 kPa: about 0.375
```

This is direct evidence that the stock controller deliberately gives the proportional loop more authority in mid-load/mid-RPM operation.

---

## 8. Proportional correction duration

The proportional term is not necessarily a one-pass correction.

Base duration versus slow O2 error is `$4D1B-$4D27`:

```text
error:        0    8   16   24   32   40   48   56    64    72    80-96
duration ms: 25   25   75  125  200  300  400  600  1200  2400   4800
```

An airflow-dependent duration offset `$4D28-$4D30` is also used off idle:

```text
about 200 ms at low airflow -> about 25 ms at highest airflow
```

Idle instead uses `$494D`.

Therefore a large slow O2 error can produce a proportional PW kick that remains active for seconds.

---

## 9. Integrator rate and agreement gate

Base integrator update delay versus airflow is `$4CE1-$4CE9`:

```text
airflow bin:   0   16   32   48   64   80   96  112  128
base delay ms: 800 600  380  250  200  170  150  150  150
```

The delay is then multiplied by `$4D85-$4D91` according to slow O2 error.

Representative multipliers:

```text
error 0-24: ~0.996
error 32:   ~0.625
error 40:   ~0.500
error 48-64:~0.375
```

So at higher airflow and meaningful O2 error the integrator can advance approximately one count every few tens to low hundreds of milliseconds.

Before INT updates, the code checks agreement between the fast and slow rich/lean states. This prevents the integrator from ratcheting while the two detectors disagree.

INT limits are stock:

```text
$4910 = 40   minimum INT
$4911 = 158  maximum INT
```

INT changes by one count per qualified update.

---

## 10. Final INT/P correction is additive PW, not a percentage trim

The final signed short-term correction is built at `$88E9-$891A`.

Conceptually:

```text
fast state lean:
    correction = INT + P - 128

fast state rich:
    correction = INT - P - 128
```

The signed result is stored in `L026F`.

Later in the fuel path, this value is added to or subtracted from the synchronous PW accumulator. It is therefore **additive injector pulse-width counts**, not an `INT/128` multiplicative percentage.

With the known BPW representation:

```text
1 PW count ~= 1 / 65.536 ms ~= 15.26 microseconds
```

Examples from INT alone:

```text
INT 120 -> -8 counts  -> about -0.122 ms
INT 112 -> -16 counts -> about -0.244 ms
INT 135 -> +7 counts  -> about +0.107 ms
```

The proportional term is added on top of that signed INT offset.

At a 4-5 ms loaded BPW, a few tenths of a millisecond is already a several-percent fuel change.

---

## 11. BLM is separately multiplicative

BLM is applied earlier in the synchronous fuel path through `$804C-$8055` and helper `$80EE`.

Effective relationship:

```text
PW after BLM ~= PW before BLM * BLM / 128
```

Examples:

```text
BLM 128 -> 1.0000
BLM 120 -> 0.9375  (-6.25%)
BLM 114 -> 0.8906  (-10.94%)
```

Important PE safeguard:

```text
if BLM < 128 and PE is active, the learned-lean BLM correction is skipped.
```

Thus PE protects enrichment from a previously learned lean correction.

---

## 12. BLM learning rate and direction

The BLM learner is around `$8E1D-$8EA6`.

Stock calibration:

```text
$48ED = 12  -> about 650 ms BLM update period
$48F7 = 2   -> normal closed-loop INT learning window
$48F8 = 4   -> idle INT learning window
$48F9 = 84  -> minimum normal BLM
$48FA = 90  -> minimum idle BLM
$48FB = 1   -> BLM step size
$48FC = 172 -> maximum BLM
```

The learner only moves BLM after INT remains sufficiently displaced from 128 and rich/lean direction agrees with the required correction.

Direction is explicit:

```text
rich -> subtract $48FB from active BLM cell
lean -> add      $48FB to active BLM cell
```

So once the controller has a persistent bias, a BLM cell can move one whole count roughly every 650 ms.

This explains why a cell can walk visibly during a several-second steady-load event.

---

## 13. BLM-cell transitions can create instantaneous PW steps

Because BLM is cell-indexed, changing cells can select a different multiplicative correction immediately. `$31` also contains options that reset/condition INT on BLM-cell changes.

Therefore a road log can show:

```text
same/similar TPS
same/similar MAP
BLM cell changes
BLM value changes abruptly
INT may reset
BPW steps abruptly
```

This can create a torque discontinuity even when the underlying VE table is smooth.

Do not automatically attribute such a BPW step to VE interpolation or driver input.

---

## 14. 2026-08-22 current-log observation

External road log:

```text
2026-08-22_19.59.25.csv
```

The log was recorded after a PCM reset and a short pre-log drive. Therefore non-128 BLM cells at log start are not evidence of reset failure; they may already have relearned during that pre-log drive.

A notable sequence around ~538-541 s shows repeated very-low instantaneous O2 readings while the logged slow state remains rich, with INT and BLM continuing downward before the slow state finally reverses.

Representative observation:

```text
raw O2 reaches tens of millivolts
slow state still reports rich
INT reaches roughly 112
BLM reaches roughly 120 and continues lower in the event
```

Static code explains how that can occur:

```text
raw O2 extreme
 -> clamped at slow-filter floor
 -> lag filtered
 -> slow state can remain rich
 -> if fast/slow agreement is satisfied, INT continues moving
 -> persistent INT bias allows BLM to ratchet
```

This does **not** prove the thresholds are wrong. It proves the observed lag and fuel correction are consistent with the stock controller architecture and that the controller has enough authority to move PW materially before reversal.

---

## 15. Tuning interpretation

For this truck, the useful tuning question is not merely:

```text
"what narrowband voltage equals stoich?"
```

The controller behavior depends on all of:

```text
raw O2 voltage and slope
mean/rich/lean thresholds
slow-filter clamp
slow-filter coefficient
P error table
P MAP/RPM gain
P duration
INT airflow delay
INT error-delay multiplier
BLM learning period/window
BLM cell boundaries and INT-reset behavior
PE entry
```

Changing only a nominal rich/lean threshold can move the reversal point while leaving excessive correction magnitude/rate intact.

---

## 16. Provisional damped-controller patch strategy

The next calibration-only experiment should isolate **controller authority** from **sensor bias**.

Until the exact post-2026-08-22 running BIN is uploaded, do not apply literal stock-byte replacements blindly.

Preferred first experiment after byte verification:

```text
1. leave mean/rich/lean voltage thresholds unchanged
2. reduce P gain in roughly 1200-2800 rpm / 60-90 kPa
3. slow INT updates in the same operating region by increasing effective delay
4. leave BLM step size at 1 initially
5. consider increasing BLM update period only after P/INT response is evaluated
6. move PE qualification earlier if high-load operation should not remain under narrowband control
```

Why this order:

```text
threshold change -> tests sensor switching bias
P/INT damping    -> tests correction amplitude/rate
BLM damping      -> tests learned-cell migration
PE entry         -> removes lean learned correction and resets short-term correction
```

A clean A/B test should change one layer at a time.

Candidate calibration targets:

```text
$4CEA-$4D04  mean/rich/lean threshold tables
$4D05-$4D0D  slow O2 filter coefficient
$4D0E-$4D1A  base proportional counts
$4D1B-$4D27  proportional duration
$4D28-$4D30  P duration offset vs airflow
$4D31-$4D84  P gain vs MAP/RPM
$4CE1-$4CE9  base INT delay vs airflow
$4D85-$4D91  INT delay multiplier vs slow error
$48ED         BLM update period
$48F7/$48F8  BLM learning INT windows
$48FB         BLM step size
```

The first truck-specific candidate is the `$4D31-$4D84` MAP/RPM P-gain surface because stock gain increases in the same mid-load region where the truck has shown the strongest correction/knock interaction.

---

## 17. Road-log interpretation rule going forward

For `$31`, never read these channels as if they were generic percentage trims:

```text
INT -> additive PW-count bias around 128
P   -> timed additive PW-count correction whose sign follows fast R/L state
BLM -> multiplicative learned correction around 128
```

A useful reconstruction for a steady non-AE event is conceptually:

```text
base PW
 -> * BLM/128
 -> downstream corrections
 -> + (INT - 128 +/- P) * PW_count_time
 -> final shaping/deadtime
```

Exact replay must preserve executable ordering and fixed-point arithmetic rather than collapsing the controller into one percentage correction.
