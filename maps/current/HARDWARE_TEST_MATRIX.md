# Hardware Test Matrix

Static pass v0.2 produced `23` explicit hardware test-item rows and `693` hardware-facing rows. This document is the working bench-test checklist derived from the split access map.

## First bench target set

| Target | Subsystem | Static role | Capture goal | Pass condition |
|---|---|---|---|---|
| `$301C/$301E` | `FUEL_SCHED_TIMER` | TOC4/TOC5 compare writes | Capture compare value source, write order, and pulse timing during crank/idle/AE/DFCO | Scheduler order known; minimum compare lead time measured |
| `$3020` | `FUEL_SCHED_TIMER` | TCTL1 output action bits | Capture set/clear/toggle patterns around injector events | Output compare pin behavior classified |
| `$3022` | `FUEL_SCHED_TIMER` | TMSK1 interrupt enable/disable | Capture enable/disable order around `$301C/$301E` writes | Stale interrupt hazard understood |
| `$3023` | `FUEL_SCHED_TIMER` | TFLG1 write-one-clear flags | Capture flag clear timing before/after compare writes | W1C sequencing proven |
| `$3FCA` | `ASIC_STATUS_REF` | RPM/event counter candidate | Correlate reads with REF/DRP/RPM during crank and idle | Counter units and update cadence known |
| `$3FFA` | `ASIC_STATUS_REF` | packed hardware status candidate | Correlate bits with crank, idle, snap, decel, stall | Bit meanings and side effects classified |
| `$3FFC` | `IO_LATCH_OUTPUT` | I/O D port / output latch candidate | Capture writes at key-on, fault, crank, idle; probe physical outputs | Latch bits mapped to outputs or ruled out |
| `$3FE6/$3FE8` | `SPARK_EST` | spark handoff candidates | Compare values against commanded spark/RPM/MAP | Units and latch timing known |
| `$3FF6` | `SPARK_EST` | EST fall/output scheduler candidate | Capture write cadence and relation to spark events | Role in EST scheduling classified |
| `$3060-$306F` | `UNKNOWN_306X_BOARD_IO` | board/ASIC-adjacent unknown | Probe physical pins and capture accesses in all states | Each address marked required or removable |

## Required trace fields

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

## Required scenarios

```text
KEY_ON
CRANK_NO_START
FIRST_START
HOT_IDLE
STEADY_1500
STEADY_2500
THROTTLE_SNAP
CLOSED_THROTTLE_DECEL
DFCO
STALL
HOT_RESTART
```

## Classification rule

A hardware register can leave the minimal OS only after trace proves it does not affect fuel, spark, IAC, sensor acquisition, watchdog/reset, ALDL/debug, or engine protection. Unknown engine-affecting behavior remains a test item.
