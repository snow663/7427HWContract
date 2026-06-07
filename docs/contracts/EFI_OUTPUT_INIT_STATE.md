# EFI Output Init State

## Purpose

Determine whether `$3FCC` and `$3FEA` are diagnostic-only, or whether they are initialized/preset before normal `$3FCE/$3FCF` runtime pulsewidth writes can work.

The companion-register adjacency pass showed no immediate write next to the normal `0x8512 STD L3FCE` runtime fuel handoff. This file maps lifetime/init-state evidence instead.

## Address Scope

Explicit candidates:

```text
$3FCC/$3FCD
$3FCE/$3FCF
$3FE8/$3FE9
$3FEA/$3FEB
$3FEC/$3FED
$3FF6/$3FF7
$3FFC/$3FFD
```

Also included: `$3FC0-$3FF8` block-clear/init row because it overlaps the EFI/ASIC window, plus status reads inside `$3FC8-$3FD2`.

## Static Summary

| Address | Total Rows | Write Rows | Static classification |
|---|---:|---:|---|
| `0x3FC0-0x3FF8` | 1 | 1 | boot ASIC-window block clear / required-init-state test item |
| `0x3FC8` | 1 | 0 | status/timing read, not fuel companion |
| `0x3FCA` | 4 | 0 | RPM/event counter read, not fuel companion |
| `0x3FCC` | 2 | 2 | fuel/output command preload candidate; ref-interrupt and diagnostic writes seen |
| `0x3FCE` | 4 | 4 | runtime EFI PW handoff plus diagnostic PW/off writes |
| `0x3FE8` | 1 | 1 | spark/EST timing handoff, not fuel companion |
| `0x3FEA` | 2 | 2 | fuel/output command preload candidate; ref-interrupt and diagnostic writes seen |
| `0x3FEC` | 1 | 0 | ASIC status/source read, not fuel companion |
| `0x3FF6` | 4 | 2 | EST fall counter/scheduler; diagnostic output cycling also writes it |
| `0x3FFC` | 23 | 13 | external output latch / I/O D global state, not local 3FCE companion |

## Key Findings

### 1. Normal `$3FCE` runtime writes still have no local companion

The normal fuel-path `$3FCE` rows remain direct 16-bit writes. No `$3FCC`, `$3FEA`, or `$3FFC` write appears in the same normal fuel routine immediately around `0x8426` or `0x8512`.

```text
0x8426 STD L3FCE  runtime fuel/no-fuel/transient gate write
0x8512 STD L3FCE  normal TBI final PW write
```

### 2. `$3FCC` and `$3FEA` are not diagnostic-only by static evidence

Both are written once in the ref/DRP interrupt area before the fuel math handoff code region, and again in the diagnostic/output-cycling routine:

```text
0x74D6 STD L3FCC  D=0xD000  ref-interrupt command/preload candidate
0x74DF STD L3FEA  D=0xDFFF  ref-interrupt command/preload candidate
0xFADC STX L3FCC  diagnostic output-cycling preload
0xFAE5 STX L3FEA  diagnostic output-cycling preload
```

Therefore `$3FCC/$3FEA` remain **possible persistent ASIC fuel/output init-state candidates**, not proven diagnostic-only.

### 3. Boot/init clears the ASIC window

A block-clear row writes even ASIC words from `$3FC0` through before `$3FFA`. This range overlaps `$3FCC`, `$3FCE`, `$3FE8`, `$3FEA`, and `$3FF6`, so any minimal OS must either reproduce or deliberately replace this ASIC-window initialization behavior.

### 4. `$3FE8/$3FEC/$3FF6` are not normal EFI-PW companions

Static rows place `$3FE8` and `$3FF6` in spark/EST timing paths, and `$3FEC` as a status/source read. They should be handled by spark/status contracts, not by the first minimal fuel-PW writer, unless bench behavior proves otherwise.

### 5. `$3FFC` is a separate global output-latch contract

`$3FFC` is heavily read/written in boot, output latch, diagnostic, ALDL, and output-cycling paths. It is probably important to board output state, but current static evidence does not make it a local `$3FCE` runtime strobe.

## Lifetime Rows

| Address | PC | Access | Width | Source | Routine | Lifetime | Role | Required? |
|---|---|---:|---:|---|---|---|---|---|
| `0x3FFC` | `0x713A` | W | 16 | `X` | `L7100` | boot_init | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0x7140` | R | 16 | `memory` | `L7100` | boot_init | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0x714A` | W | 16 | `D` | `L7100` | boot_init | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FC0-0x3FF8` | `0x715B` | W | 16 | `D` | `L7100` | boot_init | block clear of asic window including candidate fuel registers | test item required init state possible |
| `0x3FFC` | `0x71BD` | W | 16 | `X` | `L7100` | boot_init | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0x71EF` | R | 16 | `memory` | `L7100` | boot_init | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0x71F7` | W | 16 | `D` | `L7100` | boot_init | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FCA` | `0x741F` | R | 16 | `memory` | `L7100` | boot_init | asic timing status read not primary fuel companion | status read not direct 3fce |
| `0x3FCC` | `0x74D6` | W | 16 | `D=0xD000` | `L74D3` | ref_interrupt_pre_fuel_candidate | ref interrupt command preload or persistent init candidate | test item possible persistent init state |
| `0x3FEA` | `0x74DF` | W | 16 | `D=0xDFFF` | `L74D3` | ref_interrupt_pre_fuel_candidate | ref interrupt command preload or persistent init candidate | test item possible persistent init state |
| `0x3FCE` | `0x8426` | W | 16 | `D` | `L82ED` | runtime_fuel | runtime efi pw handoff | yes if 3fce bench confirmed |
| `0x3FCE` | `0x8512` | W | 16 | `D=0x7FFF` | `L84F5` | runtime_fuel | runtime efi pw handoff | yes if 3fce bench confirmed |
| `0x3FFC` | `0x8577` | R | 16 | `memory` | `L8548` | runtime_or_unknown | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0x857F` | W | 16 | `D` | `L8548` | runtime_or_unknown | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0x8587` | W | 16 | `D` | `L8548` | runtime_or_unknown | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FCA` | `0x8629` | R | 16 | `memory` | `L85B2` | runtime_or_unknown | asic timing status read not primary fuel companion | status read not direct 3fce |
| `0x3FF6` | `0xAB97` | R | 16 | `ADDD` | `LA906` | runtime_spark_est | est fall counter scheduler not primary fuel companion | not fuel writer but required for spark contract |
| `0x3FF6` | `0xABA4` | R | 16 | `SUBD` | `LA906` | runtime_spark_est | est fall counter scheduler not primary fuel companion | not fuel writer but required for spark contract |
| `0x3FE8` | `0xABAA` | W | 16 | `D` | `LA906` | runtime_spark_est | spark est timing handoff not primary fuel companion | not fuel writer but required for spark contract |
| `0x3FF6` | `0xABC8` | W | 16 | `D` | `LA906` | runtime_spark_est | est fall counter scheduler not primary fuel companion | not fuel writer but required for spark contract |
| `0x3FCA` | `0xABD3` | R | 16 | `memory` | `LA906` | runtime_or_unknown | asic timing status read not primary fuel companion | status read not direct 3fce |
| `0x3FEC` | `0xAC28` | R | 16 | `memory` | `LA906` | runtime_or_unknown | asic status source read not primary fuel companion | status read not direct 3fce |
| `0x3FFC` | `0xCC5A` | R | 16 | `memory` | `LCC4B` | runtime_or_unknown | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xCC75` | W | 16 | `D` | `LCC4B` | runtime_or_unknown | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FC8` | `0xCE81` | R | 16 | `memory` | `LCE10` | runtime_or_unknown | asic timing status read not primary fuel companion | status read not direct 3fce |
| `0x3FCA` | `0xE01E` | R | 16 | `memory` | `LDF54` | runtime_or_unknown | asic timing status read not primary fuel companion | status read not direct 3fce |
| `0x3FFC` | `0xF3EF` | R | 16 | `memory` | `LF3EE` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xF3FD` | W | 16 | `D` | `LF3EE` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xF637` | R | 16 | `memory` | `LF5E8` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xF63F` | W | 16 | `D` | `LF5E8` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xF7A2` | R | 16 | `memory` | `LF781` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xF7AA` | W | 16 | `D` | `LF781` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xF813` | R | 16 | `memory` | `LF781` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xF81B` | W | 16 | `D` | `LF781` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xFA3B` | R | 16 | `memory` | `LFA28` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xFA43` | W | 16 | `D` | `LFA28` | diagnostic_or_aldl_output_latch | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FCC` | `0xFADC` | W | 16 | `X` | `LFA5B` | diagnostic_output_cycling | diagnostic output preload or mode word candidate | probably diagnostic only but bench confirm |
| `0x3FEA` | `0xFAE5` | W | 16 | `X` | `LFA5B` | diagnostic_output_cycling | diagnostic output preload or mode word candidate | probably diagnostic only but bench confirm |
| `0x3FCE` | `0xFAEE` | W | 16 | `D=0x00C5` | `LFA5B` | diagnostic_output_cycling | diagnostic efi pw command or zero off | unknown test item |
| `0x3FF6` | `0xFB03` | W | 16 | `D` | `LFA5B` | runtime_spark_est | est fall counter scheduler not primary fuel companion | not fuel writer but required for spark contract |
| `0x3FCE` | `0xFB44` | W | 16 | `D=0x0000` | `LFA5B` | diagnostic_output_cycling | diagnostic efi pw command or zero off | unknown test item |
| `0x3FFC` | `0xFB5F` | R | 16 | `memory` | `LFA5B` | diagnostic_output_cycling | external output latch or io d port global state | required for output latch contract not direct 3fce |
| `0x3FFC` | `0xFB69` | W | 16 | `D` | `LFA5B` | diagnostic_output_cycling | external output latch or io d port global state | required for output latch contract not direct 3fce |

## Current Classification

```text
Path A-clean:
  not proven. Normal runtime has no local companion, but boot/ref init state may matter.

Path A-with-init:
  strongest current static fit. $3FCE appears to be the only runtime fuel-PW command, with possible one-time ASIC-window clear and $3FCC/$3FEA preload/init state.

Path C-runtime:
  not supported by normal local adjacency; no repeated companion write near normal $3FCE.

Path C-diagnostic-only:
  partly supported for the LFA5B output-cycling path, but $3FCC/$3FEA also have earlier ref-interrupt writes, so diagnostic-only is not proven.

Path B:
  still bench-testable, but static $3FCE handoff and unit evidence argue against treating TOC4/TOC5 as the only runtime fuel command.
```

## Minimal-OS Implication

Do not write the final minimal EFI PW writer yet. The next gate is to bench-test whether normal boot/ref init state is required before `$3FCE` commands injector pulsewidth.

If bench confirms A-with-init, split the future writer into:

```asm
EFI_OUTPUT_INIT:
    ; reproduce only proven ASIC fuel-output init/preload state
    RTS

EFI_PW_WRITE:
    ; D = pulsewidth counts in 1/65536 second units
    STD L3FCE
    RTS
```

## Open Bench Tests

See `docs/tests/EFI_OUTPUT_INIT_STATE_TEST.md`.
