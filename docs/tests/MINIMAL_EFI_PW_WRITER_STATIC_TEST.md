# Minimal EFI PW Writer Static Test

## Goal

Verify that the minimal EFI pulsewidth writer remains a clean runtime handoff stub and does not grow hidden fuel math, companion-register writes, timer scheduling, or output-mode baggage.

## Files Under Test

```text
source/minimal_os/fuel/efi_pw_writer.asm
tests/static/efi_pw_writer_vectors.csv
```

## Command

```bash
python tools/verify_minimal_writer.py \
  --source source/minimal_os/fuel/efi_pw_writer.asm \
  --vectors tests/static/efi_pw_writer_vectors.csv
```

## Required Checks

1. Routine contains exactly one hardware write.
2. Hardware write target is `$3FCE/$3FCF` through `STD L3FCE`.
3. Write width is 16-bit.
4. Routine does not touch `$3FCC`, `$3FEA`, `$301C`, `$301E`, `$3020`, `$3022`, or `$3023`.
5. Routine preserves the clean runtime assumption: caller owns math, clamps, state, and safety.
6. Static vector math matches the `1/65536 second` hypothesis:

```text
expected_ms = input_counts_dec / 65.536
```

7. Every vector expects address `0x3FCE` and width `16`.

## Pass Criteria

The static verifier passes with:

```text
hardware_write_count = 1
only_hardware_write = STD L3FCE
forbidden_write_count = 0
all_vectors_valid = true
```

## Fail Criteria

Fail if any of the following appear in `EFI_PW_WRITE`:

```text
STAA/STAB/STD/STX/STY $3FCC
STAA/STAB/STD/STX/STY $3FEA
STAA/STAB/STD/STX/STY $301C
STAA/STAB/STD/STX/STY $301E
BSET/BCLR against $3FCC/$3FEA/$301C/$301E/$3020/$3022/$3023
fuel math, clamps, AE, PE, DFCO, deadtime, or scheduler code
```

## Status

```text
static status: ready
bench status: pending
path assumption: Path A-with-init
```

This is a static structure test only. It does not prove injector output behavior. Bench proof remains in `docs/tests/EFI_PW_FORCED_VALUE_TEST.md` and `docs/tests/EFI_OUTPUT_INIT_STATE_TEST.md`.
