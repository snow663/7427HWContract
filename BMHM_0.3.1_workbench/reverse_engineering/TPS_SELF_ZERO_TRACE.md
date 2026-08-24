# TPS self-zero trace

This trace corrects the simplistic idea that the PCM treats the absolute TPS voltage as its closed-throttle baseline. `$31` learns an offset and produces a zero-referenced engine TPS value.

## Raw acquisition

`L00A6` is the raw TPS A/D result.

The engine-control loop later calls `$B1CF` and stores the resulting engine TPS into `$01D9`, which is the percent-TPS quantity used by fuel, IAC, spark and BLM logic.

## Downward zero tracking — `$B116-$B129`

Pseudo-code:

```text
raw = L00A6
if raw <= learned_zero(L02F6):
    learned_zero = lag_filter(raw, old=L02F6, constant=$5B25)
```

This lets the learned closed-throttle reference follow sensor/voltage/temperature drift downward instead of creating negative TPS.

`$5B25` is annotated as the TPS offset time constant.

## Decel-qualified upward offset step — `$B12C-$B15D`

The source does **not** simply compare current VSS against 5 mph. It does:

```text
delta = previous_filtered_speed(L00F7) - current_filtered_speed(L00D7)
if delta positive
   and required state flags qualify
   and delta > $5B2A
   and L009C.b0 qualifies:
       learned_zero_high_byte += $5B29
       clamp to $5B24
```

`$5B2A` is annotated as 5 MPH for TPS-increase/decel qualification.

`L00D7` is itself a filtered VSS/transmission-speed quantity. At `$B2A3-$B2AF`, the newly calculated speed at `$0814` is lag-filtered through `$5D20` with old `L00D7`, then stored back to `L00D7`.

Therefore the TPS auto-zero system still contains an indirect VSS dependency even though BMHM 0.3.1 removed VSS authority from the main engine-state consumers.

This is a current follow-up item: phantom speed should not be allowed to cause an upward learned-TPS-offset step.

## Startup/upward filter — `$B1AC-$B1CB`

A separate path handles raw TPS above the learned value:

```text
if raw TPS > learned_zero:
    learned_zero = lag_filter(raw, old=learned_zero, constant=$5B27)
    clamp high byte to $5B24
```

## Final engine TPS — `$B1CF-$B1EC`

The final conversion rounds the Q8.8 learned offset, subtracts it from raw TPS, clamps negative values to zero, and applies the calibrated gain:

```text
rounded_zero = round(L02F6)
delta = max(L00A6 - rounded_zero, 0)
engine_tps = scale(delta, gain=$5B26)
store -> L01A6
```

`$5B26` is annotated approximately 0.55% TPS per raw A/D count.

The main loop subsequently exposes this as the engine `%TPS` value at `$01D9`.

## Consequence for state gating

Absolute sensor voltage is not the correct variable for idle/drive state. The state gate should use the already self-zeroed engine TPS result (`$01D9` or a stock flag derived from it).

The current 0.3.1 true-idle gate uses stock `$0050.b7` as its TPS-side prerequisite. That flag is downstream of the self-zeroed TPS calculation, so ordinary baseline drift is already compensated.

Before tightening or replacing that TPS threshold, patch or otherwise neutralize the VSS/decel coupling in the upward TPS offset learner described above.
