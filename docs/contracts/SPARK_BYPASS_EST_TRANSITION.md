# Spark BYPASS / EST Transition

## Purpose

Document the crank-to-run and bypass-to-EST authority transition required before the minimal OS may command spark through the ASIC/EST handoff path.

This is an authority-transfer contract, not spark math and not a spark writer.

## Problem

`LA906` depends on rolling spark state. If `$3FF6/$3FDC` are only globally cleared at key-on, the first run-mode spark handoff may be unsafe unless stock code delays EST authority until valid period/rolling state exists.

## Scope

- crank/bypass state
- run qualification
- DRP/ref event qualification
- EST enable/monitor behavior
- Error 42 counter behavior
- ASIC status/mirror behavior related to spark authority

## Baseline Map

This pass uses the committed static baseline:

```text
maps/full/hardware_access_map_v0.2.csv
```

Do not reference `hardware_access_map_v0.3.csv` until it is generated and committed.

## Candidate State

| Symbol | Candidate role | Evidence | Confidence |
|---|---|---|---|
| `L004F bit7` | engine_running | clear at `0x7D78`, tested at `0xA510`, set at `0xA56E` | high_static |
| `L004F bit6` | EST monitor enable | tested at `0xA51B` and `0xE019`, set at `0xAC1C` | high_static |
| `L004F bit4` | run fuel / run-state gate | clear at `0x7D7B`, tested at `0xA514` | medium_high_static |
| `L0044 bit3` | first DRP valid latch | set at `0xA544`, tested at `0xA540/0xABCB`, cleared at `0xAC25` | high_static |
| `L0210` | run qualification event counter | incremented at `0xA560`, compared at `0xA566` | medium_high_static |
| `L4133` | 450 RPM bypass-to-run threshold candidate | compared at `0xA554` | high_static |
| `L3FCA` | ASIC/ref count sample source | sampled at `0xABD3` | medium_static |
| `L0205` | prior `L3FCA` sample | compared at `0xABEA`, stored at `0xAC0D` | medium_static |
| `L022C` | EST Error 42 counter candidate | incremented at `0xAC06/0xAC07`, cleared at `0xAC1F` | high_static |
| `L3FEC` | ASIC status/source | read at `0xAC28` | medium_static |
| `L3FE4` | ASIC mirror/ack target | written from `$3FEC` at `0xAC2E` | medium_static |
| `L022B` | watched legacy Error 42 candidate | not primary in captured EST monitor rows; primary rows point to `L022C` | low_for_this_path |
| `L0204` | watched prior sample candidate | adjacent to `L0205`; captured EST monitor rows use `L0205` | low_for_this_path |

## Transition Rows

| Stage | PC | Instruction | Symbol | Role | Required? | Confidence |
|---|---|---|---|---|---|---|
| safe_default_engine_running_clear | `0x7D78` | `BCLR L004F,#$80` | `L004F bit7` | engine_running | yes | high_static |
| safe_default_run_fuel_clear | `0x7D7B` | `BCLR L004F,#$10` | `L004F bit4` | run_qualification | yes | high_static |
| first_drp_valid_clear_on_startup_window | `0x7D9A` | `BCLR L0044,#$08` | `L0044 bit3` | drp_count_gate | yes | high_static |
| run_gate_engine_running_test | `0xA510` | `BRCLR L004F,#$80,LA540` | `L004F bit7` | engine_running | yes | high_static |
| run_gate_run_fuel_test | `0xA514` | `BRSET L004F,#$10,LA51B` | `L004F bit4` | run_qualification | yes | medium_high_static |
| first_drp_valid_test | `0xA540` | `BRSET L0044,#$08,LA54A` | `L0044 bit3` | drp_count_gate | yes | high_static |
| first_drp_valid_set | `0xA544` | `BSET L0044,#$08` | `L0044 bit3` | drp_count_gate | yes | high_static |
| rpm_threshold_compare | `0xA554` | `CPD L4133` | `L4133` | rpm_threshold_gate | yes | high_static |
| run_event_counter_increment | `0xA560` | `INC L0210` | `L0210` | drp_count_gate | yes | medium_high_static |
| run_event_counter_threshold | `0xA566` | `CMPA L4142` | `L4142` | drp_count_gate | yes | high_static |
| engine_running_set | `0xA56E` | `BSET L004F,#$80` | `L004F bit7` | engine_running | yes | high_static |
| startup_spark_override_clear | `0xA57C` | `STD L01F2` | `L01F2` | spark_authority_transfer | likely_yes_if_startup_override_retained | medium_static |
| est_monitor_enable_test | `0xA51B` | `BRCLR L004F,#$40,LA57F` | `L004F bit6` | est_monitor_enable | yes_if_fault_monitor_retained | high_static |
| post_la906_first_drp_gate | `0xABCB` | `BRCLR L0044,#$08,LAC31` | `L0044 bit3` | drp_count_gate | yes_if_fault_monitor_retained | high_static |
| post_la906_drp_occurred_gate | `0xABCF` | `BRCLR L0050,#$04,LAC10` | `L0050 bit2` | drp_count_gate | yes_if_fault_monitor_retained | medium_high_static |
| est_monitor_sample_read | `0xABD3` | `LDD L3FCA` | `L3FCA` | asic_status_read | yes_if_fault_monitor_retained | medium_static |
| est_monitor_prior_sample_compare | `0xABEA` | `SUBD L0205` | `L0205` | est_fault_counter | yes_if_fault_monitor_retained | medium_static |
| est_error_counter_increment | `0xAC06/0xAC07` | `INCB/STAB L022C` | `L022C` | est_fault_counter | yes_if_fault_monitor_retained | high_static |
| est_monitor_sample_store | `0xAC0D` | `STX L0205` | `L0205` | est_fault_counter | yes_if_fault_monitor_retained | medium_static |
| est_monitor_enable_set_good_path | `0xAC1C` | `BSET L004F,#$40` | `L004F bit6` | est_monitor_enable | yes_if_fault_monitor_retained | high_static |
| est_error_counter_clear_good_path | `0xAC1F` | `CLR L022C` | `L022C` | est_fault_counter | yes_if_fault_monitor_retained | high_static |
| first_drp_valid_clear_after_monitor | `0xAC25` | `BCLR L0044,#$08` | `L0044 bit3` | drp_count_gate | yes_if_stock_event_latch_retained | high_static |
| asic_status_mirror_read | `0xAC28` | `LDX L3FEC` | `L3FEC` | asic_status_read | likely_yes_until_bench_disproves | medium_static |
| asic_status_mirror_write | `0xAC2E` | `STX L3FE4` | `L3FE4` | asic_mirror_ack | likely_yes_until_bench_disproves | medium_static |
| major_loop_est_monitor_gate | `0xE019` | `BRCLR L004F,#$40,LE041` | `L004F bit6` | est_monitor_enable | yes_if_fault_monitor_retained | high_static |
| major_loop_err42_rpm_gate | `0xE023` | `CMPA L4E70` | `L4E70` | rpm_threshold_gate | yes_if_fault_monitor_retained | high_static |

## Static Transition Model

```text
key-on/stall/reset:
  L004F bit7 ENGINE RUNNING cleared
  L004F bit4 RUN FUEL cleared
  L0044 bit3 FIRST DRP VALID cleared/rearmed

crank / first-ref acceptance:
  first DRP/ref event sets L0044 bit3
  L3FC0 provides period/counter basis upstream of run qualification

run qualification:
  compare period/ref value against L4133 450 RPM bypass-to-run threshold
  increment L0210 qualifying event counter
  compare L0210 against L4142 count threshold
  set L004F bit7 ENGINE RUNNING when threshold + count gates pass
  clear startup spark override L01F2

post-LA906 EST monitor / status path:
  require first DRP valid and recent DRP occurrence before EST monitor checks
  sample L3FCA and compare against stored L0205
  increment/clear L022C EST error counter depending on result
  set L004F bit6 major-loop EST monitor enable on good path
  clear first DRP valid after event is consumed
  mirror L3FEC to L3FE4
```

## Required Questions

- What exact condition declares engine running?
- How many DRP/ref events are required before run?
- What RPM threshold enables EST handoff?
- Does `LA906` execute before or after EST authority transfer?
- Is bypass physically controlled by a CPU/ASIC write or by ASIC state?
- What increments Error 42 counter?
- What clears Error 42 counter?
- Does `$3FEC->$3FE4` participate in EST authority transfer?

## Current Static Answers

```text
engine running:
  L004F bit7 is the strongest static engine-running flag.

run qualification:
  static evidence supports RPM threshold plus DRP/ref event-count gating.

450 RPM threshold:
  L4133 is explicitly commented as 450 RPM BYPASS TO RUN ENABLE IN REF PERIOD.

EST monitor enable:
  L004F bit6 is major-loop EST monitor enable, not yet proven to be the physical EST/bypass output control.

Error 42 path:
  captured EST monitor rows point to L3FCA -> L0205 comparison and L022C counter, not L0204/L022B as the primary path.

LA906 before authority:
  post-LA906 gates at 0xABCB/0xABCF suggest LA906 may prepare timing state before monitor acceptance. Bench must determine whether coil authority is still physically bypassed/ignored.

ASIC mirror:
  $3FEC->$3FE4 appears after EST monitor/event consumption; treat as required sync/ack until bench disproves it.
```

## Minimal-OS Requirement

The minimal OS must not command EST spark until:

1. REF/DRP period is valid.
2. rolling spark state is seeded or known safe.
3. bypass/EST authority transition is safe.
4. missing-ref/dropout behavior is defined.
5. EST fault monitoring cannot falsely trip from missing factory state.

## Static Classification

```text
BYP-A:
  not sufficient alone. Static evidence shows more than RPM threshold.

BYP-B:
  strongest static fit. Transfer/run qualification requires RPM threshold plus DRP/ref event count.

BYP-C:
  possible. $3FEC->$3FE4 mirror may participate in status/ack but is not yet proven as authority gate.

BYP-D:
  plausible. LA906 appears able to prepare timing commands before EST monitor acceptance; coil effect must be bench-proven.

BYP-E:
  supported with corrected variables: Error 42 monitor depends on $3FCA/L0205/L022C in captured rows.

BYP-F:
  still possible until bypass wire and EST output are scoped through crank-to-run.
```

## Future Module Boundary

If bench confirms this model, spark should split into:

```text
SPARK_BYPASS_INIT
SPARK_RUN_QUALIFY
SPARK_ENABLE_EST_AUTHORITY
SPARK_FAULT_MONITOR
```

separate from:

```text
SPARK_CONVERT
SPARK_ROLLING_UPDATE
SPARK_ASIC_HANDOFF
```
