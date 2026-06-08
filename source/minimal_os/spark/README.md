# Minimal Spark Module

## Status

Documentation/API layout only.

No spark ASM implementation exists yet. Do not add `SPARK_WRITE`, `spark_handoff.asm`, `spark_convert.asm`, or LA906 replacement code until bench classification proves the required ASIC sequence.

## Source Contracts

- `docs/contracts/SPARK_MINIMAL_MODULE_BOUNDARY.md`
- `docs/contracts/SPARK_CONVERSION_EQUATION.md`
- `docs/contracts/SPARK_LA906_OUTPUT_SEQUENCE.md`
- `docs/contracts/SPARK_ROLLING_STATE_MODEL.md`
- `docs/contracts/SPARK_INIT_STATE.md`
- `docs/contracts/SPARK_BYPASS_EST_TRANSITION.md`
- `docs/contracts/SPARK_EST_FAULT_MONITOR_CONTRACT.md`

## Module Stack

```text
spark_math
→ SPARK_RUN_QUALIFY
→ SPARK_BYPASS_EST_AUTHORITY
→ SPARK_CONVERT_DEGREES_TO_TIME
→ SPARK_ROLLING_STATE
→ SPARK_ASIC_HANDOFF
→ optional SPARK_EST_MONITOR
```

## Submodule API Boundaries

### SPARK_RUN_QUALIFY

Owns crank/run qualification.

Inputs:

```text
REF/DRP event state
RPM / period basis
first DRP valid latch
recent DRP latch
qualifying event counter
450 RPM threshold candidate
```

Outputs:

```text
engine_running
run_qualified
period_valid
spark_allowed_candidate
```

Required because `LA906` rolling state must not be trusted before valid period/ref state exists.

---

### SPARK_BYPASS_EST_AUTHORITY

Owns safe transfer from module/base timing to PCM/ASIC EST timing.

Inputs:

```text
run_qualified
period_valid
rolling_state_valid
bypass/EST state
```

Outputs:

```text
est_authority_allowed
bypass_safe_state
first_est_event_allowed
```

Bench-gated:

```text
physical bypass/EST authority trigger
whether LA906 can prepare timing before physical EST authority
whether bypass protects bad $3FF6/$3FDC first-event state
```

---

### SPARK_CONVERT_DEGREES_TO_TIME

Owns degree-domain to timing-domain conversion.

Inputs:

```text
desired_spark_degrees
L005F/L0060 period basis
L0201 latency correction
L3FC0 anchor candidate
L004F bit0 sign convention
```

Static equation:

```text
A_count = round(abs(spark_offset_deg) * 256 / 90)
spark_time_delta = round((A_count * L005F) / 256)
D_AB97 = stock_postprocess(spark_time_delta, L0201, L3FC0, sign)
```

Outputs:

```text
D_AB97 candidate
sign flag state
```

Bench-gated:

```text
L005F physical unit
L0201 latency unit
L3FC0 anchor meaning
final shift/pack/sign behavior
```

---

### SPARK_ROLLING_STATE

Owns continuity state used by LA906-style output.

State:

```text
$3FF6 rolling anchor / EST fall counter candidate
$3FDC rolling paired-edge/prior-state candidate
L01EC timing/dwell/latency work term
```

Inputs:

```text
D_AB97
L01EC
current period/ref state
prior rolling state
```

Outputs:

```text
next $3FF6 value
next $3FDC value
rolling_state_valid
```

Bench-gated:

```text
whether $3FF6/$3FDC zero seed is safe
whether state is recomputable every event
whether first-event seed needs a separate path
```

---

### SPARK_ASIC_HANDOFF

Owns ASIC timing writes.

Inputs:

```text
D_AB97
rolling $3FF6
rolling $3FDC
L01EC
$3FEC if mirror/ack required
```

Outputs:

```text
$3FE8 timing command candidate
$3FE6 timing command candidate
$3FF6 rolling update
$3FDC rolling update
$3FE4 mirror/ack target if required
```

Required/static-likely:

```text
$3FE8
$3FE6
$3FF6
$3FDC
```

Bench-gated:

```text
$3FEC->$3FE4 mirror
exact paired role of $3FE8/$3FE6
```

---

### SPARK_EST_MONITOR

Optional unless bench proves side effects.

Owns EST/Error 42 diagnostic monitor.

State:

```text
L004F bit6 EST monitor enable
L0205 prior captured/ref sample
L022C EST error counter
L0044 bit7 ERR42A candidate
```

Inputs:

```text
L3FCA current captured/ref sample
first DRP valid
recent DRP valid
engine_running
```

Outputs:

```text
monitor_fault_count
error_42_candidate
monitor_good_path
```

Current static classification:

```text
diagnostic-only remains plausible
not proven to gate spark authority
not proven to disable LA906
not proven to alter fuel/spark fallback
```

## Forbidden Until Bench-Proven

Do not add:

```text
SPARK_WRITE
spark_handoff.asm
spark_convert.asm
LA906 replacement ASM
direct $3FE8/$3FE6 writer
physical EST authority control code
```

until bench traces classify:

```text
$3FE8/$3FE6 paired role
$3FF6/$3FDC first-event seed
$3FEC->$3FE4 requirement
bypass/EST physical authority trigger
L0201/L3FC0 final postprocess units
```

## Future Source Layout

Planned only:

```text
source/minimal_os/spark/
  README.md
  run_qualify.asm              pending
  bypass_est_authority.asm     pending
  convert_degrees_to_time.asm  pending
  rolling_state.asm            pending
  asic_handoff.asm             pending
  est_monitor.asm              optional/pending
```

No files beyond `README.md` should be created until the corresponding contract is bench-classified or explicitly marked as static stub only.

## Next Repository Artifact

The next safe artifact after this README is likely:

```text
docs/contracts/MINIMAL_OS_MODULE_BOUNDARY.md
```

That document should combine fuel and spark with the next unknown hardware subsystem boundary, likely IAC/idle air output.
