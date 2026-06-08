# Spark Minimal Module Boundary

## Purpose

Define the minimal spark-control module boundary for the clean 7427 hardware-contract OS.

This contract does not create a spark writer. It defines the required submodules, their inputs, outputs, state, and bench gates.

## Source Contracts

- `SPARK_CONVERSION_EQUATION.md`
- `SPARK_LA906_OUTPUT_SEQUENCE.md`
- `SPARK_ROLLING_STATE_MODEL.md`
- `SPARK_INIT_STATE.md`
- `SPARK_BYPASS_EST_TRANSITION.md`
- `SPARK_EST_FAULT_MONITOR_CONTRACT.md`

## Required Runtime Inputs

| Input | Meaning | Source |
|---|---|---|
| REF/DRP period | timing basis | ASIC `$3FC0`, software `L005F` |
| RPM/run state | crank/run qualification | `SPARK_RUN_QUALIFY` |
| desired spark degrees | final desired advance | future spark table/math |
| latency correction | EST/module delay correction | `L0201` path |
| bypass/EST state | authority gate | `SPARK_BYPASS_EST_AUTHORITY` |
| rolling state | continuity state | `$3FF6/$3FDC/L01EC` |
| monitor state | diagnostic/fault state | `L004F bit6/L0205/L022C` if retained |

## Required Hardware Outputs

| Output | Role | Required? |
|---|---|---|
| `$3FE8` | paired timing command 1 | likely yes |
| `$3FE6` | paired timing command 2 | likely yes |
| `$3FF6` | rolling anchor update | likely yes |
| `$3FDC` | rolling paired-edge/prior-state update | likely yes |
| `$3FE4` | mirror/ack target from `$3FEC` | bench-gated |
| bypass/EST authority output | physical authority transfer | not fully mapped |

## Module Boundary Table

| Submodule | Required static | Can disable? | Bench gate | Risk if wrong |
|---|---|---|---|---|
| `SPARK_RUN_QUALIFY` | yes | no | verify exact event count and first-run ordering | EST authority too early or never enabled; wild first spark or no run spark |
| `SPARK_BYPASS_EST_AUTHORITY` | yes | no | physical bypass/EST wire and coil authority timing | module/base timing and PCM/ASIC timing fight or first EST event occurs with invalid rolling state |
| `SPARK_CONVERT_DEGREES_TO_TIME` | yes | no | L0201/L3FC0 final postprocess units and sign/high-nibble packing | spark angle produces wrong time offset; timing moves wrong direction or wrong magnitude |
| `SPARK_ROLLING_STATE` | yes | no | $3FF6/$3FDC first-event seed behavior and recompute-vs-persist behavior | event-to-event timing discontinuity, jitter, wrong dwell/edge relationship, wild first run spark |
| `SPARK_ASIC_HANDOFF` | yes | no | which register is primary vs paired edge, and measured EST output effect | no EST timing control or wrong paired edge/dwell behavior |
| `SPARK_ASIC_MIRROR_ACK` | bench_gated | unknown_pending_bench | skip/freeze $3FEC->$3FE4 and observe authority monitor LA906 continuity | lost ACK/status sync, EST monitor false trip, broken LA906 event continuity |
| `SPARK_EST_MONITOR` | optional_or_disabled_pending_bench | yes_if_MON_A_bench_proven | MON-A vs MON-B/MON-C/MON-D classification | false Error 42, possible authority/fallback side effects if monitor is not diagnostic-only |
| `SPARK_DROPOUT_SAFE_STATE` | yes_conceptually | no | exact stock behavior during missing REF/dropout | free-running spark output after REF loss or invalid period |

## Required Static Modules

```text
SPARK_RUN_QUALIFY
SPARK_BYPASS_EST_AUTHORITY
SPARK_CONVERT_DEGREES_TO_TIME
SPARK_ROLLING_STATE
SPARK_ASIC_HANDOFF
SPARK_DROPOUT_SAFE_STATE
```

These cannot be removed from a minimal OS. They may be simplified, but the hardware contract they cover still has to exist.

## Bench-Gated Pieces

```text
$3FEC->$3FE4 mirror / ACK / status-sync requirement
$3FF6/$3FDC first-event seed behavior
physical bypass/EST authority trigger
L0201/L3FC0 final postprocess units and sign/packing
exact paired role of $3FE8/$3FE6
dropout/missing-REF safe behavior
```

These stay in the boundary as explicit gates. Do not hide them inside a writer stub.

## Optional / Disabled Pending Bench

```text
SPARK_EST_MONITOR
Error 42 accumulation through L022C
locked ERR42A behavior through L0044 bit7 candidate
diagnostic-only monitor behavior
```

The EST monitor can be omitted or kept disabled only if MON-A is bench-proven. If MON-B, MON-C, or MON-D is proven, the relevant monitor behavior becomes required.

## Design Rule

```text
spark_math produces desired spark degrees
        ↓
SPARK_RUN_QUALIFY says whether EST control is allowed
        ↓
SPARK_BYPASS_EST_AUTHORITY permits physical/ASIC authority only when safe
        ↓
SPARK_CONVERT_DEGREES_TO_TIME produces D_AB97
        ↓
SPARK_ROLLING_STATE applies continuity model
        ↓
SPARK_ASIC_HANDOFF writes $3FE8/$3FE6 and mirror/ack if required
        ↓
SPARK_EST_MONITOR remains optional/diagnostic unless bench proves authority side effects
```

## Current Boundary Position

```text
required:
  run qualify
  bypass/EST authority
  conversion equation
  rolling state
  $3FE8/$3FE6 paired write
  dropout safe state

bench-gated:
  $3FEC->$3FE4 mirror
  EST monitor/fault behavior
  exact first-event seed
  exact physical authority trigger
  final postprocess units

optional if MON-A:
  Error 42 accumulation path
  diagnostic-only EST monitor behavior
```

## Stop Condition

No ASM spark handoff stub until this boundary can be exercised against bench traces and each bench-gated item is classified.

The next safe artifact is documentation under:

```text
source/minimal_os/spark/README.md
```

That README may define module layout and API contracts. It must not implement `SPARK_WRITE` yet.
