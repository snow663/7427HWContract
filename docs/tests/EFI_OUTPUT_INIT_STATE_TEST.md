# EFI Output Init State Bench Test

## Goal

Determine whether `$3FCE/$3FCF` is enough after global ASIC initialization, or whether `$3FCC/$3FEA` or other ASIC-window state must be initialized before normal runtime `$3FCE` writes command injector pulsewidth.

## Paths Under Test

```text
Path A-clean:
  $3FCE alone works after normal boot; no special init state needed beyond global ASIC init.

Path A-with-init:
  $3FCE is the only runtime fuel command, but required ASIC init/mode writes must happen once at boot/ref-init.

Path C-runtime:
  $3FCE requires companion writes during runtime.

Path C-diagnostic-only:
  $3FCC/$3FEA are required only for diagnostic output cycling, not normal fuel.

Path B:
  $3FCE is not the controlling runtime fuel path.
```

## Registers To Watch

```text
$3FCC/$3FCD  command/preload candidate
$3FCE/$3FCF  EFI PW command
$3FE8/$3FE9  spark/EST timing handoff, verify not fuel companion
$3FEA/$3FEB  command/preload candidate
$3FEC/$3FED  status/source read
$3FF6/$3FF7  EST fall counter / scheduler
$3FFC/$3FFD  I/O D / external output latch
$3FC0-$3FF8  boot ASIC-window block clear
```

## Required Signals

- Injector A output at driver side
- Injector B output at driver side
- `$3FCE/$3FCF` write trace
- `$3FCC/$3FEA` write trace
- `$3FC0-$3FF8` init/block-clear trace if possible
- `$301C/$301E` compare writes if possible
- RPM/ref simulator state
- Battery voltage at PCM/injector supply
- Reset/key-on marker
- Crank/run/diagnostic mode marker

## Test Matrix

| Test | Setup | Expected A-clean | Expected A-with-init | Expected C-runtime | Expected B |
|---|---|---|---|---|---|
| stock boot trace | key-on → crank → run | `$3FCE` controls PW after boot | init writes appear before `$3FCE` works | companion writes recur near runtime fuel | injector PW follows TOC path |
| warm runtime trace | already running | only `$3FCE` changes with PW | only `$3FCE` changes after one-time init | `$3FCC/$3FEA` or latch writes recur | `$3FCE` irrelevant |
| force `$3FCE` after stock boot | leave init state stock | PW tracks forced `$3FCE` | PW tracks forced `$3FCE` | may require companion timing | no effect |
| block/ref-init suspect writes | skip or neutralize `$3FCC/$3FEA` preload if possible | no effect | `$3FCE` stops working or output corrupts | output corrupts | no effect on TOC-primary output |
| preload `$3FCC/$3FEA`, then force `$3FCE` | manually write stock/preload values first | no different than stock | restores `$3FCE` control | may require runtime strobe | no effect |
| force diagnostic `$00C5` | stable ref | near 3.006 ms | near 3.006 ms if init present | only works with companion/strobe | follows TOC instead |
| force zero `$3FCE` | run/idle | off/no-fuel behavior | off/no-fuel behavior if init present | may require disable companion | no change if ignored |

## Procedure

1. Capture a stock key-on → crank → run trace of `$3FC0-$3FFF` writes, especially `$3FCC`, `$3FCE`, `$3FEA`, `$3FF6`, and `$3FFC`.
2. Mark when the first injector pulse occurs relative to `$3FCC/$3FEA` and `$3FCE` writes.
3. Hold a stable RPM/ref signal and force `$3FCE` values from `maps/test_vectors/efi_pw_3fce_forced_values.csv`.
4. Repeat with `$3FCC/$3FEA` left stock.
5. Repeat with suspected `$3FCC/$3FEA` writes blocked, neutralized, or replaced if the test setup allows it.
6. Repeat with `$3FCC/$3FEA` manually preloaded to the observed stock/ref-init values, then force `$3FCE`.
7. Record injector pulsewidth and classify the path.

## Known Static Init-State Clues

```text
0x715B STD 0,X     block clears even ASIC words from $3FC0 through before $3FFA
0x74D6 STD L3FCC  D=0xD000, ref-interrupt command/preload candidate
0x74DF STD L3FEA  D=0xDFFF, ref-interrupt command/preload candidate
0x8426 STD L3FCE  runtime fuel/no-fuel/transient gate
0x8512 STD L3FCE  normal TBI final PW
0xFADC STX L3FCC  diagnostic output-cycling preload
0xFAE5 STX L3FEA  diagnostic output-cycling preload
0xFAEE STD L3FCE  diagnostic 3 ms EFI PW command
0xFB44 STD L3FCE  diagnostic/off zero command
```

## Pass Classifications

```text
Path A-clean:
  After normal global boot/init, fixed companion state + forced $3FCE changes injector PW correctly.
  Blocking $3FCC/$3FEA specific preloads does not break runtime fuel output.

Path A-with-init:
  $3FCE is the only runtime fuel PW command, but a one-time ASIC-window clear or $3FCC/$3FEA init/preload is required before it works.

Path C-runtime:
  $3FCE changes only work when a companion mode/enable/strobe is also written during runtime.

Path C-diagnostic-only:
  $3FCC/$3FEA are required for diagnostic output cycling only; normal runtime fuel uses $3FCE after ordinary global init.

Path B:
  Injector PW follows $301C/$301E or another scheduler path and ignores forced $3FCE.
```

## Data To Record

```csv
test_name,boot_init_seen,three_fcc_value,three_fea_value,forced_3fce_hex,expected_ms,measured_inj_a_ms,measured_inj_b_ms,toc4_seen,toc5_seen,companion_frozen,companion_blocked,path_result,notes
```

## Stop Conditions

- Stop and preserve the trace if `$3FCE = 0` does not suppress fuel but another companion write does.
- Stop and preserve the trace if blocking `$3FCC/$3FEA` changes injector behavior.
- Stop and preserve the trace if `$3FCE` controls pulsewidth only in diagnostic mode but not normal runtime.

## Next Step After Classification

If Path A-clean or A-with-init is confirmed, create:

```text
docs/contracts/MINIMAL_EFI_PW_WRITER.md
source/minimal_os/fuel/efi_pw_writer.asm
tests/static/efi_pw_writer_vectors.csv
```

If Path C-runtime is confirmed, define the required pre-write/post-write companion sequence before writing the minimal writer.
