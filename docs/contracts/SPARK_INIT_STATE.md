# Spark Init State

## Purpose

Document the initialization and crank-to-run seeding required before `LA906` can safely command spark through the ASIC handoff path.

This contract is about first-event validity. It does **not** create a spark handoff stub.

## Scope

This contract covers the state required before the first valid run-mode spark handoff:

- `$3FF6`
- `$3FDC`
- `$01EC`
- `$3FE4/$3FEC`
- `$3FE8/$3FE6`
- `L005F/L0060`
- `$3FC0`
- run/bypass flags that gate the first `LA906` call

## Current Model

`LA906` requires rolling timing state. Therefore the minimal OS must either:

1. reproduce the stock seed/init sequence, or
2. define an equivalent safe seed from current REF/DRP period and desired spark.

## Static Init Rows

| PC | Target | Access | Context | Candidate role | Required? | Confidence |
|---|---|---|---|---|---|---|
| `0x715B` | $3FC0-$3FF8 even words (0x3FC0:0x3FFA) | `STD 0,X` | key_on_or_reset_init | global_clear | likely_yes_global_asic_safe_default | medium_high_static |
| `0xA5E5` | L3FC0 (0x3FC0) | `LDD L3FC0` | period_basis_formation | first_ref_capture | yes_valid_period_basis_required | medium_static |
| `0xA5E8` | L005F/L0060 (0x005F) | `STD L005F` | period_basis_formation | period_basis_seed | yes_before_conversion_equation | medium_static |
| `0xA5FC` | L005F/L0060 (0x005F) | `STD L005F` | period_basis_formation_or_fallback | period_basis_seed | yes_valid_period_or_safe_fallback_required | medium_static |
| `0xA6EC` | L01EC/L01ED (0x01EC) | `STD L01EC` | timing_work_term_seed | latency_seed | likely_yes_before_first_3fe6 | medium_static |
| `0xA6F5` | L01EC/L01ED (0x01EC) | `SUBD L01EC` | timing_work_term_refine | latency_seed | likely_yes_if_stock_model_retained | medium_static |
| `0xA6FD` | L01EC/L01ED (0x01EC) | `STD L01EC` | timing_work_term_refine | latency_seed | likely_yes_before_first_3fe6 | medium_static |
| `0xAB44` | L004F bit0 (0x004F) | `BCLR L004F,#$01` | per_la906_conversion_entry | safe_default | yes_if_stock_sign_model_retained | high_static |
| `0xAB4C` | L004F bit0 (0x004F) | `BSET L004F,#$01` | per_la906_conversion_entry | safe_default | yes_if_stock_sign_model_retained | high_static |
| `0xAB97` | L3FF6/L3FF7 (0x3FF6) | `ADDD L3FF6` | first_la906_run_update | rolling_anchor_seed | must_be_valid_before_this_read | high_static_dependency_medium_init_unknown |
| `0xABB0` | L3FDC/L3FDD (0x3FDC) | `ADDD L3FDC` | first_la906_run_update | prior_edge_seed | must_be_valid_before_this_read | high_static_dependency_medium_init_unknown |
| `0xABAA` | L3FE8/L3FE9 (0x3FE8) | `STD L3FE8` | first_la906_run_update | first_run_spark_seed | yes_if_la906_path_confirmed | medium_static_pending_bench |
| `0xABBA` | L3FE6/L3FE7 (0x3FE6) | `STD L3FE6` | first_la906_run_update | first_run_spark_seed | yes_if_la906_path_confirmed | medium_static_pending_bench |
| `0xABC0` | L3FDC/L3FDD (0x3FDC) | `STX L3FDC` | first_la906_run_update | prior_edge_seed | yes_for_second_and_later_events | medium_static |
| `0xABC8` | L3FF6/L3FF7 (0x3FF6) | `STD L3FF6` | first_la906_run_update | rolling_anchor_seed | yes_for_second_and_later_events | medium_static |
| `0xAC28/0xAC2E` | L3FEC/L3FE4 (0x3FEC->0x3FE4) | `LDX/STX L3FEC -> L3FE4` | first_la906_run_update_or_ack | mirror_ack_seed | likely_yes_until_bench_disproves | medium_static_pending_bench |

## Crank-to-Run Transition

Static evidence currently supports this conservative transition model:

```text
1. key-on/reset global ASIC clear seeds $3FC0-$3FF8 even words to $0000
2. REF/DRP period capture becomes available through $3FC0
3. software period basis L005F/L0060 is seeded from $3FC0 or derived period/RPM fallback
4. timing work term L01EC is seeded/refined before LA906 uses it
5. sign flag L004F bit0 is initialized per conversion event
6. first LA906 run update consumes existing $3FF6/$3FDC
7. first LA906 run update then seeds $3FDC/$3FF6 for subsequent events
8. $3FEC->$3FE4 mirror may acknowledge or synchronize first valid output state
```

The unresolved risk is step 6: if global-clear zero is not a valid first seed for `$3FF6/$3FDC`, stock code must have a separate first-event seed or must avoid LA906 until the rolling state is valid.

## State-Specific Interpretation

### `$3FF6/$3FF7`

No non-LA906 seed has been locked yet beyond the global ASIC clear. The first LA906 read of `$3FF6` therefore creates the key first-event question: is `$0000` a safe seed, or does a bypass/run gate delay LA906 until hardware/stock state has populated it?

### `$3FDC/$3FDD`

`$3FDC` is globally cleared, then first consumed by `ADDD L3FDC` before being updated from `L01EC`. This means the first run event must either tolerate `$3FDC=$0000` or execute a separate seed path before the read.

### `L01EC/L01ED`

`L01EC` has pre-LA906 writers around `0xA6EC-$0xA6FD`. It is the strongest explicit software seed candidate for the rolling-state model because it is later subtracted before `$3FE6` and copied into `$3FDC`.

### `L005F/L0060` and `$3FC0`

The period basis must be valid before the conversion equation can generate a sane `D_AB97`. If no valid REF/DRP period exists, the minimal OS must hold spark in safe/bypass/default behavior.

### `$3FEC -> $3FE4`

The mirror/ack sequence occurs after the paired timing writes. Until bench testing says otherwise, treat it as part of first-event synchronization, not optional decoration.

## Required New-OS Behavior

The future minimal spark module must provide:

1. safe default spark state at key-on
2. valid period basis before first run spark
3. valid rolling anchor before first `$3FE8/$3FE6` write
4. valid prior-edge/paired-edge state before first `$3FDC` use
5. bypass-to-EST transition behavior that does not produce a wild spark event
6. safe behavior if REF/DRP period is missing or invalid

## Current Static Classification

```text
INIT-A:
  not proven. Static rows show period/L01EC seeds, but no locked explicit $3FF6/$3FDC seed before first LA906 beyond global clear.

INIT-B:
  plausible. $3FF6/$3FDC may only become fully meaningful after one LA906 iteration.

INIT-C:
  plausible and important. Startup/bypass may avoid ASIC spark handoff until rolling state is valid.

INIT-D:
  plausible. $3FEC->$3FE4 may acknowledge or synchronize first valid state.

INIT-E:
  possible until crank-to-run trace is captured.
```

## Minimal-OS Expected Split

```text
SPARK_INIT_STATE:
  clear/default output state
  wait for valid REF/DRP period
  seed $3FF6/$3FDC/L01EC from period/capture or safe defaults
  permit LA906-style handoff only when valid

SPARK_CONVERT:
  degrees → D_AB97

SPARK_ROLLING_UPDATE:
  maintain $3FF6/$3FDC

SPARK_ASIC_HANDOFF:
  write $3FE8/$3FE6
  mirror $3FEC->$3FE4 if required
```

## Next Contract

If this pass does not fully capture bypass/EST transition behavior, next target:

```text
SPARK_BYPASS_EST_TRANSITION.md
```
