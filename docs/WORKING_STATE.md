# Working State

This repository is the working directory for the 7427 hardware-contract and replacement-OS project. Git history is the version record. Downloadable ZIPs and older File Library documents are supporting evidence, not automatic current authority.

## Current primary target

```text
PCM: 16197427
mask: $31
BCC/object: BMHM
target production ROM: BMHM_95_C-G-K_Truck_7_4TBI_4l80.bin
working executable source: source/31/BMHM_HAC_ORG_7100_to_end.asm
```

The current closeout authority is:

- `docs/closeout/7427_EXTRACTION_CLOSEOUT.md`
- `docs/closeout/7427_DIAGNOSTIC_FAILSAFE_CLOSEOUT.md`
- `docs/closeout/7427_PRODUCTION_CALIBRATION_MANIFEST.md`
- `docs/closeout/7427_COMPLETION_STATUS.md`
- `maps/closeout/calibration_bin_audit_status.csv`
- `tools/audit_calibration_against_bin.py`

## Architecture rule

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

Classification:

```text
mathematical/control relationship = algorithm
values plugged into it             = calibration
register/mailbox/port access       = hardware/HAL
physical voltage/current/polarity  = bench endpoint
```

No control algorithm in the replacement OS may directly touch HC11 peripheral addresses, ASIC addresses, connector pins, or stock RAM mailboxes. Hardware-specific access belongs behind the 7427 HAL.

## Extraction closeout status

Scoped to semantic production-control extraction only:

```text
algorithm extraction           100%  FROZEN
scheduler/lifecycle            100%  FROZEN
diagnostics/failsafe           100%  FROZEN
calibration/tuning              98%  WAITING ONLY FOR RAW TARGET-BIN AUDIT
```

Do not reduce the first three percentages because hardware bench work remains.

Do not reopen a frozen category merely because more stock code can be traced. Reopen only for contradictory executable/ROM evidence or an explicitly expanded production feature scope.

## What the closeout pass resolved

### Spark

The prior “remaining spark trace” is no longer an algorithm backlog item.

The `$31` source now has a consolidated semantic path covering:

```text
base/open/closed-throttle spark
+ coolant/MAT/altitude/WOT/startup/idle corrections
- configured biases
- low-octane retard
- knock/burst-knock contribution where enabled
- knock-sensor-fail fixed protective retard
→ final spark intent
→ distributor/base-setting transform and clamps
→ degree/time + latency/REF-period conversion
→ rolling timing state / ASIC handoff boundary
```

Physical `$3Fxx` role/pin/polarity and EST/BYPASS authority remain HAL/bench questions only.

### IAC / idle

The prior “idle/IAC loop breakdown” is no longer an algorithm backlog item.

The `$31` source now has a consolidated semantic path covering:

```text
park/reset/startup state
desired idle RPM selection
closed-loop qualification/delay
RPM error and high/low sign
integral/base airflow
± proportional term
± derivative term
follower / P-N-drive / A-C / power-steer / DFCO transition terms where used
altitude correction
flow-to-step conversion
desired IAC count
actual-vs-desired step request
zero-step direction reversal
A/B phase-ring progression
output-shadow merge
```

Physical coil pins, direction/open-close polarity, current, hard stop, and `L3062` connector behavior remain endpoint tests.

### Scheduler / lifecycle

Production-relevant lifecycle is frozen:

```text
reset/init
HC11 register relocation
TOC3 6.25 ms heartbeat
16-segment / 100 ms complete dispatch pattern
REF/DRP event ownership and run qualification
crank/run/stall/dropout state
major-loop overrun detection
key-off state clearing
delayed shutdown using L4009/L027E
watchdog-safe responsibility
```

The physical effect of final power-control register writes is HAL/bench work.

### Diagnostics / failsafe

Replacement-relevant fault behavior is separated from DTC bookkeeping.

Material behaviors include:

```text
MAP invalid      → TPS/RPM-derived substitute, else calibrated safe default
TPS invalid      → calibrated default before filtering
coolant invalid  → calibrated safe-warm default
MAT/IAT invalid  → calibrated default
O2 invalid       → no closed-loop feedback/trim update
knock invalid    → calibrated fixed protective retard
REF/DRP invalid  → fuel no-pulse + spark safe intent + period invalidation
battery invalid  → output permission/key-off/IAC motion gating
NVRAM invalid    → deterministic learned-state/IAC seeds
cal invalid      → do not enable production actuators
scheduler fault  → safe-state policy
```

A DTC is not itself a fallback.

## Calibration state and the only remaining extraction blocker

The source calibration extract is structurally complete:

```text
226 sections
11,916 labeled records
11,431 FCB
485 FDB
$4000-$70FF
0 parse errors
96 retained source/extraction warnings
```

The production-control calibration manifest replaces heuristic keyword classification as the ownership authority.

The source header `$4000-$400F` matches existing raw-ROM-derived BMHM evidence:

```text
25 17 00 00 00 00 68 8C 31 01 91 04 B7 82 03 10
```

But the exact 64 KiB raw BMHM production BIN is not currently present in the repo/current local files and was not exposed by exact-name File Library/Drive search. Therefore the complete source-vs-BIN byte/word audit cannot honestly be claimed yet.

Prepared audit:

```text
python tools/audit_calibration_against_bin.py \
  --extract 31_HAC_calibration_extract_nowrap.html \
  --bin BMHM_95_C-G-K_Truck_7_4TBI_4l80.bin \
  --audit maps/closeout/calibration_bin_audit.csv \
  --overlay maps/closeout/calibration_bin_correction_overlay.csv
```

The audit records value mismatches, source-width problems, FDB address alignment review, and label/address-width review. BIN bytes remain numeric authority.

Until that exact raw-BIN audit is run:

```text
calibration/tuning = 98%
```

No amount of additional disassembly substitutes for the missing numeric authority.

## Source-authority cleanup

Older File Library documents include:

```text
7427_Full_Control_Model.docx                    → explicitly $0E
16196395_PCM_Architecture_Custom_OS_Developer_Guide.docx → 16196395 / BJKZ / $0E
```

They are historical/corroborating architecture material only. They do not override the current `$31` BMHM variant.

The `$31` tuning handbook remains supporting tuning context and correctly reinforces the rule that BIN/mask/file identity must be verified before calibration work.

## Hardware-contract state

Current software-facing hardware-contract completion is tracked separately from physical proof.

```text
software-facing HW contract     92%
physical endpoint confirmation   0%
```

Static/software-facing evidence is already strong for:

- HC11 relocated register ownership;
- hardware-access/write-target maps;
- ASIC register inventory;
- REF period/count software interface;
- fuel timer/output scheduling;
- spark conversion/handoff boundary;
- IAC actual/desired/phase/output-shadow path;
- SCI/ALDL interface;
- COP/watchdog service path;
- boot/init sequencing.

Software-facing work still required for 100%:

```text
one normalized HAL endpoint/API inventory for every retained production endpoint
sensor acquisition/conversion ownership in that inventory
retained auxiliary-output ownership only for features actually kept
final semantic treatment of shared ASIC mirror/ACK state that must survive
safe init/default/permission state for every retained HAL endpoint
```

These are software/HAL tasks. They do not require claiming a connector pin or physical polarity.

## Physical bench frontier

Existing physical proof is not counted until measured evidence exists.

`docs/bench/FUEL_SLICE0_BENCH_RESULTS.md` and `maps/bench/fuel_slice0_bench_results.csv` currently remain `not_run`.

Therefore:

```text
physical endpoint confirmation = 0%
```

Bench boundaries include:

- exact injector header mapping and downstream polarity/current;
- exact EST/BYPASS physical pin/authority behavior;
- ASIC-to-header ignition trace relationships;
- injector fault-feedback physical path;
- IAC A/B/enable pin mapping, polarity, current, hard-stop direction;
- sensor connector/pin voltage/frequency transfer and monotonicity;
- retained auxiliary output pin behavior.

## Existing stock-driver / bench gates remain valid

The closeout does not relax existing output proof gates.

### Fuel

```text
stock output-driver preservation: not yet accepted complete
active route: compact $3FCE SLICE-0 bench path
FUEL-001..FUEL-004: not_run until measured bench evidence exists
FUEL-004 specifically requires actual dropout/unsafe zero-path evidence
SLICE-1 remains blocked under compact route until FUEL-001..FUEL-004 pass
```

### Spark

```text
stock handoff preservation: accepted static route
clean OS may calculate semantic spark
preserved stock-compatible handoff may own ASIC writes
custom direct ASIC spark writer remains bench-required
```

### IAC

```text
stock driver preservation contract exists
preservation proof is not complete
custom direct A/B/enable/park writer remains bench-required
```

A control algorithm being complete does not authorize its actuator.

## Replacement OS status

```text
replacement-OS implementation  5%
complete runnable replacement   0%
```

Existing skeleton/minimal fuel writer/bench harness count as infrastructure only. They are not an engine-control OS and are not hardware-/production-ready.

No engine-runnable actuator slice should be enabled before the closeout phase gate and endpoint permissions are satisfied.

## Next valid work

Strict order:

```text
1. Re-expose the exact raw BMHM 64 KiB production BIN.
2. Run tools/audit_calibration_against_bin.py.
3. Review/commit calibration_bin_audit.csv and calibration_bin_correction_overlay.csv.
4. Set calibration/tuning to 100% and FREEZE the fourth extraction category.
5. Build normalized Stage-1 endpoint SETUP records from existing contracts.
6. Execute physical input tests stimulus → raw/converted software value.
7. Execute physical output tests semantic command → HAL/register → pin response.
8. Implement engine-off safe runtime:
      reset/boot
      scheduler
      sensor acquisition
      lifecycle
      diagnostics/validity
      ALDL/development observability
      safe command arbitration
      all production actuator permissions disabled
9. Bring up one endpoint at a time behind explicit permission gates:
      sensors
      IAC
      spark/EST
      injectors
      first controlled start
      closed loop/learning
      retained auxiliary outputs
```

Do not proceed to open-ended disassembly as a substitute for any of these steps.
