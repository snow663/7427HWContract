# VSS / BPW Causality Reassessment — ALDL Transport Timing

## Purpose

Correct the earlier interpretation that the 255-mph VSS sample appearing one host-log row after a BPW drop necessarily meant the VSS event occurred later internally.

Authority:

```text
docs/contracts/ALDL_SERIALIZATION_TIMING_CONTRACT.md
docs/investigations/VSS_FUELING_BPWDROP_TRACE_2026-08-20.md
```

## Revised conclusion

The earlier statement:

```text
"the VSS spike happened after the BPW drop"
```

is **not proven by ALDL row order**.

The `$31` transmitter live-dereferences each output variable during serial transmission. In the relevant engine page:

```text
VSS      = byte 31, $0284
INT      = byte 49, $020F
BLM cell = byte 54, $0247
BLM      = byte 55, $0248
BPW      = bytes 57-58, $324C/$324D alias
```

At 8192 baud, BPW is read approximately 32 ms later than VSS within the same message.

Therefore a VSS transition can occur after the VSS byte was transmitted but before BPW is read and transmitted. A resulting host row can legitimately contain an older VSS value beside a newer BPW value.

## What remains valid from the earlier trace

The following findings remain static/log-valid:

```text
1. DTC24 itself is not the normal fuel routine's VSS-fault branch; DTC16 is.
2. literal 2.bin contains real VSS-dependent fuel-control paths.
3. the loaded BLM cell transition 8 -> 4 matches the corrected RPM/MAP cell geometry and hysteresis.
4. the cell transition changes BLM 129 -> 120 and INT 134 -> 128, both capable of reducing PW.
5. at ~20% TPS, normal loaded BLM cell selection is based on RPM/MAP rather than the idle VSS precheck.
```

Thus the BLM-cell transition remains a valid contributor to the observed BPW decrease.

What is no longer valid is using the *next-row* 255-mph display as evidence that VSS could not have participated earlier in the same internal event.

## Current causal classification

```text
BLM-cell transition contribution to BPW drop:   STRONGLY SUPPORTED
VSS as direct initiator of same event:           NOT RULED OUT BY ROW ORDER
DTC24 direct BPW command:                        NOT FOUND
DTC16 fallback during examined log:              NOT ACTIVE PER LOGGED FLAG
VSS-dependent engine authority in literal 2.bin: CONFIRMED STATIC
```

## Calibration-policy consequence for this truck

The current vehicle does not provide a trustworthy VSS to the PCM. Vehicle speed is therefore unsuitable as an integral/required engine-management state.

For this manual/cable-speedometer application, the preferred policy is:

```text
ENGINE-ESSENTIAL CONTROL
  RPM
  MAP
  TPS
  coolant
  battery
  O2/mixture state
  knock
  REF/engine rotation
  baro as applicable

OPTIONAL VEHICLE-MOTION LAYER
  VSS, only if later supplied and validated
```

VSS should not have authority to unexpectedly alter:

```text
fuel cut / MPH limiter
DFCO qualification
PE qualification/delay
loaded fueling
AE scaling
BLM selection except an optional dedicated moving/idle policy
spark or torque intervention
```

Any vehicle-motion feature retained should either:

1. have a validated VSS source, or
2. fail neutral when VSS is absent/invalid.

For the immediate stock-OS tuning path, the clean experiment is a **literal `2.bin` baseline plus VSS-neutralization only**, preserving its current VE, spark, AFR, BLM, injector model, and other calibration behavior. That isolates whether the bogus vehicle-speed state contributes to the stumble without reintroducing unrelated later-bin changes.
