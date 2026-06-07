# ASIC / Hardware Register Contract

Concise working contract from static pass v0.2. Static evidence identifies accesses; dynamic trace must prove side effects, units, and timing.

## Confirmed HC11 timer / injector scheduler cluster

| Address | Name / role | Access | Why it matters | Required proof |
|---|---|---|---|---|
| `$300E/$300F` | `TCNT` free-running timer | read | timebase used to schedule future compare events | confirm timer rate and minimum safe compare lead time |
| `$301C/$301D` | `TOC4` compare | write/read | injector/output compare path | prove start/end role and write order |
| `$301E/$301F` | `TOC5` compare | write/read | injector/output compare path | prove companion injector channel role and write order |
| `$3020` | `TCTL1` output action | RMW | sets output compare pin action bits | map bits to actual injector/output pin action |
| `$3022` | `TMSK1` interrupt mask | RMW/write | arms/disarms compare interrupt sources | prove enable timing relative to compare writes |
| `$3023` | `TFLG1` timer flags | write/read | write-one-clear event flags | prove stale-flag handling before arm |

Minimal OS status: required. Do not rewrite fuel scheduling until this order is proven:

```text
compute compare target
clear relevant TFLG1 bit
arm relevant TMSK1 bit
set TCTL1 action bits
write TOC4/TOC5 compare
handle ISR and disable/retime as needed
```

## ASIC/ref/status candidates

| Address | Proposed role | Access | Required proof |
|---|---|---|---|
| `$3FC0` | last DRP/ref period counter candidate | read | correlate value with REF/RPM during crank and idle |
| `$3FC4` | period/status latch candidate | read | identify latch/update semantics |
| `$3FC6/$3FC8` | timing/status candidates | read | correlate with event timing and state transitions |
| `$3FCA` | 16-bit RPM/event counter candidate | read | determine units, cadence, rollover behavior |
| `$3FEC` | hardware status/source candidate | read | identify bits and possible read-clear behavior |
| `$3FFA` | packed ASIC status candidate | read | decode bits by key-on/crank/idle/snap/decel/stall |

Minimal OS status: required or test item. These are the eyes into the ASIC/ref-event hardware.

## ASIC command/output candidates

| Address | Proposed role | Access | Required proof |
|---|---|---|---|
| `$3FCC` | ASIC command/config latch | write | determine init value and physical effect |
| `$3FCE` | EFI pulsewidth/fuel handoff candidate | write | verify whether this is fuel command, shadow, or diagnostic path |
| `$3FD4/$3FD6/$3FD8/$3FDA` | ASIC command/output candidates | write | probe output effect and state dependence |
| `$3FE0/$3FE4` | ignition/output companion candidates | write | correlate with spark/EST state |
| `$3FE6/$3FE8` | spark handoff candidates | write | determine units and latch timing vs commanded spark |
| `$3FEA` | ASIC command/output candidate | write | classify by scenario and physical effect |
| `$3FF2/$3FF6/$3FF8` | scheduler/output command candidates | write | identify relation to EST fall/output event scheduling |
| `$3FFC` | I/O D port / output latch candidate | read/write | map latch bits to physical outputs and safe states |

Minimal OS status: required or test item until proven otherwise.

## Board / ASIC-adjacent unknowns

| Range | Role | Required proof |
|---|---|---|
| `$3060-$306F` | board/ASIC-adjacent unknown hardware area | bench-probe physical pins/outputs and capture all accesses across scenarios |

These are not removable just because the semantic label is unknown. They must be sorted into:

```text
required but not yet understood
not required for minimal fuel/spark/idle/debug operation
```

## ADC / sensor acquisition cluster

| Address | Name / role | Required proof |
|---|---|---|
| `$3030` | `ADCTL` ADC control/status | channel select, conversion complete timing |
| `$3031-$3034` | ADC result registers | channel-to-sensor mapping and scaling |

Minimal OS status: required for clean sensor acquisition.

## SCI / ALDL cluster

| Address | Name / role | Required proof |
|---|---|---|
| `$302C-$302F` | SCI/ALDL registers | baud/control setup, RX/TX behavior, debug-frame safety |

Minimal OS status: required for debug visibility.

## Boot / watchdog / core CPU cluster

| Address | Name / role | Required proof |
|---|---|---|
| `$303D` | `INIT` register relocation | confirm `$3000` register block relocation sequence |
| `$3039` | `OPTION` | preserve clock/COP/ADC/IRQ configuration |
| `$303A` | COP watchdog service | prove required service cadence |
| `$3035/$3038/$3024` | protection/options/timer config | preserve init until minimal boot is proven |

## Contract rule

No hardware write is removed until its effect is classified. No output path is rewritten until the write order, timing constraints, and side effects are known.
