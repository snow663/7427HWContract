# V1 Rotation / Reference Geometry Configuration

## Status

`DESIGN BASELINE — physical/setup calibration authority`

This document separates physical engine geometry from REF-trigger geometry so the replacement OS does not hard-code the stock V8/reference relationship.

## 1. Editable physical/setup values

```text
CYLINDER_COUNT
REF_EVENTS_PER_CRANK_REV
REF_TO_EVENT_TDC_OFFSET_DEG
```

`CYLINDER_COUNT` describes the engine.

`REF_EVENTS_PER_CRANK_REV` describes the hardware reference signal and is independent of cylinder count.

`REF_TO_EVENT_TDC_OFFSET_DEG` is the signed crank-angle phase from a REF edge to the nominal TDC associated with that event. Sign convention is defined as:

```text
positive = REF edge occurs before the corresponding event TDC
negative = REF edge occurs after the corresponding event TDC
```

The value is setup geometry, not a spark-tuning correction.

## 2. Derived reference geometry

For a four-stroke engine:

```text
REF_EVENTS_PER_ENGINE_CYCLE = 2 * REF_EVENTS_PER_CRANK_REV
REF_EVENT_SPACING_DEG = 360 / REF_EVENTS_PER_CRANK_REV
```

For evenly spaced combustion events:

```text
COMBUSTION_EVENTS_PER_ENGINE_CYCLE = CYLINDER_COUNT
COMBUSTION_EVENT_SPACING_DEG = 720 / CYLINDER_COUNT
```

These values are derived/read-only and must not be independently edited.

Example for an eight-cylinder engine with four REF events per crank revolution:

```text
CYLINDER_COUNT               = 8
REF_EVENTS_PER_CRANK_REV     = 4
REF_EVENTS_PER_ENGINE_CYCLE  = 8
REF_EVENT_SPACING_DEG        = 90 crank degrees
COMBUSTION_EVENT_SPACING_DEG = 90 crank degrees
```

This is a one-REF-event-per-combustion-event arrangement.

## 3. RPM derivation

RPM is derived from measured REF period and configured REF event count, rather than from a hard-coded stock constant.

If `REF_PERIOD_SEC` is the elapsed time between consecutive REF edges:

```text
RPM = 60 / (REF_PERIOD_SEC * REF_EVENTS_PER_CRANK_REV)
```

The implementation may use timer counts and a precomputed fixed-point scale, but the tuner-facing meaning remains this equation.

Changing `REF_EVENTS_PER_CRANK_REV` therefore automatically changes the RPM conversion factor.

## 4. Angular reference model

The timing system treats each REF edge as a known angular landmark.

For evenly spaced REF edges:

```text
REF_EVENT_SPACING_DEG = 360 / REF_EVENTS_PER_CRANK_REV
```

The configured phase establishes where the corresponding event TDC lies relative to the observed edge:

```text
EVENT_TDC_ANGLE = REF_EDGE_ANGLE + REF_TO_EVENT_TDC_OFFSET_DEG
```

The internal timer-to-angle conversion then uses the configured event spacing and measured REF period to schedule semantic crank angles.

`REF_TO_EVENT_TDC_OFFSET_DEG` must be applied at the reference-coordinate layer before normal spark advance is applied.

It must not be hidden inside the main spark table or base-timing calibration.

## 5. Relationship to spark advance

The intended separation is:

```text
REF hardware geometry
    -> REF_TO_EVENT_TDC_OFFSET_DEG
    -> true crank-angle coordinate
    -> requested spark advance/retard
    -> preserved spark timing island
```

For example, if a timing light shows that the software's nominal 0-degree command occurs 6 crank degrees away from true TDC because the REF relationship is displaced, the setup offset is the correct place to characterize that relationship. The main spark table remains an actual desired advance table.

This corrects timing-reference alignment. It does not mechanically alter distributor rotor-to-cap phasing; rotor phasing remains a separate physical distributor constraint.

## 6. Cylinder count ownership

`CYLINDER_COUNT` is also used by other physically derived quantities, including:

```text
AIR_MASS_PER_CYLINDER = AIR_MASS_CYCLE / CYLINDER_COUNT
COMBUSTION_EVENT_SPACING_DEG = 720 / CYLINDER_COUNT
```

It is a setup value and should be editable in TunerPro.

Changing cylinder count must not directly alter VE, target lambda, spark tables, injector flow, or sensor transfers.

## 7. Reference/event ratio

Expose the derived relationship:

```text
REF_EVENTS_PER_COMBUSTION_EVENT =
    REF_EVENTS_PER_ENGINE_CYCLE / CYLINDER_COUNT
```

For the normal V8 case:

```text
8 REF events / 8 combustion events = 1.0
```

V1 should explicitly validate the configured relationship. A one-to-one relationship is the simplest supported case. Future applications with multiple REF edges per combustion event or fewer REF edges than combustion events may be supported through an explicit event-mapping/synchronization strategy rather than by assuming cylinder count and REF count are always identical.

## 8. Configuration validation

Reject or flag at minimum:

```text
CYLINDER_COUNT <= 0
REF_EVENTS_PER_CRANK_REV <= 0
non-finite REF offset
unsupported REF/combustion event relationship
```

A configuration error must not silently produce an incorrect RPM or crank-angle scale.

## 9. XDF exposure

Suggested `Engine / Rotation Setup` entries:

```text
Cylinder Count                         editable
REF Events per Crank Revolution        editable
REF to Event TDC Offset, crank deg     editable signed

REF Events per Engine Cycle            derived/read-only
REF Event Spacing, crank deg            derived/read-only
Combustion Event Spacing, crank deg     derived/read-only
REF Events per Combustion Event         derived/read-only
```

## 10. ADX observability

Expose:

```text
REF_PERIOD
REF_EVENTS_PER_CRANK_REV
REF_EVENTS_PER_ENGINE_CYCLE
REF_EVENT_SPACING_DEG
REF_TO_EVENT_TDC_OFFSET_DEG
RPM
CYLINDER_COUNT
COMBUSTION_EVENT_SPACING_DEG
REF_EVENTS_PER_COMBUSTION_EVENT
```

This makes RPM scaling and crank-angle geometry directly auditable from a log.

## 11. Non-effect contract

```text
Cylinder count defines physical engine/event geometry only.
REF event count defines reference-signal geometry and RPM scaling only.
REF offset defines the crank-angle coordinate relationship only.
REF offset does not retune desired spark advance.
Changing REF count does not directly change fuel, VE, lambda, or injector calibration.
Derived spacing/ratio values are read-only.
```
