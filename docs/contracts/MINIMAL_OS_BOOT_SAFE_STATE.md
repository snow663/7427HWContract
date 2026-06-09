# Minimal OS Boot / Safe-State Contract

## Purpose

Define the reset, crank, first-reference, run-qualification, and dropout-safe-state boundary for the minimal OS.

This document does not implement reset code, scheduler code, or runtime ASM.

## Source Dependencies

- `MINIMAL_OS_EXECUTION_SCHEDULER.md`
- `MINIMAL_OS_MODULE_BOUNDARY.md`
- `EFI_OUTPUT_INIT_STATE.md`
- `EFI_OUTPUT_INIT_ROUTINE.md`
- `MINIMAL_EFI_PW_WRITER.md`
- `SPARK_INIT_STATE.md`
- `SPARK_BYPASS_EST_TRANSITION.md`
- `SPARK_ROLLING_STATE_MODEL.md`
- `IAC_INIT_PARK_CONTRACT.md`
- `IAC_ENABLE_FAULT_GATE_CONTRACT.md`
- `source/minimal_os/fuel/efi_pw_writer.asm`
- `source/minimal_os/iac/README.md`
- `source/minimal_os/spark/README.md`

## Boot State Machine

```text
RESET_ENTRY
→ ASIC / output window safe clear
→ OUTPUT_SAFE_DEFAULTS
→ RAM_STATE_SEED
→ REF_DRP_WAIT
→ CRANK_QUALIFY
→ FIRST_PERIOD_VALID
→ RUN_QUALIFY
→ NORMAL_SCHEDULER_HANDOFF
→ DROPOUT_SAFE_STATE on signal loss or unsafe state
```

## Safe Output Rules

Fuel:

- `$3FCE` may be zeroed.
- Nonzero `$3FCE` requires fuel calculation and enable/no-fuel gate.
- `$3FCE` may only be written through `EFI_PW_WRITE` / `MINIMAL_EFI_PW_WRITER` or documented output-init clear path.

Spark:

- no direct timing ASIC writes.
- no EST/bypass authority implementation yet.
- rolling timing seed remains bench-gated.

IAC:

- no direct `L3062` writes.
- no physical IAC motion implementation yet.
- software seed only until physical direction, Enable, park/reset behavior, and cadence are bench-gated.

## Dropout Rules

On missing REF/DRP or unsafe state:

```text
fuel → zero/no-pulse
spark → safe/bypass/dropout intent only
IAC → hold current software state or defined safe target
watchdog → force output-safe defaults
```

## Boot-State Table

| Boot stage | State | Module | Submodule | Output default | Hardware write | Allowed now | Bench gate | Safe value | Dropout value |
|---|---|---|---|---|---|---|---|---|---|
| reset_entry | `RESET_ENTRY` | boot | entry | all runtime control outputs inactive | no `none` | planning_only | yes | no runtime control outputs active | re-enter RESET_ENTRY or WATCHDOG_SAFE_STATE |
| asic_clear | `ASIC_WINDOW_CLEAR` | boot | asic_window | candidate output/window safe clear | candidate `ASIC/window registers` | no_runtime_code_yet | yes | safe/inactive output windows | safe/inactive output windows |
| output_defaults | `OUTPUT_SAFE_DEFAULTS` | boot | safe_defaults | fuel zero; spark no-authority intent; IAC hold/software-only | candidate `mixed` | no_runtime_code_yet | yes | all outputs safe/inactive | all outputs safe/inactive |
| ram_seed | `RAM_STATE_SEED` | boot | ram_state | software state initialized; hardware outputs unchanged | no `none` | planning_only | yes | known software defaults | known software defaults |
| fuel_zero | `FUEL_SAFE_STATE` | fuel | safe_zero | $3FCE zero/no-pulse intent | yes_provisional_via_contract `$3FCE` | yes_provisional | yes | $3FCE = 0 / no pulse | $3FCE = 0 / no pulse |
| fuel_nonzero_block | `FUEL_SAFE_STATE` | fuel | nonzero_block | nonzero fuel output blocked | no `$3FCE` | no | yes | nonzero blocked | zero/no-pulse |
| dfco_gate_preserve | `FUEL_SAFE_STATE` | fuel | no_fuel_gate | D=0 can be forced | candidate `$3FCE` | yes_provisional_via_contract | yes | D=0 path available | D=0 path forced |
| spark_safe | `SPARK_SAFE_STATE` | spark | safe_intent | no direct ASIC timing writes | forbidden `$3FE8/$3FE6/$3FF6/$3FDC` | no | yes | no-authority / bypass-intent only | safe/bypass/dropout intent only |
| spark_roll_seed | `SPARK_SAFE_STATE` | spark | rolling_seed | rolling state held/uncommitted | forbidden `$3FF6/$3FDC` | no | yes | no direct seed write | no direct seed write |
| spark_bypass_safe | `SPARK_SAFE_STATE` | spark | bypass_est_authority | no physical authority action | forbidden `EST/bypass hardware` | no | yes | remain safe/no-authority | safe/bypass/dropout intent |
| iac_safe | `IAC_SAFE_STATE` | iac_idle | software_hold | software seed/hold only | forbidden `L3062` | no | yes | software hold / no motion | hold software state or safe target only |
| iac_seed | `IAC_SAFE_STATE` | iac_idle | position_seed | software state seeded; output unchanged | no `L3062` | no | yes | seed only | hold or reset policy |
| iac_motion_block | `IAC_SAFE_STATE` | iac_idle | motion_block | no phase output | forbidden `L3062` | no | yes | no motion | hold/no motion |
| wait_for_ref | `REF_DRP_WAIT` | scheduler | ref_wait | fuel/spark run outputs blocked; IAC no motion | no `mixed` | planning_only | yes | wait with safe outputs | dropout safe outputs |
| crank_qualify | `CRANK_QUALIFY` | scheduler | crank_gate | crank-safe input permissions | no `none` | planning_only | yes | crank inputs may become valid | return to REF_DRP_WAIT or DROPOUT_SAFE_STATE |
| crank_outputs | `CRANK_QUALIFY` | scheduler | crank_outputs | fuel intent may be computed; spark/IAC intent only | candidate `$3FCE only` | fuel_only_provisional | yes | fuel zero or crank PW if intentionally enabled; spark/IAC intent only | fuel zero; spark safe; IAC hold |
| first_period | `FIRST_PERIOD_VALID` | ref_rpm_period | period_valid | RPM/timebase usable by modules | no `none` | planning_only | yes | timebase valid | timebase invalidated |
| run_qualify | `RUN_QUALIFY` | scheduler | run_gate | normal scheduler handoff permitted | no `none` | planning_only | yes | normal scheduler handoff | dropout safe state |
| normal_handoff | `RUN_QUALIFY` | scheduler | normal_scheduler_handoff | module events may run per scheduler contract | no `none` | planning_only | yes | scheduler dispatch allowed | dropout safe state |
| dropout_entry | `DROPOUT_SAFE_STATE` | watchdog_safe_state | dropout_entry | modules forced to safe policy | candidate `mixed` | planning_only | yes | safe state | safe state |
| dropout_fuel | `DROPOUT_SAFE_STATE` | fuel | fuel_zero | $3FCE zero/no-pulse intent | yes_provisional_via_contract `$3FCE` | yes_provisional | yes | $3FCE=0 | $3FCE=0 |
| dropout_spark | `DROPOUT_SAFE_STATE` | spark | spark_safe | safe intent only | forbidden `$3FE8/$3FE6/$3FF6/$3FDC` | no | yes | safe/bypass intent | safe/bypass intent |
| dropout_iac | `DROPOUT_SAFE_STATE` | iac_idle | iac_hold | software hold/safe target only | forbidden `L3062` | no | yes | hold/no motion | hold/no motion |
| watchdog_safe | `WATCHDOG_SAFE_STATE` | watchdog_safe_state | watchdog_fallback | output-safe defaults requested | candidate `mixed` | no_runtime_code_yet | yes | safe defaults | safe defaults |
| bench_gated_spark | `BENCH_GATED_OUTPUTS` | spark | bench_gate | no write | forbidden `$3FE8/$3FE6/$3FF6/$3FDC` | no | yes | blocked | blocked |
| bench_gated_iac | `BENCH_GATED_OUTPUTS` | iac_idle | bench_gate | no write | forbidden `L3062` | no | yes | blocked | blocked |
| forbidden_outputs | `FORBIDDEN_OUTPUTS` | boot | forbidden_matrix | forbidden outputs blocked | forbidden `$3FE8/$3FE6/$3FF6/$3FDC/L3062` | no | yes | blocked | blocked |
| unknown_boot | `UNKNOWN` | unknown | unknown | unknown remains unknown | no `unknown` | unknown | no | unknown | unknown |

## Explicit Forbidden Outputs

No boot state may directly write:

```text
$3FE8
$3FE6
$3FF6
$3FDC
L3062
```

No boot state may create:

```text
reset vector ASM
runtime scheduler ASM
SPARK_WRITE
IAC_WRITE
physical EST/bypass authority code
idle strategy ASM
```

Exception:

```text
$3FCE may be forced to zero only through the existing EFI_PW_WRITE / MINIMAL_EFI_PW_WRITER contract or a documented output-init clear path.
```

## Unknown Ownership Rule

Unknown boot ownership must remain `UNKNOWN`; it must not be silently assigned to reset, fuel, spark, IAC, watchdog, or scheduler code until source/bench evidence assigns it.

## Next Contract

The next useful artifact is:

```text
MINIMAL_OS_STATE_VARIABLES
```

That pass should consolidate the minimal RAM/state map across fuel, spark, IAC, scheduler, boot, watchdog, and ALDL without writing the OS.
