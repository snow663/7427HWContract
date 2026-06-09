# IAC Minimal Module Inputs Test

## Goal

Verify that the IAC input-boundary planning pass defines inputs only and does not imply that IAC motion or output-latch writing is implementation-ready.

This test validates the planning boundary. It does not implement IAC motion, write `L3062`, create an IAC writer, or implement idle strategy code.

## Required Files

```text
docs/contracts/IAC_MINIMAL_MODULE_INPUTS.md
maps/contracts/iac_minimal_module_inputs.csv
tools/build_iac_minimal_module_inputs.py
```

## Required Static Checks

| Test | Expected |
|---|---|
| no IAC writer | no `IAC_WRITE` file/symbol is created by this pass |
| no ASM | no `source/minimal_os/iac/*.asm` file is created |
| no direct latch writer | no direct `L3062` writer is introduced |
| phase path | remains bench-gated |
| Enable behavior | remains bench-gated |
| park/reset behavior | remains bench-gated |
| cadence/rate limit | represented and bench-gated |
| actual-position seed validity | represented |
| desired idle target | represented |
| crank/start/park target | represented |
| trans/EGR/EVAP | not marked required |
| unknowns | listed, not guessed |
| calibration-only promotion | no calibration section promotes itself to required |

## Command

```bash
python tools/build_iac_minimal_module_inputs.py \
  --cal-index maps/contracts/calibration_source_index.csv \
  --out-md docs/contracts/IAC_MINIMAL_MODULE_INPUTS.md \
  --out-csv maps/contracts/iac_minimal_module_inputs.csv
```

## Must Remain Forbidden

```text
IAC_WRITE
iac_output.asm
iac_phase_step.asm
iac_init_park.asm
iac_enable_gate.asm
direct L3062 writer code
idle strategy ASM
```

## Required Input Presence

The CSV must include rows for:

```text
RPM / engine speed
actual idle RPM
desired idle RPM
RPM error
coolant temperature
crank/run state
startup/crank air request
park/reset state
bad-shutdown state
reset-in-work state
R/S requested state
battery voltage
IAC enable/protection state
actual IAC position
IAC actual-position seed validity
desired IAC target
IAC position error
step direction
A/B phase state
step cadence / rate limit
closed-throttle / idle-mode state
stall/dropout safe state
```

## Bench-Gated Output Dependencies

The contract must keep these bench-gated:

```text
physical A/B pin mapping
open/close direction
whether count increment opens or closes IAC
Enable physical function
park-down physical direction
L4EB0 physical meaning
whether every software step equals one motor step
safe step cadence
actual-position validity after normal shutdown
```

## Exclusion Discipline

These must not be required for first minimal OS:

```text
transmission shift/TCC idle modifiers
EGR idle correction
EVAP/purge idle correction
emissions-only diagnostics
```

## Pass Criteria

```text
PASS:
  all required input categories are represented.
  output latch remains bench-gated.
  no writer or ASM file is created.
  no direct L3062 writer is introduced.
  Enable, phase, park/reset, and cadence behavior remain bench-gated.
  trans/EGR/EVAP idle-adjacent sections are excluded.
  unknown inputs remain visible.
  no calibration-only row marks itself required without a hardware/source dependency.
```

## Fail / Rework Criteria

```text
REWORK:
  any file or row implies direct IAC output implementation is ready.
  any direct L3062 writer appears.
  physical A/B mapping or open/close direction is treated as solved.
  Enable physical function is treated as solved.
  park/reset physical behavior is treated as solved.
  EGR/trans/EVAP idle modifiers are promoted to required.
  unknown IAC-adjacent calibration sections are silently guessed.
```

## Next Planning Artifact

After this pass, the module input-planning set is complete:

```text
FUEL_MINIMAL_MODULE_INPUTS
SPARK_MINIMAL_MODULE_INPUTS
IAC_MINIMAL_MODULE_INPUTS
```

Then continue with:

```text
MINIMAL_OS_EXECUTION_SCHEDULER
```
