# EFI Output Init Routine Test

## Goal

Determine which one-time EFI output initialization state is required before `EFI_PW_WRITE` can command injector pulsewidth through `$3FCE/$3FCF`.

## Files Under Test

```text
source/minimal_os/init/efi_output_init.asm
tests/static/efi_output_init_vectors.csv
tools/verify_efi_output_init.py
```

## Static Verification Command

```bash
python tools/verify_efi_output_init.py \
  --source source/minimal_os/init/efi_output_init.asm \
  --vectors tests/static/efi_output_init_vectors.csv
```

## Static Verification Requirements

1. `EFI_OUTPUT_INIT` exists.
2. ASIC-window clear loop starts at `$3FC0`.
3. ASIC-window clear loop stops before `$3FFA`.
4. Clear writes are 16-bit `STD 0,X` with `D = $0000`.
5. `$3FCE` is cleared only as part of the window clear.
6. No active writes to `$3FCC/$3FEA` exist in the provisional path.
7. `$3FCC/$3FEA` optional preloads are comment-marked pending bench proof.
8. No writes to `$301C/$301E/$3020/$3022/$3023` appear.
9. Routine does not call `EFI_PW_WRITE`.

## Bench Variants

### Variant 1: global clear only

Run `EFI_OUTPUT_INIT` with only the `$3FC0-$3FF8` ASIC-window clear active, then force `$3FCE` values from `maps/test_vectors/efi_pw_3fce_forced_values.csv`.

Expected classification if injector PW tracks `$3FCE`:

```text
A-with-global-init
```

### Variant 2: global clear plus `$3FCC/$3FEA` preload

Run the ASIC-window clear, then write:

```text
$3FCC = $D000
$3FEA = $DFFF
```

Then force `$3FCE` values.

Expected classification if Variant 1 fails but Variant 2 works:

```text
A-with-3FCC-3FEA-init
```

### Variant 3: no custom init / stock boot state

Let stock code initialize hardware. Patch or intercept only runtime `$3FCE` writes.

Expected purpose:

```text
baseline forced-value comparison
```

## Path Classification

```text
A-clean:
  $3FCE works without special custom init beyond normal hardware reset.

A-with-global-init:
  $3FCE works after $3FC0-$3FF8 clear.

A-with-3FCC-3FEA-init:
  $3FCE works only after $3FCC/$3FEA preload.

C-runtime:
  $3FCC/$3FEA or another companion must be updated during each runtime command.

B:
  injector output does not follow $3FCE.
```

## Signals To Capture

- Injector A driver output
- Injector B driver output
- `$3FC0-$3FF8` init clear writes if possible
- `$3FCC/$3FEA` preload writes if enabled
- `$3FCE/$3FCF` forced runtime writes
- `$301C/$301E` timer writes if possible
- RPM/ref simulator state
- battery voltage at PCM/injector supply
- reset/key-on marker

## Test Matrix

| Variant | Init Clear | `$3FCC/$3FEA` Preload | Runtime Writer | Expected If Valid |
|---|---:|---:|---|---|
| stock baseline | stock | stock | forced `$3FCE` | baseline tracking result |
| global clear only | yes | no | forced `$3FCE` | Path A-with-global-init |
| global clear + preload | yes | yes | forced `$3FCE` | Path A-with-3FCC-3FEA-init |
| no init | no | no | forced `$3FCE` | Path A-clean if it still works |
| runtime preload/strobe | yes/stock | repeated | forced `$3FCE` | Path C-runtime if required |

## Data To Record

```csv
test_name,init_clear_enabled,preload_3fcc_3fea_enabled,forced_3fce_hex,expected_ms,measured_inj_a_ms,measured_inj_b_ms,toc4_seen,toc5_seen,path_result,notes
```

## Stop Conditions

- Stop and preserve the trace if `$3FCE = 0` fails to suppress fuel but `$3FCC/$3FEA` changes do suppress fuel.
- Stop and preserve the trace if `$3FCE` only works after `$3FCC/$3FEA` preload.
- Stop and preserve the trace if injector output follows `$301C/$301E` and ignores `$3FCE`.

## Next Step

If A-clean, A-with-global-init, or A-with-3FCC-3FEA-init is confirmed, keep the two-piece fuel-output skeleton:

```text
EFI_OUTPUT_INIT   = one-time init only
EFI_PW_WRITE      = runtime STD $3FCE only
```

If C-runtime is confirmed, create a separate runtime companion/strobe contract before modifying `EFI_PW_WRITE`.
