# V1 Physical Configuration and Derived-Value Model

## Status

`DESIGN BASELINE — pre-assembly planning artifact`

This document separates physical engine/injector facts from operating settings and derived control values. Tuner-facing configuration must not require the user to manually recalculate dependent constants.

## 1. Three classes of values

### A. Physical design-point configuration

These values describe hardware and normally remain unchanged until hardware is physically replaced.

```text
ENGINE_DISPLACEMENT
CYLINDER_COUNT
INJECTOR_COUNT
INJECTOR_DESIGN_FLOW
INJECTOR_DESIGN_PRESSURE
FUEL_STOICH_AFR
```

Example injector design point for the current application:

```text
INJECTOR_DESIGN_FLOW     = 80.0 lb/hr per injector
INJECTOR_DESIGN_PRESSURE = 13.0 psi gauge
```

Those two injector values remain fixed when only regulator pressure is changed.

### B. Operating/setup configuration

These values describe how the installed hardware is currently being operated and may be changed without redefining the hardware itself.

```text
OPERATING_FUEL_PRESSURE
```

Future examples may include explicitly configured sensor transfer choices or other physical operating settings, but they must remain separate from tune corrections.

### C. Derived values

Derived values are calculated automatically from physical design-point and operating configuration. They are observable but are not independently tuneable.

For TBI injector flow:

```text
EFFECTIVE_INJECTOR_FLOW =
    INJECTOR_DESIGN_FLOW
    * sqrt(OPERATING_FUEL_PRESSURE / INJECTOR_DESIGN_PRESSURE)
```

The TBI injectors discharge above the throttle plates, so configured fuel gauge pressure is the injector pressure differential used by this model. MAP is not part of this equation.

The user changes only `OPERATING_FUEL_PRESSURE` when regulator pressure changes. `EFFECTIVE_INJECTOR_FLOW` is recalculated automatically.

## 2. Configuration ownership rule

Physical configuration describes what the engine and fuel system actually are.

It must not be adjusted merely to correct a tune error.

```text
ENGINE_DISPLACEMENT      -> physical engine size only
INJECTOR_DESIGN_FLOW     -> injector characterized flow only
INJECTOR_DESIGN_PRESSURE -> pressure used for that characterization only
OPERATING_FUEL_PRESSURE  -> measured/current regulator pressure only
EFFECTIVE_INJECTOR_FLOW  -> derived only
```

If fueling is incorrect while these physical values are correct, correction belongs elsewhere, for example:

```text
VE / air-charge model
short-pulse correction
deadtime
startup/warmup fuel
AE
feedback
```

## 3. Engine displacement

`ENGINE_DISPLACEMENT` is a physical configuration value consumed by both speed-density and Alpha-N air-charge estimators.

It must never be altered to compensate VE or fuel-delivery calibration.

The semantic air equations therefore use the actual configured displacement directly.

## 4. Injector design-point model

The injector definition consists of a pair:

```text
(INJECTOR_DESIGN_FLOW, INJECTOR_DESIGN_PRESSURE)
```

Neither value is meaningful without the other.

For example:

```text
80.0 lb/hr @ 13.0 psi gauge
```

is the injector's modeled design point.

Changing operating pressure from 13 psi to another value does not rewrite this design point. It changes only the derived effective flow.

## 5. TunerPro presentation

The future XDF should present these values in an `Engine / Fuel System Setup` category.

Editable physical/setup values:

```text
Engine displacement
Cylinder count
Injector count
Injector design flow
Injector design pressure
Operating fuel pressure
Fuel stoichiometric AFR
```

Read-only/derived display values where practical:

```text
Effective injector flow
Effective injector flow per ms in internal units
Total effective injector capacity
```

The derived value should also be visible in the ADX so the tuner can confirm exactly what injector flow the running OS is using.

## 6. Change workflow

### Regulator/fuel-pressure change only

```text
change OPERATING_FUEL_PRESSURE
-> automatically recalculate EFFECTIVE_INJECTOR_FLOW
-> no VE-table rewrite
-> no injector-design-point rewrite
```

### Injector replacement

```text
change INJECTOR_DESIGN_FLOW
change INJECTOR_DESIGN_PRESSURE
retain or update OPERATING_FUEL_PRESSURE as physically appropriate
-> automatically recalculate EFFECTIVE_INJECTOR_FLOW
```

### Engine displacement change

```text
change ENGINE_DISPLACEMENT
-> air-charge model automatically uses new physical displacement
-> tune surfaces may then require recalibration because the physical engine changed
```

## 7. Derived-value policy

A value should be derived automatically whenever it is mathematically determined by more fundamental physical/setup values.

Do not expose redundant independently editable constants when doing so can make the calibration internally inconsistent.

Examples:

```text
configured injector design flow + design pressure + operating pressure
    -> effective injector flow

RPM period
    -> RPM

MAP + BARO
    -> pressure ratio

final air mass + cylinder count
    -> air mass per cylinder
```

## 8. Validation policy

The build/runtime configuration layer must reject or flag impossible or unsafe combinations rather than silently producing nonsense.

Examples:

```text
zero/negative displacement
zero injector design pressure
zero/negative operating pressure
zero injector count
invalid stoichiometric AFR
```

Range limits will be frozen later with the XDF exposure matrix.

## 9. Non-effect contract

```text
Changing operating fuel pressure changes only derived injector flow/delivery conversion.
Changing injector design flow changes only injector characterization/delivery conversion.
Changing injector design pressure changes only injector characterization/delivery conversion.
Changing engine displacement changes physical air-charge scaling only.
None of these values directly alters target lambda, VE, AE, warmup, spark, or idle gains.
```

Any implementation that requires manual IFR recalculation after a pressure change violates this contract.
