# BMHM 0.3.5

Experimental successor to BMHM 0.3.4. This build keeps the Bosch-style PART / DECEL / TRUE-IDLE state layer and adds a corrected STARTUP FAST-IDLE spark/target path, actual-load PE entry, logged high-load spark corrections, and a small mid-load VE correction.

## Binary identity

- File: `BMHM_0.3.5.bin`
- SHA-256: `5376e39cea7a58cfde6ec3414bfd9d8d8c0e0adc427cda0f01c2e4a89a49baf3`
- `$31` checksum: `$3DB8`
- Stock ALDL-visible PROM ID `$4000-$4001`: `03 05`
- Canonical platform/version bytes `$4002-$4005`: `00 03 00 05`

## Main changes

### FAST-IDLE target ordering

The stock desired-idle calculation finalizes `L0857` at `$99A8`. 0.3.5 hooks that final write and applies the coolant FAST-IDLE target immediately afterward, before downstream RPM-error/spark control consumes the target. This removes the 0.3.4 behavior where the logged desired RPM alternated between the FAST-IDLE target and the warm idle target.

### FAST-IDLE spark authority

Before the first real throttle opening, STARTUP FAST IDLE is allowed to use the stock idle-spark feedback path at `$A862+` even above the normal TRUE-IDLE RPM ceiling. This preserves the stock overspeed/underspeed/derivative spark control tables (`$44F0`, `$4502`, `$451B`). After the startup latch is cancelled, idle spark again requires centralized TRUE IDLE.

No startup IAC ceiling is added in this build.

### Actual-load PE entry

The stock corrected-TPS PE comparison at `$8AE7` is wrapped by a helper at `$FF2E`.

- If manifold vacuum `L01C9 <= 15 kPa`, the helper sets the stock fast-PE-bypass bit and returns the PE-qualified carry state.
- Otherwise it performs the original corrected-TPS comparison and returns its carry unchanged.

The threshold operand is `$FF32 = 15` kPa and is intentionally easy to calibrate.

At approximately 94 kPa barometric pressure, 15 kPa manifold vacuum corresponds to roughly 79 kPa MAP.

### PE spark

The PE/WOT spark adder table `$44BF-$44CF` is changed from raw `6` everywhere (+2.109375 degrees) to zero. Entering PE on actual load therefore cannot add timing on top of the base spark surface.

### High-load base spark

A smoothed retard island is applied to the repeatable knock region observed in the 2026-08-25 drive log. Core corrections are approximately -2 to -3 degrees in the 1400-3200 RPM / 65-90 kPa region with -1 to -2 degree tapers around it. Exact cells are recorded in `PATCH_MAP.csv`.

### Mid-load VE

The 2400-3100 RPM / 50-70 kPa region showed about +1.4% persistent learned fuel demand with INT near neutral. Approximately half delta is moved into base VE: +0.78125% in the core with +0.390625% tapers. Main 30-50 kPa cruise is unchanged.

### Closed loop

DAMP1 is unchanged. No O2 centering, proportional gain, INT-delay, or BLM-learning changes are included in 0.3.5.

## Validation targets

Cold start should show one stable coolant-dependent Desired Idle RPM, idle-spark authority during STARTUP FAST IDLE, spark pulled back from the former ~38 degree overspeed condition, and RPM converging toward the FAST-IDLE target. First real throttle opening must still cancel STARTUP FAST IDLE for the rest of that engine run.

During driving, near-full-load operation at <=15 kPa manifold vacuum should enter PE without requiring the old high TPS thresholds. Repeat high-load pulls should show reduced knock retard, while cruise lambda trims should remain near neutral.

See `SOURCE_TRACE_2026-08-25.md` and `DRIVE_LOG_ANALYSIS_2026-08-25.md` for the source and log evidence behind this build.
