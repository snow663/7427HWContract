# IAC Minimal Module Inputs

## Purpose

Define the input boundary for a minimal IAC / idle-air module.

This document does not implement IAC motion, does not write `L3062`, and does not create an IAC writer.

## Output Boundary Status

IAC output is source-mapped but bench-gated.

Owned by:

- `IAC_IDLE_AIR_OUTPUT_CONTRACT.md`
- `IAC_PHASE_SEQUENCE_CONTRACT.md`
- `IAC_ENABLE_FAULT_GATE_CONTRACT.md`
- `IAC_INIT_PARK_CONTRACT.md`
- `source/minimal_os/iac/README.md`

## Known Source Boundary

```text
L0007 = actual/present IAC position
L0008 = desired/target IAC position
L0009 bit0 = reset-in-work candidate
L0009 bit2 = R/S requested candidate
L000A bit0 = direction
L000A bit2 = A candidate
L000A bit3 = B candidate
L000A bit4 = Enable candidate
L004C bits2/3/4 = output shadow
L3062 = hardware latch write
L4EB0 = 145-step park-down value
L00A7 = battery voltage, VDC/10
L003E bit2 = low-battery/protection flag candidate
```

## Required Input Classes

| Input class | Required? | Role | Calibration dependency | Notes |
|---|---:|---|---|---|
| RPM / engine speed | required | sensor | CAL_4EA1/CAL_4EAA/CAL_4F92 candidates $4EA1-$4FEC | Required for idle RPM error, step-rate/cadence, and target correction. |
| actual idle RPM | required | sensor | iac_idle RPM-error sections $4EA1-$4FEC | Needed to compute RPM error against desired idle. |
| desired idle RPM | required | idle_target | CAL_4EA1/CAL_4EAA and related idle sections $4EA1-$4EB0 | First minimal IAC module needs an idle target even if initial target is fixed/simple. |
| RPM error | likely_required | idle_target | CAL_4EAA; CAL_4F92..CAL_4FE1 candidates $4EAA-$4FE1 | Needed for closed-loop idle-air correction, but first minimal can use a simplified policy. |
| coolant temperature | likely_required | sensor | CAL_4E92 IAC position vs coolant; coolant-indexed idle sections $4E92-$4EA0 | Needed for crank/cold idle/park target planning. |
| crank/run state | required | mode_gate | none none | IAC target and reset/park behavior differ before crank, during crank, and in run. |
| startup/crank air request | likely_required | startup_park | CAL_4E92; CAL_4EB0; CAL_57A0 candidates $4E92-$4EB0;$57A0-$57AA | Needed to get starting air without trusting closed-loop idle strategy. |
| park/reset state | required | startup_park | CAL_4EB0 $4EB1-$4EB5 | Required before actual position can be trusted. |
| bad-shutdown state | likely_required | startup_park | none none | Bad-shutdown path affects setup clear and position trust policy. |
| reset-in-work state | required | startup_park | none none | Controls desired=0 reset path until L0007 reaches zero. |
| R/S requested state | likely_required | startup_park | none none | Used in ignition-off park-down desired request. |
| battery voltage | required | sensor | CAL_4EB6 voltage threshold candidate $4EB6 | Voltage gates Enable/protection and may block movement. |
| IAC enable/protection state | required | enable_gate | CAL_4EB6 $4EB6 | Must be valid before physical stepping is trusted; not step-pulsed in source path. |
| actual IAC position | required | position_state | none none | Software actual/present position used by desired/actual compare. |
| IAC actual-position seed validity | required | position_state | CAL_4EB0 $4EB1-$4EB5 | Minimal OS must not trust L0007 until deliberately seeded or proven retained valid. |
| desired IAC target | required | position_state | CAL_4E92; CAL_4EB0; CAL_57A0 candidates $4E92-$4EB0;$57A0-$57AA | Target value compared against L0007 to decide motion. |
| IAC position error | required | position_state | none none | Core desired-vs-actual decision feeding direction and count update. |
| step direction | required | phase_state | none none | Direction selects next neighbor in A/B ring. |
| A/B phase state | required | phase_state | none none | Required to advance stepper phase safely. |
| step cadence / rate limit | required | cadence | CAL_4EA1/CAL_4EAA/CAL_4F92 candidates $4EA1-$4FE1 | Must exist before any writer; output path alone is not enough. |
| dashpot / follower state | optional_initially | dashpot | CAL_57A0; vehicle-speed/TPS sections candidates $57A0+;various | Optional initially; avoid full GM strategy baggage. |
| closed-throttle / idle-mode state | required | mode_gate | sensor_scaling/TPS sections various | Required so IAC does not chase idle target off-idle. |
| TPS / throttle state | likely_required | sensor | sensor_scaling sections various | Supports idle-mode gate and dashpot/follower decisions. |
| vehicle speed if used for dashpot/follower | optional_initially | sensor | vehicle-speed/TPS sections various | Useful for dashpot/follower; not required for first stationary idle control. |
| stall/dropout safe state | required | safety_gate | none none | Required to avoid uncontrolled idle-air state on invalid RPM/ref/reset. |
| output shadow/latch dependency | required | output_scale | none none | Defines output dependency only; no writer allowed. |

## Minimal IAC Pipeline

```text
startup / reset / park state
→ actual-position validity
→ desired idle / crank / park target
→ enable / voltage / protection gate
→ desired-vs-actual position compare
→ step cadence gate
→ direction decision
→ A/B phase step
→ output shadow update
→ L3062 latch service
```

## Bench-Gated Dependencies

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

## Optional Initially

```text
dashpot refinement
follower airflow
vehicle-speed idle airflow modifiers
closed-loop idle trim sophistication
AC load compensation
power steering load compensation
gear/load idle compensation
```

## Explicitly Excluded

- transmission shift/TCC idle modifiers unless hardware-required
- EGR idle correction
- EVAP/purge idle correction
- emissions-only diagnostics unless tied to a safety gate

## Explicitly Forbidden

Do not add:

```text
IAC_WRITE
iac_output.asm
iac_phase_step.asm
iac_init_park.asm
iac_enable_gate.asm
direct L3062 writer code
idle strategy ASM
```

until bench classification proves physical direction, Enable behavior, park/reset behavior, and cadence/rate limit.

## Input Boundary Rows

| Submodule | Input | Role | Required first OS | Hardware dependency | Bench dependency | Confidence |
|---|---|---|---|---|---|---|
| sensor_inputs | RPM / engine speed | sensor | required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md | RPM source and idle-loop cadence remain source/bench-gated | medium_planning |
| sensor_inputs | actual idle RPM | sensor | required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md | actual RPM acquisition/cadence still source-gated | medium_planning |
| idle_target | desired idle RPM | idle_target | required | IAC_INIT_PARK_CONTRACT.md | exact desired-idle table/source still needs source trace | medium_planning |
| idle_target | RPM error | idle_target | likely_required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md | gain/table use remains source-gated | medium_planning |
| sensor_inputs | coolant temperature | sensor | likely_required | IAC_INIT_PARK_CONTRACT.md | coolant-to-target mapping is source-gated | high_planning |
| mode_gates | crank/run state | mode_gate | required | IAC_INIT_PARK_CONTRACT.md | crank/run transition behavior source-gated | high_static |
| startup_park | startup/crank air request | startup_park | likely_required | IAC_INIT_PARK_CONTRACT.md | physical meaning of targets bench-gated | medium_planning |
| startup_park | park/reset state | startup_park | required | IAC_INIT_PARK_CONTRACT.md | park/reset physical direction and hard-stop behavior bench-gated | high_static |
| startup_park | bad-shutdown state | startup_park | likely_required | IAC_INIT_PARK_CONTRACT.md | bad-shutdown physical recovery behavior bench-gated | high_static |
| startup_park | reset-in-work state | startup_park | required | IAC_INIT_PARK_CONTRACT.md | actual-zero/home behavior bench-gated | high_static |
| startup_park | R/S requested state | startup_park | likely_required | IAC_INIT_PARK_CONTRACT.md | ignition-off/park request behavior bench-gated | high_static |
| enable_gate | battery voltage | sensor | required | IAC_ENABLE_FAULT_GATE_CONTRACT.md | physical Enable behavior around voltage thresholds bench-gated | high_static |
| enable_gate | IAC enable/protection state | enable_gate | required | IAC_ENABLE_FAULT_GATE_CONTRACT.md | physical Enable pin/function bench-gated | high_static |
| position_state | actual IAC position | position_state | required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_INIT_PARK_CONTRACT.md | physical open/closed meaning and seed validity bench-gated | high_static |
| position_state | IAC actual-position seed validity | position_state | required | IAC_INIT_PARK_CONTRACT.md | normal-shutdown retention and reset/home hard-stop behavior bench-gated | high_static |
| position_state | desired IAC target | position_state | required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_INIT_PARK_CONTRACT.md | physical target meaning bench-gated | high_static |
| position_state | IAC position error | position_state | required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md | count sign vs airflow/open direction bench-gated | high_static |
| phase | step direction | phase_state | required | IAC_PHASE_SEQUENCE_CONTRACT.md | open/close direction bench-gated | high_static |
| phase | A/B phase state | phase_state | required | IAC_PHASE_SEQUENCE_CONTRACT.md | physical A/B mapping and external driver behavior bench-gated | high_static |
| cadence | step cadence / rate limit | cadence | required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md | safe physical cadence/rate limit bench-gated | medium_planning |
| dashpot | dashpot / follower state | dashpot | optional_initially | source/minimal_os/iac/README.md | dashpot/follower behavior source-gated | low_medium_planning |
| mode_gates | closed-throttle / idle-mode state | mode_gate | required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md | closed-throttle threshold/source behavior source-gated | medium_planning |
| sensor_inputs | TPS / throttle state | sensor | likely_required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md | TPS scaling/threshold source-gated | medium_planning |
| dashpot | vehicle speed if used for dashpot/follower | sensor | optional_initially | source/minimal_os/iac/README.md | vehicle-speed IAC modifiers source-gated | low_medium_planning |
| safety | stall/dropout safe state | safety_gate | required | MINIMAL_OS_MODULE_BOUNDARY.md; IAC_INIT_PARK_CONTRACT.md | safe default/park behavior bench-gated | medium_planning |
| output_latch | output shadow/latch dependency | output_scale | required | IAC_IDLE_AIR_OUTPUT_CONTRACT.md; IAC_PHASE_SEQUENCE_CONTRACT.md; IAC_ENABLE_FAULT_GATE_CONTRACT.md | direct L3062 writer forbidden until physical pins and cadence are proven | high_static |
| excluded | transmission shift/TCC idle modifiers | excluded | excluded | none | none | high_policy |
| excluded | EGR idle correction | excluded | excluded | none | none | high_policy |
| excluded | EVAP/purge idle correction | excluded | excluded | none | none | high_policy |
| excluded | emissions-only diagnostics | excluded | excluded | none | none | high_policy |
| unknown | unresolved IAC inputs | unknown | unknown | IAC_MINIMAL_MODULE_INPUTS.md | requires future source trace | low_unclassified |

## Required Discipline

This contract may define what the IAC module needs, but it must not imply the output path is implementation-ready.

No calibration-only section is marked required unless tied to an existing IAC hardware/source contract. Unknown IAC-adjacent sections remain unknown rather than guessed.
