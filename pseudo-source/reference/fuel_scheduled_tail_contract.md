# Scheduled fuel tail and joined cycle — BMHM $852C..$8547

Authority: literal $31/BMHM stock ROM, with the already reconstructed
`pcm_fuel_calculate` $7E4F..$852B, `pcm_oxygen_control` $863D..$891D,
`pcm_fuel_afr_learning` $891E..$8EB3, and raw VSS/battery producers.
The factory HAC comments are descriptive only; branch masks and call targets
come from instructions.

## $852C phase selection

| `phase & 0x06` | Factory successor sequence | Callable C |
|---|---|---|
| 0x00 | 8530 JSR 863D; 8533 JSR D4A3 | `pcm_oxygen_control` then `pcm_vss_calculate` |
| 0x02 | 8538 JSR 8613; 8544 JSR 8EB4 | `pcm_fuel_battery_state` then `pcm_fuel_governor_target` |
| 0x04 | 8530 JSR 863D; 8533 JSR D4A3 | Same oxygen/VSS pair, bit4 is not tested when bit2=0 |
| 0x06 | 8538 JSR 8613; 853F JSR 891E | `pcm_fuel_battery_state` then `pcm_fuel_afr_learning` |

The actual source tests 0002.1 before 0002.2. The gate does not touch
injector commands after their already-completed $7E4F..$852B path. Failure
in the first selected call prevents the second call, leaving its successful
state prefix intact. A failed prelude or calculation prevents **all** tail work.

## $8EB4 governor entry

The initial stock branch tests configuration $400F.0, $004F.7 running
and whether any $006F bits 2,4,5 are set. If disabled, not running or
status nonzero under mask $34, it writes target $0299=255 and returns.
This default is resident in `pcm_fuel_governor_target`, with canonical
owner `PcmTransmission.governor_requested_throttle`. When enabled,
running and $006F&$34 equals zero, the source continues at $8EC9;
`PCM_GOVERNOR_TARGET` is an explicit task boundary for that remaining
governor calculation. The earlier $90D3 call reached at $7E3D when
$400F.0 is enabled is independently represented by
`PCM_FUEL_GOVERNOR`. No guessed PID gains, throttle targets, actuator
commands or optional $1809 heads-up semantics are supplied.

## Joined source and foreground gate

`pcm_fuel_cycle` composes the actual source order:

1. `pcm_fuel_input_prefix` — $7D4B..$7E4E ignition, MAP, TPS, O2, optional governor, density
2. `pcm_fuel_calculate` — $7E4F..$852B, existing crank/run/AE/VE/feedback/injector routing
3. `pcm_fuel_scheduled_tail` — $852C..$8547 selected O2/VSS or battery/AFR/governor continuation

The stock fast dispatcher still calls `pcm_fuel_control`, currently
bound to task `PCM_FUEL_CONTROL`. It has **not** been switched to
`pcm_fuel_cycle`. Required before that admission: close enabled governor
subroutines, verify coherent logical RAM aliases between C named state
and the platform provider, run connected ROM/control-flow/failure-prefix
and retained-cycle checks, and confirm no factory branch is skipped.
The isolated host tests for phase routing and the joined prelude are
registered, not yet executed by a full integration/ROM suite on this branch.

Nothing in this batch creates a target 68HC11 binary, changes a
calibration BIN or authorizes live injector output.
