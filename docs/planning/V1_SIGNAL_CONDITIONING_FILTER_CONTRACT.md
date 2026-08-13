# V1 Signal Conditioning and Filtering Contract

## Status

`DESIGN BASELINE — sensor/input conditioning authority`

This document defines the V1 signal-conditioning layer between hardware acquisition and control algorithms. Filtering is explicit, sensor-specific, observable, and separated from sensor transfer calibration and from behavioral control calibration.

## 1. Processing order

For analog channels:

```text
RAW ADC
  -> ADC-to-voltage conversion
  -> electrical plausibility / spike screening
  -> sensor transfer to engineering units
  -> sensor-specific low-pass filtering
  -> engineering plausibility / rate validation
  -> FILTERED / CONTROL engineering value
```

For digital/state inputs:

```text
RAW DIGITAL OBSERVATION
  -> optional electrical/sample qualification
  -> assert/release qualification timers or counts
  -> qualified semantic state
```

Timing-critical event inputs are treated separately.

## 2. Analog filtering goals

The filter must reduce quantization noise, isolated ADC glitches, and harness/electrical noise without creating unacceptable control lag.

No single filter constant is used for every sensor.

Required classes:

```text
FAST_ANALOG    TPS, MAP
MEDIUM_ANALOG  battery and similar supply/load observations
SLOW_ANALOG    CTS, MAT
SPECIAL        NB/WB oxygen inputs
```

## 3. Isolated-sample spike screening

A lightweight prefilter may reject a single implausible sample before it enters the main low-pass state.

Preferred V1 method for non-timing-critical analog inputs:

```text
DELTA = abs(SAMPLE - PREVIOUS_ACCEPTED_SAMPLE)

if DELTA <= SPIKE_LIMIT:
    ACCEPT SAMPLE
else:
    require confirmation from the next sample before accepting the step
```

This prevents one corrupted ADC conversion from moving the filtered value while still allowing a real fast signal change to pass after confirmation.

For TPS and MAP the spike threshold must be loose enough not to suppress genuine throttle transients.

## 4. First-order low-pass filter

The standard V1 analog low-pass form is:

```text
FILTERED[n] = FILTERED[n-1]
            + ALPHA * (INPUT[n] - FILTERED[n-1])
```

where `ALPHA` is sensor-specific.

Implementation may use fixed-point shift/add coefficients where practical.

Equivalent tuner-facing calibration may be expressed as either:

```text
FILTER_ALPHA
```

or the more intuitive:

```text
FILTER_TIME_CONSTANT_MS
```

The build/runtime layer may derive the internal coefficient from scheduler period and time constant.

## 5. Separate control and diagnostic paths

Where useful, retain both:

```text
ENG_UNFILTERED
ENG_FILTERED
```

Control modules normally consume `ENG_FILTERED`.

ADX should expose raw ADC, voltage, unfiltered engineering value, and filtered engineering value for important channels so filtering behavior can be diagnosed directly.

## 6. TPS

TPS requires fast response.

Preferred path:

```text
TPS_RAW
 -> TPS_VDC
 -> TPS_PERCENT_UNFILTERED
 -> light low-pass
 -> TPS_PERCENT_FILTERED
```

`TPS_RATE` should be derived from a deliberately chosen filtered or rate-specific signal, not blindly from noisy raw ADC counts.

A separate light rate filter is allowed:

```text
TPS_RATE_RAW = d(TPS_PERCENT_FILTERED) / dt
TPS_RATE = rate_filter(TPS_RATE_RAW)
```

The main TPS position filter must not materially delay throttle-opening detection.

## 7. MAP

MAP also requires fast response but benefits from modest noise suppression.

Preferred path:

```text
MAP_RAW
 -> MAP_VDC
 -> MAP_KPA_UNFILTERED
 -> modest low-pass
 -> MAP_KPA_FILTERED
```

Air-charge steady-state calculations use filtered MAP.

A separate transient signal may use a faster path or filtered derivative:

```text
MAP_RATE = rate_filter(d(MAP_KPA_FAST)/dt)
```

This prevents the main steady-state filter from forcing sluggish transient detection.

## 8. CTS and MAT

CTS and MAT change slowly and may use stronger filtering.

```text
CTS_CONTROL_C = slow_filter(CTS_C)
MAT_CONTROL_C = slow_filter(MAT_C)
```

Their filter time constants should be measured in hundreds of milliseconds or seconds as appropriate, not in one or two scheduler samples.

This prevents ADC noise and thermistor-divider noise from modulating warmup, density, or temperature corrections.

## 9. Battery voltage

Battery voltage may use moderate filtering:

```text
BATTERY_CONTROL_V = medium_filter(BATTERY_V)
```

However, key-off/low-voltage detection may also monitor an explicitly defined faster qualified path so a long smoothing time constant cannot hide a real power-state transition.

## 10. Oxygen inputs

NB and WB filtering must preserve the dynamics required by the selected feedback controller.

### Narrowband

NB should not be heavily averaged because switching behavior itself is useful information.

Allowed processing:

```text
small electrical-noise filter
rich/lean threshold hysteresis
switch-activity timing
```

### Wideband

WB may use light/moderate filtering sufficient to reject controller/output noise while retaining actual lambda response.

Feedback-controller gains must be tuned against the filtered signal actually used by the controller.

## 11. Digital/state inputs

Ordinary digital states use asymmetric qualification rather than single-sample decisions.

Define per signal where needed:

```text
ASSERT_CONFIRM_TIME
RELEASE_CONFIRM_TIME
```

Semantic state:

```text
if raw state remains asserted for ASSERT_CONFIRM_TIME:
    QUALIFIED_STATE = TRUE

if raw state remains released for RELEASE_CONFIRM_TIME:
    QUALIFIED_STATE = FALSE
```

Separate assert/release times allow fast fault-safe release with slower noise-resistant assertion, or vice versa.

## 12. Threshold-derived digital states

States derived from analog values should use both filtering and hysteresis.

Example pattern:

```text
if VALUE <= ENTER_THRESHOLD for ENTER_CONFIRM_TIME:
    STATE = TRUE

if VALUE >= EXIT_THRESHOLD for EXIT_CONFIRM_TIME:
    STATE = FALSE
```

This applies to idle qualification, PE/DFCO thresholds, low-voltage/key-off qualification, and similar state decisions.

## 13. REF / rotational timing

REF is not processed through ordinary debounce or generic low-pass filtering because edge timing carries crank-angle information.

Use hardware/event timestamps directly.

Derived period may receive plausibility filtering for display and noncritical derived quantities, but production rotational timing must retain real edge timing.

Allowed REF conditioning includes:

```text
minimum physically possible edge spacing rejection
maximum/stale timeout
period-to-period plausibility comparison
qualified rotation state
```

Rejected impossible edges must not advance the semantic event count.

## 14. Knock/event-count inputs

Pulse/event-count inputs such as knock activity should be accumulated over an explicit observation window rather than low-pass filtering individual pulses as if they were analog samples.

Example:

```text
KNOCK_ACTIVITY = event_count_delta / observation_window
```

Any smoothing is applied to the derived activity metric.

## 15. Calibration classes

Normal tuner-facing setup/tuning should expose only parameters that materially benefit calibration.

Likely advanced/developer calibration:

```text
TPS position filter time constant
TPS rate filter time constant
MAP steady filter time constant
MAP rate filter time constant
CTS filter time constant
MAT filter time constant
battery filter time constant
sensor spike-confirm thresholds
ordinary digital assert/release times
```

These are not substitutes for incorrect sensor transfer tables or incorrect behavioral calibration.

## 16. ADX observability

For important analog channels expose where practical:

```text
RAW_ADC
INPUT_VDC
ENG_UNFILTERED
ENG_FILTERED / CONTROL_VALUE
FILTER_DELTA or rate where useful
VALIDITY
```

For digital channels expose:

```text
RAW_STATE
QUALIFIED_STATE
ASSERT/RELEASE TIMER where diagnostically useful
```

For REF expose:

```text
RAW/accepted event count
REF_PERIOD
REF_PERIOD_FILTERED for display if retained
REF_AGE
REF_VALID
ROTATION_VALID
rejected-edge count if implemented
```

## 17. Non-effect contract

```text
Filtering changes signal noise/bandwidth only.
Filtering does not change sensor calibration.
Filtering does not directly change VE, target lambda, injector characterization, spark tables, or idle targets.
A filter must not conceal sensor invalidity.
Timing-critical REF edges are not delayed by generic debounce/low-pass logic.
Digital qualification is explicit and asymmetric where useful.
```
