# Bench Proof Package

## Purpose

Define the bench proof matrix required before implementation work proceeds.

This document converts source/hardware contracts into physical and ALDL-observable proof tasks.

This is still planning/test definition only:

```text
no runtime ASM
no bench hook implementation
no ALDL packet code
no fuel-only runnable code yet
```

## Scope

Included:

- fuel `$3FCE` pulsewidth proof
- spark handoff/rolling/bypass proof
- IAC A/B/Enable/park proof
- boot/dropout/watchdog proof
- ALDL/debug visibility proof

Excluded:

- tuning changes
- runtime ASM implementation
- ALDL packet implementation
- spark writer
- IAC writer

## Implementation Gates

Fuel-only runnable slice:

- allowed after fuel PW output and boot-safe fuel gates are bench-proven
- specifically, `FUEL-001` through `FUEL-004` must pass before the first fuel-only runtime slice proceeds

Spark implementation:

- blocked until spark handoff, rolling state, EST/bypass authority, and safe-state behavior are bench-classified
- specifically, `SPARK-001` through `SPARK-006` must be resolved or explicitly replaced by a safer documented hardware strategy

IAC implementation:

- blocked until physical A/B mapping, direction, Enable behavior, park behavior, and cadence are bench-classified
- specifically, `IAC-001` through `IAC-009` must be resolved before any IAC writer is created

## Proof Group Summary

| Proof group | Count |
|---|---:|
| `aldl_debug_visibility` | 2 |
| `boot_safe_state` | 2 |
| `dropout_safe_state` | 3 |
| `fuel_pw_output` | 4 |
| `iac_enable` | 2 |
| `iac_park` | 2 |
| `iac_phase` | 5 |
| `spark_bypass_est` | 1 |
| `spark_handoff` | 3 |
| `spark_rolling_state` | 2 |

## Proof Matrix

| Proof ID | Group | State/signal | Forced condition | Expected observation | Pass condition | Gate |
|---|---|---|---|---|---|---|
| `FUEL-001` | `fuel_pw_output` | EFI PW command counts | command fixed known PW count vector | $3FCE raw counts match requested command and observed injector pulse width | ALDL/debug raw counts and scope pulse width agree within defined tolerance | fuel-only runnable slice blocked until FUEL-001 through FUEL-004 pass |
| `FUEL-002` | `fuel_pw_output` | 3.0 ms PW vector | force D=$00C5 with fuel enabled and safe bench load | scope sees about 3.006 ms pulse | $00C5 produces approximately 3.006 ms because 197/65.536=3.006 ms | fuel-only runnable slice blocked until FUEL-001 through FUEL-004 pass |
| `FUEL-003` | `fuel_pw_output` | fuel no-pulse / zero gate | force no-fuel or DFCO gate active | $3FCE = 0 and no injector pulse | no-fuel/DFCO gate forces zero output | fuel-only runnable slice blocked until FUEL-001 through FUEL-004 pass |
| `FUEL-004` | `dropout_safe_state` | dropout fuel safe state | simulate missing REF/DRP or unsafe runtime state | dropout asserted, $3FCE = 0, no injector pulse | dropout/unsafe state forces fuel no-pulse | fuel-only runnable slice blocked until FUEL-001 through FUEL-004 pass |
| `FUEL-005` | `aldl_debug_visibility` | low-PW transfer observability | run low-PW transfer test vector sequence | input PW, corrected PW, and final $3FCE are observable | ALDL/debug exposes enough state to validate low-PW transfer curve | low-PW correction implementation blocked until observable |
| `SPARK-001` | `spark_handoff` | spark ASIC handoff candidates | observe stock/source-side candidate values over events | $3FE8/$3FE6 candidates are visible without any minimal writer | candidate values can be logged and correlated to timing events | no spark writer until SPARK-001 through SPARK-006 are resolved or replaced by safer strategy |
| `SPARK-002` | `spark_handoff` | spark intent and conversion path | run known RPM/MAP spark table points or simulated event stream | desired spark, L01FD, L01EE, and sign flag correlate coherently | spark accumulator/offset/sign path can be reconstructed | spark conversion implementation blocked until correlation proven |
| `SPARK-003` | `spark_handoff` | DRP/ref period basis | feed known REF/DRP periods | L005F/L0060 follows REF/DRP period and derived RPM | period basis matches known input within tolerance | spark and fuel RPM/timebase use blocked until period proof |
| `SPARK-004` | `spark_rolling_state` | rolling timing state | capture across reset, first REF/DRP, crank, and run event sequences | rolling state evolves deterministically across events | rolling state seed/anchor behavior classifiable | no spark rolling-state writer until SPARK-004 pass |
| `SPARK-005` | `spark_rolling_state` | status/mirror/ack path | observe across spark events and EST monitor states | $3FEC->$3FE4 behavior is visible and classifiable | mirror/ack path role is classified or marked unused | no spark writer until mirror/ack requirement resolved |
| `SPARK-006` | `spark_bypass_est` | EST/bypass authority transition | capture key-on, crank, first REF/DRP, and run qualification | physical authority transition can be classified | safe authority strategy is known or output remains blocked | no physical EST/bypass authority code until SPARK-006 pass |
| `IAC-001` | `iac_phase` | physical A/B mapping | single-step or observe stock ring transitions | L3062 bit2/bit3 physical A/B mapping classified | each bit maps to a physical driver input or transform is documented | no IAC writer until IAC-001 through IAC-009 resolved |
| `IAC-002` | `iac_phase` | desired greater than actual path | force desired > actual | A/B ring follows direction bit0=0 sequence | software ring and physical pin order are classifiable | no IAC writer until direction/ring proven |
| `IAC-003` | `iac_phase` | desired less than actual path | force desired < actual | A/B ring follows reverse direction bit0=1 sequence | reverse software ring and physical pin order are classifiable | no IAC writer until direction/ring proven |
| `IAC-004` | `iac_phase` | desired equals actual hold behavior | force desired == actual | A/B state holds; no step pulse occurs | no physical step when desired equals actual | IAC hold behavior required before writer |
| `IAC-005` | `iac_enable` | Enable physical behavior | observe enable bit during normal voltage and fault/low-voltage cases | bit4 physical function classified | Enable pin or driver behavior is identified | no IAC writer until Enable physical behavior resolved |
| `IAC-006` | `iac_enable` | Enable not step-pulsed | observe Enable during multi-step movement | Enable remains gated/static rather than pulsed per step | Enable behavior is not A/B step-pulsed | no IAC writer until Enable timing proven |
| `IAC-007` | `iac_park` | L0008=0 physical movement | force/select L0008=0 path under bench-safe conditions | physical movement direction classified | L0008=0 maps to open or closed direction or no-motion policy documented | no IAC writer until park direction resolved |
| `IAC-008` | `iac_park` | L4EB0=145 park-down behavior | force/observe stock park-down path using L4EB0 | 145-step park-down physical behavior classified | park-down reaches expected stop or direction behavior documented | no IAC writer until park behavior resolved |
| `IAC-009` | `iac_phase` | safe step cadence / rate limit | run controlled repeated step sequence | safe step cadence measured and upper limit defined | minimum safe delay/rate limit established | no IAC writer until cadence resolved |
| `BOOT-001` | `boot_safe_state` | reset safe defaults | reset / power cycle | output-safe defaults entered; runtime outputs inactive | no unsafe output activity during reset | runtime implementation blocked until boot defaults proven |
| `BOOT-002` | `boot_safe_state` | fuel zero before enable | reset then wait before valid crank/fuel enable | $3FCE stays zero and no injector pulse | fuel remains zero until valid crank/fuel-enable state | fuel-only runnable slice blocked until BOOT-002 and FUEL-001..004 pass |
| `BOOT-003` | `dropout_safe_state` | missing REF/DRP dropout | remove/stop REF/DRP stream | dropout state asserts and outputs move to safe policies | dropout-safe state occurs on missing REF/DRP | all runtime slices require dropout proof |
| `BOOT-004` | `dropout_safe_state` | watchdog safe fallback | simulate foreground loop stall/watchdog failure | watchdog-safe fallback requests output-safe defaults | outputs return to safe defaults when watchdog proof fails | runtime scheduler blocked until watchdog fallback defined/proven |
| `BOOT-005` | `aldl_debug_visibility` | boot/dropout/watchdog debug visibility | reset, dropout, watchdog-safe scenarios | boot/dropout/watchdog states are visible in debug stream | state transitions can be reconstructed from ALDL/debug | bench proof package requires visibility before implementation |
| `ALDL-001` | `aldl_debug_visibility` | debug map completeness | static review plus bench capture plan | all Priority 1 values have a debug path | every required bench proof row names required ALDL/debug values | must pass before bench data capture plan freezes |

## Write-Authority Rule

No proof row grants write authority by itself.

```text
Observing $3FE8/$3FE6/$3FF6/$3FDC does not permit spark writes.
Observing L3062/L004C does not permit IAC writes.
Observing $3FCE does not permit nonzero fuel unless fuel gates permit it.
Bench hooks, if later implemented, must be explicitly gated and documented.
```

## Unknown Mapping Rule

Unknown physical mappings remain unresolved until bench data exists. The proof package may define how to observe them; it must not pre-classify them as solved.

## Next Step

After this package, choose:

```text
first minimal fuel-only runnable slice
```

That slice must remain limited to reset-safe state, available sensor/RPM/MAP inputs, open-loop fuel PW computation stub or fixed test PW, DFCO/no-fuel zero gate, `EFI_PW_WRITE` to `$3FCE` only, and ALDL/debug visibility. Spark and IAC writers remain forbidden.
