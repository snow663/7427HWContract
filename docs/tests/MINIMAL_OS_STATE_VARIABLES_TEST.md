# Minimal OS State Variables Test

## Goal

Verify that the state-variable map consolidates source-proven symbols, minimal-OS logical state, hardware shadows, scheduler/boot/watchdog state, ALDL/debug state, bench-gated state, exclusions, and unknowns without creating a RAM allocator, linker map, or runtime ASM.

This test validates planning only.

## Required Files

```text
docs/contracts/MINIMAL_OS_STATE_VARIABLES.md
maps/contracts/minimal_os_state_variables.csv
tools/build_minimal_os_state_variables.py
```

## Required Static Checks

| Test | Expected |
|---|---|
| planning-only | no runtime ASM, RAM allocator, or linker map created |
| one owner per carried variable | every `yes`, `likely`, or `bench_gated` row has `module_owner` and `submodule_owner` |
| fuel output state | `L3FCE/L3FCF` represented as EFI PW command |
| fuel source state | `L024E`, `L0250`, no-fuel gate, DFCO gate, deadtime, and low-PW correction represented |
| spark intent state | `L01FD`, `L01EE`, `L004F bit0`, `L0201`, `L005F/L0060` represented |
| spark output candidates | `$3FE8/$3FE6/$3FF6/$3FDC` represented as bench-gated / not writer-safe |
| spark monitor state | `L004F bit6`, `L004F bit7`, `L0044 bit3`, `L0210`, `L022C`, `L0205` represented |
| IAC position state | `L0007`, `L0008`, `L0009`, `L000A` represented |
| IAC shadow/latch | `L004C` and `L3062` represented as hardware shadow/candidate and bench-gated |
| IAC calibration reference | `L4EB0` represented as calibration reference, not RAM allocation |
| battery/protection state | `L00A7` and `L003E bit2` represented |
| scheduler/boot/dropout | RPM valid, REF/DRP valid, first-period-valid, crank/run qualification, dropout, output-safe represented |
| watchdog | watchdog-alive/protection represented |
| ALDL/debug | bench hook and debug snapshot represented as visibility state only |
| hardware shadows | identified separately from logical state |
| exclusions | trans/EGR/EVAP/emissions/GM baggage not carried forward |
| unknowns | listed, not guessed |
| stock variable rule | no state is carried forward solely because it exists in stock code |

## Command

```bash
python tools/build_minimal_os_state_variables.py \
  --out-md docs/contracts/MINIMAL_OS_STATE_VARIABLES.md \
  --out-csv maps/contracts/minimal_os_state_variables.csv
```

## Carry-Forward Validation

Allowed values:

```text
yes
likely
bench_gated
no
unknown
```

Each row with:

```text
carry_forward_to_minimal_os = yes | likely | bench_gated
```

must have:

```text
module_owner != unknown
submodule_owner != unknown
source_contract_dependency populated
```

## Hardware Shadow Validation

Allowed values:

```text
yes
no
candidate
```

Rows with `hardware_shadow = yes` or `candidate` must include:

```text
hardware_address
source_contract_dependency
bench_dependency if output behavior is not proven
```

## Exclusion Discipline

These must remain `carry_forward_to_minimal_os = no`:

```text
transmission shift/TCC state
EGR state
EVAP/purge state
emissions diagnostic-only state
unused GM mode baggage
```

## Pass Criteria

```text
PASS:
  state map is planning-only.
  all carried-forward state has an owner.
  fuel, spark, IAC, scheduler, boot, watchdog, and ALDL/debug states are represented.
  hardware shadows are separated from logical state.
  spark and IAC output candidates remain bench-gated.
  trans/EGR/EVAP/emissions/GM baggage are excluded.
  unknown state remains visible.
  no full stock RAM map is created.
```

## Fail / Rework Criteria

```text
REWORK:
  runtime ASM appears.
  RAM allocation or linker-map layout appears.
  a variable is carried forward only because it exists in stock code.
  spark `$3FE8/$3FE6/$3FF6/$3FDC` candidates are treated as writer-safe.
  IAC `L3062` is treated as writer-safe.
  excluded strategy baggage is carried forward.
  unknown state is silently assigned to a module.
```

## Next Planning Artifact

After this pass, continue with:

```text
MINIMAL_OS_ALDL_DEBUG_MAP
```

That pass should decide which state variables get exposed for bench proof and live debugging before implementation.
