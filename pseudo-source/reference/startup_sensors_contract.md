# Initial acquisition and factory-test admission

`pcm_reset_sensors` now implements 718A..71C2: F20D auxiliary acquisition,
F245 engine inputs, C56F battery acquisition and the new `pcm_factory_admit`.
The earlier RESET_SENSORS task identifier remains reserved and unused. Existing
named input owners, fresh mux reads, ADC timeout-and-publish behavior and
battery's SEI/CLI/store ordering are retained. Successful sampling leaves the
literal battery CLI in effect; no new boot-wide mask is invented.

7193 captures diagnostic input082F once and tests 28<=sample<64 hexadecimal.
Passing that window sets0050.3 before any later test. Admission then requires
raw throttle00A6>=FC, raw coolant082D>=FC and auxiliary reference00A5<=05.
Failure retains prior factory and diagnostic flags; it does not undo0050.3.
Complete admission sets0044.0, clears the separate factory byte0001, and writes
the literal B93A word to3FFC. These state stores precede the word write, so a
failed backend write retains them. No normal scheduler busy/pending flag is
substituted for0001. `system.factory_flags` is its canonical owner.

The existing reset-sequence wrapper returns FACTORY_BOUNDARY after admission,
before ordinary retained/controller stages. Native C does not synthesize the
target JMP7459 continuation or reset SP. The periodic handler now also retains
7952's raw phase-byte increment before returning at the FA5B factory boundary.
It wraps FF->00 without the ordinary 160-phase clamp and preserves the ordered
old-compare+819, acknowledgement and seen-flag prefix. It does not run ordinary
fast service, stack checks, idle/service expiry or dispatcher work on that path.

The startup-sensor fixture compares C state and exact ordered byte/word/mask
transactions against SHA256-checked BMHM instructions. It sweeps each admission
input byte against retained flag states, tests the threshold cross-product,
ADC readiness including timeout, selected input/PORTD/mask mutations, every raw
factory phase byte and selected compare-wrap values. Selected failure prefixes,
retained admission histories and acquisition-to-first-factory-timer joins are
included. The kernel contract also joins the real reset RAM and sensor stages,
verifying that factory admission skips ordinary later dependencies.

ROM authority remains BMHM SHA256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The suite passes 10,728 comparisons across all 32 new scoped instruction starts.
The new scoped entries cover 718A..71C2 and793D..7957; their existing ADC callees
also execute in the joined fixture. Physical ADC identity/behavior, interrupt
frames, target stack and actual factory callback/upload/output cycling remain
separate work. No target BIN is produced by this source translation.

This completes the third source PR in the current batch, after service lifecycle
PR #30 and working-RAM initialization PR #45. Run and check the required batch
tests before merging in dependency order. Next implement retained boot checks
and factory recurring execution while keeping arbitrary received-code callbacks
and target nonreturning control transfers explicit.
