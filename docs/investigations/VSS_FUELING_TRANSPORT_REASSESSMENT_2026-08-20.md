# VSS / BPW Causality Reassessment — ALDL Transport Timing

## Status / supersession

This investigation **supersedes the temporal row-order inference** in:

```text
docs/investigations/VSS_FUELING_BPWDROP_TRACE_2026-08-20.md
```

Specifically, the earlier statements equivalent to:

```text
"VSS = 255 appears on the next host-log row, therefore the VSS event occurred after the BPW drop internally"
```

are no longer authoritative.

The earlier investigation remains valid for its static code traces, calibration-byte checks, BLM-cell geometry, MAP/BLM/INT correlation, and identification of real VSS-dependent engine-control paths. Only the exact internal timing conclusion inferred from host-row order is superseded here.

## Current running calibration

```text
PCM:                 16197427
mask:                $31
engine:              L19 7.4L TBI
current running BIN: 2.bin
2.bin SHA-256:       2387d708c8d4cc82b78fabda579e48b7daef79f331543a54b669b70b6262877e
```

## Purpose

Correct the earlier interpretation that a 255-mph VSS sample displayed one host-log row after a BPW decrease necessarily meant the VSS transition occurred later inside the PCM.

Authority:

```text
docs/contracts/ALDL_SERIALIZATION_TIMING_CONTRACT.md
docs/investigations/VSS_FUELING_BPWDROP_TRACE_2026-08-20.md
source/31/BMHM_HAC_ORG_7100_to_end.asm
```

## Revised conclusion

The `$31` transmitter live-dereferences each output variable while serializing the message. It does not first freeze the whole ALDL row into one atomic snapshot.

Relevant engine-page ordering:

```text
VSS      = byte 31, $0284
INT      = byte 49, $020F
BLM cell = byte 54, $0247
BLM      = byte 55, $0248
BPW      = bytes 57-58, $324C/$324D alias
```

At 8192 baud with normal 10-bit asynchronous framing, one transmitted byte is approximately:

```text
10 / 8192 s ~= 1.2207 ms
```

Thus BPW is live-read roughly 26 transmitted-byte slots after VSS:

```text
VSS byte 31 -> BPW byte 57 ~= 31.7 ms
```

A VSS transition can therefore occur **after the VSS field for row N has already been read/transmitted but before BPW for that same row is read**.

One physically possible sequence is:

```text
t0          transmitter reads VSS = 9 mph for row N
+t few ms   VSS internal state glitches/changes
+t control  engine code reacts to the newer state
+t ~32 ms   transmitter later reads the now-changed BPW for row N
next frame  transmitter finally reads/displays VSS = 255 mph
```

The resulting host log can show:

```text
row N:     VSS normal, BPW changed
row N+1:   VSS = 255
```

without proving that the internal VSS event happened after the BPW change.

Therefore:

```text
host-row order != exact PCM internal event order
```

## What remains valid from the earlier BPW trace

The following findings remain useful/authoritative at their existing evidence level:

```text
1. DTC24 itself was not found as the normal fuel routine's direct VSS-fault BPW branch; DTC16 is the relevant fault branch there.
2. current running 2.bin contains real VSS-dependent engine-control paths.
3. the loaded BLM cell transition 8 -> 4 matches the decoded RPM/MAP cell geometry and hysteresis.
4. that transition changes BLM 129 -> 120 and INT 134 -> 128, both capable of reducing synchronous PW.
5. MAP also decreased across the same displayed transition, reducing the base speed-density air-charge term.
6. at substantial TPS, normal loaded BLM-cell selection is RPM/MAP based rather than the idle VSS precheck.
```

The BLM/MAP/INT transition remains a strong **contributor** to the displayed BPW decrease.

What is no longer valid is claiming that the next-row 255-mph display proves VSS could not have participated earlier in the same internal event.

## Current causal classification

```text
BLM-cell transition contribution to BPW decrease: STRONGLY SUPPORTED
MAP decrease contribution:                         STRONGLY SUPPORTED
INT reset/removal contribution:                    STRONGLY SUPPORTED
VSS as direct initiator of same internal event:    NOT RULED OUT BY ROW ORDER
DTC24 direct BPW command:                          NOT FOUND
DTC16 fallback during examined log:                NOT ACTIVE PER LOGGED FLAG
VSS-dependent engine authority in 2.bin:           CONFIRMED STATIC
```

This classification deliberately separates:

```text
"we have strong evidence these terms reduced PW"
```

from:

```text
"we have proven which internal event occurred first"
```

The latter requires static dependency/order proof, denser/reordered telemetry, replay, or direct instrumentation rather than host-row sequence alone.

## Calibration-policy consequence

The truck does not provide a trustworthy VSS state to the PCM, while current running `2.bin` contains real VSS engine authority.

For this manual/cable-speedometer application, the preferred policy is:

```text
ENGINE-ESSENTIAL CONTROL
  RPM
  MAP
  TPS
  coolant
  battery
  O2 / mixture state
  knock
  REF / engine rotation
  baro as applicable

OPTIONAL VEHICLE-MOTION LAYER
  VSS only if later supplied and validated
```

VSS should not unexpectedly control required engine behavior such as:

```text
MPH fuel cut / limiter
DFCO qualification
PE qualification/delay
loaded fueling
speed-specific AE modifiers
required BLM selection policy
spark / torque intervention
```

unless the corresponding vehicle-speed input is known-valid and the feature is intentionally retained.

The consumer-by-consumer removal authority is:

```text
docs/investigations/BIN2_VSS_AUTHORITY_AUDIT_2026-08-20.md
maps/analysis/bin2_vss_consumer_audit.csv
```

## Interpretation rule going forward

For slow steady-state periods, fields within one ALDL row can often be treated as approximately contemporaneous.

For fast events:

```text
1. static executable dependency/order proof
2. calibration thresholds and state requirements
3. sustained multi-sample behavior
4. field-order-corrected timing correlation
5. raw adjacent-row order only as weak evidence
```

Any future analyzer/replay should ideally attach an approximate within-message acquisition offset to each ALDL field rather than assigning one perfectly shared timestamp to all channels.