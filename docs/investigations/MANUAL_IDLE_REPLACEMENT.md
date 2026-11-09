# Manual-only idle replacement: trace and source implementation

This document records the original source/in-memory development stage. The
controller is now integrated in [the Rev B candidate](MANUAL_IDLE_REVB_RELEASE.md),
which adds the decel spark gate and cold-idle table revision. Historical
no-BIN and Rev A snapshot statements below describe the earlier stage.

The implementation removes both Park and Drive idle-air strategies in a
simulation overlay of the exact Rev A image. It is not a selector flip or a
copy of Drive tables into Park. No BIN has been released or changed. The
source's new calibration is a development proposal, requiring truck-specific
calibration before release.

Authority: current Rev A SHA-256
`d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e`.
OEM roles are cross-checked with the existing
[controller](../analysis/FACTORY_IAC_CONTROLLER.md),
[learning/output](../analysis/FACTORY_IAC_LEARNING_AND_OUTPUT.md),
[scheduling closure](../analysis/FACTORY_IDLE_SPEED_CONTROL_CLOSURE.md) and
[earlier exact Rev A trace](REVA_PARK_DRIVE_TRACE_20261106.md). Image bytes take
precedence over those documents' stock-only calibration and selection details.

## Complete idle strategy boundary

The rooted direct CFG covers vectors and all 16 dispatcher entries. The original
Rev A idle/driver/service scope `$91A3..$A465` contains 1,904 reachable instruction
starts. The [access inventory](../../maps/maintenance/manual_idle_original_accesses.csv)
records each scoped direct/indexed read, write and read-modify-write. Indexed
accesses are explicitly qualified, not invented absolute addresses. The
existing ROM-backed C contracts resolve the local bank, proposal, table, stack
and position-table families. General serial uploads and arbitrary external
memory accesses are not assigned fixed roles.

| Original scope | Role and dependency | Replacement decision |
|---|---|---|
| `$925E..$92A3` | Boot software-position seed, retained setup, output-enable shadow | Preserve boot mechanics; calls to cell seeding/restoration enter the new initializer |
| `$92A4..$93C4` | Dual default cells, snapshots, retained-cell restoration and adjustment | Retire; keep ABI stubs at $92A4 and $92F1, both entering one initializer |
| `$93C5..$93CF` | Conditional phase reset | Preserve byte for byte |
| `$93D0..$9410` | Service escape, homing-in-progress, completion, ignition-off parking and stopped/running selection | Preserve byte for byte |
| `$9411..$9536` | Separate startup curves, integral/cold bank choice, startup state and direct cold park target | Replace with one initializer, shared target and air composition |
| `$9537..$969D` | Forced Drive context, AC/gear transitions and queued integral/cold commits | Remove both contexts and all bank transitions; use one controller |
| `$969E..$9748` | Switch adders, transition holds, absolute RPM error and filter | Replace with explicit error/deadband and shared-direction publication |
| `$9752..$983C` | Integral/cold/P/D/startup/AC/gear sum, AE, follower, DFCO air and PE cap | Replace air composition; preserve IAC-change AE calculation and its position in the sum |
| `$983D..$989B` | BARO compensation, kicker option, flow-to-position conversion, direct-target/return tails | Preserve byte for byte, including service tail entry $9899 and return $989B |
| `$989C..$99C4` | Background RPM target, battery/roughness/BLM/startup/switch additions and stall threshold | Replace with shared `$FF60` lookup, downward slew and explicit stall margin |
| `$99C5..$9C1F` | Integral qualification, cold/baseline allocation, bank writes and position reconciliation | Replace with one bounded integral; eliminate strategy-level position reconciliation |
| `$9C20..$9C95`, `$9C96` pointer data | Park/Drive proportional curves and speed hysteresis | Replace with one proportional gain and limit |
| `$9CA6..$9CFC` | RPM-ratio derivative filter | Remove derivative term and its history |
| `$9CFD..$9E98` | Gear/speed-sensitive follower, hot-start floor and decay | Replace with one TPS follower and fixed bounded decay |
| `$9E99..$A2AF` | Movement/kicker/cold state, two-bound snapshot gate, AC decay, cross-bank proposals, snapshot publication | Remove; slot7 invokes only the shared target publisher |
| `$A2B0..$A3F9` | Second follower/decay updater, Drive cap, kicker/learning diagnostics and VSS reset admission | Replace slot9 with a returning stub; initialize the removed learning-fault bit clear |
| `$A3FA..$A406` | Software homing request: position255, target0, reset flag | Preserve byte for byte |
| `$A407..$A465` | Diagnostic reset, direct position, RPM override and kicker service with nonlocal return | Preserve byte for byte and verify its return ABI |
| `$91A3..$920D`, board output path | Battery/enable gating, compare, count, direction, phase ring, output shadow and later latch | Preserve byte for byte; no new hardware writer |

The motor's ignition-off **park position** is unrelated to transmission Park.
Keeping that homing/parking operation does not keep a Park idle strategy.
The original very-cold direct prestart target is strategy and is replaced by
the common computed prestart air request; it is not described as preserved
startup airflow behavior.

All running target, follower, qualification, P/I and composition state is
updated at the existing main-IAC admission. Background retains a target
publication call; the old slow path no longer runs another set of decays.
These are admission counts, not a guarantee of wall time under busy skips.

## Inputs and the engine interfaces that must survive

| Interface | Producer or consumer | Treatment |
|---|---|---|
| `$0063`, `$0283`, `$01D9` | Existing RPM-high, coolant-index and normalized-TPS producers | Read existing published engine inputs, no new ADC or sensor interpretation |
| `$0052.5` | Existing A/C request owner | One explicit load-air adder; no A/C learned bank |
| `$0046.3` | Existing DFCO state | Freeze P/I qualification/action during cut; no extra DFCO air history |
| `$003E.2` | Existing step-driver low-battery state | Freeze integral learning while the driver holds motion |
| `$0036.0/.2/.3/.4/.7` | AC, capture, integral admission, stall and RPM-error direction | Publish the corresponding single-controller meanings |
| `$0036.1` | Original Drive selector | Clear, never test or set it to choose a strategy |
| `$0036.5`, `.6` | Shared spark override and unowned bit | Preserve; do not claim ownership of the entire flag byte |
| `$0857` | Fuel classifier atFF0F and idle control | Shared target produced by the same curve at startup/running |
| `$0858` and `$0036.7` | Fuel-state publication atE3A8/E3B2 | Keep absolute error and direction semantics |
| `$0036.4` | Retained decision atCB74 | Publish explicit stall status, including when the air sum saturates |
| `$087F` | Fuel AE consumer at $810C | Preserve pre-follower composite-change AE using $50A8/$50A9/$50A2 |
| `$0862`, `$086A`, `$086D`, `$087D`, `$0880`, `$0889`, `$088B` | Controller/debug compatibility | Publish selected baseline, baseline high, P magnitude, composites/follower/air |
| `$0007..$000A`, `$004C`, hardware output latches | Existing reset, step and board-output services | Retain those writers and execution context; custom strategy only commands0008 through the preserved converter |
| Service `$0391.5`, `$0395`, `$0396`, `$038F.6` | Existing serial/diagnostic controls | Retain original reset/direct-position/RPM-override/service escapes |

No fuel calibration, injector model, base spark table, knock logic or normal
spark-output code is edited. Idle strategy still changes engine air and its
associated existing AE request. The proposed deceleration **spark** cleanup is
not included. The retained low-load spark slope also remains, so this work
alone does not establish that the logged warm-up oscillation is resolved.

## One state set and simpler behavior

The [HC11 source](../../source/manual_idle/manual_idle.asm) implements the same
algorithm as the [native reference](../../source/manual_idle/manual_idle.c):

1. Initialize one baseline word with a defined zero fraction. The old warm
   flags and removed learning-fault indication are cleared deliberately.
2. Look up the existing FF60 schedule in both startup and running paths.
   Retain a one-count downward slew and the existing service RPM override.
3. Maintain one bounded TPS follower and a deterministic starting-air fade.
   No P/N input, VSS, first-throttle latch or opposite-bank bound participates.
4. Capture idle using target-relative RPM and normalized-TPS hysteresis.
   Qualify integration for a specified number of main calls.
5. Apply error deadband, bounded P and one bounded Q8.8 integral. Freeze
   integration during startup/follower/DFCO/low voltage and at adverse command
   rails; allow correction away from a rail.
   Closed-throttle overspeed can use P before capture, while integral learning
   stays frozen until capture. A poor initial airflow calibration can still
   exceed this bounded correction's capture ability and must be corrected.
6. Add one cold-air schedule, startup air, A/C air and stall recovery.
   Publish pre-follower change AE, then add follower and enter the original
   BARO/position converter.

The initialized old composite isFFFF, as in the original startup path, to
prevent a false IAC-change fuel pulse during initialization. The learned
baseline is **runtime-only**; resetting it on restart is an intentional
simplification. Persistent single-cell learning can be added separately after
the one-cell controller is calibrated, with an explicit validity/retention
contract. There are no hidden warm snapshots or opposite-bank transfers.

The proposed RAM and ROM ownership is separately recorded in
[the planning map](../../maps/maintenance/manual_idle_address_plan.csv).
It is not installed into the root non-OEM workbooks: those must describe the
unchanged Rev A BIN. The trace adds missing existing $0036 bit-field roles to the
maintained books without falsely marking this replacement installed. The OEM
books remain untouched. On a later release, apply the planned omitted/reused
roles and update the image snapshot together.

## Verification evidence and practical limits

- [Static audit](../../maps/maintenance/manual_idle_static_audit.json): all
  vectors and 16 dispatcher roots. Every live incoming call to retired strategy
  has a valid replacement entry. No direct gear-selection decision, direct
  read of the old Drive bank, conflicting decode or execution into retired
  strategy/data remains. Preserved image ranges are compared byte for byte.
- [Differential tests](../../maps/maintenance/manual_idle_test_results.json):
  native C versus actual assembled HC11 state/air results, plus independent
  hysteresis, feedback-direction, anti-windup, deterministic decay, stall,
  input-independence, startup-AE and service/reset properties.
- [Reset fixtures](../../maps/maintenance/manual_idle_runtime_cases.json):
  key-on, cranking, hot/cold idle, cruise, power and legacy-input noise. Each
  reaches all 16 scheduler slots with reset/interrupt admission and no retired
  execution or ROM-checksum error.
- Extended [hot](../../maps/maintenance/manual_idle_runtime_hot_extended.json)
  and [cold](../../maps/maintenance/manual_idle_runtime_cold_extended.json)
  reset runs each complete 320 main calls, beyond the whole startup-air fade.
  Both end with zero starting air and qualified single-controller state.

The default comparison fixture is made from
[recorded original excerpts](../../maps/maintenance/manual_idle_reva_evidence.json).
It is not a bootable image. Full-image scripts require the exact Rev A hash,
overlay bytes only in memory and confirm the input file is unchanged. They do
not output a BIN. Local stack/cycle observations are supplied as observations,
not a WCET, stack-fit or interrupt-preemption proof.

The new strategy has no indexed RAM access. Retained lookup/conversion helpers
still use reviewed stack/table indexing, and the rest of the engine program
still has runtime-indexed operations. The whole-ROM direct CFG does not prove
every possible indirect data access or arbitrary externally uploaded entry.
The simulator imposes RPM and ADC fixtures. Its successful execution does not
predict closed-loop engine stability, physical IAC motion, delivered mixture
or the correct cold-air/gain values. Those remain calibration/measurement work
before a combined release with the pending spark changes.
