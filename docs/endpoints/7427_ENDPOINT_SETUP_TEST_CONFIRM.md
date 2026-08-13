# 7427 Endpoint SETUP / TEST-CONFIRM Contract

## Purpose

Convert all remaining physical uncertainty into explicit endpoint records without reopening completed algorithm extraction.

Canonical machine-readable files:

- `maps/endpoints/7427_endpoint_setup.csv`
- `maps/endpoints/7427_endpoint_test_confirm.csv`

## Evidence levels

```text
SOFTWARE_PROVEN
  executable/static dataflow establishes software acquisition/command semantics

ELECTRICAL_INFERRED
  electrical behavior is inferred from device class/common implementation but not measured on this PCM

PHYSICAL_PIN_INFERRED
  candidate board/connector mapping exists or hardware class is known, but connector/polarity is not bench-confirmed

BENCH_CONFIRMED
  applied physical stimulus/command and observed software/pin response are recorded with PASS
```

Software evidence and physical evidence are independent. A software-proven endpoint does not become bench-confirmed because its physical behavior is obvious or conventional.

## Stage 1 — SETUP

Each row defines:

```text
semantic signal
software acquisition/command location
hardware class
candidate connector/pin
expected electrical behavior
expected range/polarity/frequency
scaling/conversion
sample/update cadence
software evidence
physical evidence
permission default
explicit bench stimulus/test procedure
```

Current retained/meaningful inventory includes:

### Inputs

```text
TPS
MAP
coolant
MAT/IAT
narrowband O2
battery/ignition-power sense
REF/DRP timing
knock event/count
VSS optional
A/C request optional
```

BMHM calibration byte `$5D02 = 01`; source semantics define bit2 set as separate BARO+MAP and bit2 clear as MAP-only. Therefore the current BMHM target uses the MAP-only branch and no separate physical BARO endpoint is required for the first replacement runtime. BARO remains a derived semantic state.

### Outputs / I/O

```text
injector pulsewidth
fuel-pump relay
IAC A/B/Enable phase command
spark timing handoff
EST/BYPASS authority
ALDL/development serial
power-hold/delayed shutdown
MIL optional
```

## Stage 2 — TEST-CONFIRM

No row may be changed to `BENCH_CONFIRMED` without measured evidence.

### Input proof direction

```text
physical stimulus
→ board/input circuit
→ hardware register/raw acquisition
→ semantic raw snapshot
→ conversion/scaling
→ validated/substituted value
```

Required observations:

```text
applied physical stimulus
observed raw software value
observed converted value
polarity/monotonicity
scaling/timebase
confirmed connector/pin
PASS / FAIL
```

### Output proof direction

```text
semantic command
→ permission/arbitration
→ HAL command
→ register/latch/mailbox
→ board driver
→ physical pin/load response
```

Required observations:

```text
applied semantic/software command
observed hardware register/mailbox state
observed physical pin/output response
polarity
pulsewidth/frequency/timebase where applicable
confirmed connector/pin
PASS / FAIL
```

## Initial safety policy

```text
fuel_permission  = FALSE
spark_permission = FALSE
iac_permission   = FALSE
pump_permission  = FALSE
aux_permissions  = FALSE
```

`ALDL_DEBUG` is the only endpoint that may be enabled early because it is observability-only, provided its HAL cannot touch production actuators.

## Input bench order

Recommended order minimizes risk and maximizes observability:

```text
1. BATTERY_IGN
2. ALDL_DEBUG transport
3. TPS
4. MAP
5. COOLANT
6. MAT_IAT
7. O2_NARROWBAND
8. REF_DRP
9. KNOCK_EVENT
10. VSS/A-C only if retained
```

The first seven can be tested with the engine completely stationary.

## Output bench order

```text
1. FUEL_PUMP with no fuel/load or isolated dummy load
2. IAC_PHASE_ENABLE with motor disconnected
3. IAC with current-limited motor after phase proof
4. SPARK_TIMING with ignition output isolated/dummy-loaded
5. EST_BYPASS_AUTHORITY with isolated ignition module
6. EFI_PW using existing FUEL-001..FUEL-004 harness
7. POWER_HOLD_SHUTDOWN
8. optional MIL/aux outputs
```

Existing subsystem gates remain authoritative; this endpoint table does not bypass them.

## Key source-proven software endpoints

### ADC group

Normal multi-channel ADC service proves:

```text
$3031 -> L00A6  TPS raw
$3032 -> L082E  MAP raw
$3033 -> L01D5  O2 raw
```

Other selected ADC modes prove:

```text
L00A5  coolant raw
L0230  inverted MAT raw
L00A7  battery raw / scaled representation
L0055  battery volts * 10 path
```

### REF / timing

```text
L3FC0 -> L005F -> RPM/timebase/run qualification
```

### Fuel pump

Source routine at `A59B+` executes on a documented 12.5 ms loop and clears `L306F` after the calibrated no-DRP timeout. Startup/IRQ code also writes `FF` to `L306F`. Physical inversion and connector routing remain bench questions.

### IAC

```text
L0007 actual position
L0008 desired position
L000A bits0/2/3/4 direction/A/B/Enable state
L004C bits2/3/4 output shadow
L3062 hardware latch write
```

### Spark

The software-facing handoff remains the preserved stock route using the proven conversion/rolling-state path around:

```text
$3FE8
$3FE6
$3FF6
$3FDC
$3FEC -> $3FE4 sync candidate
```

Physical roles remain bench-gated.

## Completion rule for physical endpoint percentage

The physical endpoint percentage is calculated only from retained production endpoints that have complete Stage-2 PASS records.

Optional disabled endpoints do not block the first engine start, but they remain visibly `NOT_RUN` rather than being silently counted complete.
