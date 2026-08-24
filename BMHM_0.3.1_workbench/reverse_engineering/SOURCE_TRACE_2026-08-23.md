# Stock `$31` source trace — 2026-08-23

This document records source behavior decoded during the BMHM 0.3.1 work. Addresses refer to the stock BMHM/HAC `$31` source.

## Closed-loop O2 controller

The stock controller is a hybrid fast/slow narrowband controller, not a simple percentage PI loop.

Data flow:

`raw O2 L01D5 -> fast R/L state + clamped/filtered slow O2 L01D2 -> slow error -> proportional correction + timed INT L020F -> signed additive PW correction L026F -> synchronous BPW`

BLM is a separate multiplicative correction applied earlier in the fuel path.

Important regions:

- `$7E09-$7E33` — slow O2 filter.
- `$863D-$891D` — rich/lean state, proportional correction and INT.
- `$8906-$891A` — INT/P combination into signed PW correction.
- `$804C` area — BLM multiplier application.
- `$E51E-$E561` — BLM enable qualification.

At `$8906-$891A` the effective signed correction is:

- fast rich: `INT - P - 128`
- fast lean: `INT + P - 128`

The result is stored in `$026F` and later add/subtracted directly as injector-PW counts. It is **not a percentage**. With the `$31` PW scale, one count is about 15.26 us.

BLM remains multiplicative and centered at 128.

## `$400C` bits 4 and 5

The source at `$871A-$8739` shows:

- `$400C.b5/$20` — INT reset on first acceleration-enrichment event.
- `$400C.b4/$10` — INT reset associated with BLM cell change logic.

These are controller state-management options, not closed-loop-enable bits.

## `$400E` bits 0 and 1 / altitude CMAP

Stock BMHM 7.4 TBI has `$400E=$03`, so both bits are enabled despite some XDF notes associating them with CPI applications.

Actual consumers:

- `$81BD-$81C7`: bit1 chooses `L01CF` instead of `L01C0` for DFCO MAP/load hysteresis.
- `$8D0C-$8D35`, `$8D51-$8D5E`: bit0 chooses `L01CF` instead of ordinary MAP for BLM cell-boundary selection.
- `$E53B-$E548`: bit0 chooses `L01CF` rather than `L01C6` for BLM-enable load qualification.

`L01CF` is built at `$A499-$A4B0` from a MAP-derived quantity (`L0257`) divided by a BARO-derived quantity (`L01CE`) with fixed-point scaling. It is therefore an altitude-normalized load coordinate ("ALT CMAP"), not simply another MAP reading.

`$400E.b3` is the option explicitly annotated as CPI manifold-tune control.

## BARO source selection / pseudo-BARO

`$5D02.b2` selects the BARO hardware strategy:

- 0: MAP-only; derive pseudo-BARO.
- 1: separate BARO + MAP sensors.

At `$C583-$C59B`, bit2=1 selects an A/D BARO channel and stores the result in `$02F3`.

At `$C5A6-$C606`, MAP-only operation conditionally updates pseudo-BARO. Qualification includes RPM, coolant, TPS and TPS stability. `$4558` is the RPM/TPS correction table explicitly described as a term added to MAP A/D to make pseudo-BARO.

Both paths converge through the BARO filter (`$4158`) and conversion to `$01CC` BARO kPa.

## MAT/IAT capability

`$400B.b6/$40` is the MAT-sensor option.

Acquisition/diagnostic path:

- `$DBFB-$DC0D`: read A/D, invert value, store `$0230`.
- `$DC17-$DC6F`: MAT DTC 23/25 logic.
- `$DC72-$DC85`: linearize through table `$FE45`; normal output `$022F`, default substituted on MAT fault.

A later fuel-model path at `$E2C8-$E2F8` branches on `$400B.b6`. With MAT disabled it begins with coolant. With MAT enabled it uses the MAT/IAT path and `$4AE3` before building `$0236`.

Important no-VSS caveat: MAT diagnostics at `$DC17` still use `$0284` VSS. If MAT is enabled later, that diagnostic qualifier should be redesigned rather than relying on the phantom VSS input.

## VSS/idle interaction proven in logs

The original phantom-speed issue was not merely an ALDL display artifact. Stock consumers read the same VSS RAM state:

- `$899B`: VSS qualifier in idle classification.
- `$8CA0`: VSS qualifier in idle BLM-cell selection.
- `$99F2`: VSS qualifier in IAC closed-loop qualification.
- `$A85A`: VSS qualifier in idle spark.

Stationary logs showed phantom VSS bursts coincident with idle flag loss, BLM cell changes, closed-loop fuel entry, IAC qualification loss and idle-spark loss.

BMHM 0.3.1 leaves the VSS acquisition/filter path intact but removes engine-control authority at the consumers listed in `mods/BMHM_0.3.1_PATCH_NOTES.md`.

## True-idle state split

The no-VSS conversion intentionally allows closed-throttle fuel tuning to collapse into a simpler regime while keeping closed-loop IAC and idle spark as a distinct engine state.

0.3.1 adds RPM hysteresis:

- enter true idle <=1100 RPM (`$FF88`)
- exit true idle >1200 RPM (`$FF89`)

This creates a useful architecture for future states:

- drive: TPS open.
- decel/dashpot: TPS closed but RPM above idle window.
- normal idle: TPS closed and RPM inside idle window.
- future auxiliary high idle: explicit AUX request can override the normal RPM ceiling and select its own RPM/MAP calibration zone.

The TPS side of the state selector uses the stock learned/zeroed engine TPS path, documented in `TPS_SELF_ZERO_TRACE.md`.
