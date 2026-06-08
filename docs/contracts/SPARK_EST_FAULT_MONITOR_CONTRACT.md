# Spark EST Fault Monitor Contract

## Purpose

Classify the EST/Error 42 monitor path and determine whether it is required for minimal spark authority or only diagnostic behavior.

This contract does not create a spark writer and does not define the final minimal module boundary.

## Current Static Context

The bypass/EST transition pass found:

```text
L004F bit7 = engine-running flag
L0044 bit3 = first DRP valid latch
L4133 = 450 RPM bypass-to-run threshold candidate
L0210 = qualifying DRP/ref event counter
L004F bit6 = EST monitor enable
L3FCA -> L0205 -> L022C = captured Error 42 monitor path
$3FEC -> $3FE4 = possible status/mirror/ack
```

## Core Question

Can the minimal OS safely keep EST monitor disabled or simplified while still allowing EST authority and LA906 spark handoff?

## Monitor Path Summary

| Symbol | Candidate role | Evidence | Confidence |
|---|---|---|---|
| `L004F bit6` | EST monitor enable | tested at `0xA51B` and `0xE019`, set at `0xAC1C` | high_static |
| `L004F bit7` | engine-running context | tested/set by run qualification | high_static |
| `L0044 bit3` | first DRP valid gate | tested at `0xABCB`, cleared at `0xAC25` | high_static |
| `L0050 bit2` | recent DRP gate | tested at `0xABCF` | medium_high_static |
| `L3FCA` | current captured/ref sample | read at `0xABD3` | medium_static |
| `L0205` | prior captured/ref sample | read at `0xABEA`, written at `0xAC0D` | medium_static |
| `L022C` | EST error counter | incremented at `0xAC06/0xAC07`, cleared at `0xAC1F` | high_static |
| `L0044 bit7` | locked ERR42A candidate | set at `0xAC13` | medium_high_static |
| `$3FEC->$3FE4` | status/mirror/ack candidate | read/write at `0xAC28/0xAC2E` | medium_static |

## Static Monitor Rows

| Stage | PC | Instruction | Symbol | Role | Required? | Confidence |
|---|---|---|---|---|---|---|
| monitor_enable_precheck | `0xA51B` | `BRCLR L004F,#$40,LA57F` | `L004F bit6` | est_monitor_enable | only_if_stock_fault_monitor_retained | high_static |
| engine_running_context | `0xA510/0xA56E` | `BRCLR/BSET L004F,#$80` | `L004F bit7` | engine_running_gate | yes_for_run_qualification | high_static |
| first_drp_gate | `0xABCB` | `BRCLR L0044,#$08,LAC31` | `L0044 bit3` | first_drp_gate | yes_if_stock_monitor_retained | high_static |
| recent_drp_gate | `0xABCF` | `BRCLR L0050,#$04,LAC10` | `L0050 bit2` | recent_drp_gate | yes_if_stock_monitor_retained_or_equivalent_dropout_gate_needed | medium_high_static |
| captured_ref_current_read | `0xABD3` | `LDD L3FCA` | `L3FCA` | captured_ref_current | only_if_stock_fault_monitor_retained | medium_static |
| captured_ref_previous_compare | `0xABEA` | `SUBD L0205` | `L0205` | captured_ref_previous | only_if_stock_fault_monitor_retained | medium_static |
| err42_mask_gate | `0xABDD` | `BRCLR 0,Y,#$20,LAC1C` | `ERR word 4 bit5` | est_fault_threshold | no_if_monitor_omitted_or_disabled | medium_static |
| monitor_enabled_shortcut | `0xABE2` | `BRSET L004F,#$40,LAC25` | `L004F bit6` | est_monitor_enable | only_if_stock_fault_monitor_retained | high_static |
| est_error_counter_increment | `0xAC06/0xAC07` | `INCB/STAB L022C` | `L022C` | est_fault_counter | no_if_MON_A; yes_if_MON_B_or_MON_C | high_static |
| first_good_flag_clear_on_fault_path | `0xAC0A` | `BCLR L0044,#$40` | `L0044 bit6` | est_fault_set | no_if_monitor_omitted_or_disabled | medium_static |
| captured_ref_previous_store | `0xAC0D` | `STX L0205` | `L0205` | captured_ref_previous | only_if_stock_fault_monitor_retained | medium_static |
| locked_err42a_set | `0xAC13` | `BSET L0044,#$80` | `L0044 bit7` | est_fault_threshold | no_if_MON_A; yes_if_monitor_retained | medium_high_static |
| monitor_enable_set_good_path | `0xAC1C` | `BSET L004F,#$40` | `L004F bit6` | est_monitor_enable | only_if_stock_fault_monitor_retained | high_static |
| est_error_counter_clear | `0xAC1F` | `CLR L022C` | `L022C` | est_fault_clear | only_if_stock_fault_monitor_retained | high_static |
| event_latch_clear_after_monitor | `0xAC25` | `BCLR L0044,#$08` | `L0044 bit3` | first_drp_gate | yes_if_stock_event_latch_retained | high_static |
| asic_status_mirror_read | `0xAC28` | `LDX L3FEC` | `L3FEC` | asic_status_mirror | likely_yes_until_bench_disproves_if_LA906_path_retained | medium_static |
| asic_status_mirror_write | `0xAC2E` | `STX L3FE4` | `L3FE4` | asic_status_mirror | likely_yes_until_bench_disproves_if_LA906_path_retained | medium_static |
| major_loop_monitor_gate | `0xE019` | `BRCLR L004F,#$40,LE041` | `L004F bit6` | est_monitor_enable | only_if_stock_fault_monitor_retained | high_static |
| major_loop_rpm_fault_gate | `0xE023` | `CMPA L4E70` | `L4E70` | rpm_threshold_gate | only_if_stock_fault_monitor_retained | high_static |

## Static Fault-Monitor Model

```text
enable/gating:
  L004F bit6 is the monitor-enable state.
  L0044 bit3 first-DRP-valid and L0050 bit2 recent-DRP gates prevent false checks.
  Major-loop monitor also gates on L004F bit6 and RPM threshold L4E70.

sample/delta:
  current hardware/ref sample comes from L3FCA.
  prior sample is stored in L0205.
  monitor compares or differences L3FCA against L0205.

fault accumulation:
  L022C is the captured EST error counter.
  L4E72 is the threshold candidate: 4 EST errors for 42A.
  threshold path sets a locked ERR42A candidate bit in L0044.

good/recovery path:
  good path sets L004F bit6 monitor enable.
  good path clears L022C.
  current L3FCA sample is stored to L0205 for next comparison.

shared mirror path:
  L3FEC is read and mirrored to L3FE4 after event/monitor path completion.
```

## Required Answers

- What enables EST monitoring?
- What disables it?
- What increments `L022C`?
- What clears `L022C`?
- What threshold sets Error 42?
- Does Error 42 force bypass/module timing?
- Does Error 42 inhibit `LA906`?
- Does Error 42 change spark command, fuel, or limp behavior?
- Does `$3FEC->$3FE4` belong to the monitor, handoff ACK, or both?
- Can a minimal OS safely omit the monitor?
- Can a minimal OS keep monitor disabled without side effects?

## Current Static Answers

```text
monitor enable:
  L004F bit6 is clearly a monitor-enable/control flag.

monitor fault condition:
  captured static path compares current L3FCA behavior against stored L0205 behavior and increments L022C on fault path.

counter clear:
  good path clears L022C at 0xAC1F.

fault threshold:
  L4E72 is the static threshold candidate with source comment indicating 4 EST errors for 42A.

authority side effect:
  not proven. Static rows show monitor/error state, but no locked direct write that forces bypass or disables LA906 in this contract.

fuel/run side effect:
  not proven in this pass.

mirror path:
  $3FEC->$3FE4 remains shared/ambiguous: monitor completion, handoff ACK, status sync, or all three.
```

## Minimal-OS Impact

If MON-A is bench-proven, the minimal OS can omit or keep the EST monitor disabled while still implementing safe run qualification, bypass/EST authority, LA906 conversion, rolling state, and ASIC handoff.

If MON-B/MON-C/MON-D is bench-proven, the monitor or parts of it become required hardware-contract behavior and must be represented in the minimal module boundary.

## Classification

```text
MON-A:
  possible. Static evidence has not proven a direct authority/fuel side effect.

MON-B:
  not proven. L004F bit6 gates the monitor, but is not yet proven to gate physical spark authority.

MON-C:
  possible after fault threshold, but no direct fallback/bypass side effect is locked yet.

MON-D:
  plausible. $3FEC->$3FE4 is shared with the LA906 post-event path and cannot be omitted until bench disproves it.

MON-E:
  possible until fault-threshold and bypass-wire behavior are bench-classified.
```

## Next Contract

After this pass, the next non-code artifact should be:

```text
SPARK_MINIMAL_MODULE_BOUNDARY.md
```

No `SPARK_WRITE` or spark handoff stub until the module boundary is written and the bench gates are explicit.
