# Minimal OS Module Boundary

## Purpose

Define the OS-level module boundary for the clean 7427 hardware-contract minimal OS.

This contract combines the mapped fuel and spark output contracts with the next unmapped hardware subsystem. It does not create new ASM runtime code.

## Module Classes

```text
static-ready:
  statically mapped enough to define a provisional module/API, but still bench-pending.

bench-gated:
  likely required but must be scoped/bench-proven before implementation.

not yet mapped:
  do not implement. Create a focused hardware-output/input contract first.

forbidden until proven:
  do not add strategy baggage or direct hardware writes without contract evidence.
```

## Top-Level Module Map

| Module | Status | Runtime outputs | Next contract |
|---|---|---|---|
| `RESET_INIT` | partial_static | HC11 register relocation; stack; ASIC clear/default state; output-safe defaults; SCI/ALDL base state; watchdog base state | WATCHDOG_SAFE_STATE_CONTRACT or ALDL_DEBUG_CONTRACT after IAC |
| `SENSOR_ACQUIRE` | planned_not_fully_contracted | filtered sensor values; plausibility/default flags; battery correction inputs; RPM/load basis | SENSOR_ADC_INPUT_CONTRACT |
| `REF_RPM_PERIOD` | partial_static | RPM; period basis L005F/L0060; first DRP valid; recent DRP valid; run qualification inputs | REF_RPM_PERIOD_CONTRACT |
| `FUEL_OUTPUT` | static_ready_bench_pending | STD $3FCE runtime EFI pulsewidth handoff; zero/off command candidate | FUEL_MATH_MODULE_BOUNDARY after hardware outputs are bench-proven |
| `SPARK_OUTPUT` | boundary_only_no_asm | $3FE8/$3FE6 paired timing writes; $3FF6/$3FDC rolling updates; possible $3FEC->$3FE4 mirror; EST authority permission | bench classification before any spark ASM; then source/minimal_os/spark static stubs only if explicitly marked |
| `IDLE_AIR_OUTPUT` | next_unmapped_subsystem | IAC step direction; coil phase/latch sequence; present-count update; park/default position commands | IAC_IDLE_AIR_OUTPUT_CONTRACT |
| `ALDL_DEBUG` | planned | debug frames; trace visibility; module-state exports; bench instrumentation frames | ALDL_DEBUG_CONTRACT |
| `WATCHDOG_SAFE_STATE` | required_not_fully_contracted | watchdog service; no-ref fuel-off; spark/bypass safe state; IAC default/safe state; reset/fault response | WATCHDOG_SAFE_STATE_CONTRACT |
| `TRANSMISSION_EMISSIONS_EXCLUDED` | excluded_unless_hardware_required | none planned | none unless hardware-required evidence appears |

## RESET_INIT

Owns:

```text
HC11 register relocation
stack
ASIC window clear
output safe defaults
watchdog setup
SCI/ALDL setup
```

Status: `partial`.

Bench gates:

```text
ASIC init side effects
required $3FCC/$3FEA EFI output state
spark rolling-state first seed
watchdog service sequence
```

## SENSOR_ACQUIRE

Owns ADC/raw-input acquisition, filtering/defaulting, and sensor-state exports to fuel, spark, idle, and safe-state modules.

Status: `planned_not_fully_contracted`.

Next focused contract:

```text
SENSOR_ADC_INPUT_CONTRACT
```

## REF_RPM_PERIOD

Owns REF/DRP period/capture state and the period basis used by spark and run qualification.

Current known state:

```text
$3FC0 = period/capture source candidate
L005F/L0060 = spark period basis
L0044 bit3 = first DRP valid latch
L0050 bit2 = recent DRP occurred gate
L0210 = qualifying DRP/ref event counter
```

Status: `partial_static`.

## FUEL_OUTPUT

Status: `static-ready / bench-pending`.

Owns:

```text
EFI_OUTPUT_INIT
EFI_PW_WRITE
```

Required runtime output:

```asm
; D = EFI pulsewidth in 1/65536 second units
STD $3FCE
```

Hard boundary:

```text
Fuel may have a provisional runtime writer.
Do not add per-pulse companion writes unless bench proves they are required.
```

Bench gates:

```text
$3FCE controls injector PW
zero command behavior
whether companion init is required
```

## SPARK_OUTPUT

Status: `boundary-only / no ASM`.

Owns:

```text
run qualification
bypass/EST authority
degree-to-time conversion
rolling state
ASIC handoff
optional EST monitor
dropout-safe behavior
```

Likely required outputs:

```text
$3FE8
$3FE6
$3FF6
$3FDC
```

Bench gates:

```text
$3FE8/$3FE6 paired role
$3FEC->$3FE4 mirror
physical bypass authority
first-event seed
L0201/L3FC0 packing
Error 42 side effects
dropout/missing-REF safe behavior
```

Hard boundary:

```text
No SPARK_WRITE.
No direct $3FE8/$3FE6 writer.
No LA906 replacement ASM.
No physical EST authority code.
```

## IDLE_AIR_OUTPUT

Status: `next unmapped subsystem`.

Owns:

```text
IAC present position
desired position
step direction
phase/latch output
park/crank/run behavior
```

Likely targets:

```text
IAC stepper ASIC/output registers
IAC RAM state
idle state flags
$3Fxx ASIC/output registers
$3FFC output latch candidate
```

Next contract:

```text
IAC_IDLE_AIR_OUTPUT_CONTRACT
```

Hard boundary:

```text
No IAC writer until output registers and phase sequence are extracted.
```

## ALDL_DEBUG

Status: `planned`.

Owns debug frames, hardware trace visibility, and module-state exports for bench validation. It must not perturb timing-critical output behavior.

## WATCHDOG_SAFE_STATE

Status: `required but not fully contracted`.

Owns:

```text
watchdog service
no-ref safe state
fuel-off safe state
spark/bypass safe state
IAC safe/default state
```

Hard boundary:

```text
Do not disable watchdog or leave outputs live during missing REF unless explicitly proven safe.
```

## Excluded Unless Hardware-Required

```text
no TCC
no shift logic
no EGR
no EVAP
no inherited mode-word baggage unless proven hardware-required
```

## Next Technical Target

Start the next focused hardware-output subsystem:

```text
docs/contracts/IAC_IDLE_AIR_OUTPUT_CONTRACT.md
maps/contracts/iac_idle_air_output_contract.csv
docs/tests/IAC_IDLE_AIR_OUTPUT_TEST.md
tools/build_iac_output_contract.py
```

The IAC pass should trace:

```text
IAC desired counts
IAC present counts
step direction
step rate
coil phase sequence
ASIC/output latch writes
park position
crank position
reset behavior
```
