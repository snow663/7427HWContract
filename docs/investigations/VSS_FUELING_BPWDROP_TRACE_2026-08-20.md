# VSS / Fueling / BPW-Drop Trace — 2026-08-20

## Purpose

Determine whether the VSS faults present with literal numbered `2.bin` can directly reduce synchronous injector pulse width enough to cause the observed road stumble, and correlate the stock-code paths against the available ALDL log evidence.

## Calibration / evidence basis

Literal numbered calibration:

```text
454_bin_versions_1-4.zip / 2.bin
SHA-256: 2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

Relevant literal `2.bin` bytes:

```text
$400F = $80   manual-mode bit7 set
$4921 = 0
$4922 = 0
$4923 = 0
$4926/$4927 = $0000
$4938 = $80
$4939 = 6 mph
$493B = 10 mph
$493C = 7 mph
$4965 = 120       overspeed qualification timer
$4966 = 48        1200 RPM fuel-on threshold
$4967-$496A = C0 BE C0 BE
$496B-$496E = 62 60 00 20
$5156 = 16 mph
$5157 = 160       4000 RPM
$5158 = 152       3800 RPM
$5159 = 192       75% TPS
$5B01 = $A2       DTC24 mask enabled
$5B2B = $F1       DTC16 mask enabled
```

Road log examined:

```text
2026-08-19_16.58.52.csv
```

In that log:

```text
Code 16 Vehicle Speed Sensor Failure = OK for the entire log
Code 24 Transmission Output Speed Low = Error for the entire log
Vehicle Speed channel is not trustworthy; it contains 0, normal-small values, 141, 181, 192, 255, etc.
```

## Classification

```text
DTC24 DIRECT BPW REDUCTION:            NOT FOUND IN NORMAL FUEL PATH
DTC16 / VSS-BUFFER FUEL BRANCHES:      CONFIRMED STATIC
RAW-VSS FUEL DEPENDENCIES:             CONFIRMED STATIC
LITERAL-2.BIN THRESHOLD STATE:          BYTE VERIFIED
2026-08-19 BPW-DROP CORRELATION:        LOG VERIFIED
BLM-CELL SWITCH CAUSE OF DROP:          STATIC + LOG CORRELATED
```

---

## 1. DTC24 is not the fuel-path VSS fault bit

`$31` uses two different speed-related faults:

```text
DTC16 / L0016 bit4 = VSS buffer / 2002-PPM VSS failure
DTC24 / L0017 bit5 = output transmission speed / low VSS
```

The running fuel routine explicitly branches on **DTC16** (`L0016 bit4`) at:

```asm
8058: BRSET L0016,#$10,L809C    ; VSS-buffer fault
...
80B5: BRSET L0016,#$10,L80BD    ; VSS-buffer fault
...
8205: BRSET L0016,#$10,L8218    ; VSS-buffer fault
```

A direct `DTC24 -> L024E` or `DTC24 -> L0250` reduction branch was not found in the normal synchronous-fuel calculation.

DTC24 is heavily used in transmission/output-speed diagnostics and related transmission logic, but its mere presence is not equivalent to a direct injector-PW cut command.

This matters for the current log because:

```text
DTC16 = OK
DTC24 = Error
```

Therefore the fuel routine is **not** taking the DTC16 fallback branches merely because DTC24 is set.

---

## 2. VSS-dependent low-speed abuse fuel reduction

With `$400F bit7 = 1`, literal `2.bin` is in the manual-mode branch at `805C-8073`.

The code then checks:

```asm
8073: LDAA L0812          ; VSS
8076: CMPA L5156          ; 16 mph
...
807B: LDAA L01D9          ; TPS
807E: CMPA L5159          ; 75% TPS
...
8083/808A: RPM threshold  ; 4000/3800 RPM hysteresis
...
8099: JMP L821D           ; enter fuel-reduction / cutoff machinery
```

Literal `2.bin` therefore can treat a false-low VSS as "low vehicle speed" and invoke the abuse path, but only with roughly:

```text
VSS <= 16 mph
TPS > 75%
RPM ~4000+ rpm (3800 hysteresis once active)
```

### Relevance to the observed low-RPM stumble

The previously discussed heavy-load event was approximately:

```text
1375-1600 RPM
~80-87 kPa
~32-52% TPS
```

That event cannot satisfy the literal `2.bin` abuse thresholds. Therefore this path cannot explain that specific stumble.

---

## 3. RPM/MPH overspeed fuel cut

The overspeed path begins at `809C`.

The final cut is explicit:

```asm
80E2: BSET L0046,#$10
80E5: LDD  #$0000
80E8: STD  L024E           ; synchronous BPW = 0
```

Literal `2.bin` calibration gives approximately:

```text
RPM cutoff: about 4800 RPM, ~4750 RPM hysteresis
MPH cutoff: 98 mph, ~96 mph hysteresis
minimum RPM for MPH cutoff continuation: 1200 RPM
qualification time: ~1.5 s
```

A garbage VSS value above 98 mph can therefore become dangerous **if it persists long enough while RPM is above 1200**.

However, in `2026-08-19_16.58.52.csv`, the high garbage-speed episodes are short. Representative runs are on the order of ~0.1-0.9 s before the VSS channel falls back below the threshold. The timer is cleared when qualification is lost.

No sustained ~1.5 s >98-mph interval coincident with the analyzed BPW drop was found.

Thus the MPH limiter is a real theoretical VSS-induced fuel-cut mechanism in `2.bin`, but it does not match the examined BPW-drop event.

---

## 4. DFCO speed qualification

DFCO uses VSS at `8205-8218`.

Normal state:

```text
10 mph threshold to enter
7 mph threshold while active
```

Literal `2.bin` bytes:

```text
$493B = 10
$493C = 7
```

When **DTC16** is set, the code bypasses the VSS qualification and can enter DFCO based on its remaining TPS/MAP/RPM/coolant conditions.

But the examined log has:

```text
DTC16 = OK
```

and the road event being investigated had high MAP and substantial throttle rather than the low-TPS / low-MAP deceleration conditions required for DFCO.

The ALDL `Deceleration Enleanment Flag` is also inactive through the identified loaded BPW drop.

Therefore DFCO does not explain that event.

---

## 5. Other raw-VSS fuel dependencies in literal 2.bin

### TPS acceleration enrichment

At `7F45`, VSS below 30 mph selects a low-speed TPS-AE multiplier.

For a missing/low VSS this path adds transient fuel; it is not a lean cut.

### Closed-throttle VE selection

At `7F92-7FA6`, the idle/closed-throttle VE table requires approximately:

```text
TPS < 2.3%
VSS < 2 mph
RPM < 1800
```

At substantial throttle the code jumps directly to the open-TPS VE table before the VSS test, so VSS cannot switch the VE table during the 20-50% TPS loaded events under discussion.

### Separate idle BLM-cell selection

At `8C91-8CA8`, VSS affects the dedicated idle-cell selection only after TPS is below the ~2.3% idle threshold.

Again, it is not involved in the normal loaded BLM cell map at ~20%+ TPS.

### PE entry/delay

Literal `2.bin` has:

```text
$4921 = 0
$4922 = 0
$4923 = 0
$4926/$4927 = 0
```

Thus the VSS-dependent PE delay/speed-delta comparisons are effectively neutral in this calibration. A bad VSS does not explain the loaded BPW drop through those particular PE gates.

### Cold PE

Low VSS can enable extra cold-PE enrichment below its coolant/RPM limits. That effect adds fuel, not removes it.

### Decel enlean low-speed term

VSS below 6 mph enters a low-speed modifier branch, but literal `2.bin` has `$4938 = $80`; regardless, this path requires a deceleration condition and was inactive in the examined loaded event.

---

## 6. Actual BPW-drop event found in the 2026-08-19 log

A clear synchronous-BPW step occurs here:

| Time s | VSS | RPM | MAP kPa | TPS % | BLM cell | BLM | INT | BPW ms |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 600.824 | 7 | 1500 | 54.6 | 20.0 | 8 | 129 | 134 | 3.49 |
| 600.986 | 9 | 1650 | 51.3 | 19.2 | 4 | 120 | 128 | 2.69 |
| 601.139 | 255 | 1625 | 49.5 | 20.0 | 4 | 120 | 128 | 2.70 |

Important ordering:

```text
BPW drop / BLM-cell switch occurs at 600.986 s
VSS = 9 mph at that sample
VSS = 255 mph appears on the NEXT sample at 601.139 s
```

Therefore the 255-mph VSS glitch did **not** initiate this BPW drop.

The drop is temporally locked to a BLM cell transition.

---

## 7. Why BLM cell 8 changed to cell 4

Normal loaded BLM cell selection at `8CCB-8D73` uses RPM and MAP boundaries. VSS is only used in the separate-idle-cell precheck, and that precheck is bypassed when TPS is above the idle threshold.

Relevant code:

```asm
8C98: LDAB L01D9
8C9B: CMPB L48DA       ; ~2.3% TPS
8C9E: BCC  L8CCB       ; loaded TPS -> normal BLM map, bypass VSS idle test
...
8CFD: LDX  #$48F1      ; MAP BLM boundaries
...
8D73: BSET L003D,#$0C  ; BLM address changed / delay update
8D79: LDX  #$02B3      ; BLM-cell storage
...
8D98: STAA L0248       ; active BLM
8D9B: STAB L0247       ; active BLM cell
```

Literal `2.bin` BLM boundaries are shifted from stock. Relevant bytes:

```text
$48EE = 72   ~1800 RPM low boundary
$48EF = 96   ~2400 RPM mid boundary
$48F0 = 128  ~3200 RPM high boundary

$48F1 = 42   ~26 kPa low MAP boundary
$48F2 = 121  ~55 kPa mid MAP boundary
$48F3 = 208  ~87 kPa high MAP boundary

$48F4 = 3    75-RPM hysteresis
$48F5 = 8    ~2.5-kPa MAP hysteresis
```

The existing cell was in the `55-87 kPa` MAP band. With ~2.5 kPa downward hysteresis, the switch to the next lower MAP band occurs at roughly:

```text
55 - 2.5 ~= 52.5 kPa
```

The log goes:

```text
54.6 kPa -> still cell 8
51.3 kPa -> crosses hysteresis threshold -> cell 4
```

That is an exact match to the code behavior.

The new cell contains:

```text
BLM = 120
```

instead of the previous cell's:

```text
BLM = 129
```

Since BLM is a multiplicative fueling correction, this alone changes fuel multiplier from:

```text
129/128 = 1.0078
120/128 = 0.9375
```

or roughly a **7% immediate fuel reduction** from the BLM term.

At the same transition, logged INT falls:

```text
134 -> 128
```

Literal `2.bin` has `$400C = $37`, including the INT-reset-on-BLM-cell-change option. The cell transition therefore also removes the previous positive closed-loop integrator contribution.

Meanwhile MAP itself falls:

```text
54.6 -> 51.3 kPa
```

which reduces the underlying speed-density air-charge term.

Those three effects all point in the same direction:

```text
lower MAP
+ leaner BLM cell (129 -> 120)
+ INT reset (134 -> 128)
= abrupt BPW reduction
```

This combination is a much stronger explanation of the observed `3.49 -> 2.69 ms` step than DTC24 or the subsequent 255-mph VSS glitch.

---

## 8. Current conclusion

For the specific loaded BPW drop identified in `2026-08-19_16.58.52.csv`:

```text
DTC24 itself:                  not the cause found
DTC16 VSS-buffer fallback:     not active (Code16 stayed OK)
MPH overspeed fuel cut:        qualifications not sustained
DFCO:                          conditions/flags do not match
VSS idle/closed-VE logic:      bypassed by ~20% TPS
PE VSS logic:                  neutralized by zero thresholds in literal 2.bin
BLM-cell transition:           exact temporal/code match
```

### Strongest current explanation

```text
MAP crossed the BLM-cell hysteresis boundary
        ↓
BLM cell 8 -> 4
        ↓
BLM 129 -> 120
INT 134 -> 128
MAP 54.6 -> 51.3 kPa
        ↓
BPW 3.49 -> 2.69 ms
```

A bad/unconnected VSS **can** cause other fueling disturbances in literal `2.bin`, including the manual low-speed abuse path or MPH limiter under their specific thresholds. It is therefore still worth removing VSS authority for the manual truck calibration. But it is not the best explanation for this particular BPW step.

## Source anchors

```text
7F45-7F67   low-speed VSS TPS-AE modifier
7F92-7FA8   closed-TPS VE VSS qualification
8058-8099   DTC16 / manual low-speed abuse branch
809C-8109   RPM/MPH overspeed fuel cut -> L024E=0
8175-824D   DFCO including DTC16/VSS qualification
82BC-82E5   VSS-related decel-enlean modifier
8A92-8AB9   VSS-dependent PE delay-bypass path
8BC1-8BDD   cold-PE VSS condition
8BF3-8C32   PE speed-delta delay path
8C79-8C8B   VSS speed-delta bookkeeping
8C91-8CA8   idle BLM VSS qualification
8CCB-8D9B   normal BLM RPM/MAP cell selection and active BLM load
DD/DE       DTC16/DTC24 diagnostic generation
```
