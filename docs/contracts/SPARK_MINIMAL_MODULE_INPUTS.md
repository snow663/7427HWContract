# Spark Minimal Module Inputs

## Purpose

Define the input boundary for a minimal spark module.

This document does not implement spark math, does not write ASIC timing registers, and does not create a spark writer.

## Output Boundary Status

Spark output is source-mapped but bench-gated.

Owned by:

- `SPARK_ASIC_HANDOFF_CONTRACT.md`
- `SPARK_LA906_TIMING_BRIDGE.md`
- `SPARK_DEGREE_TO_TICK_DEPENDENCY.md`
- `MATH_HELPER_LF550.md`
- `SPARK_TIMEBASE_PERIOD_CONTRACT.md`
- `SPARK_MAGNITUDE_SCALE_CONTRACT.md`
- `SPARK_CONVERSION_EQUATION.md`
- `SPARK_LA906_OUTPUT_SEQUENCE.md`
- `SPARK_ROLLING_STATE_MODEL.md`
- `SPARK_INIT_STATE.md`
- `SPARK_BYPASS_EST_TRANSITION.md`
- `SPARK_EST_FAULT_MONITOR_CONTRACT.md`
- `SPARK_MINIMAL_MODULE_BOUNDARY.md`
- `source/minimal_os/spark/README.md`

Output side remains bench-gated:

```text
desired spark degrees / timing intent
→ stock-proven conversion path
→ LA906 timing bridge model
→ rolling state
→ ASIC handoff candidates $3FE8/$3FE6/$3FF6/$3FDC/$3FE4
```

No direct writer is permitted by this input-boundary contract.

## Known Source Boundary

```text
L01FD = final spark advance accumulator candidate
L01EE = signed spark offset into conversion path
L004F bit0 = spark sign/direction flag
L0201 = spark latency correction candidate
L005F/L0060 = DRP/ref period basis
L3FC0/L3FC1 = ASIC timing/period source candidate
L3FE8 = first ASIC timing command candidate
L3FE6 = second ASIC timing command candidate
L3FDC = rolling timing state candidate
L3FF6 = rolling timing anchor candidate
L3FEC -> L3FE4 = status/mirror/ack candidate
```

## Required Input Classes

| Input class | Required? | Role | Calibration dependency | Notes |
|---|---:|---|---|---|
| RPM / engine speed | required | sensor | CAL_4166/CAL_428A/CAL_44BF candidates $4166-$44CF | Required before any base spark lookup or degree-to-time conversion. |
| MAP / load | required | sensor | CAL_449D/CAL_44AE/CAL_485D candidates $449D-$44BE | Required for load-indexed base spark and modifiers. |
| TPS / throttle state | likely_required | sensor | sensor_scaling sections various | Useful for idle, transient, and authority gating but not enough to permit writer. |
| coolant temperature | likely_required | sensor | CAL_452D/CAL_4537/CAL_4541/CAL_46E4 candidates $452D-$46F8 | Needed for startup/coolant spark correction. |
| baro / altitude basis | likely_required | sensor | sensor_scaling/spark MAP/baro sections various | Altitude/load correction input; do not inherit full GM baggage blindly. |
| crank/run state | required | mode_gate | none none | Required so spark logic does not use run timing during crank/bypass. |
| bypass/EST authority state | required | mode_gate | none none | Input boundary only; no physical EST control code. |
| reference/DRP period basis | required | timebase | none none | Required for converting desired degrees into timing-domain units. |
| desired base spark table | required | calibration | CAL_4166; CAL_428A; CAL_44BF candidates $4166-$44CF | Primary timing intent source; still planning-only. |
| startup spark | likely_required | calibration | CAL_452D/CAL_4537 candidates $452D-$4540 | Needed before clean crank/start timing behavior can be defined. |
| idle spark modifier | optional_initially | calibration | CAL_44F1..CAL_451A candidates $44F1-$451A | Optional for first fixed/open-loop spark; likely needed for stable idle later. |
| coolant spark modifier | likely_required | calibration | CAL_452D..CAL_454A; CAL_46E4 $452D-$46F8 | Coolant-based spark intent input. |
| MAP/RPM spark modifiers | likely_required | calibration | CAL_449D..CAL_44BE; CAL_4585..CAL_4593 $449D-$4593 | Load/RPM modifiers to final desired spark. |
| knock retard input | bench_gated | retard_source | spark/knock candidates unknown | Represented but not required for first no-knock minimal spark. |
| burst knock / transient retard input | optional_initially | retard_source | unknown unknown | Keep as unresolved refinement, not required. |
| low-octane or learned retard input | optional_initially | retard_source | low-octane spark candidates unknown | Optional initially; do not promote without source path. |
| spark latency correction | required | latency | CAL_454B usec RPM candidate $454B-$4557 | Required by known conversion path before ASIC handoff is safe. |
| battery/voltage latency if present | bench_gated | latency | battery_voltage candidates various | Represent but do not require until source ties voltage to spark latency. |
| spark magnitude scale | required | output_scale | none none | Required for degree-domain to timing-domain path. |
| degree-to-time conversion dependency | required | output_scale | none none | Defines inputs to conversion, not writer implementation. |
| rolling timing state seed | required | rolling_state | none none | Required before handoff can be safe; no direct writer yet. |
| EST fault monitor state | bench_gated | safety_gate | none none | Optional/diagnostic unless bench proves authority or fallback side effects. |
| spark enable / dropout safe state | required | safety_gate | none none | Required to avoid commanding timing on invalid period/reference state. |

## Minimal Spark Pipeline

```text
sensor acquire
→ crank/run/bypass qualification
→ base spark lookup
→ startup/idle/coolant/load modifiers
→ knock/retard modifiers
→ final desired spark
→ degree-scale conversion
→ period/latency conversion
→ rolling timing state
→ ASIC handoff
→ optional EST fault monitor
```

## Bench-Gated Output Dependencies

```text
physical EST/bypass authority trigger
$3FE8/$3FE6 exact physical role
$3FF6/$3FDC first-event seed
$3FEC->$3FE4 mirror/ack requirement
final LA906 packing/sign behavior
EST fault monitor side effects
knock-retard hardware behavior
```

## Optional Initially

```text
closed-loop knock learning
low-octane learned retard
burst knock refinement
torque-management retard
transmission-related retard
EGR spark correction
```

## Explicitly Excluded

- transmission torque-management spark unless hardware-required
- EGR spark correction
- EVAP/emissions spark modifiers
- diagnostic-only spark behavior unless it affects hardware authority or safe state

## Explicitly Forbidden

Do not add:

```text
SPARK_WRITE
spark_handoff.asm
spark_convert.asm
direct $3FE8/$3FE6 writer
direct $3FF6/$3FDC rolling-state writer
physical EST/bypass authority code
```

until bench classification proves output behavior.

## Input Boundary Rows

| Submodule | Input | Role | Required first OS | Hardware dependency | Bench dependency | Confidence |
|---|---|---|---|---|---|---|
| sensor_inputs | RPM / engine speed | sensor | required | SPARK_TIMEBASE_PERIOD_CONTRACT.md; SPARK_BYPASS_EST_TRANSITION.md | RPM source and DRP period unit still bench/source-gated | high_planning |
| sensor_inputs | MAP / load | sensor | required | SPARK_CONVERSION_EQUATION.md | MAP table axes and load mode still need source linkage per table | medium_planning |
| sensor_inputs | TPS / throttle state | sensor | likely_required | SPARK_BYPASS_EST_TRANSITION.md | TPS role in idle/PE/transient modifiers is source-gated | medium_planning |
| sensor_inputs | coolant temperature | sensor | likely_required | SPARK_CONVERSION_EQUATION.md | coolant correction units and sign need table-specific source proof | medium_planning |
| sensor_inputs | baro / altitude basis | sensor | likely_required | SPARK_CONVERSION_EQUATION.md | baro load effect must be traced before use | medium_planning |
| mode_gates | crank/run state | mode_gate | required | SPARK_BYPASS_EST_TRANSITION.md | run qualification and transition behavior bench-gated | high_static |
| mode_gates | bypass/EST authority state | mode_gate | required | SPARK_BYPASS_EST_TRANSITION.md | physical EST/bypass authority trigger is bench-gated | high_static |
| timebase | reference/DRP period basis | timebase | required | SPARK_TIMEBASE_PERIOD_CONTRACT.md; MATH_HELPER_LF550.md | physical unit and update cadence bench-gated | high_static |
| calibration | desired base spark table | calibration | required | SPARK_CONVERSION_EQUATION.md | exact table axes and final accumulator path still source-gated | medium_planning |
| calibration | startup spark | calibration | likely_required | SPARK_BYPASS_EST_TRANSITION.md; SPARK_INIT_STATE.md | crank/run transition and bypass authority bench-gated | medium_planning |
| calibration | idle spark modifier | calibration | optional_initially | SPARK_CONVERSION_EQUATION.md | idle torque/spark correction behavior source-gated | low_medium_planning |
| calibration | coolant spark modifier | calibration | likely_required | SPARK_CONVERSION_EQUATION.md | units/sign/priority require source proof | medium_planning |
| calibration | MAP/RPM spark modifiers | calibration | likely_required | SPARK_CONVERSION_EQUATION.md | axis/combination rules require source proof | medium_planning |
| retard | knock retard input | retard_source | bench_gated | SPARK_EST_FAULT_MONITOR_CONTRACT.md | knock-retard hardware behavior and side effects are bench/source-gated | low_medium_planning |
| retard | burst knock / transient retard input | retard_source | optional_initially | SPARK_CONVERSION_EQUATION.md | source path not classified | low_planning |
| retard | low-octane or learned retard input | retard_source | optional_initially | SPARK_CONVERSION_EQUATION.md | learning/retard source not required for first static spark module | low_medium_planning |
| latency | spark latency correction | latency | required | SPARK_CONVERSION_EQUATION.md; SPARK_LA906_TIMING_BRIDGE.md | L0201 unit/final postprocess bench-gated | high_static |
| latency | battery/voltage latency if present | latency | bench_gated | SPARK_CONVERSION_EQUATION.md | battery-to-latency coupling not proven | low_medium_planning |
| scale | spark magnitude scale | output_scale | required | SPARK_MAGNITUDE_SCALE_CONTRACT.md; MATH_HELPER_LF550.md | final scale/rounding bench/source-gated | high_static |
| conversion | degree-to-time conversion dependency | output_scale | required | SPARK_CONVERSION_EQUATION.md | final sign/packing behavior bench-gated | high_static |
| rolling_state | rolling timing state seed | rolling_state | required | SPARK_ROLLING_STATE_MODEL.md; SPARK_INIT_STATE.md | $3FF6/$3FDC first-event seed behavior bench-gated | high_static |
| diagnostic | EST fault monitor state | safety_gate | bench_gated | SPARK_EST_FAULT_MONITOR_CONTRACT.md | monitor side effects not proven | high_static |
| safety | spark enable / dropout safe state | safety_gate | required | SPARK_DROPOUT_SAFE_STATE in source/minimal_os/spark/README.md | dropout/missing-ref behavior bench-gated | high_static |
| excluded | transmission torque-management spark | excluded | excluded | none | none | high_policy |
| excluded | EGR spark correction | excluded | excluded | none | none | high_policy |
| excluded | EVAP/emissions spark modifiers | excluded | excluded | none | none | high_policy |
| unknown | unresolved spark inputs | unknown | unknown | SPARK_MINIMAL_MODULE_BOUNDARY.md | requires future source trace | low_unclassified |

## Required Discipline

This contract may define what the spark module needs, but it must not imply the spark output path is implementation-ready.

No calibration-only section is marked required unless tied to an existing spark hardware/source contract. Unknown spark-adjacent sections remain unknown rather than guessed.
