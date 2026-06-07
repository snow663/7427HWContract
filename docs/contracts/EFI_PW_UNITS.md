# EFI PW Units Contract

## Purpose

Document the static unit hypothesis for the `$3FCE/$3FCF` EFI pulsewidth handoff before writing any new minimal fuel-output routine.

## Hypothesis

`$3FCE/$3FCF` is a 16-bit EFI pulsewidth command in `1/65536 second` units.

```text
PW_counts = PW_seconds × 65536
PW_ms     = PW_counts / 65.536
PW_counts = round(PW_ms × 65.536)
```

Equivalently:

```text
1 count = 1 / 65536 second
1 count = 15.2587890625 microseconds
65.536 counts = 1 millisecond
```

## Confidence

```text
static confidence: high
bench confidence: pending
```

## Supporting Static Evidence

The diagnostic output-cycling routine writes `$00C5` to `L3FCE` and the source comment identifies that command as `3 msec pulses`.

```text
$00C5 hexadecimal = 197 decimal
197 / 65.536 = 3.0059814453125 ms
```

That is close enough to the comment's 3 msec pulse label to strongly suggest a 1/65536 second timebase.

## Reference Values

| Name | Counts | Decimal | Expected ms | Notes |
|---|---:|---:|---:|---|
| zero | `$0000` | 0 | 0.000 | expected off/no fuel or minimum-off behavior |
| half_ms | `$0021` | 33 | 0.504 | below likely useful injector range |
| one_ms | `$0042` | 66 | 1.007 | low-PW test |
| one_point_five_ms | `$0062` | 98 | 1.495 | idle-floor region |
| two_ms | `$0083` | 131 | 1.999 | low normal pulse |
| three_ms_diag | `$00C5` | 197 | 3.006 | matches stock diagnostic comment |
| four_ms | `$0106` | 262 | 3.998 | linear check |
| five_ms | `$0148` | 328 | 5.005 | linear check |
| six_ms | `$018A` | 394 | 6.012 | linear check |
| eight_ms | `$020C` | 524 | 7.996 | upper low-speed check |
| ten_ms | `$028F` | 655 | 9.995 | larger command check |

## Required Bench Proof

Static evidence is strong enough to drive the next test, but not enough to lock the hardware contract. Bench proof must show that forced `$3FCE` values produce measured injector pulsewidths matching:

```text
measured_ms ≈ $3FCE_counts / 65.536
```

The most important points are:

```text
$0000  off/no-fuel behavior
$0042  about 1 ms
$0083  about 2 ms
$00C5  about 3 ms / stock diagnostic clue
$0106  about 4 ms
```

## New-OS Implication If Confirmed

If the bench test confirms this unit scale and confirms `$3FCE` alone controls injector pulsewidth, the first minimal fuel-output writer becomes:

```asm
; D = desired pulsewidth counts, 1/65536 second units
; D = 0 means no fuel if bench confirms
EFI_PW_WRITE:
    STD L3FCE
    RTS
```

High-level new-OS fuel-output conversion:

```text
new_os_bpw_ms
→ counts = round(ms × 65.536)
→ clamp
→ if DFCO/no-fuel: counts = 0
→ STD $3FCE
```

## Open Questions

- Does `$0000` fully suppress injector output, or is a companion enable/disable bit also required?
- Does `$3FCE` latch automatically on write, or is it sampled by the ASIC on ref/DRP events?
- Are `$3FCC`, `$3FEA`, or other nearby registers required as mode/enable/strobe companions?
- Does crank use the same unit scale as run?
- Does async/AE fuel arrive at `$3FCE` already folded into the final command?
- Does the CPU need to maintain TOC4/TOC5 support when `$3FCE` is forced?
