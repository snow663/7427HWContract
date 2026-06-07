# EFI Output Companion Registers

## Purpose

Determine whether `$3FCE/$3FCF` is a standalone EFI pulsewidth handoff or whether nearby ASIC registers provide enable, mode, latch, strobe, diagnostic, or zero-fuel behavior.

## Anchor

`$3FCE/$3FCF` is the suspected 16-bit EFI pulsewidth command in 1/65536-second units.

Current static result:

```text
normal run/TBI path:  STD L3FCE at 0x8512
zero/transient path:  STD L3FCE at 0x8426
diagnostic 3 ms:     STD L3FCE at 0xFAEE
diagnostic/off zero: STD L3FCE at 0xFB44
```

## Address Window

Window searched:

```text
$3FC8-$3FD2
$3FE8-$3FEC
```

No direct standalone rows were found for `$3FCD`, `$3FCF`, or `$3FD0`. `$3FCD` is the low byte of the 16-bit `$3FCC` write pair, and `$3FCF` is the low byte of the 16-bit `$3FCE` write pair.

| Address | Access | Width | Static role | Same routine as `$3FCE` | Required? | Confidence |
|---|---|---:|---|---|---|---|
| `$3FC8` | R | 16 | timing/status candidate, TOC1/knock-window side | no | no unless dependency proves | medium |
| `$3FCA` | R | 16 | RPM/event counter candidate | no | no unless dependency proves | medium |
| `$3FCC/$3FCD` | W | 16 | ASIC fuel/scheduler command candidate A | yes only in diagnostic/output-cycling routine | test item | medium-high |
| `$3FCE/$3FCF` | W | 16 | EFI PW anchor | yes | yes if confirmed | high |
| `$3FD0` | none found | - | no direct static row | no | unknown/no evidence | low |
| `$3FE8` | W | 16 | EST/spark timing output engine | no | no for EFI PW | high |
| `$3FEA/$3FEB` | W | 16 | ASIC fuel/scheduler command candidate B | yes only in diagnostic/output-cycling routine | test item | medium-high |
| `$3FEC` | R | 16 | hardware status/source read | no | no for EFI PW unless dependency proves | medium |

## `$3FCE` Write Sites

| PC | Routine | Value source | Path | Nearby writes | Notes |
|---|---|---|---|---|---|
| `0x8426` | `L82ED` | `D` after `CLRA/CLRB` | zero/transient gate | none in same routine/window | writes zero to EFI PW before short delay and `$3FC0` timing read |
| `0x8512` | `L84F5` | `D` final BPW after sync BPW/min/BPW bias/max clamp | normal TBI final PW | none immediately before/after in searched window | bypassed if CPI/PFI mode bit is set |
| `0xFAEE` | `LFA5B` | `D=0x00C5` | diagnostic output cycling | `$3FCC` at `0xFADC`, `$3FEA` at `0xFAE5` before it | source comment says `SET UP FOR 3msec PULSES`, `SAVE TO EFI PW` |
| `0xFB44` | `LFA5B` | `D=0x0000` | diagnostic/output-off | nearby `$3062` port clear before it, no `$3FCC/$3FEA` immediately before | likely EFI PW zero/off behavior |

## Companion Register Candidates

### `$3FCC/$3FCD`

```text
all PCs:
  0x74D6 STD L3FCC ← D=0xD000, routine L74D3
  0xFADC STX L3FCC ← X=0xDFFF, routine LFA5B

access type: 16-bit write
same routine as $3FCE: yes only in diagnostic/output-cycling routine LFA5B
before/after $3FCE: before $3FCE at 0xFAEE by 0x12 bytes in LFA5B
hypothesis: ASIC command/mode preload, possible diagnostic output enable/mode, not proven required for normal run $3FCE
confidence: medium-high static candidate, bench pending
```

Test: freeze or vary `$3FCC` while forcing `$3FCE`; if injector output stops/arms/changes mode, `$3FCC` is required as a companion.

### `$3FEA/$3FEB`

```text
all PCs:
  0x74DF STD L3FEA ← D=0xDFFF, routine L74D3
  0xFAE5 STX L3FEA ← X=0xDFFF, routine LFA5B

access type: 16-bit write
same routine as $3FCE: yes only in diagnostic/output-cycling routine LFA5B
before/after $3FCE: before $3FCE at 0xFAEE by 0x09 bytes in LFA5B
hypothesis: ASIC command/mode/output-enable candidate, maybe diagnostic output-cycling companion
confidence: medium-high static candidate, bench pending
```

Test: with fixed `$3FCE`, vary or freeze `$3FEA`; if injector output arms/disarms or changes only with `$3FEA`, classify Path C.

### `$3FCA`

```text
all PCs:
  0x741F LDD L3FCA
  0x8629 LDX L3FCA
  0xABD3 LDD L3FCA
  0xE01E LDX L3FCA

access type: 16-bit read only
same routine as $3FCE: no
hypothesis: ASIC RPM/event counter/status input, not EFI PW latch/strobe
confidence: medium
```

### `$3FE8`

```text
all PCs:
  0xABAA STD L3FE8

access type: 16-bit write
same routine as $3FCE: no
hypothesis: spark/EST timing output engine, not EFI PW companion
confidence: high for non-EFI role
```

### `$3FEC`

```text
all PCs:
  0xAC28 LDX L3FEC

access type: 16-bit read only
same routine as $3FCE: no
hypothesis: hardware status/source read, probably spark/status-side, not EFI PW strobe
confidence: medium
```

## Static Pattern Findings

### Normal TBI path

No immediate companion write was found near the normal final TBI `STD L3FCE` at `0x8512` within the searched address windows.

Static implication:

```text
normal BPW path looks like Path A unless bench proves a persistent mode/enable state from init is required.
```

### Diagnostic/output-cycling path

The diagnostic output-cycling routine writes `$3FCC` and `$3FEA` before writing `$00C5` to `$3FCE`.

Static implication:

```text
diagnostic output cycling may preload ASIC mode/enable values before commanding EFI PW.
This is the strongest static Path C clue.
```

### Zero/off path

The diagnostic/off path writes `$0000` to `$3FCE` after clearing `$3062` bits. No immediate `$3FCC`/`$3FEA` write appears in that zero path.

Static implication:

```text
$3FCE = 0 is likely a valid no-fuel/off command, but `$3062` and other output-port state may still matter in diagnostic mode.
```

## Required New-OS Behavior

Classify one of:

```text
Path A:
  $3FCE/$3FCF alone is sufficient.

Path C:
  $3FCE/$3FCF plus companion enable/mode/strobe is required.

Path B:
  $3FCE/$3FCF is not sufficient; timer scheduler is primary.
```

Do not write the minimal EFI PW writer until the bench test proves whether `$3FCC` and/or `$3FEA` are required as persistent preconditions or active strobes.

## Open Bench Tests

See `docs/tests/EFI_OUTPUT_COMPANION_REGISTER_TEST.md`.

Key unresolved questions:

- Are `$3FCC` and `$3FEA` persistent ASIC output-mode preloads?
- Are `$3FCC` and `$3FEA` diagnostic-only output-cycling commands?
- Does normal-run `$3FCE` require a mode already established by init?
- Does `$3FCE = 0` suppress fuel without touching `$3FCC/$3FEA`?
- Does `$3FEA` act like an output-enable, latch, or strobe?
