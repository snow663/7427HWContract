# Minimal IAC Module

## Status

Documentation/API layout only.

No IAC ASM implementation exists yet. Do not add `IAC_WRITE`, direct `L3062` writer code, or IAC phase/park implementation until bench classification proves physical direction, Enable behavior, park/reset behavior, and step cadence/rate-limit behavior.

## Source Contracts

- `docs/contracts/IAC_IDLE_AIR_OUTPUT_CONTRACT.md`
- `docs/contracts/IAC_PHASE_SEQUENCE_CONTRACT.md`
- `docs/contracts/IAC_ENABLE_FAULT_GATE_CONTRACT.md`
- `docs/contracts/IAC_INIT_PARK_CONTRACT.md`

## Proven Source Boundary

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
```

## Module Stack

```text
IAC_INIT_PARK
→ IAC_ENABLE_GATE
→ IAC_POSITION_COMPARE
→ IAC_PHASE_STEP
→ IAC_OUTPUT_LATCH
```

## Submodule API Boundaries

### IAC_INIT_PARK

Owns startup/restart actual-position validity.

Inputs:

```text
NVM/reset state
bad-shutdown state
reset-in-work flag
R/S requested flag
park-down scalar L4EB0
battery/enable state
```

Outputs:

```text
L0007 actual position seed if source path writes it
L0008 desired park/crank/start target
reset-in-work state
R/S requested state
```

Bench gates:

```text
whether L4EB0=145 physically drives open or closed
whether L0008=0 drives the opposite direction
whether park movement reaches a hard stop
whether Enable is active during park
whether retained L0007 is trustworthy after normal shutdown
```

---

### IAC_ENABLE_GATE

Owns driver enable/protection state.

Inputs:

```text
L00A7 battery voltage, VDC/10
L003E bit2 low-battery/protection flag
L0044 bit4 status gate
fault/test/reset state
```

Outputs:

```text
L000A bit4 Enable candidate
L004C bit4 output shadow
L3062 bit4 hardware latch candidate
```

Static rule:

```text
Enable is not step-pulsed.
It is voltage/status/protection gated.
```

Bench gates:

```text
physical bit4 equals driver Enable pin
high-voltage behavior around CMPA #169
low-voltage/protection behavior
reset/test/fault clear behavior
```

---

### IAC_POSITION_COMPARE

Owns desired/actual error decision.

Inputs:

```text
L0007 actual/present position
L0008 desired/target position
```

Static behavior:

```text
actual == desired:
  no step

actual < desired:
  direction bit0 clear path
  actual increment candidate

actual > desired:
  direction bit0 set path
  actual decrement candidate
```

Bench gates:

```text
whether actual increment means more open or more closed
whether desired larger means more air or less air
```

---

### IAC_PHASE_STEP

Owns A/B ring state.

State:

```text
L000A bit0 = direction
L000A bit2 = A candidate
L000A bit3 = B candidate
```

Static ring:

```text
direction bit0 = 0:
  0x00 -> 0x04 -> 0x0C -> 0x08 -> 0x00

direction bit0 = 1:
  0x00 -> 0x08 -> 0x0C -> 0x04 -> 0x00
```

Bench gates:

```text
whether bit2/bit3 are physically A/B or swapped
whether external driver transforms the two-bit states
whether every software ring step equals one physical motor step
```

---

### IAC_OUTPUT_LATCH

Owns final hardware output update.

Static path:

```text
L000A bits2/3/4
→ L004C bits2/3/4 shadow update
→ L3062 full-byte hardware latch write
```

Static classification:

```text
normal IAC A/B update is full-field/shadow update
not separate hardware BSET/BCLR on the driver pins
```

Bench gates:

```text
L3062 bit2 physical A/B candidate
L3062 bit3 physical A/B candidate
L3062 bit4 physical Enable candidate
full-byte latch timing at driver input
```

---

### IAC_STEP_CADENCE

Owns timing/rate-limit permission for the next step.

Inputs:

```text
IAC step timer/cadence state, not yet isolated
current desired/actual error
voltage/enable state
startup/reset/park state
```

Outputs:

```text
step_allowed
next_step_delay_or_timer_reload
```

Bench/source gates:

```text
exact timer or counter that permits the next step
whether cadence changes during reset/park versus normal idle
whether voltage/protection state slows or blocks stepping
```

This module is planned because cadence is required before a safe writer exists. It is not yet separately contracted.

---

### IAC_TARGET_COMPUTE

Owns desired-position strategy, not hardware output.

Inputs:

```text
crank/start state
coolant/startup state
idle state
closed-loop idle corrections
calibration tables/scalars
```

Outputs:

```text
L0008 desired/target equivalent
```

Boundary:

```text
This module is strategy/calibration-side work.
The hardware contract only requires that the final desired target be compared against trusted actual position before stepping.
```

---

### IAC_DIAGNOSTIC_MONITOR

Optional unless bench/source proof shows side effects.

Owns diagnostic/fault behavior related to IAC output state.

Candidate inputs:

```text
low-battery/protection flags
bad-shutdown/reset flags
physical driver behavior if observable
```

Outputs:

```text
diagnostic/fault state
possible output disable request
```

Current status:

```text
not enough proof to require a full diagnostic monitor in the minimal OS
keep disabled or stubbed until bench/source contracts prove side effects
```

## Forbidden Until Bench-Proven

Do not add:

```text
IAC_WRITE
iac_output.asm
iac_phase_step.asm
iac_init_park.asm
direct L3062 writer code
```

until bench classification proves:

```text
physical A/B pin mapping
open/close direction
Enable physical function
park/reset behavior
step cadence/rate limit
actual-position seed validity
```

## Planned Future Layout

Pending only:

```text
source/minimal_os/iac/
  README.md
  init_park.asm          pending
  enable_gate.asm        pending
  position_compare.asm   pending
  phase_step.asm         pending
  step_cadence.asm       pending
  output_latch.asm       pending
  target_compute.asm     pending
  diagnostic_monitor.asm optional/pending
```

No files beyond `README.md` should be created until the corresponding bench gates are resolved or the file is explicitly marked as static stub only.

## Next Project Step

After this source-side boundary, proceed to the calibration-side index:

```text
tools/build_calibration_source_index.py
docs/contracts/CALIBRATION_SOURCE_INDEX.md
maps/contracts/calibration_source_index.csv
```

The calibration index should classify the local calibration extract by module relevance, but it should not replace the hardware contracts as the primary architecture driver.
