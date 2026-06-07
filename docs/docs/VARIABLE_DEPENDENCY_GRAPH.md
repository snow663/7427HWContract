# 7427 Variable Dependency Graph v0.2

Static dependency draft. This file records confirmed visible chains and marks where deeper backward slicing is still needed.

## Fuel scheduler path — confirmed static chain anchors

```text
TOC5 compare write $301E / TOC4 compare write $301C
← D compare value
← TCNT $300E + delay/minimum lead-time clamp
← L0821/L0823/L0825/L0827 compare scratch
← L0250 BPW runtime pulse width
← L024C/L024E/L0254 sync/async BPW handoff
← BPW fuel math, battery multiplier, VE, AE, DFCO, crank fuel
← MAP/RPM/TPS/CTS/BATT/VSS/state
```

Contract details to preserve:

```text
clear TFLG1 bit at $3023
set/clear TMSK1 bit at $3022
set/clear TCTL1 output action bits at $3020
write TOC4/TOC5 compare at $301C/$301E
```

## Fuel math / AE / DFCO anchors

```text
L024E sync BPW
← VE result L0231
← current MAP L01C0/L01C6
← RPM L0062/L0063/L0068
← AFR L024A
← injector flow calibration L4D92
← BLM L0248 / PE and closed-loop modifiers if enabled
← AE accumulators L023A/L023E/L023F
← DFCO flags L0046 bit3 and mode word L003E bits
```

## Spark / EST anchors

```text
ASIC spark handoff candidates $3FDC/$3FE4/$3FE6/$3FE8/$3FF6
← spark delay/dwell/count value
← final spark calculation
← base spark table
← idle correction / coolant correction / knock retard
← MAP/RPM/CTS/state
```

Unproven: exact unit conversion and latch timing for `$3FE6/$3FE8/$3FF6`.

## Sensor acquisition anchors

```text
ADC control $3030
← channel select / conversion start command
ADC results $3031-$3034
→ raw sensor RAM L082D/L082E/L082F and related direct RAM
→ filtered MAP/TPS/CTS/BATT variables
→ fuel/spark/idle state
```

## ASIC/ref/status anchors

```text
$3FCA read
→ L0205 and RPM/event reference logic

$3FFA read
→ L0073 status mirror
→ event/status branch logic
→ scheduler/filtered RPM updates

$3FC4 read
→ L080D/L080C event-change tracking
```

## IAC/output latch anchors

```text
IAC desired/present state
← idle target, RPM error, CTS, TPS, VSS
→ phase/output bits
→ external output latch path, including $3FFC and 306x candidates
```

Unproven: exact physical phase-bit mapping.

## Watchdog/init anchors

```text
$303A COPRST
← #$55 then #$AA cadence
← reset path and periodic loop service
```

Preserve cadence until standalone OS boot is proven.
