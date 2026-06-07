# EFI Output Companion Register Bench Test

## Goal

Determine whether `$3FCE/$3FCF` is standalone pulsewidth storage or whether nearby ASIC registers provide a required enable, mode, latch, strobe, diagnostic command, or zero-fuel qualifier.

## Registers Under Test

```text
anchor:
  $3FCE/$3FCF  EFI PW command candidate

primary companion candidates:
  $3FCC/$3FCD  ASIC fuel/scheduler command candidate A
  $3FEA/$3FEB  ASIC fuel/scheduler command candidate B

watch-only/context:
  $3FC8        timing/status candidate
  $3FCA        RPM/event counter candidate
  $3FD0        no direct static row, watch anyway
  $3FE8        spark/EST output engine
  $3FEC        hardware status/source
```

## Required Signals

- Injector A output at driver side
- Injector B output at driver side
- `$3FCE/$3FCF` writes
- `$3FCC/$3FCD` writes
- `$3FEA/$3FEB` writes
- `$301C/$301E` writes if possible
- `$3020/$3022/$3023` writes if possible
- RPM/ref simulator state
- Battery voltage at PCM/injector supply

## Test Matrix

| Test | Setup | Action | Expected Path A | Expected Path C | Expected Path B |
|---|---|---|---|---|---|
| stock baseline | stock code, stable ref | log `$3FCE`, `$3FCC`, `$3FEA`, injector PW | `$3FCE` tracks PW; companions static or irrelevant | companion state appears required before PW works | injector PW follows TOC4/TOC5 |
| force `$3FCE` only | leave companions stock | force vector values into `$3FCE` | injector PW follows forced values | works only if companion already in correct state | no PW change |
| force `$3FCE`, freeze `$3FCC` | fixed `$3FCC` | sweep `$3FCE` values | PW still follows `$3FCE` | output changes/stops if `$3FCC` required | no PW change |
| force `$3FCE`, freeze `$3FEA` | fixed `$3FEA` | sweep `$3FCE` values | PW still follows `$3FCE` | output changes/stops if `$3FEA` required | no PW change |
| force zero | run/idle | write `$0000` to `$3FCE` | fuel off/min-off behavior | off only with correct companion state | no change if ignored |
| force diagnostic value | run/idle | write `$00C5` to `$3FCE` | about 3.006 ms pulse | about 3.006 ms only with companion state | no change if ignored |
| toggle `$3FCC` | fixed `$3FCE` | vary/toggle `$3FCC` | no pulsewidth effect | arms/disarms/changes output mode | maybe no effect |
| toggle `$3FEA` | fixed `$3FCE` | vary/toggle `$3FEA` | no pulsewidth effect | arms/disarms/strobes output | maybe no effect |

## Procedure

1. Establish a stock baseline with stable reference signal.
2. Scope injector A and B output pulsewidths.
3. Log or capture writes to `$3FCE`, `$3FCC`, and `$3FEA`.
4. Force `$3FCE` values from `maps/test_vectors/efi_pw_3fce_forced_values.csv` while leaving companion registers stock.
5. Repeat the forced `$3FCE` sweep while freezing `$3FCC` at a known value.
6. Repeat the forced `$3FCE` sweep while freezing `$3FEA` at a known value.
7. With `$3FCE` fixed at `$00C5`, vary or toggle `$3FCC` and `$3FEA` separately.
8. Record whether injector output follows `$3FCE`, companion state, or TOC4/TOC5 timing.

## Pass Classifications

```text
Path A:
  fixed companion state + forced $3FCE changes injector PW correctly.
  $3FCC/$3FEA do not need active strobing for each PW update.

Path C:
  $3FCE changes only work when a companion mode/enable/strobe is also correct.
  $3FCC and/or $3FEA must be reproduced in the minimal OS.

Path B:
  $3FCE changes do not control injector PW; TOC scheduler dominates.
```

## Data To Record

```csv
test_name,forced_3fce_hex,forced_3fcc_hex,forced_3fea_hex,measured_inj_a_ms,measured_inj_b_ms,toc4_seen,toc5_seen,path_result,notes
```

## Bench Notes

- Capture actual injector pulsewidth at the driver output, not only CPU writes.
- Treat `$3FCC` and `$3FEA` as persistent mode/enable candidates until proven diagnostic-only.
- Watch `$3FD0` even though no direct static row exists; a hardware latch may appear as a paired or implicit access.
- Do not write the minimal EFI PW output routine until this test says whether the writer is simply `STD L3FCE` or needs companion pre/post actions.
