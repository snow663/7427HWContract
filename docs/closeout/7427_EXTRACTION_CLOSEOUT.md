# 7427 Extraction Closeout

## Authority and scope

Primary variant for this closeout:

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
production ROM authority: BMHM_95_C-G-K_Truck_7_4TBI_4l80.bin
working executable source: source/31/BMHM_HAC_ORG_7100_to_end.asm
calibration source: 31_HAC_calibration_extract_nowrap.html
```

Evidence policy:

- actual BMHM production ROM bytes are numeric calibration authority;
- executable BMHM source/disassembly is semantic-use and provenance authority;
- source comments are descriptive evidence only and lose to executable cadence/dataflow;
- physical voltage/current/polarity/pin behavior is not proven from software;
- no cross-mask convergence is required for this closeout.

Architecture rule:

```text
CALIBRATION
    ↓
ALGORITHM / CONTROL LOGIC
    ↓
COMMANDS / ARBITRATION
    ↓
HAL
    ↓
7427 HARDWARE CONTRACT
```

Classification rule:

```text
mathematical/control relationship = algorithm
values plugged into it             = calibration
register/mailbox/port access       = hardware/HAL
physical voltage/current/polarity  = bench endpoint
```

## A. Audit baseline at start of this closeout pass

These percentages are scoped to semantic production-control extraction only. They do not include connector confirmation, electrical polarity, driver current, real-load actuator behavior, replacement-ROM boot validation, standalone-OS implementation, unrelated masks, or future configurator work.

| Category | Start | Reason it was not yet frozen |
|---|---:|---|
| Major algorithm reverse engineering | 94% | Fuel was substantially closed; spark composition and idle/IAC control law existed in source but were fragmented and were still represented as open work. |
| Scheduler / lifecycle understanding | 97% | 6.25 ms / 16-segment scheduler was mapped; key-off/shutdown state clearing and semantic power-down boundary were not consolidated into closeout. |
| Diagnostics / failsafe understanding | 90% | DTC/diagnostic machinery was heavily mapped, but actual replacement-relevant substitutions/fallbacks were not separated cleanly from reporting/bookkeeping. |
| Calibration / tuning extraction | 93% | Full source calibration extract existed, but module classification was heuristic and the required target-BIN numeric audit had not been run to completion. |

## B. Exact items that prevented the first four categories from reaching 100%

At the start of this pass the genuine semantic work was:

1. Consolidate the production spark calculation from table/modifier inputs through final spark intent and conversion boundary.
2. Consolidate the idle/IAC control loop from desired idle through error, P/I/D/follower/transition terms to desired IAC steps.
3. Fold key-off/shutdown, run-state clearing, timer cadence, and scheduler dispatch into one lifecycle model.
4. Separate diagnostic reporting from actual fallback behavior and document the substitutions that materially change engine control.
5. Replace heuristic calibration routing with an explicit production-control calibration manifest.
6. Compare directly labeled calibration data against the actual BMHM production BIN and record any disagreements in a correction overlay.

Items 1-5 are closed by this pass. Item 6 remains open only because the raw BMHM BIN is not currently retrievable from the repo, File Library, current local project files, or the exact-name Drive search. Existing ROM-derived reports prove the target identity and some exact bytes, but a derivative report is not a substitute for the raw BIN in a byte-for-byte calibration audit.

## C. Apparent unknowns removed from the algorithm backlog

The following are not algorithm gaps and must not reduce algorithm completion:

### Spark / ignition HAL and bench boundaries

- physical EST/bypass authority pin and polarity;
- exact physical role of `$3FE8` versus `$3FE6`;
- physical meaning/necessity of `$3FF6/$3FDC` first-event rolling seed;
- whether `$3FEC -> $3FE4` is monitor ACK, handoff synchronization, or both;
- physical missing-REF behavior of ignition hardware;
- output voltage, current, edge polarity, dwell waveform, and connector pin.

The software path is sufficiently understood to expose a semantic `SparkCommand`; the above belong behind the HAL and endpoint test gate.

### IAC HAL and bench boundaries

- which connector pins are coil A and coil B;
- whether source `EXTEND` corresponds physically to pintle extend / airflow close on this harness;
- physical phase polarity and driver current;
- exact effect of the `L3062` output bits at the connector;
- hard-stop direction, stall current, park-motion result, and step time under load.

The source already proves desired-vs-actual comparison, zero-step direction reversal, count update, phase-ring progression, output-shadow merge, and desired-position calculation. Physical direction is an endpoint test, not an algorithm trace.

### Fuel HAL and bench boundaries

- physical injector output pins/current waveform;
- exact `$3FCE` physical transfer relation and zero-command behavior;
- companion ASIC initialization side effects.

These remain output-contract / bench questions, not fuel-math questions.

### Sensor/input bench boundaries

- connector pin identity where not already physically confirmed;
- actual voltage range, polarity, pullup/pulldown behavior, source impedance, frequency amplitude, and ground reference;
- real ADC transfer measured at the pin.

Software acquisition/scaling can be complete while these remain unconfirmed.

## D. Shortest ordered worklist

The closeout worklist is:

1. **Spark semantic closeout** — consolidate the source-computed spark intent and conversion boundary. **DONE.**
2. **IAC semantic closeout** — consolidate desired idle, RPM error, P/I/D/follower/transition flow terms, flow-to-step conversion, and stepper command intent. **DONE.**
3. **Scheduler/lifecycle closeout** — freeze reset, 6.25 ms heartbeat, 16-segment dispatch, REF/DRP lifecycle, key-off state clearing, shutdown delay, and safe dropout responsibilities. **DONE.**
4. **Diagnostics/failsafe closeout** — preserve only substitutions/fallbacks and safety gates that materially affect control; separate them from DTC reporting. **DONE.**
5. **Calibration semantic manifest** — replace keyword-only section routing for production-control use. **DONE by companion artifact.**
6. **Target-BIN calibration audit** — run the prepared audit tool against the exact 64 KiB BMHM production BIN, preserve source and BIN evidence, and emit the correction overlay. **BLOCKED ONLY BY RAW BIN AVAILABILITY.**
7. When step 6 is complete, set calibration/tuning to 100%, freeze all four extraction categories, and immediately proceed to endpoint test-confirm and engine-off safe-runtime implementation.

## Definition of 100% for the four extraction categories

### 1. Major algorithm reverse engineering — 100% means

For the production engine-control scope, every material control output has a semantic relationship from inputs/state/calibration to command intent:

- fuel: crank, run speed-density/VE, open-loop AFR, closed-loop trim, warmup/afterstart, AE, PE, DFCO, injector correction/deadtime/low-PW behavior;
- spark: base/open/closed-throttle spark, coolant/MAT/altitude/WOT/startup/idle corrections, low-octane and knock-retard behavior, knock-fail fallback, limits, final spark intent, and degree/time conversion inputs;
- idle air: park/reset/startup air, desired idle selection, enable qualifications, RPM error, integral/proportional/derivative terms, follower and transition terms, flow-to-step conversion, and semantic step request;
- production command arbitration/safe inhibits are identified separately from hardware writers.

It does **not** require physical output proof.

**Status after this pass: 100% — FREEZE.** Reopen only for contradictory executable evidence or a newly included production feature.

## Production spark closeout

The remaining spark trace is classified as **already semantically understood but poorly consolidated**, not genuinely incomplete.

Key executable chain:

```text
load/RPM/base table paths
+ altitude / MAT / coolant / WOT / startup / idle corrections
- configured biases
- low-octane retard
- applicable production retard terms
→ L01FD final spark advance
→ subtract initial distributor setting L4132
→ L01EE signed/current timing intent
→ max-advance/retard clamps
→ burst-knock / knock-retard contribution
→ knock-sensor-fault fixed retard when required
→ sign/magnitude and latency/period conversion
→ rolling timing state / ASIC handoff boundary
```

Source anchors include:

- `A77A-A78F`: low-octane MAP/RPM multiplier applied to learned/base low-octane retard;
- `A7D7-A81B`: final spark component summation and bias/retard subtraction into `L01FD`;
- `A857-A900`: idle spark qualification and underspeed/overspeed correction path;
- `AA1A+`: initial-distributor-setting transform and maximum-advance handling;
- `AA33+`: burst-knock qualification/retard;
- `AAB0`: knock-sensor failure uses calibrated fixed retard (`L4E77`, source comment 4 deg);
- `AB41+`: final sign/magnitude, latency/period conversion and timing handoff sequence.

Transmission torque-management and EGR-specific spark modifiers are not replacement blockers and remain excluded unless intentionally enabled in a future feature set.

## Production IAC / idle-air closeout

The remaining IAC work is classified as **already semantically understood but poorly documented**.

### Command/output state path

`L91A3-L920D` proves:

```text
actual IAC count L0007
vs desired IAC count L0008
→ choose extend/retract semantic direction in L000A bit0
→ on a direction reversal, change direction first without changing count
→ otherwise increment/decrement L0007 one step
→ advance A/B coil phase ring in L000A bits2/3
→ merge IAC bits into output shadow L004C
```

The zero-step direction reversal is deliberate and must be preserved semantically even if the replacement HAL uses different implementation details.

### Desired-position/control-law path

`L93D0+` establishes reset/park, closed-loop enable delay, startup air, and desired-idle selection. `L96F0+` computes absolute RPM error and a high/low sign. The production loop then calls the IAC control terms and combines them:

```text
base/integral airflow L0862
+ follower / transition airflow L0871
± proportional term L086D
± derivative term L0870
+ startup air L086B
+ power-steer add L087B when feature used
± A/C transition term L0876
+ park/drive transition term L0879
± DFCO-related airflow correction L0887
+ other explicitly qualified production idle-air terms
→ bounded desired airflow
→ altitude correction
→ flow-to-step table rooted at L4E92
→ desired IAC count L0008 (store at L9899)
```

`L99C5`, `L9C20`, and `L9CA6` are the integral/proportional/derivative-side production-control helpers used in this loop; the derivative path uses the fast/slow coefficients at `L503A/L503B` and preserves its add/subtract sign separately.

Desired idle RPM tables include the calibrated P/N, drive, and A/C state families rooted at `$4F32/$4F41/$4F50/$4F5F`, with startup/not-running initialization also represented.

This is enough to implement a clean semantic idle controller without carrying GM RAM packing or direct `L3062` access into the algorithm.

### 2. Scheduler / lifecycle understanding — 100% means

The replacement can reproduce all production-relevant timing/lifecycle obligations without copying OEM task-bookkeeping:

- reset/initialization ordering;
- hardware-register relocation;
- heartbeat/base cadence;
- foreground/background dispatch relationship;
- REF/DRP event ownership and run qualification;
- timer/event contexts needed by production engine control;
- key-on, crank, run, stall/dropout, key-off, delayed shutdown, and watchdog-safe semantic states;
- overrun awareness.

**Status after this pass: 100% — FREEZE.**

Key lifecycle facts:

- boot relocates HC11 registers to `$3000` and initializes timer/ASIC state;
- `L7459` seeds TOC3 from `TCNT + 8` and enters the `WAI` background model;
- `L793D` reschedules TOC3 by `0x0333` = 819 timer counts, giving the documented 6.25 ms heartbeat;
- low nibble of major-loop counter dispatches 16 segments through the table at `L7A85`, yielding a 100 ms complete 16-segment cycle;
- overrun is explicitly detected/flagged rather than hidden;
- REF/DRP event paths update period/RPM and crank/run state independently of foreground bookkeeping;
- ignition-off qualification clears run/fuel/RPM/DRP state after the shutdown sequence begins;
- `L7D4B+` compares shutdown counter `L027E` against calibration `L4009` before final power-down register action;
- the physical interpretation of the final power-control register write is HAL/bench territory and does not make lifecycle semantics incomplete.

A clean replacement scheduler may use the same necessary cadences without reproducing the OEM major-loop counter encoding.

### 3. Diagnostics / failsafe understanding — 100% means

Every fault that materially changes production fuel/spark/idle/lifecycle behavior has a defined validation/substitution/safe-state rule. DTC counting/reporting need not be cloned unless required for observability. A DTC is never treated as the fallback itself.

**Status after this pass: 100% — FREEZE.**

Material substitutions/safe behaviors are captured in `7427_DIAGNOSTIC_FAILSAFE_CLOSEOUT.md`.

### 4. Calibration / tuning extraction — 100% means

- all production-control calibration items have semantic ownership and scaling/provenance sufficient for the replacement modules;
- excluded transmission/EGR/EVAP/service material is separated from production engine-control calibration;
- directly labeled source bytes/words are audited against the **actual target BMHM BIN** wherever practical;
- source/BIN mismatches, width/address issues, and odd-word-address cases are machine-readable;
- stock-equivalent numeric reconstruction uses BIN values when source and BIN disagree, unless executable behavior proves another interpretation.

Source extraction is structurally complete: 226 sections, 11,916 data records, 11,431 FCB records, 485 FDB records, `$4000-$70FF`, zero parser errors.

The source header `$4000-$400F` matches the known ROM-derived header evidence exactly:

```text
25 17 00 00 00 00 68 8C 31 01 91 04 B7 82 03 10
```

However, a complete byte-level target-BIN audit cannot be claimed without the raw 64 KiB BMHM file itself.

**Status after this pass: 98% — NOT FROZEN.** The remaining 2% is exclusively the raw-BIN comparison/correction-overlay execution, not more semantic disassembly.

## Current phase-1 classification

### COMPLETE major production algorithms

- crank/run fuel and injector command intent;
- speed-density/VE and AFR target logic;
- warmup/afterstart and crank transition;
- AE / pump-shot behavior;
- PE / WOT enrichment;
- DFCO/decel fuel behavior;
- closed-loop O2 trim/learning semantics;
- spark base tables and production corrections;
- idle spark correction;
- low-octane/knock-retard logic and knock-fail fixed retard;
- final spark intent and degree/time conversion dependency;
- IAC park/startup, target RPM, feedback correction, transition/follower, and flow-to-step control;
- semantic IAC step direction/phase request.

### Genuine remaining algorithm gaps

None in the defined production engine-control replacement scope.

A newly added optional subsystem or intentionally retained OEM feature is a new scope item, not an old algorithm gap.

### Calibration extraction gap

One: execute the source-vs-raw-BMHM-BIN audit and apply any correction overlay.

### Diagnostic/failsafe gaps

None in semantic production-control scope. Physical fault-line behavior remains endpoint/HAL work where applicable.

### Scheduler/lifecycle gaps

None in semantic production-control scope. Physical power-control semantics remain HAL/bench work.

### Hardware/HAL gaps

- sensor ADC channel/pin endpoint proof;
- REF/DRP physical input characteristics;
- injector ASIC/driver physical behavior;
- spark ASIC pair/rolling-state/EST-bypass physical behavior;
- IAC latch-to-driver/pin behavior;
- fuel-pump, MIL, A/C, fan/auxiliary outputs retained by final feature set;
- watchdog/power-control peripheral effects where not already processor-defined.

### Physical bench boundaries

For every retained input/output: connector/pin, polarity, voltage/current/frequency range, physical scaling, monotonicity, timing, load behavior, and PASS/FAIL confirmation.

### Optional/disabled/service-test code not required for production replacement OS

- factory test mode;
- ALDL forced-control/service overrides other than development observability;
- transmission/TCC/shift strategy;
- EGR/EVAP strategy when disabled in the replacement feature set;
- remote-broadcast/OEM bookkeeping not required by hardware;
- OEM DTC counter packing where a semantic diagnostic state is equivalent;
- shadow/export variables used only for reporting;
- torque-management spark/fuel behavior tied solely to excluded transmission strategy.

## Freeze rule

Algorithms, scheduler/lifecycle, and diagnostics/failsafe are frozen at 100% under the scopes above. They are not to be reopened merely because more stock code can be traced.

Calibration remains at 98% until the raw BMHM audit is executed. No additional open-ended disassembly is authorized as a substitute for that missing numeric evidence.
