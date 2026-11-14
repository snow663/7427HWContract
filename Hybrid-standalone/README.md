# Hybrid Standalone — 16197427 engine controller

Independent, clean-room engine-control firmware for the GM 16197427 ($7427) hardware.

## Project boundary

This directory is a **new standalone project**. It does not replace or extend `pseudo-source/`, which remains a separate stock-$31 equivalence/reconstruction project with its own source, tests, targets, and history. Do not move, modify, or link against `pseudo-source/` as part of the Hybrid build.

`source/`, `maps/`, `docs/`, `ROMFlow_Studio/`, and `pseudo-source/` may provide reviewed *evidence* to cite, but no factory algorithm, memory mapping, ISR or hardware behavior becomes authoritative in Hybrid simply because it appears in an annotated listing. Record provenance and verification for every imported contract. D8/BAMW HAC labels are provisional until checked against ROM bytes. **Engine lineage and algorithm authority are distinct from hardware authority:** the engine originally ran the $D8 strategy; $31 is native to the current 7427 firmware, not the original engine control-law baseline.

## Control-law baseline and non-equivalence

The 1993 7.4L TBI engine came with the **$D8-family strategy on its donor controller**. The substantial mathematical and scaling differences between $D8 and $31 made apparent calibration-table matching unreliable: equivalent table numbers, VE values, or nominal injector flow do **not** establish equivalent commanded pulse width or timing. Treat $D8 as the engine-algorithm reference and the $7427/$31 work as evidence for the *target hardware interface*, not as a shortcut to the engine math.

Our own Hybrid calculations may improve upon $D8, but each intentional change must be defined against an independently verified $D8 numerical baseline, including intermediate stages, unit conversions, fuel-per-event convention and electrical output encoding. Never blindly copy $31 fuel formulas, feedback gains, hidden offsets or table encodings. See [architecture and calibration equivalence requirements](docs/ARCHITECTURE.md).

## Intent

- Use a verified $D8-native engine-control mathematical baseline for speed-density airflow, fuel, spark, idle/IAC and DFCO, then simplify and improve it deliberately.
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
    airflow/        # D8-derived speed-density model
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
