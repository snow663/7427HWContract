# EFI PW $3FCE Forced-Value Bench Test

## Goal

Determine whether `$3FCE/$3FCF` alone controls injector pulsewidth, verify the suspected `1/65536 second` unit scale, and determine whether TOC4/TOC5 support is required.

## Paths Under Test

```text
Path A:
  BPW_final → $3FCE → ASIC injector output

Path B:
  BPW_final → HC11 TOC4/TOC5 compare scheduler → injector output

Path C:
  BPW_final → $3FCE plus TOC4/TOC5 support/arming → injector output
```

## Required Signals

- Injector A output at driver side
- Injector B output at driver side
- `$3FCE/$3FCF` write trace if available
- `$301C/$301E` writes if possible
- `$3020/$3022/$3023` writes if possible
- RPM/ref simulator state
- BPW variable/log value if available
- DFCO/no-fuel flag if available
- Battery voltage at PCM/injector supply

## Test Vector Source

Use:

```text
maps/test_vectors/efi_pw_3fce_forced_values.csv
```

Unit hypothesis:

```text
expected_ms = counts / 65.536
```

Highest-value first points:

```text
0x0000  off/no-fuel behavior
0x0042  about 1 ms
0x0083  about 2 ms
0x00C5  about 3 ms, matches stock diagnostic comment
0x0106  about 4 ms
```

## Core Procedure

1. Run PCM on bench with stable reference signal.
2. Keep fuel math/state constant.
3. Patch, intercept, or manually force the final `$3FCE` write.
4. Force known values from the test vector table.
5. Scope injector A and injector B outputs.
6. Compare measured pulsewidth to `expected_ms`.
7. Record whether pulsewidth tracks `$3FCE`.
8. Record whether TOC4/TOC5 writes change, remain constant, or remain necessary.

## Test Matrix

| Test | Condition | Forced `$3FCE` | Expected if `$3FCE` controls EFI PW | Expected if TOC4/TOC5 required |
|---|---|---:|---|---|
| key-on | no ref | unchanged / zero | no injector pulse | no injector pulse |
| crank fixed BPW | fixed RPM/ref | stock | injector PW matches stock `$3FCE` | injector PW follows timer compare |
| idle fixed BPW | stable ref | stock | PW stable with `$3FCE` | PW follows TOC writes |
| force zero | run/idle | `$0000` | injector off or explicit minimum/off behavior | no change if ignored |
| force one_ms | run/idle | `$0042` | injector PW near 1.007 ms | no change if ignored |
| force two_ms | run/idle | `$0083` | injector PW near 1.999 ms | no change if ignored |
| force three_ms_diag | run/idle | `$00C5` | injector PW near 3.006 ms | no change if ignored |
| force four_ms | run/idle | `$0106` | injector PW near 3.998 ms | no change if ignored |
| DFCO/no-fuel | no-fuel | observe/force zero | `$3FCE` zero or output disabled | TOC scheduler disabled |

## Measurement Rules

- Capture actual injector pulsewidth at the injector driver output, not only CPU register writes.
- Record both commanded `$3FCE` value and measured injector pulsewidth.
- Keep reference frequency stable during each forced-value sweep.
- Keep injector supply voltage stable or record it with each measurement.
- If possible, log whether `$301C/$301E` continue to move while `$3FCE` is forced.

## Pass Criteria

`$3FCE` is confirmed as the EFI PW handoff if controlled changes to `$3FCE` produce proportional injector pulsewidth changes while other scheduler variables remain fixed or stock.

Expected relationship:

```text
measured_ms ≈ $3FCE_counts / 65.536
```

Acceptable error should be judged against scope resolution, injector driver delay, and any minimum pulse clipping. Start by accepting approximate linear tracking; refine tolerance after the first clean capture.

## Fail Criteria

`$3FCE` is not sufficient if injector pulsewidth does not change with forced `$3FCE`, or if injector pulsewidth follows `$301C/$301E` compare values independently of `$3FCE`.

## Path Classification

```text
Path A confirmed if:
  forced $3FCE directly changes injector PW and TOC4/TOC5 changes are not required.

Path B confirmed if:
  injector PW follows TOC4/TOC5 compare scheduling and ignores forced $3FCE.

Path C confirmed if:
  forced $3FCE changes injector PW, but TOC4/TOC5 or companion registers are still required to arm/qualify output events.
```

## Data To Record

```csv
test_name,forced_counts_hex,forced_counts_dec,expected_ms,measured_inj_a_ms,measured_inj_b_ms,rpm_ref_hz,battery_v,toc4_seen,toc5_seen,notes,path_result
```

## Notes

Do not start new fuel math until this test proves the hardware command unit and whether `$3FCE` is standalone or requires companion arming/strobe behavior.
