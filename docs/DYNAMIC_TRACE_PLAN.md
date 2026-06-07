# Dynamic Trace Plan

Static analysis identifies where hardware is touched. Dynamic trace proves what actually happens under engine states.

## Required capture fields

```text
cycle_or_timestamp
pc
bank_or_page
opcode
mnemonic
access_type
address
value
A
B
D
X
Y
SP
CCR
engine_state
rpm
map
tps
cts
battery
vss
notes
```

## Engine states to capture

```text
KEY_ON
CRANK
FIRST_START
IDLE
STEADY_1500
STEADY_2500
THROTTLE_SNAP
POWER_ENRICH
CLOSED_THROTTLE_DECEL
DFCO
STALL
RESTART
```

## First hardware targets

| Address / range | Reason | Required proof |
|---|---|---|
| `$301C/$301E` | TOC4/TOC5 compare writes | confirm injector pulse start/end sequencing and minimum lead time |
| `$3020` | TCTL1 output action bits | confirm output pin set/clear/toggle behavior for injector compare paths |
| `$3022` | TMSK1 interrupt mask | confirm enable/disable order around compare writes |
| `$3023` | TFLG1 flags | confirm write-one-clear timing and stale-flag behavior |
| `$3FCA` | ASIC/ref timing candidate | identify read cadence and relation to RPM/ref pulses |
| `$3FFA` | packed ASIC status candidate | identify bit meanings by scenario |
| `$3FFC` | I/O/output latch candidate | identify physical outputs and startup/fault behavior |
| `$3FE6/$3FE8/$3FF6` | spark/EST candidates | identify spark handoff units, latch timing, and bypass/EST transition |
| `$3060-$306F` | board/ASIC-adjacent unknowns | prove required/not-required for minimal fuel/spark/idle operation |

## Trace scenarios

### 1. Key-on no crank

Purpose: identify initialization-only writes, safe output states, watchdog/COP handling, SCI setup, and ASIC latch defaults.

### 2. Crank no start

Purpose: identify crank fuel scheduler behavior, REF/RPM capture path, spark/bypass transition, and compare write order.

### 3. Start and warm idle

Purpose: identify run fuel handoff, stable spark handoff, IAC movement path, and recurring ASIC status reads.

### 4. Throttle snap

Purpose: identify AE handoff changes, async/sync fuel switching, and spark transient writes.

### 5. Closed-throttle decel / DFCO

Purpose: identify BPW zero gating, re-enable hysteresis, VSS dependency, and stale compare handling.

### 6. Fault/stall/restart

Purpose: identify bad-shutdown flags, output shutdown behavior, watchdog cadence, and restart initialization differences.

## Test-item rule

A register cannot be removed from the minimal OS unless it is either:

1. classified as non-engine/non-hardware-required by trace, or
2. replaced by a proven equivalent initialization/output sequence.

Unknown engine-affecting behavior remains a test item, not a warning note.
