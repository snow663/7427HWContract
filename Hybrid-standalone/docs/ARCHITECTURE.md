# Hybrid Standalone architecture — design baseline v0.1

Status: **design only; no executable or PCM build in this directory**.

## Authoritative distinction: engine strategy vs target hardware

The engine was originally controlled by the **$D8 family**; the current `pseudo-source/` work reconstructs the **$31** firmware, which belongs to the 7427 hardware being reused. These are not interchangeable mathematical strategies. Even similar-looking VE/spark/AFR tables can yield different real injector pulse widths, operating states and idle behavior because of different air-charge normalization, base pulse-width constant, pulse frequency, injector-flow/voltage corrections, integer scaling, interpolation, feedback and scheduling conventions. These are **candidate mismatch mechanisms**, not a claim that every listed mechanism has already been numerically proven.

**Algorithmic authority:** verified D8 ROM/BIN plus controlled observations from the working D8-on-7427 port. **Hardware authority:** verified 16197427 register, ASIC, timer, IRQ, latch and electrical contracts. **Comparative reference only:** stock-$31 ROM and its separate C equivalence work. **New design authority:** documented Hybrid equations and measured results. No undocumented cross-mask parameter import.

Before enlarging any table or changing resolution, explicitly decode what each source table value means *to its algorithm*. A number displayed as VE% under $31 cannot be assumed to represent the same resulting fuel mass as the same number under $D8. Preserve the D8 stage-by-stage numerical model as a reference fixture, then make changes individually and record the expected differences.

## Separate codebase

`Hybrid-standalone/` owns its complete code, build system, tests, symbols, calibration format and release process. `pseudo-source/` is not a library and is not to be copied into Hybrid wholesale. Existing stock-$31 evidence in the parent repository is a reference for **verified 7427 interface semantics**, not a mandatory factory scheduler or algorithm design.

## Layers and API contracts

1. **Hardware**: typed reads/writes of HC11 timer, IRQ, ADC, serial, ASIC and output latches, including register ordering, atomicity and meaningful error return codes. No airflow/fuel/spark equations.
2. **Event kernel**: deterministic REF timing, hard-realtime outputs, interrupt arbitration, watchdog, state transitions and budgeted cooperative background tasks. No implicit firmware mode-word inheritance.
3. **Sensors**: one snapshot of raw/filtered RPM, MAP, TPS, CTS, battery voltage, optional MAT/BARO/NB O2 and knock, with age/validity flags.
4. **Engine algorithms**: pure or explicitly stateful functions with engineering-unit inputs/outputs. Airflow, fuel, spark, idle, AE/PE/DFCO and diagnostics never access hardware addresses.
5. **Calibration**: one validated, versioned immutable definition, with independent table-axis objects and generated target data / matching tuning definitions.
6. **Diagnostics**: publish commanded and final PW, final ignition advance, IAC steps, active cell/weights, mode/limiter/fault flags and sensor validity without silently changing core timing.

### Output data contract

- Fuel output: requested **electrical injector on-time** in microseconds, with explicit scheduling phase and inhibit condition; distinguish modeled fuel-equivalent PW, after-compensation PW and actually armed output PW.
- Spark output: desired crank-angle degrees BTDC with explicit base timing, clamp and dwell/bypass status; hardware converts to compare/ASIC values.
- Idle output: requested IAC step position and rate limit, with separate actuator commutation.
- All units, saturation and rounding are documented and tested. A calibration value never means a hidden factory offset without being declared.

## Engine states

BOOT -> KEY_ON -> CRANK -> RUN, with IDLE, POWER and DECEL/DFCO as qualified submodes. STALL/FAULT exits preserve safe output and restart semantics. Manual transmission only at baseline; no VSS dependency. Hysteresis, edge filtering and transition timing are explicit per mode. PE should be qualified by high load, not inverse load.

## Fuel calculation

The native-engine $D8 base path must first be independently reconstructed and compared with the actual running D8-port image. The following is a **proposed clean output pipeline** rather than a transcription of factory arithmetic:

```
base_fuel = SpeedDensity(MAP_abs, RPM, displacement, charge_temperature,
                         VE_interpolated, injector_flow, target_AFR)
requested_fuel = base_fuel * warmup * afterstart * PE_factor
                 + transient_fuel_correction
electrical_PW = injector_transfer(requested_fuel, battery_voltage,
                                   low_PW_characterization)
final_PW = safe_limits_and_DFCO(electrical_PW)
```

This is **an interface-level model, not a claim about exact D8 integer operations**. Derive the actual D8 math from evidence before choosing how much to preserve. Start with a numeric trace at each boundary: raw MAP/RPM/temperature inputs, air-charge intermediate, table lookup coordinates/weights, fuel constant, requested fuel per event, synchronous/async division, battery/short-pulse compensation and the final electrical pulse width. Compare $D8, the working port and Hybrid with the **same inputs**; compare $31 separately to explain divergence, not to define the target. Do not multiply AFR, injector opening delay or pulse counts together ambiguously. AE additive corrections and wall-film state are explicit and observable. Define the pulse interval convention for simultaneous TBI injectors so event frequency cannot introduce a hidden factor-of-two error.

Closed loop is an optional **single well-defined trim path**, not a parallel inherited $31 INT/BLM chain. Base VE tuning remains understandable with feedback disabled. When feedback is on, report instantaneous correction and learned multiplier separately, plus the actual total pulse-width correction.

## Calibration-equivalence gate

The first acceptance fixture must run the same sensor/event vectors through original $D8 arithmetic, the working D8 port (after any measured hardware/OS adaptations), and Hybrid. Log each intermediate and output stage, including integer rounding, saturations, fuel-per-event conventions and injector timing. Deliberate improvements get individual assertions; differences cannot be hidden inside a retuned VE map. Test steady cruise, idle near short-PW behavior, startup, throttle steps, power load, DFCO entry/exit and voltage changes. This comparison precedes any claim that an expanded table is correctly calibrated.

## Proposed calibration resolution

| Surface | Initial target | Storage |
| --- | --- | --- |
| VE (MAP × RPM) | 24 × 24 | uint16, e.g. 0.1% |
| Main spark (MAP × RPM) | 24 × 24 | int16, e.g. 0.1 degree |
| Target AFR (MAP × RPM) | 16 × 16 | uint16, e.g. AFR ×100 |
| Idle target (CTS) | 16 points | uint16 RPM |
| IAC feed-forward (CTS) | 16 points | uint16 steps |
| Cranking fuel (CTS) | 16 points | uint16 microseconds |

All dimensions are **proposals subject to actual ROM space and execution budgets**. Use nonuniform, tuneable axis breakpoint arrays so resolution is concentrated in idle/load transition regions. Piecewise bilinear interpolation has defined saturation at the boundary. Target RPM/MAP axis choices are not yet calibrated.

Table values are 16-bit where it adds actual resolution; source and UI may display engineering units while the target uses fixed-point integer operations. Never silently wrap or extrapolate outside a table. Internal intermediates need overflow proofs and cycle budgets. A 24×24 uint16 table uses 1,152 bytes, so two primary tables occupy 2,304 bytes before axes.

## Timing model

Event-critical REF and output handoff paths get hard deadlines and run ahead of background work. Noncritical sensing, idle control, O2 and serial are periodic cooperative tasks with measured worst-case execution times; no serial operation blocks fuel or ignition timing. The original $31 kernel and 16-slot dispatch are references, **not a mandated clone**.

The hardware contract must be separately bench-verified for ASIC $3FC0/$3FCA reference signals, $3FCE fuel handoff, $3FE6/$3FE8 spark handoff, $3FEC feedback, $004C→$3062 IAC phase path, timer flags, SCI and watchdog. Source-level names or successful emulation do not prove electrical timing and output polarity.

## Development milestones

1. **Source authority**: inventory the original-engine $D8 BIN, running D8-port BIN and matching $D8/BAMW source; validate equations, scaling, fuel-per-event convention, lookup encoding and command handoffs. Quantify disagreements with $31 and document confirmed vs inferred items.
2. **Pure control math**: create independent table lookup, speed-density, fuel and spark libraries with exact host tests, including 8/16-bit saturation and rounding.
3. **Idle/transients**: independent idle speed/stepper controller, AE, warmup, power enrichment and DFCO state tests. Explicit reset and stall behavior.
4. **7427 hardware interface**: direct contract drivers, interrupts, watchdog and limited ISR work; simulate and bench-check write order/timing.
5. **Target image**: map, vectors, calibration generator, XDF and ALDL protocol, checksum and footprint checks; never overwrite existing releases.
6. **Controlled bench/vehicle validation**: compare against a known-good ROM and staged output takeover with a rollback image.

## First implementation decision

Keep the new project physically isolated now. Begin with the calibration/lookup and source-evidence layers while deriving hardware and exact D8 fuel-model equivalence. Do not import existing `pseudo-source/src` objects or alter that project's build.
