# Resident scheduled fuel controller

Stock BMHM remains byte authority (SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`).
The complete7D4B..8547 scheduled root now calls resident C through crank/running
calculation, injector publication and the scheduled tail. The former
`PCM_FUEL_CONTROL` task slot is reserved and unused. This group generates no BIN.

| C entry | Stock range | Responsibility |
|---|---|---|
| `pcm_fuel_control` | 7D4B..8547 | Ignition→inputs→calculation→tail join. |
| `pcm_fuel_ignition` | 7D4B..7DB5 | Captured ignition counter, ordered cleanup/restart, COP55 and STOP boundary. |
| `pcm_fuel_inputs` | 7DB6..7E4E | MAP context, TPS, oxygen filtering, governor admission and density. |
| `pcm_fuel_schedule` | 852C..8547 | Phase-qualified oxygen/VSS or battery/AFR/governor target. |
| `pcm_governor_target` | 8EB4..90D2 | RPM/VSS modes, accumulator/lead, anticipation/recovery and target. |
| `pcm_governor_actuator` | 90D3..9166 | Position error, scaled P/I, overrides and literal1F command. |

## Ignition and scheduling

Ignition captures word027E before its first gate. With0044.4 set, a count below8
skips shutdown cleanup. Count8 or greater clears the specified flags, run timer,
delivered pulse and startup state in source order. The later comparison uses
the captured count and word4009. Reaching that limit writes08 to OPTION3039.
`PCM_STOP_BOUNDARY` returns **before**7D8C TAP/STOP. The target shim must provide
CCR50, STOP, wake handling and the terminal7D8E successor. No host resume into
fuel calculation is invented.

Ordinary ignition clears the specified old shutdown state, sets0086.3 and
incrementsFFFF to0000. Continuing shutdown increments the captured count with
word wrap. COP55 follows the counter store. Failed operations retain the
completed prefix; STOP does not perform the final counter/COP pair.

Inputs preserve previous TPS before normalization, and oxygen filtering before
governor/density. Option400F.0 is sampled at its consuming position. The existing
7E4F calculation runs real crank/authorization, running construction, cut/decel,
reservoir and sync/async publication bodies.

The tail samples phase bit1 first. Clear selects oxygen control then raw VSS
calculation. Set selects battery/capture, then a **fresh** phase bit2 sample:
set runs AFR/BLM; clear runs the governor target. The odd-phase caller admits
oxygen/VSS on phases1/5, governor target on3 and AFR/BLM on7 modulo8. Callback
cases change phase during capture to check that second gate.

## Governor arithmetic and boundaries

Accumulator0286, actuator integral0288, step028A, lead0290, correction0292 and
target0299 remain separate. Disabled admission writes only targetFF. Mode
changes retain partial clears, entry high-byte stores, word fractions and their
individual equality admissions. Floor comparison/replacement reads stay distinct.
The F550 word-gain helper samples its low byte before its high byte.

The derivative branch uses signed N xor V for zero-minus028D, including80
overflow. Anticipation reduction reads the fraction at9086, but both routes join
9093 `CLRB`: **its stored fraction becomes zero even above the floor**. The
actual-ROM comparison corrected the earlier
[governor note](../../docs/analysis/FACTORY_RPM_VSS_GOVERNOR.md). VSS entry's
high-byte-only store and the other routes retain their own fraction behavior.

Actuator gains retain separate live error reads and saturated shifted products.
An integral-add carry selectsFF00. TargetFF clears that integral after building
the current candidate. Voltage inhibit precedes service override. The word1Fxx
command goes to306C. Existing TCC/factory writers of306C remain separate owners;
the port introduces no arbitration or physical polarity assumption.

Optional1809 receives captured error A through `governor.extension_value`.
`PCM_GOVERNOR_EXTENSION` explicitly returns that byte and carry. Carry publishes
returned A immediately; clear continues the resident body. Missing binding returns
`PCM_UNIMPLEMENTED`. These payload fields allocate no factory RAM and define no
machine ABI. Optional1800 AFR code remains a separate dependency. Stock400F is10,
with electronic governor disabled; enabled paths are still checked here.

## Focused verification

The new suite passes **16,493 compiled-C/actual-ROM comparisons**, covering all
**389 newly scoped software instruction starts**. TAP, STOP and the terminal
loop remain target boundaries excluded from that count.

| Cases | Behavior |
|---:|---|
| 9 | Entries, complete controller and REF joins. |
| 512 | Captured ignition count, cleanup/restart, wrap and STOP boundary. |
| 1,280 | All shared flag bytes in shutdown RMW sequences. |
| 1,024 | Governor option, engine and every partial inhibit mask. |
| 4,608 | Mode bytes across RPM/VSS entry, hysteresis and release. |
| 3,072 | Signed derivative, anticipation and recovery. |
| 1,215 | Actuator signs, bounds, live error/curve reads and targetFF. |
| 48 | Command header and voltage/service priority. |
| 1,024 | Raw profiles, fractions and live-read mutation. |
| 2 | Reduction overflow and crank BARO floor. |
| 1,920 | Every phase and battery boundary, including phase mutation. |
| 24 | Optional1809 absence, errors, returned carry and A. |
| 1,260 | Real inputs/calculation/tail, governor, crank/running and REF calls. |
| 367 | Each failed provider/mask/module operation on selected paths. |
| 128 | Retained controller/REF histories. |

All337 production/calibration files compile with strict C11 warnings as errors.
All eight kernel and64 hardware contracts pass. The kernel160-phase cycle now
supplies a nominal battery ADC sample and observes160 COP writes (housekeeping
AA and resident fuel55), with zero fuel task callbacks. The EGR suite still
passes8,950 cases. A preliminary delivery subset passes7,821 comparisons;8432
overflow is outside that quick subset. No complete rerun of the older665,548-case
delivery suite is claimed here.

New logical bodies compare operand widths, order, values and failed prefixes.
Previously checked native bodies contribute actual state and physical-address
I/O; native field operations are not fabricated provider calls. Phase gates use
their existing native owner. Literal IRQ assignments and nominal11/33-cycle delays
remain visible. ADC completion is an explicit fixture. Private HC11 stack traffic
and older math scratchAD..B2 are excluded consistently with the bounded native
math contracts. The fixture binds involved named owners to logical RAM.

Remaining work includes slot4/F producer admissions and initialization, wider
scheduled/REF interleavings, optional modules, target assembly/STOP ABI, physical
backend, timing and delivered fuel. Full project regression, PR and merge remain
deferred until the user's "pull and merge" instruction.

The later [slow-producer group](slow_fuel_contract.md) closes slot1 and supplies
the callable slotF suffix. Its C4F5 diagnostic prefix and slot4 callers remain
separate; this controller suite retains its original entry scope.
