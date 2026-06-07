# SPARK ASIC Handoff Contract

## Purpose

Document the CPU-to-ASIC contract candidates for commanded ignition timing, EST/bypass state, and spark-related hardware handoff.

This is static evidence only. Do not create a spark writer from this file until bench testing proves the final handoff register, unit scale, and write sequence.

## Scope

Address window:

```text
$3FD8-$3FFE
```

Primary candidates:

```text
$3FDC
$3FE4
$3FE6
$3FE8
$3FEC
$3FF6
$3FFA
$3FFC
```

## Known Problem

The new OS must not assume spark table degrees are directly written to hardware. Stock code appears to convert final spark into a hardware timing/delay domain using reference-period state, then writes one or more ASIC registers.

Important split:

```text
spark angle domain:
  table spark / final spark in degrees

hardware timing domain:
  delay/count/tick/work-period value written to ASIC
```

## Register Summary

| Address | Access | Width | Static role | Runtime? | Required? | Confidence |
|---|---|---:|---|---|---|---|
| `$3FC0-$3FF8` | W | 16 | boot ASIC-window clear overlapping spark candidates | boot init | init overlap | medium range inferred |
| `$3FDC` | R/W | 16 | spark dwell/work-period register candidate | runtime spark calc / diagnostic output cycling | yes or test item for spark | high |
| `$3FE4` | W | 16 | possible `$3FEC` mirror/handshake | runtime spark calc | yes or test item for spark | high |
| `$3FE6` | W | 16 | runtime spark companion command candidate | runtime spark calc | yes or test item for spark | high |
| `$3FE8` | W | 16 | runtime spark/EST timing handoff candidate | runtime spark calc | yes or test item for spark | high |
| `$3FEC` | R | 16 | ASIC status/source read before `$3FE4` write | runtime spark calc | yes or test item for spark | high |
| `$3FF6` | R/W | 16 | EST fall counter / scheduling basis | runtime spark calc / diagnostic output cycling | yes or test item for spark | high |
| `$3FFA` | R | 16 | packed ASIC status read | ref/status contexts | status decode test item | high |
| `$3FFC` | R/W | 16 | global output latch / I/O D, separate contract | boot/runtime/diagnostic/ALDL | separate output-latch contract | high |
| `$3FD8/$3FDA` | W | 16 | diagnostic/output scheduler slots | diagnostic/output or unknown | not primary spark until proven | high |

## Runtime Write Sites

| PC | Address | Instruction | Value source | Routine | Action | Notes |
|---|---|---|---|---|---|---|
| `0xABAA` | `$3FE8` | `STD L3FE8` | `D` | `LA906` | spark_delay_write | ASIC EST/spark timing output engine |
| `0xABBA` | `$3FE6` | `STD L3FE6` | `D` | `LA906` | spark_command_write | ASIC spark handoff path |
| `0xABC0` | `$3FDC` | `STX L3FDC` | `X` | `LA906` | spark_dwell_write | ASIC spark dwell / spark work period handoff |
| `0xABC8` | `$3FF6` | `STD L3FF6` | `D` | `LA906` | est_fall_counter_write | ASIC EST fall counter / output scheduler |
| `0xAC2E` | `$3FE4` | `STX L3FE4` | `X` | `LA906` | asic_handshake_mirror | ASIC ignition/output companion write |
| `0xFAF7` | `$3FDC` | `STX L3FDC` | `X` | `LFA5B` | spark_dwell_write | diagnostic/output-cycling spark work period/dwell |
| `0xFB03` | `$3FF6` | `STD L3FF6` | `D` | `LFA5B` | est_fall_counter_write | diagnostic/output-cycling EST fall counter |

## Runtime Read Sites

| PC | Address | Instruction | Used for | Routine | Notes |
|---|---|---|---|---|---|
| `0xAB97` | `$3FF6` | `ADDD L3FF6` | ref_timing_read | `LA906` | EST fall counter / output scheduler |
| `0xABA4` | `$3FF6` | `SUBD L3FF6` | ref_timing_read | `LA906` | EST fall counter / output scheduler |
| `0xABB0` | `$3FDC` | `ADDD L3FDC` | spark_dwell_read_add | `LA906` | spark dwell / work-period value added into command path |
| `0xAC28` | `$3FEC` | `LDX L3FEC` | spark_status_read | `LA906` | ASIC hardware status/source before `$3FE4` write |
| `0x7765` | `$3FFA` | `LDD L3FFA` | est_status_read | `L7765` | packed ASIC status |
| `0x7BF6` | `$3FFA` | `LDD L3FFA` | est_status_read | `L7BA7` | packed ASIC status |

## Runtime Spark Cluster

The strongest runtime spark cluster is routine `LA906`:

```text
0xAB97  ADDD L3FF6   read EST fall counter / timing basis
0xABA4  SUBD L3FF6   subtract EST fall counter / timing basis
0xABAA  STD  L3FE8   write spark/EST timing output candidate
0xABB0  ADDD L3FDC   add dwell/work-period candidate
0xABBA  STD  L3FE6   write spark companion command candidate
0xABC0  STX  L3FDC   update dwell/work-period candidate
0xABC8  STD  L3FF6   update EST fall counter / scheduler
0xAC28  LDX  L3FEC   read ASIC status/source
0xAC2E  STX  L3FE4   write possible status mirror/handshake
```

This supports Path S-B or S-C more than Path S-A: final spark is probably converted into delay/tick/work-period values before ASIC handoff, and `$3FE4/$3FEC/$3FF6` may be handshake/status/timing companions.

## Dependency Chain

```text
$3FE8 / $3FE6 / $3FDC / $3FF6 spark ASIC candidate writes
← hardware delay/tick/work-period value
← final spark after modifiers
← base spark table
← idle correction
← coolant correction
← knock retard
← MAP/RPM/CTS/state
← REF period / $3FF6 / ASIC timing basis
```

## Required New-OS Behavior

The new OS must reproduce, once bench-proven:

1. EST/bypass-safe startup behavior
2. crank/run spark transition
3. final spark to hardware-unit conversion
4. correct ASIC register write order
5. correct refresh timing
6. zero/limp/default behavior if spark command is invalid
7. optional knock-retard subtraction if knock is retained

## Open Questions

- Which register is the final spark command handoff?
- Is the handoff angle-based or delay/tick-based?
- Is `$3FEC → $3FE4` a required mirror/handshake?
- Does `$3FE6` or `$3FE8` receive the final spark timing command?
- What does `$3FF6` do in spark/output scheduling?
- Which bits in `$3FFA` report EST/ref/status?
- Is `$3FFC` involved in EST/bypass or only general output latch state?

## Current Static Classification

```text
Path S-A:
  weak static support. No single obvious angle-domain spark register is proven.

Path S-B:
  strongest static candidate. Final spark likely becomes delay/tick-domain values written to ASIC.

Path S-C:
  also plausible. `$3FE4/$3FEC/$3FF6` may be companion status/handshake/timing state.

Path S-D:
  not ruled out, but static evidence strongly shows ASIC spark/EST candidate writes in LA906.
```

## No Writer Yet

Do not create `source/minimal_os/spark/spark_write.asm` until the bench test identifies:

```text
final handoff register(s)
unit scale
write order
required companion/handshake behavior
safe default behavior
```
