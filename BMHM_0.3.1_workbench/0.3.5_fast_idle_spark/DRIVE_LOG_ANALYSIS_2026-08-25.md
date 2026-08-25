# 2026-08-25 15:41:49 drive log — BMHM 0.3.4 analysis

## Context

Warm drive following the BMHM 0.3.4 reset/cold-start validation. PCM VSS remained 0 throughout this log while GPS speed reached ~108, so the engine-state results below are not being driven by road-speed input.

## Bosch-style state layer validation

Corrected TPS <= 1.2%, RPM >= 1225:

- 480 samples
- TRUE-IDLE flag ON: 1/480 (~0.2%)
- RPM closed-loop/IAC enabled: 1/480 (~0.2%)
- idle spark enabled: 1/480 (~0.2%)
- BLM cell 16: 0/480

Corrected TPS <= 1.2%, RPM <= 1100:

- 454 samples
- TRUE-IDLE flag ON: ~99.1%
- RPM closed-loop/IAC enabled: ~93.8%
- idle spark enabled: ~99.1%
- BLM cell 16: ~99.3%

The DECEL versus TRUE-IDLE split remains coherent.

## Lambda / DAMP1 authority

Clean part-load filter: closed loop, no AE, no PE, no DFCO, non-idle, TPS > 1.2%, BPW > 0.

Overall clean closed-loop region (3994 samples):

- INT mean: 127.89
- BLM mean: 128.49
- mean abs(INT-128): 2.90 counts
- raw O2 mean: ~489 mV
- slow-rich occupancy: ~52.4%

Stable clean region (2921 samples):

- INT mean: 127.91
- BLM mean: 128.44
- mean abs(INT-128): 2.85 counts
- raw O2 mean: ~481 mV
- slow-rich occupancy: ~51.6%

Conclusion: lambda center and DAMP1 authority are good. No gain/centering change is indicated by this drive.

### Dominant cruise

~2400-3300 RPM, 30-50 kPa, stable closed loop (1320 samples):

- INT mean: 128.42
- BLM mean: 128.41
- approximate combined persistent/INT correction: +0.6%
- knock retard max: 0.5 deg

This region is effectively centered; do not change base VE materially here.

### Mid-load

~2400-3100 RPM, 50-70 kPa, stable closed loop (350 samples):

- INT mean: 128.22
- BLM mean: 129.73
- approximate correction: +1.45%
- knock retard: 0

This region is slightly lean in the base model. A small VE increase (~1%, or half-delta ~0.7%) is defensible, but not urgent.

### High-load closed-loop region

~1800-3100 RPM, 75-90 kPa, stable closed loop (58 samples):

- INT mean: 109.95
- BLM mean: 126.12
- raw O2 mean: ~692 mV
- slow-rich occupancy: ~86%
- WBO2 mean: ~14.56 AFR (transport-lagged downstream sensor)
- approximate trim indicated by BLM + additive INT alone: about -6.6%
- knock retard max: 4.0 deg

Do not simply lean the VE table here. This region should be treated as a full-load/PE and spark-calibration problem rather than tuned back to stoichiometric closed-loop operation.

## Knock / spark evidence

Two repeatable load-related knock-retard episodes were present.

### Episode 1

~110.84-113.57 s:

- 1550-1775 RPM
- ~68-73 kPa at onset
- TPS ~28%
- KR 3-4 deg
- delivered spark roughly 29-33 deg through the loaded portion

### Episode 2

~352.55-369.89 s:

- 1800-3150 RPM
- ~75-86 kPa through the sustained pull
- TPS ~40-63%
- KR repeatedly 3-4 deg
- delivered spark roughly 29-36 deg depending on RPM/load

Suggested base-spark correction direction for the next calibration:

- 1400-1800 RPM, 65-75 kPa: remove about 2 deg, blended into neighbors
- 1800-3000 RPM, 80-90 kPa: remove about 3 deg, blended into neighbors
- 3000-3400 RPM, 70-90 kPa: remove about 2 deg

This is intended to move repeatable KR back into the base table rather than making the knock controller repeatedly supply the same retard.

## PE qualification problem exposed by this drive

Power Enrichment never became active anywhere in the 788-second log, even though MAP reached 86 kPa at ~94.1 kPa baro (~91% of local barometric pressure) and TPS reached ~63%.

Current stock-style TPS PE thresholds decoded from BMHM 0.3.4:

### Normal WOT/PE-enable TPS table `$4C64`

- 800-2000 RPM: raw `$9A` = ~60.2% TPS
- 2400-4000 RPM: raw `$B3` = ~69.9% TPS

### High-TPS fast-WOT entry table `$4C5A`

- 800-2000 RPM: ~69.9% TPS
- 2400 RPM: ~85.2% TPS
- 2800-4000 RPM: ~94.9% TPS

The sustained pull reached high manifold load well before those throttle thresholds, so the engine remained at commanded 14.1 AFR while the knock controller was active.

The PE delay scalar `$4919` is also raw `$46` (70 in the stock calibration notation), so partial-throttle high-load events can remain in normal closed-loop operation for a long time unless a bypass/fast-entry condition is met.

Architecture implication: for this engine, throttle angle alone is a poor full-load proxy. The next PE revision should either add a load-based full-load override (preferable) or substantially reshape TPS PE thresholds/delay. A load-based decision is more consistent with the project goal of separating engine load from vehicle/transmission state.

## Cold fast-idle spark reminder

The preceding cold-start log showed high fast-idle RPM coincident with non-idle spark around 38.3 deg while IAC was already retracting. Source confirms the stock idle-spark controller has overspeed retard (`$44F0`), underspeed advance (`$4502`), and derivative correction (`$451B`), all keyed to desired RPM `$0857`.

BMHM 0.3.5 should therefore:

1. make the FAST-IDLE desired-RPM target authoritative before RPM error / idle-spark feedback consumes `$0857`;
2. allow FAST IDLE to use the stock idle-spark feedback controller even though normal TRUE-IDLE RPM criteria are not met;
3. avoid adding an IAC hard ceiling unless later evidence still requires it.

## Version signature

BMHM 0.3.4's `$4002-$4005` platform signature is not visible in stock Mode-1 logging. Stock ALDL reports `$4000/$4001` as PROM ID, so BMHM 0.3.5 and later should stamp both the ALDL-visible PROM-ID bytes and the full canonical platform-ID bytes.
