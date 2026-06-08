# Spark Degree-to-Tick Dependency

## Purpose

Trace the upstream dependency chain that converts commanded spark/retard state into the timing-domain value consumed by `LA906`.

This file defines the future spark API boundary. It does **not** define a spark writer.

## Sink

`LA906` timing bridge, first critical arithmetic:

```text
0xAB97  ADDD L3FF6
```

The value in `D` at this point is the sink input to be explained.

## Working Hypothesis

Software spark is calculated in degree-domain RAM variables, then corrected by startup/knock/latency logic and converted to timing-domain units using REF/DRP period before `LA906` writes ASIC timing registers.

## Watched Variables

| Variable | Candidate role | Domain | Confidence |
|---|---|---|---|
| `L01FC` | spark table/additive source, comment: `FROM TABLE L44BF` / spark adder | degree-domain | medium static |
| `L01FD` | final spark advance accumulator | degree-domain | high static label confidence |
| `L01EE` | current retard / LA906-side signed offset state | degree-domain until conversion | high static label confidence |
| `L01EC` | timing correction / previous period term used after `$3FDC` add | time/tick-domain candidate | medium static |
| `L0201` | spark latency lookup result | tick/correction candidate | medium static |
| `L020B` | low-octane spark retard | degree-domain | high static label confidence |
| `L020C` | knock retard | degree-domain | high static label confidence |
| `L01F2` | startup spark override/filter state | degree-domain | high static label confidence |
| `L005F` | last DRP period work value / multiplicand | time/tick-domain | medium static |
| `L3FC0` | last REF/DRP period ASIC source | time/tick-domain | medium static |
| `L3FF6` | EST fall counter / rolling timing anchor | time/tick-domain | high static label confidence |
| `L3FDC` | rolling timing state / spark work-period candidate | time/tick-domain | medium static |
| `L3FE8` | ASIC spark timing command candidate | time/tick-domain | medium static |
| `L3FE6` | ASIC spark timing companion command candidate | time/tick-domain | medium static |
| `L3FEC` | ASIC source/status read | status/mode-domain | medium static |
| `L3FE4` | mirror/ack/handshake target from `$3FEC` | status/mode-domain | medium static |

## Static Dependency Chain

```text
spark table / idle spark / modifiers
→ L01FD final spark advance
→ L01EE current retard / signed offset state
→ knock, burst knock, low-octane, torque-management, startup corrections
→ sign flag L004F bit0 and magnitude transform
→ RPM-indexed spark latency lookup → L0201
→ LF550 multiply against last DRP-period basis at L005F
→ latency subtract using L0201
→ period/timebase term using L3FC0
→ D at 0xAB97
→ LA906 rolling ASIC state: L3FF6, L3FDC
→ ASIC timing writes: $3FE8, $3FE6
→ ASIC status mirror: $3FEC → $3FE4
```

## Key Static Findings

### 1. `L01FD` is the final spark accumulator before the bridge

`L01FD` is repeatedly labeled `FINAL SPK ADV` and is updated by the base spark/modifier path before `LA906`. Relevant rows include final spark writes at `0xA81B`, `0xA841`, `0xA84B`, `0xA900`, `0xA977`, `0xA9DD`, and `0xAA0F`, then a read at `0xAA1A` before conversion into `L01EE`.

### 2. `L01EE` is the direct LA906-side pre-conversion value

`L01EE` is labeled `CURRENT RETARD (2's CMP)` in multiple rows. The bridge reads it at:

```text
0xAB1A  LDD L01EE
```

Then serial/ALDL control adjustments may alter it and store it again at:

```text
0xAB3E  STD L01EE
```

The final signed/magnitude handling before latency conversion begins at:

```text
0xAB47  LDD L01EE
0xAB4A  BPL LAB50
0xAB4C  BSET L004F,#$01   ; 1 = retard, 0 = advance
0xAB4F  NEGB
```

### 3. Knock and low-octane retard are degree-domain before conversion

`L020B` is explicitly labeled `LOW OCTAINE SPK RETARD` and is subtracted from final spark before `L01FD` is stored.

`L020C` is explicitly labeled `DEG, KNOCK RETARD`. It is updated at `0xAACB` and subtracted from `L01EE` at `0xAAD1-0xAAD8` through stack/magnitude handling.

### 4. Startup spark can bypass or replace the normal magnitude path

`L01F2` is labeled `START UP SPARK`. At `0xAB55`, startup spark is loaded and multiplied if the relevant flag path is active, meaning crank/startup spark is not simply the normal `L01FD` final spark path.

### 5. `L0201` is a latency correction from an RPM-indexed table

`LAB69` performs a lookup from table `$454A` using `ENGINE RPM/25`, then stores the result to `L0201`:

```text
0xAB69  PSHA
0xAB6A  LDAA L0062        ; ENGINE RPM/25
0xAB6C  LDX  #$454A       ; index table
0xAB6F  JSR  LF499        ; 2D lookup entry
0xAB72  STAA L0201
```

Later:

```text
0xAB84  SUBB L0201
```

So `L0201` is a correction applied after the period multiply and before the rolling timing-anchor addition.

### 6. The degree-to-time conversion uses DRP/REF period basis before `0xAB97`

After sign/startup handling and latency lookup, the path calls:

```text
0xAB76  LDX #$005F        ; last DRP period value address, multiplicand
0xAB79  JSR LF550         ; MUL 8x16 subroutine
```

Then it subtracts `$3FC0`, shifts right four times, ORs the high byte with `$F0`, and only then reaches:

```text
0xAB97  ADDD L3FF6        ; EST FALL CNT'R
```

This strongly indicates `D` at `0xAB97` is already in hardware timing domain, not raw spark degrees.

### 7. LA906 consumes timing-domain input and rolling state

After `0xAB97`, the routine subtracts the stack-stored timing value, writes `$3FE8`, combines with `$3FDC` and `$01EC`, writes `$3FE6`, updates `$3FDC`, restores and writes `$3FF6`, then mirrors `$3FEC` to `$3FE4`.

## Critical Trace Rows

| PC | Instruction | Role | Domain |
|---|---|---|---|
| `0xA81B` | `STD L01FD` | final spark write | degree-domain |
| `0xAA1A` | `LDD L01FD` | final spark read | degree-domain |
| `0xAA22` | `STD L01EE` | current retard/signed offset write | degree-domain until conversion |
| `0xAACB` | `STAA L020C` | knock retard update | degree-domain |
| `0xAB1A` | `LDD L01EE` | LA906-side entry source | degree-domain until conversion |
| `0xAB55` | `LDAB L01F2` | startup spark override input | degree-domain |
| `0xAB72` | `STAA L0201` | latency lookup result | correction/tick candidate |
| `0xAB79` | `JSR LF550` | multiply against `L005F` period basis | degree-to-time conversion candidate |
| `0xAB84` | `SUBB L0201` | latency subtract | correction/tick candidate |
| `0xAB8E` | `SUBD L3FC0` | period/timebase term | time-domain |
| `0xAB97` | `ADDD L3FF6` | LA906 timing sink input | time-domain |
| `0xABAA` | `STD L3FE8` | ASIC timing write candidate | time-domain |
| `0xABBA` | `STD L3FE6` | ASIC timing companion write candidate | time-domain |
| `0xABC0` | `STX L3FDC` | rolling state update | time-domain |
| `0xABC8` | `STD L3FF6` | rolling anchor update | time-domain |
| `0xAC28` | `LDX L3FEC` | ASIC source/status read | status/mode-domain |
| `0xAC2E` | `STX L3FE4` | mirror/ack candidate | status/mode-domain |

## Required New-OS Boundary

Current static evidence favors this boundary:

```text
minimal OS spark math produces final spark/retard in degree-domain
conversion layer converts degree-domain result using DRP/REF period and latency correction
LA906-compatible bridge consumes timing-domain value and rolling ASIC state
```

Possible future APIs:

```text
Option 1:
  minimal OS provides final spark degrees;
  stock-style conversion layer produces LA906-compatible timing-domain input.

Option 2:
  minimal OS provides spark delay/tick command directly;
  LA906-compatible bridge consumes that plus rolling state.

Option 3:
  minimal OS must maintain stock-style intermediate RAM variables:
    L01FD, L01EE, L0201, L01EC, L3FF6, L3FDC
```

## Current Classification

```text
D2T-A:
  supported. Degree-domain final spark/retard appears to feed a conversion before LA906.

D2T-B:
  also supported downstream. LA906 consumes an already converted tick-domain value.

D2T-C:
  likely. Rolling state in $3FF6/$3FDC and timing correction L01EC appear interleaved with command writes.

D2T-D:
  not supported by current static evidence, but bench testing remains required.
```

## Open Questions

- What is the exact unit of `L01FC` and `L01FD`? Several comments imply scaled degrees, likely related to `256/90`, but this is not yet locked.
- Is knock retard always subtracted before conversion, or can later paths bypass it?
- Is startup spark override replacing final spark or acting as a magnitude multiplier/offset under specific flags?
- Is `L0201` pure latency in timer ticks, or a table-scaled correction that still needs period context?
- Does `L3FC0` represent last REF period, DRP period, or ASIC-captured timing base in this exact conversion?
- What is `D` at `0xAB97` in physical units?

## Stop Condition

Do not write spark output code until this contract can answer:

```text
For desired spark advance X degrees at RPM Y,
what timing-domain value must enter the LA906 path,
and what rolling state must be maintained?
```
