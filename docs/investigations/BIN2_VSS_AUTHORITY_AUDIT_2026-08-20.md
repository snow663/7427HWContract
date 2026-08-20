# Literal `2.bin` VSS Authority Audit — 2026-08-20

## Purpose

Trace every stock `$31` use of vehicle speed that is reachable from the literal numbered `2.bin`, separate active engine-control authority from dormant/peripheral use, and define a VSS-elimination method that does **not** globally force the VSS variable to an arbitrary value.

Literal calibration under audit:

```text
454_bin_versions_1-4.zip / 2.bin
SHA-256: 2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

Primary source:

```text
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

## Top-level conclusion

There is **no globally neutral VSS value** in `$31`.

```text
forcing VSS = 0
  -> enables/qualifies several stationary/low-speed paths
  -> can qualify manual low-speed abuse logic
  -> changes AE, idle/VE, BLM, IAC, spark, purge, etc.

forcing VSS = 255
  -> defeats low-speed paths
  -> can exercise MPH limiter / IAC high-speed authority
  -> changes other speed-qualified logic
```

Therefore the correct architecture is:

```text
VSS acquisition/filter may remain for ALDL/optional telemetry
                 |
                 X  no engine authority
                 |
engine management uses RPM/TPS/MAP/ECT/etc. only
```

The VSS producer does not need to be destroyed. Engine-facing consumers must be patched or replaced individually.

## VSS data-flow root

The complete stock speed data flow is narrow and traceable:

```text
$3FC4 capture/timing state
  -> L080D/L080F + event count L080C
  -> D4A3-D4D9 speed calculation
  -> L0812 raw VSS
  -> D4DA-D4E7 lag filter
  -> L0284:L0285 filtered MPH
  -> direct consumers

L0284:L0285
  -> 8C79-8C85 absolute speed delta L0818
  -> 8C88-8C8B previous speed L081A
  -> 8BF3 PE speed-delta comparison
```

`L0818` is consumed only by the PE speed-delta path at `8BF3`.

## Current `2.bin` mode/calibration facts relevant to reachability

```text
$400F = $80
  bit7 = 1 manual mode
  bit6 = 0 non-electronic TCC path disabled
  bit2 = 0 A/C-clutch-control path disabled
  bit0 = 0 electronic governor option disabled

$4921 = 0 mph        PE speed/delay gate is behaviorally neutral
$4926/$4927 = $0000  PE speed-delta threshold is behaviorally neutral
$490B = 0            special lean-decel VSS branch is unreachable in normal MAP
$48DD = 255          derivative-RPM VSS gate is unreachable at normal coolant
$50DA = 0            governor VSS term bypassed
$4EC0 = 255          first-drive-away IAC VSS test cannot be exceeded by 8-bit VSS
$46FE = 0            EGR VSS minimum is behaviorally neutral
$5B02 bit6 = 0       EGR DTC32 path disabled by mask
$5B01 bit6 = 0       MAT DTC23 path disabled by mask
```

These are byte-verified against literal `2.bin`.

---

# Engine-control VSS consumers

## Fuel / mixture / transient fuel

### `$7F45` — low-speed TPS acceleration-enrichment multiplier

```asm
LDAB L0284
CMPB L48C5      ; 30 mph
```

Below 30 mph, TPS AE is multiplied by the low-speed factor at `$48C4`.

**Authority:** active.

**Elimination:** remove the speed-specific multiplier and retain TPS/MAP-rate AE. A safe same-length technique is to feed this compare a local high sentinel so the low-speed multiplier is always skipped. Do not change global `L0284`.

### `$7F9A` — closed-TPS/idle VE table qualification

Stock requires:

```text
TPS < existing idle threshold
VSS < 2 mph
RPM < 1800
```

**Authority:** active.

**Elimination:** replace the VSS qualifier with an RPM-only stationary/idle-context qualifier. Recommended coherent manual-engine rule:

```text
TPS closed + RPM < 1100 -> closed/idle VE eligible
otherwise -> open-TPS VE
```

The existing later RPM<1800 test may remain as a redundant outer limit.

### `$8073` — manual-trans low-speed abuse fuel reduction

Uses raw `L0812`:

```text
VSS <= 16 mph
TPS > 75%
RPM ~4000+ (3800 hysteresis)
```

and enters the fuel-reduction/cut machinery.

**Authority:** active but condition-specific.

**Elimination:** bypass the VSS-based abuse path. Preserve the ordinary RPM overspeed limiter separately.

### `$80C5` — MPH overspeed fuel cut

After the RPM cutoff comparison, stock compares filtered VSS against the MPH cutoff and can eventually execute:

```asm
LDD #$0000
STD L024E
```

Literal `2.bin` uses about 98 mph off / 96 mph on hysteresis with a ~1.5 s qualification timer.

**Authority:** active and potentially dangerous with garbage speed.

**Elimination:** branch directly from the RPM-cutoff section to the limiter-clear/continue path after the RPM test. This retains RPM protection and deletes MPH fuel cutoff.

### `$8213` — DFCO 10/7-mph qualification

**Authority:** active.

**Elimination:** remove only the VSS comparison. Retain existing TPS, MAP, coolant, RPM, timing and hysteresis conditions. DFCO becomes an engine-state decision rather than a road-speed decision.

### `$82BC` — low-speed decel-enlean modifier

Below 6 mph, stock applies an additional speed-specific decel multiplier.

**Authority:** active during decel.

**Elimination:** skip the low-speed-only multiplier; retain TPS/MAP-rate decel enlean.

### `$82FC` — VSS gate on derivative RPM calculation

This derivative ratio later feeds IAC-flow and idle-spark derivative logic (`L006C`).

Literal `2.bin` has `$48DD=255`, making the path effectively unreachable at normal coolant temperature.

**Authority:** latent/dormant in current calibration.

**Elimination:** remove the VSS gate anyway for a future-proof engine-only derivative path; retain TPS/coolant/RPM conditions.

### `$8765` — closed-loop lean-decel special handling

Literal `2.bin` has `$490B=0`, so the preceding MAP comparison exits before the VSS test under normal operation.

**Authority:** dormant in current calibration.

**Elimination:** optional hardening: bypass the VSS-specific special branch and use ordinary O2 handling, or reformulate it strictly from MAP/RPM.

### `$899B` — idle-state classification used by AFR/idle logic

Stock requires low VSS plus low TPS.

**Authority:** active.

**Elimination:** replace VSS with coherent idle-context RPM:

```text
TPS below existing threshold + RPM <= ~1100 -> idle state
```

### `$8A92` — PE delay bypass VSS comparison

Literal `2.bin` has `$4921=0`, therefore unsigned VSS is always >= threshold and the read cannot change behavior.

**Authority:** behaviorally neutral in current calibration.

**Elimination:** optional hardening; remove the read so future calibration changes cannot reintroduce VSS authority.

### `$8BCF` — cold-PE speed qualification

Below the cold coolant/RPM thresholds, VSS <25 mph allows additional cold PE enrichment.

**Authority:** active only cold / low RPM / PE.

**Elimination:** remove the VSS condition and retain coolant+RPM+PE qualification. This is the conservative direction because it preserves cold enrichment rather than deleting it.

### `$8C79/$8C88 -> L0818 -> $8BF3` — PE speed-delta bookkeeping

Literal `2.bin` threshold `$4926/$4927=$0000`, so the comparison is behaviorally neutral.

**Authority:** latent only.

**Elimination:** force the local speed-delta state to zero (or bypass the delta test) so future table changes cannot restore VSS authority.

### `$8CA0` — separate idle BLM cell qualification

Stock requires low TPS and VSS<2 mph.

**Authority:** active.

**Elimination:** replace VSS with the same manual idle-context RPM rule used by `$7F9A/$899B`:

```text
TPS closed + RPM <1100 -> idle BLM cell eligible
```

This keeps VE/idle-state/BLM semantics aligned.

---

# IAC / throttle-follower VSS consumers

### `$99F2` — closed-loop IAC qualification

Stock uses TPS plus a low-VSS gate (`$4EF3=4` in literal `2.bin`).

**Authority:** active.

**Recommended elimination:** use RPM<1100 instead of forcing a fake 0-mph value. This prevents closed-loop idle from being entered at high coasting RPM merely because VSS no longer exists.

### `$9C4D` — IAC proportional-authority limiting versus high VSS

Stock uses 100/255-mph thresholds; a garbage 255 value can exercise this logic.

**Authority:** active when the idle-RPM-too-high path is active.

**Elimination:** bypass this speed-based proportional-authority limiter completely and retain the normal RPM-error authority calculation.

### `$9D15` — throttle-follower filtered-TPS delay versus VSS

**Authority:** active in the throttle-follower path.

**Elimination:** use a fixed local lookup input rather than VSS. For a clean `2.bin` A/B, use the existing 0-mph endpoint without changing the table itself.

### `$9D47` — throttle-follower filter coefficient versus VSS

**Authority:** active.

**Elimination:** same as `$9D15`: fixed local 0-mph lookup input; retain the original `2.bin` table and MAP modifier.

This removes VSS without importing the later "door closer" calibration changes, keeping the experiment isolated.

### `$9EA7` — first-drive-away IAC kickdown

`$4EC0=255`; an 8-bit VSS cannot exceed it, so the speed-dependent action cannot occur in literal `2.bin`.

**Authority:** behaviorally neutral.

**Elimination:** optional local zero substitute for hard isolation.

### `$9F6C` and `$9FD3` — throttle-kicker speed qualification

Uses a 10-mph threshold.

**Authority:** conditional IAC/throttle-kicker authority.

**Elimination:** remove local VSS reads. For current-bin preservation, use the low-speed/local-zero branch behavior; do not globally zero VSS.

### `$A3F2` — VSS-triggered IAC motor reset

At >=30 mph the stock code can initiate IAC motor reset/re-home state while running.

**Authority:** active and important with garbage high VSS.

**Elimination:** delete the running VSS-triggered reset path. Preserve the separate ignition-off/reset path.

---

# Spark / knock VSS consumers

### `$A85A` — idle-spark enable below 3 mph

**Authority:** active.

**Recommended elimination:** replace VSS<3 mph with RPM<1100, retaining the existing TPS/coolant/RPM-error idle-spark machinery.

### `$AA9D` — knock-retard low-speed qualification

Stock behavior:

```text
VSS >=2 mph -> proceed to knock logic
VSS <2 mph  -> require RPM >=800
```

At normal road RPM above 800 this usually makes no difference, but VSS is still an authority input.

**Elimination:** always execute the existing RPM>=800 check, then continue with normal knock logic. No VSS required.

---

# Speed diagnostics and indirect failure-state authority

## DTC16 / `L0016 bit4`

DTC16 is the VSS-buffer fault actually read by engine routines.

Engine-side DTC16 branches exist at:

```text
$8058  manual-abuse/fuel path fallback
$80B5  overspeed RPM-threshold selection
$8205  DFCO VSS bypass
$9B8A  IAC adaptive/fallback behavior
$9BDA  IAC fallback minimum flow behavior
$A3A3  IAC diagnostic qualification
$CBD2  A/C fallback (dormant in 2.bin)
$CF90  EGR fallback
```

Therefore merely disabling the dashboard code is insufficient: if the DTC16 bit is allowed to set, it changes engine behavior.

**Elimination:** prevent the DTC16 state bit from being set (force its set site to clear/no-op), then remove the direct VSS gates listed above. This leaves the IAC/fuel algorithms on their normal non-fault paths.

## DTC24 / `L0017 bit5`

DTC24 is transmission/output-speed low. No direct DTC24-to-BPW path was found, but it is irrelevant/noisy in this manual no-VSS configuration.

**Elimination:** prevent both DTC24 set paths from asserting the state bit. Keep it clear.

---

# Peripheral or dormant VSS consumers in literal `2.bin`

These are part of the complete trace but are **not integral engine-control authority in the current calibration**.

| Address | Subsystem | Literal `2.bin` status | Recommended treatment |
|---|---|---|---|
| `$8EE9` | electronic governor | `$400F bit0=0`; `$50DA=0` | leave dormant |
| `$ACFC` | shift-light/gear estimator | peripheral | leave or disable separately; do not use as core state |
| `$ADB4/$ADDE/$AE11` | TH700R4/non-electronic TCC | `$400F bit6=0` | leave dormant |
| `$CBD6` | A/C clutch control | `$400F bit2=0` | leave dormant |
| `$CF94` | EGR VSS qualification | threshold `$46FE=0` | behavior-neutral; leave peripheral |
| `$D2EC` | canister purge speed qualification | emissions peripheral | isolate/disable with purge feature if desired |
| `$D2F9` | purge zero-speed reset | threshold `$402F=0`, behavior-neutral | leave peripheral |
| `$DC17` | MAT DTC23 qualification | DTC23 mask bit disabled | no core authority |
| `$DEBF` | EGR DTC32 qualification | DTC32 mask bit disabled | no core authority |

The VSS producer/filter at `$D4A3-$D4E7` may also remain. Keeping it allows ALDL to show what the PCM thinks VSS is, which is diagnostically useful even after engine authority has been removed.

---

# Recommended elimination architecture for a clean `2.bin` A/B test

Do **not** import the later door-closer calibration reshaping. Start from literal `2.bin` and change only VSS authority.

## Group A — replace "vehicle stopped" semantics with engine idle context

Use one coherent rule:

```text
IDLE_CONTEXT := TPS below existing local idle threshold AND RPM <~1100
```

Apply to:

```text
$7F9A closed-TPS VE
$899B idle-state classification
$8CA0 idle BLM cell
$99F2 closed-loop IAC qualification
$A85A idle spark
```

## Group B — remove road-speed modifiers from engine math

```text
$7F45 TPS AE low-speed multiplier        -> remove
$8213 DFCO road-speed gate               -> remove
$82BC low-speed decel-enlean multiplier  -> remove
$82FC derivative-RPM VSS gate            -> remove
$8765 VSS-specific lean-decel handling   -> remove/engine-state only
$8BCF cold-PE VSS gate                   -> remove; retain cold enrichment
$8C79/$8C88 PE speed-delta state         -> force local zero / no authority
```

## Group C — retain engine protection, delete road-speed protection

```text
$8073 manual low-speed abuse cut -> bypass
$80C5 MPH limiter                -> bypass
RPM overspeed limiter            -> RETAIN
```

## Group D — remove VSS from IAC/throttle follower

```text
$9C4D speed-based prop limit -> bypass
$9D15/$9D47 VSS lookup input -> fixed local endpoint
$9F6C/$9FD3 kicker VSS gates -> local neutral behavior
$A3F2 running VSS reset      -> delete; key-off reset retained
```

## Group E — knock

```text
$AA9D -> always require existing >=800 RPM qualification
```

## Group F — diagnostics

```text
DTC16 state -> cannot set
DTC24 state -> cannot set
```

## Group G — leave telemetry/peripherals isolated

Do not globally rewrite `L0284`. Let the PCM continue to calculate/report VSS, but engine-control decisions must no longer consume it.

---

# Why this is superior to global-zero VSS

A global zero is not neutral:

```text
0 mph would:
  select low-speed AE multiplier
  satisfy idle/closed-VE and idle-BLM speed gates
  qualify low-speed manual-abuse check
  alter DFCO/decel behavior
  alter IAC/throttle-kicker logic
  alter purge behavior
```

A global 255 is not neutral either:

```text
255 mph can:
  enter MPH-limiter logic
  exercise IAC high-speed proportional authority
  defeat idle/closed-VE/BLM gates
  alter multiple peripheral controls
```

Per-consumer authority removal is therefore the only robust method.

## Classification

```text
VSS-DATAFLOW-ROOT:                    CONFIRMED STATIC
DIRECT-L0284/L0812-CONSUMER SET:      CONFIRMED STATIC
L0818 SPEED-DELTA DEPENDENCY:         CONFIRMED STATIC
LITERAL-2.BIN MODE/THRESHOLD STATE:   BYTE VERIFIED
GLOBAL-ZERO/255 NOT NEUTRAL:           CONFIRMED STATIC
CORE VSS-ELIMINATION METHOD:          DESIGN RECOMMENDATION BASED ON STATIC TRACE
```

## Next implementation gate

Build a **literal-`2.bin` VSS-authority-only derivative** with:

```text
no VE changes
no spark-table changes
no PE-threshold changes
no injector-flow changes
no BLM changes
no door-closer calibration changes
```

Only the authority-removal groups above plus checksum should differ.

Then road-test A/B against literal `2.bin` with the same ADX/logger so any change in stumble/transition behavior can be attributed to VSS authority removal rather than a mixed calibration change.
