# Hybrid Standalone — 16197427 engine controller

Independent, clean-room engine-control firmware for the GM 16197427 ($7427) hardware.

## Project boundary

This directory is a **new standalone project**. It does not replace or extend `pseudo-source/`, which remains a separate stock-$31 equivalence/reconstruction project with its own source, tests, targets, and history. Do not move, modify, or link against `pseudo-source/` as part of the Hybrid build.

`source/`, `maps/`, `docs/`, `ROMFlow_Studio/`, and `pseudo-source/` may provide reviewed *evidence* to cite, but no factory algorithm, memory mapping, ISR or hardware behavior becomes authoritative in Hybrid simply because it appears in an annotated listing. Record provenance and verification for every imported contract. D8/BAMW HAC labels are provisional until checked against ROM bytes.

## Intent

- Use the simplest proven $D8-inspired speed-density airflow, fuel, spark, idle/IAC and DFCO principles.
- Implement **our own** explicit reset/startup, interrupt, dispatcher, state and scheduling system within the actual $7427 timing/hardware constraints.
- Separate physical input/output and ASIC transactions from algorithms and calibration.
- Expose large, appropriately resolved tune tables with explicit engineering units, axis dimensions, signedness, scale and clamping.
- Default to manual-transmission, no VSS dependency, no automatic-transmission or emissions actuator strategy.
- Keep optional closed-loop fueling, knock correction and transient features understandable, observable and individually configurable without hidden modifiers.
- Provide an isolated host simulation/test path before any target image or live control.

## Architecture

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for module ownership, calibration design and validation gates.

## Proposed tree (to be populated incrementally)

```text
Hybrid-standalone/
  README.md
  docs/
    ARCHITECTURE.md
  include/          # typed interfaces and units
  src/
    boot/           # reset, vectors, hardware init
    kernel/         # dispatcher and state machine
    irq/            # REF, compare, SCI, periodic ISR
    sensors/        # acquisition, conversion, filtering
    airflow/        # D8-inspired speed-density model
    fuel/           # base PW, AE, PE, WUE, DFCO, O2
    spark/          # main spark and corrections
    idle/           # rpm target, IAC and spark idle trim
    hw/             # 7427-only ASIC, timer and latch drivers
    diagnostics/    # transparent state and ALDL
  calibration/      # human-readable definitions, generator
  tools/            # deterministic calibration/BIN builders
  tests/            # independent host and timing tests
  targets/          # future HC11-specific startup/linker
```

The listed directories are a layout proposal, not implemented modules. They will be created as source is added.

## Baseline development rule

A successful host compilation is **not** proof of a runnable PCM image. Live-output capability requires verified hardware contracts, hard timing/stack budgets, reset/bypass and watchdog testing, target linker/map review, pin-level bench tests and an explicitly labeled test BIN. Maintain known-good firmware for rollback.

The Hybrid release must use its own OS ID, calibration header, XDF/ADX identities and build manifest; never identify a D8/$31 binary as a Hybrid image.
