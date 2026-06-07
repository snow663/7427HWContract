# EFI PW $3FCE Bench Test

## Goal

Determine whether `$3FCE` alone controls injector pulsewidth, and document the required write timing, width, byte order, and units.

The test decides between:

```text
Path A:
  BPW_final -> $3FCE -> ASIC injector output

Path B:
  BPW_final -> HC11 TOC4/TOC5 compare scheduler -> injector output

Path C:
  BPW_final -> $3FCE plus TOC4/TOC5 support/arming -> injector output
```

## Required Signals

- Injector A output at driver/load
- Injector B output at driver/load
- `$3FCE/$3FCF` write trace: PC, D/A/B value, timestamp/cycle
- `$3FCC` and `$3FEA` writes if possible, because they appear near output-cycling enable/setup paths
- `$301C/$301E` writes if possible, to compare against timer scheduler behavior
- `$3020/$3022/$3023` writes if possible, to see whether TOC action/mask/flag state changes are required
- RPM/ref simulator state
- BPW variable/log value: `$024E`, `$024C`, `$0250`, `$0254`, `$02CF` if available
- DFCO/no-fuel flag if available

## Static Setup Values To Use

Static source gives these initial test anchors:

```text
$3FCE = $00C5  -> diagnostic output-cycling comment says 3 msec pulses
$3FCE = $0000  -> output-cycling disable/off path
$3FCE normal   -> direct 16-bit STD after low-BPW correction, bias, and clamp
```

Unit inference before bench lock:

```text
$00C5 decimal 197 / 3 ms = 65.7 counts/ms
nearby fuel comments use approx 65.536 counts/ms
therefore 1 count is probably about 15.26 us
```

## Test Matrix

| Test | Condition | Command / perturbation | Expected if `$3FCE` controls EFI PW | Expected if TOC4/TOC5 required | Capture notes |
|---|---|---|---|---|---|
| key-on | no ref pulses | stock | no injector pulse | no injector pulse | verify no unintended prime unless commanded elsewhere |
| crank fixed BPW | fixed RPM/ref | stock | injector PW matches latest `$3FCE` value | injector PW follows `$301C/$301E` scheduling | compare `$3FCE` unit to measured pulse |
| idle fixed BPW | stable ref | stock | PW stable and correlated to `$3FCE` refresh | PW follows TOC writes | note update rate/event timing |
| force `$3FCE` low | same fuel math/ref | reduce `$3FCE` only | injector PW shortens proportionally | little/no change if ignored | keep TOC path unchanged if possible |
| force `$3FCE` high | same fuel math/ref | increase `$3FCE` only | injector PW lengthens proportionally | little/no change if ignored | watch max/clip/saturation |
| force `$3FCE` zero | run/idle | write `$0000` | injector off or documented min/off behavior | no change if ignored | primary no-fuel proof |
| diagnostic 3ms | output-cycling mode | allow `$00C5` write | measured injector pulse near 3 ms | diagnostic may still need TOC/support | compare both injectors |
| DFCO/no-fuel | closed-throttle decel/ref present | stock no-fuel | `$3FCE` zero or separate output disable | TOC scheduler disabled/flags stopped | determine actual no-fuel contract |
| one-channel observe | stable run/ref | observe A/B separately | both channels reflect same PW handoff, phase handled elsewhere | A/B tied to TOC4/TOC5 individually | determines whether `$3FCE` is width-only |

## Procedure

1. Establish a safe bench harness with injector loads or current-limited substitute loads.
2. Run stock code with controlled ref pulses.
3. Log `$3FCE`, `$3FCC`, `$3FEA`, `$301C`, `$301E`, `$3020`, `$3022`, and `$3023` writes.
4. Scope injector A and B at the actual driver/load output.
5. Confirm the diagnostic `$00C5` path first if output-cycling mode is available.
6. Force or patch `$3FCE` values while keeping the rest of fuel math and scheduler behavior as unchanged as possible.
7. Compare measured pulsewidth against `$3FCE` value using the static scale estimate of about `65.536 counts/ms`.
8. Repeat with `$3FCE = $0000` and document whether fuel stops immediately, at next ref event, or not at all.

## Pass Criteria

`$3FCE` is confirmed as EFI PW handoff if controlled changes to `$3FCE` produce proportional injector pulsewidth changes while other scheduler variables remain fixed or stock.

Strong pass:

```text
measured_pw_ms ≈ $3FCE / 65.536
$3FCE = $0000 suppresses injector pulse or produces documented off/min behavior
$00C5 produces about 3 ms in diagnostic output-cycling mode
```

## Fail Criteria

`$3FCE` is not sufficient if injector pulsewidth follows `$301C/$301E` compare values independent of `$3FCE`.

Partial / Path C result:

```text
$3FCE changes pulsewidth magnitude,
but TOC4/TOC5 or TCTL1/TMSK1/TFLG1 must also be armed for outputs to occur.
```

## Safety Notes

- Capture actual pulsewidth at the injector driver/load output, not only CPU register writes.
- Use current-limited loads or dummy injector loads during early bench tests.
- Avoid holding a real low-impedance TBI injector on continuously while forcing values.
- Treat `$3FCC/$3FEA` as possible output-engine enables until proven otherwise.

## Result Template

```text
date:
code/tune:
bench harness:
ref RPM:
commanded $3FCE:
measured injector A PW:
measured injector B PW:
$301C/$301E behavior:
$3020/$3022/$3023 behavior:
observed no-fuel behavior:
conclusion: Path A / Path B / Path C / inconclusive
notes:
```
