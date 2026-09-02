# Validation record

## Contract snapshot

The simulator profile was derived from `snow663/7427HWContract` main commit:

```text
c902ff4c53356c089cefa8f92263454e960bf667
```

Primary authorities used:

```text
docs/WORKING_STATE.md
docs/ASIC_HARDWARE_REGISTER_CONTRACT.md
docs/DYNAMIC_TRACE_PLAN.md
maps/by_subsystem/hc11_core.csv
maps/by_subsystem/boot_watchdog_cpu.csv
maps/by_subsystem/sensor_adc.csv
maps/by_subsystem/asic_command_output.csv
maps/by_subsystem/asic_status_ref.csv
maps/by_subsystem/io_latch_output.csv
maps/by_subsystem/unknown_306x_board_io.csv
```

The supplied HAC HTML and source-trace CSVs were used only to check source locations and optional labels. Their comments do not define simulator behavior.

## Automated tests

```text
12 tests pass with the exact stock BMHM integration image; 10 self-contained tests pass without a ROM file.
```

Coverage includes:

- Real `$FFFE -> $FC29 -> $7100` reset-stub shape.
- `INIT` relocation from `$1000` to `$3000`.
- BMHM indexed bit-operation encoding.
- Interrupt stack/RTI round trip.
- ADC start, conversion delay, result, and CCF.
- E/32 reference-period contract model.
- ROM write protection and explicit debugger patching.
- Named/traced `$3FCE` fuel output handoff.
- Headless import of the desktop GUI without opening a window.
- GUI workbench controls for PCM-style numeric notation, inputs, stepping, breakpoints, memory reads, ROM protection, and explicit session-only patches.

## Stock BMHM real-ROM smoke run

Image identity:

```text
file:   BMHM.BIN
size:   65536 bytes
sha256: 6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004
status: exact match to the repo's stock BMHM authority
```

Command:

```bash
python3 tools/smoke_real_bin.py /path/to/BMHM.BIN --instructions 100000
```

Observed result for the default explicit/zeroed hardware inputs:

```text
completed instructions: 100000
elapsed E cycles:        458134
unimplemented opcodes:   0
final PC:                $7959
register mapping:        $3000
RAM mapping:             $0000
named output events:     1031
$3FCE fuel handoffs:     1
```

The run exercised contract-named HC11/ASIC accesses and interrupt entry/return. Counts are deterministic for the same image, profile, simulator version, and inputs.

## What this proves

- The stock image is loaded at the right CPU addresses.
- The reset vector and register-relocation path execute correctly.
- The implemented instruction set is sufficient for this 100,000-instruction startup/runtime path.
- The modular CPU/bus/device boundary can run actual `$31` code and expose its hardware contract.
- The trace can distinguish contract-high outputs from unresolved `$306x` test items.

## What remains modeled

- Intra-instruction E-bus phase timing.
- Physical meanings and bit polarities inside unresolved `$306x` and `$3FFA` state.
- Exact ADC external-mux-to-sensor binding.
- TCTL1 pin-level output actions.
- Full 7427 ASIC spark/fuel scheduling behavior.
- ALDL byte-serialization timing and live-dereference skew.
- Closed-loop engine/vehicle plant response.

Those items remain visible fidelity gates rather than hidden assumptions.
