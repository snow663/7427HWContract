# EST monitor and resident spark controller

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The monitor at ABCB..AC50 and its shared ACA0/ACA3 exits now have a C body.
Production `pcm_spark_control` joins admission, normal calculation, peripheral
publication and this monitor. Production `pcm_alternate_rpm` directly calls the
implemented AC51..ACA6 body. Both dispatcher call sites use these resident
adapters without `PCM_SPARK_CONTROL` or `PCM_ALTERNATE_RPM` task bindings.
Those enum values remain reserved to avoid renumbering existing dependencies;
setting their platform bindings has no effect on the production adapters.

## Ownership and state

| Routine | ROM scope | Responsibility |
|---|---|---|
| `pcm_spark_monitor` | ABCB..AC50 and shared ACA0/ACA3 exits | Counter qualification, fault latches, feedback handoff and request/service routing |
| `pcm_spark_control` | A466..ACA6 | Resident normal/alternate flow, stopping at the first failed prefix or pre-SWI boundary |
| `pcm_alternate_rpm` | AC51..ACA6 | Resident alternate adapter, also called directly by the special fast group |

Each public routine has its own source file. The root calls
`pcm_spark_publish(pcm,&published)` and runs the monitor only after completed
normal publication. Alternate success has already performed its cleanup and
returns without entering the normal monitor. A timeout returns TRAP_BOUNDARY
before SWI; this does not implement the target trap handler or its stack/frame
recovery. Optional 180F/1812 modules remain explicit dependencies.

| Factory location | C state/interface | Meaning established by the resident code |
|---|---|---|
| 0044.3 | Existing `spark.first_reference` | Gates counter monitoring/alternate sampling; handoff clears it |
| 0050.2 | Existing `reference.consumed` | Enables one monitor observation; successful monitor exits clear it |
| 0044.6 | `spark.bypass_qualified` | Prior acceptable-delta observation |
| 0044.7 | `spark.bypass_fault_latched` | Retained counter-count fault indication |
| 0019.5 | `spark.est_fault` | Retained diagnostic indication; this body only sets it |
| 0205,022C | `spark.bypass_baseline`, `bypass_count` | Saved counter word and wrapping observation count |
| 004F.6 | Existing `spark.startup_gain_enabled` | Same flag used by admission/startup gain, not a second copy |
| 0004.7 | `spark.bypass_supervision` | Upstream request/fault gate, producer still outside this body |
| 0044.2 | Existing `runtime.output_override` | Shared dispatcher/service state |
| 0391.3 | `spark.service_bypass` | Separate service bit from existing 0391.7 heartbeat inhibition |
| 004B.4 | Existing `spark.output_request` | Set on the request route and conditionally cleared |
| 3FCA | `PCM_EST_COUNTER` | Independent read16 counter sample |
| 3FEC,3FE4 | `PCM_EST_FEEDBACK`, `PCM_EST_HANDOFF` | One read16 followed by a write16 of the sampled word |

Names describe the software role. Counter edge meaning, feedback word semantics
and physical bypass/EST behavior still require board measurements.

## Counter observation

If first-reference is clear, skip counter work and enter the request route.
If first-reference is set but consumed is clear, only clear consumed and return;
retain the request, baseline, counter and all latches.

With both set, sample 3FCA. If 5B03.5 is clear, enable startup gain, zero 022C,
save the sample to 0205 and perform the handoff. This option route precedes the
fault-latch check. Otherwise, an already enabled 004F.6 goes directly to handoff
without resetting the count or saving the current counter baseline. Next, an
existing 0044.7 sets 0019.5 and exits through consumed cleanup.

For the remaining observation, form `delta=u16(sample-baseline)`. A nonzero high
byte is a failed observation regardless of its low byte. With high byte zero,
`low(delta)<=cal4E71` is acceptable, including equality:

| Observation | Prior state | Effects before consumed cleanup |
|---|---|---|
| Acceptable | Qualified clear | Set qualification and save the current baseline |
| Acceptable | Qualified set | Enable startup gain, zero count, save baseline, then handoff |
| Failed | Old count <=4E72 | Increment as a byte, clear qualification and save baseline |
| Failed | Old count >4E72 | Set 0044.7 and 0019.5; retain count, qualification, baseline and request |

The comparison uses the old count and is strictly greater. With default limit
04, an old count of 04 becomes 05; the next failed observation latches the fault.
A limit of FF allows FF to wrap to zero. An acceptable observation does not
clear the count unless it is the second qualifying observation. These fault and
qualification flags are not globally cleared by the monitor.

## Handoff and request exits

Clear first-reference before reading 3FEC. Write that sampled word to 3FE4.
The intervening F3ED is the actual RTS, so no invented delay callback is added.
Then set output-request and sample its gates in order:

| Gate | Result |
|---|---|
| Supervision set and output-override clear | Set EST fault, clear request, then consumed cleanup |
| Otherwise engine-service set and 0391.3 set | Set shared output-override, clear request, then consumed cleanup |
| Neither | Retain the newly set request, then consumed cleanup |

The supervision fault route precedes the service route. A counter fault exits
earlier and does not set or clear the request. No path in this body clears the
retained diagnostic flag. Callback fixtures verify that state is sampled after
the counter/feedback/handoff transactions rather than cached at function entry.
They do not model every instruction-level interrupt point.

## Profiles and failed prefixes

The three newly represented defaults are 5B03=BC, 4E71=00 and 4E72=04. They live
in the immutable `PcmSparkCalibration` profile, independent of the eventual
serialized calibration layout. All 1,197 fixture bytes match the stock image.

The consumed counter route requires a profile; its host configuration check
precedes the first peripheral read. Inactive/request-only routes require no
profile or hardware. Missing hardware and failed callbacks return NO_HARDWARE
at the successful prefix. A failed feedback read retains the cleared first flag,
and a failed handoff write retains the earlier startup/baseline changes. Neither
continues to request routing or consumed cleanup. Earlier timing writes from
normal publication stay committed if a later monitor transaction fails.

These statuses are source-development contracts, not new instructions in the
factory ROM. A physical backend still needs a deliberate fault disposition.

## Verification and integration limits

The complete-controller test target links the production adapter and runs the
actual stock A466 entry through normal, alternate and pre-SWI returns. It compares
mapped RAM/peripheral bytes, ordered byte/word and mask/hook events, final mask,
missing module identity and completed ROM stack balance. Earlier admission,
period and output suites alone link `tests/alternate_boundary.c` to retain their
original narrower dependency fixtures. This substitution is outside `src/`;
production has no runtime alternate/controller override.

The suite adds 468,978 comparisons: 196,608 delta/count/qualification cases,
264,192 gate/service cases, 4,772 joined/callback witnesses, 2,894 failure
prefixes and 512 history calls. All 50 monitor/cleanup instruction starts execute.
The corpus covers every 16-bit wrapped counter difference, all count/limit and
low-delta/limit byte pairs, option/startup/fault gates, request/service precedence,
changed profiles, independent word samples, selected callback changes, failure
prefixes and repeated reference/startup/monitor histories. New C contracts and
the full 160-phase kernel fixtures also exercise ordinary and special dispatcher
calls with the production task bindings absent. The source inventory is now
141 public routines: 65 implemented outlines, 41 explicit boundaries and 35
algorithms. Both host verification routes include 28 CTest entries.

This establishes the resident controller's implemented source path under its
named inputs and explicit external boundaries. Upstream acquisition, slot7's
other producers, remaining engine controllers, reset/interrupt assembly, native
ABI, linker/RAM/stack fit and physical peripheral/timing validation remain.
The [slot7 wrapper](slot7_contract.md) now connects the real scheduled CA6B
producer in its five-call order. Next are its named background-IAC and shift-lamp
bodies; C9F7 environmental precomputation belongs to slot4. Inputs retain their
factory producer cadence.

See the [output contract](spark_output_contract.md),
[admission contract](spark_admission_contract.md),
[period/RPM contract](spark_period_contract.md) and
[physical boundaries](../../docs/analysis/FACTORY_EXTERNAL_HARDWARE_BOUNDARIES.md).
