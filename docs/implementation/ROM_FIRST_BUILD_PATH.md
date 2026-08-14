# 7427 ROM-First Implementation Path

## Decision

The replacement OS will be built from the executable ROM outward.

The project will **not** freeze a complete binary-encoding matrix, RAM partition,
XDF address map, or ADX packet map before implementation.

The built ROM and its assembly/map output are the placement authority.

## Why

The hardware contract already provides the fixed boundaries that matter:

- stock reset code begins at `$7100`
- stock stack top is `$03FF`
- HC11 registers relocate from `$1000` to `$3000`
- calibration/header data exists at `$4000+`
- active HC11 vectors occupy `$FFD6-$FFFE`
- stock code proves additional RAM use at `$0800-$08FF`
- hardware/ASIC addresses remain owned by the HAL

Everything else can be allocated when the implementation creates a real need.

## Allocation policy

### RAM

RAM is allocated incrementally.

```text
module needs state
    -> add state to semantic or HAL-private RAM declarations
    -> assembler assigns the next location
    -> build/map verifies no collision with stack or hardware
```

Do not reserve broad fixed subsystem blocks merely for organizational symmetry.
If a later module needs a different location for direct-page, timing, interrupt,
or hardware reasons, move the symbol and let the map remain authoritative.

### Calibration ROM

Calibration storage is created with the code that consumes it.

```text
implement control feature
    -> define the required scalar/table
    -> choose only the representation needed by that implementation
    -> allocate it in ROM
    -> expose the resulting address/scaling in the definition
```

Frozen semantic units and table geometry remain design authority, but they do
not require addresses to exist before the executable exists.

### XDF

The XDF describes the actual calibration layout in the built ROM.

It does not dictate ROM placement ahead of the implementation.

### ADX

The ADX describes the actual telemetry packet/page layout implemented by the
ROM. The semantic telemetry manifest remains the channel-requirement authority,
but packet addresses are assigned when transport is built.

## Current first ROM milestone

`source/replacement_os/7427_rom.asm` is the first master image.

Its initial job is deliberately small:

1. enter through the real external-reset vector
2. set the stock-proven stack top
3. relocate HC11 registers to `$3000`
4. apply the stock-proven CPU-side startup register values
5. clear only RAM allocated by the current build
6. initialize semantic state with all actuator permissions disabled
7. initialize IAC software state without touching the IAC hardware latch
8. service the COP indefinitely in a stable engine-off loop
9. route every unowned interrupt to a COP-serviced safe halt

This image does **not** yet take control of fuel, spark, IAC, pump, or auxiliary
outputs.

## Next implementation increments

Proceed by adding one observable capability at a time:

```text
ROM bootstrap / vectors
    -> verify assembly and binary map
    -> read-only ADC acquisition
    -> read-only REF acquisition / cranking RPM
    -> base scheduler timer
    -> SCI/ALDL debug transport
    -> calibration header/integrity object
    -> first real calibration objects as algorithms are implemented
    -> preserved spark/EST island
    -> engine-running control modules
```

Each increment must preserve the rule that no production output becomes
executable merely because its module is linked.

## Definition generation rule

For every implemented calibration or telemetry object, retain enough metadata
to generate/maintain its external definition:

```text
symbol
actual address
storage width
signedness
scaling / conversion
engineering unit
table dimensions / axis symbols if applicable
```

That metadata follows the executable allocation. It does not precede it.

## Evidence correction discovered during bootstrap

The earlier ADC HAL labeled `$3008` as `HC11_OPTION`. Stock `F275` proves `$3008`
is relocated CPU PORTD and that bits 3..5 are used as the external ADC/mux
selector. The actual relocated HC11 OPTION register used during reset is
`$3039`.

The bootstrap corrects that naming/semantic error before it can become part of
the new ROM contract.
