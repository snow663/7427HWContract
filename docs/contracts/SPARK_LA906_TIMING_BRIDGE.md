# SPARK LA906 Timing Bridge

## Purpose

Document the routine-level bridge between software spark calculation and ASIC spark/EST timing registers.

This is a static routine slice. It is not a complete data-flow proof and is not a spark writer contract.

## Scope

Routine cluster:

```text
LA906
$3FDC
$3FE4
$3FE6
$3FE8
$3FEC
$3FF6
```

Instruction slice captured in `maps/contracts/spark_la906_timing_bridge.csv` covers `0xAB1A` through `0xAC31`, which includes more than 40 instructions before the first key ASIC arithmetic at `0xAB97` and continues through the `$3FEC → $3FE4` mirror/ack candidate.

## Current Hypothesis

`LA906` converts or advances spark-related timing state in hardware time units. It writes at least two ASIC command/timing values and updates rolling timing state.

The routine does not write spark table degrees directly to hardware. It works in a timing/delay domain built from:

```text
current retard / final spark offset state
startup spark override path
spark latency lookup
last DRP/ref period timing basis
$3FC0 hardware timing basis
$3FF6 rolling EST fall counter / timing anchor
$3FDC rolling work-period / prior timing state
$01EC latency/reference correction
```

## Candidate Register Roles

| Register | Static role candidate | Confidence |
|---|---|---|
| `$3FE8` | computed timing command / compare-like value | medium |
| `$3FE6` | computed timing command / companion timing value | medium |
| `$3FDC` | rolling state / prior timing delta / work-period state | medium-low |
| `$3FF6` | rolling timing base / next timing anchor / accumulator | medium |
| `$3FEC` | ASIC status/source register | medium |
| `$3FE4` | mirror/ack/handshake target from `$3FEC` | medium |
| `$3FC0` | DRP/ref period hardware timing basis used in conversion | medium |
| `$3FCA` | ASIC RPM/event counter used by EST monitor, not primary command | medium |

## Instruction-Level Sequence

### Entry-side software spark/retard state

| PC | Instruction | Role |
|---|---|---|
| `0xAB1A` | `LDD L01EE` | load current retard / final spark-offset accumulator |
| `0xAB1D`-`0xAB3C` | serial/controller mode override logic | optional add/subtract from `L0398` |
| `0xAB3E` | `STD L01EE` | store adjusted current retard |
| `0xAB41` | `STD L01F0` | store retard shadow |
| `0xAB44`-`0xAB50` | direction/magnitude handling | sets retard/advance flag and makes magnitude positive |
| `0xAB51`-`0xAB61` | startup spark path | may use `L01F2` startup spark before continuing |

### Degree/offset to timing-domain bridge

| PC | Instruction | Role |
|---|---|---|
| `0xAB69` | `PSHA` | save spark magnitude |
| `0xAB6A` | `LDAA L0062` | load engine RPM/25 |
| `0xAB6C` | `LDX #$454A` | spark latency table index |
| `0xAB6F` | `JSR LF499` | 2D lookup |
| `0xAB72` | `STAA L0201` | save spark latency result |
| `0xAB75` | `PULA` | restore spark magnitude |
| `0xAB76` | `LDX #$005F` | last DRP period address / multiplicand |
| `0xAB79` | `JSR LF550` | multiply spark magnitude by last DRP period |
| `0xAB7C`-`0xAB87` | sign and latency correction | advance/retard sign plus `L0201` latency subtraction |
| `0xAB89`-`0xAB8B` | push D, TSX | saved timing-domain value becomes stack-addressed via X |

### ASIC timing-domain write cluster

| PC | Instruction | Static role |
|---|---|---|
| `0xAB8E` | `SUBD L3FC0` | uses hardware DRP/ref-period timing basis |
| `0xAB91`-`0xAB94` | four `LSRD` | scales hardware period basis by 16 |
| `0xAB95` | `ORAA #$F0` | forces high-nibble bias/sign in timing-domain value |
| `0xAB97` | `ADDD L3FF6` | adds rolling EST fall counter / timing anchor |
| `0xAB9A` | `SUBD 0,X` | subtracts saved computed spark-offset timing value |
| `0xAB9C`-`0xABA0` | sign check and stack clamp/update | modifies saved timing value only on one branch |
| `0xABA2` | `LDD 0,X` | reloads saved timing-domain value |
| `0xABA4` | `SUBD L3FF6` | forms first ASIC command relative to EST fall counter |
| `0xABAA` | `STD L3FE8` | writes first computed spark/EST timing command candidate |
| `0xABB0` | `ADDD L3FDC` | adds rolling work-period / prior timing state |
| `0xABB3` | `SUBD L01EC` | subtracts latency/reference correction |
| `0xABB7` | `LDX L01EC` | loads new correction/state into X |
| `0xABBA` | `STD L3FE6` | writes second computed spark/EST timing command candidate |
| `0xABC0` | `STX L3FDC` | updates rolling state with `L01EC` |
| `0xABC8` | `STD L3FF6` | updates rolling EST fall counter / timing anchor from saved D |

### EST monitor / mirror-ack tail

| PC | Instruction | Static role |
|---|---|---|
| `0xABCB` | `BRCLR L0044,#$08,LAC31` | first DRP valid gate |
| `0xABCF` | `BRCLR L0050,#$04,LAC10` | DRP occurred 6.25 ms test gate |
| `0xABD3` | `LDD L3FCA` | reads ASIC RPM/event counter for EST monitor |
| `0xABEA` | `SUBD L0205` | compares ASIC counter to previous monitor value |
| `0xAC0D` | `STX L0205` | updates EST monitor previous counter |
| `0xAC25` | `BCLR L0044,#$08` | clears first DRP valid flag |
| `0xAC28` | `LDX L3FEC` | reads ASIC status/source/capture candidate |
| `0xAC2E` | `STX L3FE4` | mirrors/acknowledges source into companion target candidate |
| `0xAC31` | `BSET L004B,#$10` | marks post-bridge status flag |

## Register Value Flow

```text
$3FE8 ← D
       ← LDD 0,X
       ← saved timing-domain stack value
       ← prior math using L3FC0, L3FF6, and spark-offset timing value
       ← SUBD L3FF6
```

```text
$3FE6 ← D
       ← value after $3FE8 write path
       ← ADDD L3FDC
       ← SUBD L01EC
```

```text
$3FDC ← X
       ← LDX L01EC
       ← likely rolling/reference correction state update
```

```text
$3FF6 ← D
       ← PULA/PULB restores original saved timing-domain value
       ← updated rolling EST fall counter / timing anchor
```

```text
$3FE4 ← X
       ← LDX L3FEC
       ← possible mirror/ack/handshake from ASIC status/source register
```

## Current Static Interpretation

```text
D at 0xAB97:
  not a final spark degree value.
  It has already been transformed through spark magnitude, DRP/ref period, latency correction, stack storage, and hardware timing basis from $3FC0.

$3FF6:
  behaves like a rolling timing anchor / EST fall counter.
  It is read before $3FE8 and updated after the paired writes.

$3FE8:
  first computed ASIC timing command candidate.
  Value is relative to $3FF6.

$3FE6:
  second computed ASIC timing command candidate.
  Value incorporates $3FDC and subtracts $01EC.

$3FDC:
  rolling state / previous work-period or correction state.
  Updated from L01EC after $3FE6 is written.

$3FEC → $3FE4:
  likely mirror/ack/handshake or capture transfer.
  It is gated by first-DRP/DRP-occurred logic, separate from the immediate $3FE6/$3FE8 writes.
```

## Open Questions

- What exactly is the unit of the timing-domain value entering `0xAB97`?
- Is `$3FF6` a timing accumulator, last scheduled point, or EST-fall event counter?
- Are `$3FE6` and `$3FE8` two spark edges, spark/dwell pair, or command plus deadline?
- Is `$3FDC` previous event timing state or dwell/work-period storage?
- Is `$3FEC → $3FE4` a required acknowledge/mirror for EST hardware?
- Which RAM variable is the clean software final spark value before conversion: `L01EE`, `L01F0`, or an upstream degree-domain byte?

## Required New-OS Behavior Pending Bench Proof

A future spark writer must not simply write spark degrees. It must reproduce whatever timing-domain bridge bench testing proves:

1. final spark / retard input handling
2. RPM/ref-period scaling
3. latency correction
4. rolling `$3FF6` timing anchor maintenance
5. paired `$3FE8/$3FE6` writes if required
6. `$3FDC` state update if required
7. `$3FEC → $3FE4` mirror/ack if required
8. crank/run/bypass-safe behavior

## Next Static Target

After this bridge contract, trace the upstream dependency from degree-domain final spark into the value entering this routine:

```text
SPARK_DEGREE_TO_TICK_DEPENDENCY
```

Candidate upstream variables to resolve:

```text
L01EE  current retard / final spark-offset accumulator
L01F0  retard shadow
L0201  latency lookup result
L020C  knock retard
L005F  last DRP period
L01EC  spark latency / reference correction
L3FC0  hardware DRP/ref period basis
```
