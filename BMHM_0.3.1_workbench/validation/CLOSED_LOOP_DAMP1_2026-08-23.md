# Closed-loop DAMP1 validation — 2026-08-23

## Logs

Reference:
- `2026-08-22_19.59.25.csv` — pre-DAMP1 reference.

Current:
- `2026-08-23_23.20.05.csv` — BMHM 0.3.1 / DAMP1 / no-VSS consumer patch / true-idle RPM gate.

This is not a controlled dyno A/B; road load and learned BLM state differ. The comparison is therefore evidence of direction/magnitude, not a transfer-function measurement.

## DAMP1 target region

For a comparable closed-loop subset the analysis used:

- closed loop active,
- PE inactive,
- AE inactive,
- DFCO off,
- TPS >2.5%,
- RPM 1200-3200,
- MAP 50-100 kPa.

Results:

| Metric | Pre-DAMP1 | BMHM 0.3.1 |
|---|---:|---:|
| samples | 382 | 485 |
| INT mean | 127.07 | 128.45 |
| INT median | 127 | 128 |
| INT std dev | 5.44 | 4.72 |
| mean `abs(INT-128)` | 4.07 | 3.15 |
| observed INT range | 112-138 | 115-141 |

Mean absolute INT displacement is about 22.6% lower in the current log.

## Stable-load pulse-width movement

To reduce load-change contamination, 10-sample (~1.5 s) windows were retained only when:

- closed loop remained active,
- PE/AE/DFCO stayed inactive,
- TPS standard deviation <=0.6 percentage point,
- MAP standard deviation <=1.2 kPa,
- RPM standard deviation <=50 RPM,
- BLM cell and BLM value did not change.

There were 116 qualifying reference windows and 120 current windows.

Median BPW range within a stable window:

- pre-DAMP1: 6.84%
- BMHM 0.3.1: 5.43%

That is about a **20.6% reduction in short-term BPW range**, which is directionally consistent with the ~25% P-gain reduction in the DAMP1 table.

75th-percentile stable-window BPW range:

- pre-DAMP1: 8.51%
- BMHM 0.3.1: 6.26%

## What did not clearly improve

The downstream wideband did not show a tighter AFR range in this uncontrolled comparison. Median stable-window AFR range was approximately 6.3 AFR points in the reference and 6.7 in the current log after excluding pegged 20.0 values.

That does not contradict the narrower injector-PW movement: the wideband is after transport delay and the narrowband controller intentionally cycles rich/lean. It does mean we should not claim that DAMP1 has already produced visibly tighter exhaust AFR.

## BLM behavior

The configured BLM base-update constant is 50% longer and the non-idle INT learning window is widened to ±4.

In the current log, repeated same-cell one-count BLM movements commonly occur on roughly 1.35-1.6 s spacing in sustained cells. Runtime gating and ALDL serialization prevent using those observed intervals as a direct measurement of the base timer.

## Current assessment

DAMP1 is doing what it was intended to do:

- INT spends less time displaced far from 128 in the targeted load region.
- short-term injector-PW movement under steady load is materially smaller.
- BLM is less eager near neutral and has a slower configured base update.
- O2 interpretation/filtering remains unchanged.

It is **not** a complete cure for all narrowband oscillation. Occasional INT excursions and >5% PW movement still exist, and the wideband does not yet show a reduced swing.

Recommendation at this stage: keep DAMP1 while VE/state logic is stabilized rather than reducing closed-loop authority again immediately.

Additional observation: knock retard was 0.0 for all 3792 samples in the current log.
