# Spark Rolling State Model

## Purpose

Model the rolling timing state used by `LA906` between spark/EST events.

This is the persistence/continuity contract. It does **not** create a spark writer.

## Scope

This contract explains the persistent state around:

- `$3FF6`
- `$3FDC`
- `$01EC`
- `$3FE8`
- `$3FE6`
- `$3FEC → $3FE4`

Secondary boundary/context terms:

- `$3FC0`
- `L005F/L0060`
- `L01EE/L01EF`
- `L0201`
- `L004F bit0`

## Known Static Sequence

```text
D_AB97 + $3FF6       → timing state
...
STD $3FE8

D + $3FDC - $01EC    → timing state
...
STD $3FE6

STX $3FDC
STD $3FF6

LDX $3FEC
STX $3FE4
```

## Candidate Model

Static evidence suggests:

```text
$3FF6 = rolling timing anchor / EST fall counter candidate
$3FDC = rolling timing state / prior edge candidate
$01EC = latency/work-period correction term
$3FE8 = first paired ASIC timing command
$3FE6 = second paired ASIC timing command
$3FEC = ASIC feedback/status/capture
$3FE4 = mirror/ack target
```

## State Rows

| Stage | PC | Instruction | State | Access | Candidate role | Persistence | Recompute? | Required? |
|---|---|---|---|---|---|---|---|---|
| entry_anchor_read | `0xAB97` | `ADDD L3FF6` | `L3FF6` | read | rolling_event_anchor | likely_yes | unknown_pending_bench | likely_yes_if_la906_path_retained |
| anchor_difference_for_3fe8 | `0xABA4` | `SUBD L3FF6` | `L3FF6` | read | previous_est_edge_or_anchor_delta | likely_yes | unknown_pending_bench | bench_classify |
| first_command_write_context | `0xABAA` | `STD L3FE8` | `L3FE8` | write | next_est_edge_or_timing_command_1 | runtime_write_required_pending_bench | yes_from_current_bridge_state_if_model_known | likely_yes_pending_bench |
| prior_state_read_for_3fe6 | `0xABB0` | `ADDD L3FDC` | `L3FDC` | read | previous_est_edge_or_paired_edge_state | likely_yes | unknown_pending_bench | likely_yes_if_paired_edge_model_confirmed |
| work_term_subtract_for_3fe6 | `0xABB3` | `SUBD L01EC` | `L01EC` | read | dwell_or_latency_offset | likely_yes_as_work_term | possible_from_period/latency_if_model_known | bench_classify |
| work_term_load_for_state_update | `0xABB7` | `LDX L01EC` | `L01EC` | read | software_prediction_state | yes_if_3fdc_update_required | possible_from_current_period_if_model_known | likely_yes_pending_bench |
| second_command_write_context | `0xABBA` | `STD L3FE6` | `L3FE6` | write | next_est_edge_or_timing_command_2 | runtime_write_required_pending_bench | yes_from_current_bridge_state_if_model_known | likely_yes_pending_bench |
| update_prior_state | `0xABC0` | `STX L3FDC` | `L3FDC` | write | software_prediction_state | likely_yes | maybe_from_current_L01EC_each_event | likely_yes_if_3fdc_read_path_required |
| update_event_anchor | `0xABC8` | `STD L3FF6` | `L3FF6` | write | rolling_event_anchor | likely_yes | unknown_pending_bench | likely_yes_if_la906_path_retained |
| feedback_read | `0xAC28` | `LDX L3FEC` | `L3FEC` | read | hardware_capture_feedback | unknown_pending_bench | no_if_real_hardware_feedback | bench_classify |
| feedback_mirror_ack | `0xAC2E` | `STX L3FE4` | `L3FE4` | write | asic_ack_state | likely_if_ack_required | no_if_ack_must_mirror_hardware_value | likely_yes_until_bench_disproves |
| period_source_context | `0xAB8E` | `SUBD L3FC0` | `L3FC0` | read | hardware_capture_feedback | context_required_for_conversion | no_if_hardware_period_capture | owned_by_conversion_equation_not_rolling_update |

## Register/State Interpretation

### `$3FF6/$3FF7`

`$3FF6` is read at the start of the bridge, subtracted again before `$3FE8`, and then rewritten at the end. Static evidence strongly suggests it is not a one-shot command register. It behaves like a rolling event anchor, previous/next EST fall counter, or hardware-synchronized timing base.

### `$3FDC/$3FDD`

`$3FDC` is read before the `$3FE6` command calculation and then rewritten from `X`, where `X` was loaded from `L01EC`. That makes it look like prior-edge or paired-edge rolling state, not a simple mode register.

### `L01EC/L01ED`

`L01EC` is subtracted immediately before `$3FE6`, then loaded into `X` and persisted into `$3FDC`. Static evidence makes it a high-priority dwell/latency/work-period correction candidate. It may be recomputable, but only after its physical meaning is known.

### `$3FE8/$3FE9` and `$3FE6/$3FE7`

These appear to be paired timing-output writes. `$3FE8` is produced from the `$3FF6` relationship; `$3FE6` is produced from the `$3FDC - L01EC` relationship.

### `$3FEC → $3FE4`

The read/mirror sequence is suspicious enough to treat as required until bench testing says otherwise. If it is an ACK/capture handshake, a minimal OS cannot synthesize it without reading the real hardware source.

## Required Questions

- Does `$3FF6` represent the previous event anchor, next event anchor, or a fall-edge counter?
- Does `$3FDC` represent a prior EST edge, a dwell-related edge, or an ASIC feedback copy?
- Is `$01EC` a latency term, dwell term, or period correction?
- Can a minimal OS recompute `$3FF6/$3FDC` each loop, or must it preserve continuity?
- Is `$3FEC → $3FE4` required every event?
- Which state must be initialized before the first run spark event?

## Current Static Classification

```text
ROLL-A ($3FF6 required rolling event anchor):
  strongly supported statically; read/subtract/update pattern.

ROLL-B ($3FDC required prior/paired-edge state):
  strongly supported statically; read before $3FE6 and update from L01EC.

ROLL-C (L01EC required timing/dwell/latency correction):
  strongly supported statically; subtract before $3FE6 and source for $3FDC update.

ROLL-D ($3FEC->$3FE4 feedback/ack):
  plausible; explicit read/mirror pair, bench required.

ROLL-E (state recomputable each event):
  possible only after L01EC/$3FF6/$3FDC units are known; not safe to assume.

ROLL-F (static model incomplete):
  possible until scoped/bench traced.
```

## Minimal-OS Implication

If rolling state is required, the future spark module must be split into:

```text
SPARK_INIT_STATE
SPARK_CONVERT_DEGREES_TO_TIME
SPARK_UPDATE_ROLLING_STATE
SPARK_ASIC_HANDOFF
```

Current expectation:

```text
$3FF6 is probably not optional.
$3FDC is probably not optional.
$3FE8/$3FE6 are probably a paired output.
$3FEC->$3FE4 is suspicious enough to treat as required until bench says otherwise.
```

## Next Contract

Before any provisional spark handoff stub, document first-event/init behavior:

```text
SPARK_INIT_STATE.md
```
