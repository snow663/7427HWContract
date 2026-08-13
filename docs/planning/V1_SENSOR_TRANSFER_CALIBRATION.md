# V1 Sensor Transfer Calibration

## Status

`DESIGN BASELINE — physical/setup calibration authority`

This document defines how analog sensor voltages are converted into engineering values in the V1 replacement OS.

## Core rule

Analog sensor calibration is represented as an electrical-input to engineering-output transfer.

Preferred representation:

```text
X axis / breakpoints = sensor signal voltage, VDC
Y values             = engineering quantity
```

Runtime conversion uses piecewise-linear interpolation between adjacent points.

For points `(V0,Y0)` and `(V1,Y1)`:

```text
Y = Y0 + (V - V0) * (Y1 - Y0) / (V1 - V0)
```

X-axis voltage points must be strictly increasing. Y may increase or decrease with voltage.

A physically linear sensor may use two points. A nonlinear sensor may use as many points as needed to represent its curve accurately.

## MAT / IAT

For the current L19/TBI application, MAT/IAT is not assumed to be a factory-installed sensor. V1 supports it as an optional added analog sensor.

When installed/enabled:

```text
MAT_C = MAT_TRANSFER(MAT_VDC)
MAT_K = MAT_C + 273.15
```

The tuner-facing table is conceptually:

```text
VDC        Temperature C
0.xx       xxx
...
4.xx       xxx
```

In TunerPro terms this is a 1-D table: voltage is the X axis and temperature is the Y value.

This allows a GM thermistor, another automotive thermistor, or a conditioned analog temperature sensor to be used without changing firmware; only the physical transfer table changes.

When MAT is not installed/enabled, the air-charge and spark systems use the explicitly defined disabled/fallback policy. The OS must not report a substituted temperature as a valid measured MAT value.

## CTS

CTS uses the same transfer architecture:

```text
X = CTS sensor voltage, VDC
Y = coolant temperature, deg C

CTS_C = CTS_TRANSFER(CTS_VDC)
```

Because a thermistor is nonlinear, its table should contain enough breakpoints to match the sensor plus PCM bias circuit over the useful temperature range.

## MAP

MAP uses:

```text
X = MAP sensor voltage, VDC
Y = manifold pressure, kPa absolute

MAP_KPA_ABS = MAP_TRANSFER(MAP_VDC)
```

A linear MAP sensor normally requires only two points. More points are permitted for alternate sensors or conditioning circuits.

## Wideband analog input

An analog wideband controller uses:

```text
X = controller output voltage, VDC
Y = lambda

WB_LAMBDA = WB_TRANSFER(WB_VDC)
```

A linear controller normally requires two points; nonlinear/custom outputs may use more.

## TPS

TPS is normally linear. It may be represented either as the same generic transfer table or as the equivalent named endpoints:

```text
TPS_CLOSED_V
TPS_WOT_V
```

with derived percentage:

```text
TPS_PERCENT = 100 * (TPS_V - TPS_CLOSED_V) / (TPS_WOT_V - TPS_CLOSED_V)
```

The generic transfer representation remains available if a nonstandard sensor or linkage requires it.

## Battery voltage

Battery sensing is also an electrical transfer, usually linear:

```text
X = ADC input voltage, VDC
Y = vehicle battery voltage, VDC
```

Two points are normally sufficient.

## ADC raw-to-voltage layer

Sensor transfer tables use actual input VDC rather than raw ADC counts so the sensor definition remains independent of ADC resolution.

Conceptually:

```text
ADC_VDC = ADC_RAW * ADC_REFERENCE_V / ADC_FULL_SCALE_COUNT
```

If hardware characterization requires channel-specific correction:

```text
SENSOR_VDC = ADC_VDC * ADC_GAIN + ADC_OFFSET
```

ADC reference, gain, and offset are physical hardware/setup calibration, not engine tuning values.

## Calibration classes

Sensor transfer tables are `SETUP`, not `TUNE`.

Examples:

```text
SETUP:
  MAT VDC -> deg C
  CTS VDC -> deg C
  MAP VDC -> kPa
  WB VDC -> lambda
  TPS endpoint/transfer
  battery input transfer

TUNE:
  idle TPS threshold
  PE threshold
  DFCO threshold
  temperature fuel/spark corrections
  O2 feedback gains
```

A behavioral calibration problem must not be corrected by falsifying the sensor transfer unless the electrical/engineering conversion itself is wrong.

## Required observability

For analog sensors, ADX should expose where practical:

```text
raw ADC value
calculated sensor VDC
converted engineering value
filtered/control value
validity state
substitution state
```

For MAT specifically:

```text
MAT_RAW
MAT_VDC
MAT_C
MAT_K
MAT_CONTROL_C
MAT_ENABLED
MAT_VALID
MAT_SUBSTITUTED
```

## Non-effect contract

```text
Changing a sensor transfer changes only electrical-to-engineering conversion.
It does not directly change VE, fuel pressure, injector flow, target lambda, AE, spark tables, idle gains, or feedback gains.
Optional MAT may be absent without requiring a different firmware build.
Derived engineering values are read-only runtime quantities.
```
