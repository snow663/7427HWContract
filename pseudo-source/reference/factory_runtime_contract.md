# Recurring factory-test contract

This group implements stock BMHM FA5B..FBD6's resident qualification, command
selection, upload and output behavior. Image authority remains SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
The existing [factory protocol analysis](../../docs/analysis/FACTORY_SERVICE_AND_TEST.md)
remains the descriptor and output-row evidence.

| C entry | Source | Behavior |
|---|---|---|
| `pcm_factory_cycle` |FA5B..FBD6|Entry precondition; two ADC qualifications; CLI/COP; captured ID routing; wait/trap boundary.|
| `pcm_factory_call` |FA9F..FAA6|Arm0001.0, capture full word038E/038F and dispatch through `call_address`.|
| `pcm_factory_upload` |FAAD..FAC6|Disarm0001.0, capture destination, copy32 live bytes and complement the live final ID.|
| `pcm_factory_outputs` |FACA..FBD6|Captured-ID admission, literal phase/coil/row logic, delayed output writes and actual serial-start join.|

`PCM_FACTORY_ENTRY` is a required platform precondition binding. A target must
abandon the interrupted factory frame and establish SP=03FF **before** entering
the C body. Returning success from this binding only verifies that precondition;
it must not reset SP inside an active C frame. Ordinary timer processing still
returns `PCM_FACTORY_BOUNDARY` at the FA5B transfer. The host join fixture then
enters the verified factory body explicitly.

Failed qualification returns `PCM_TRAP_BOUNDARY` at FA82 before executing SWI.
The actual bytes require channel1 in **40..99 decimal**, then channel3>26.
The inherited HAC40-hex lower-bound annotation is incorrect. ADC timeout retains
its flags and still consumes the sample. The initial mask is an entry condition;
the successful CLI is literal, not a save/restore operation.

The body returns `PCM_FACTORY_WAIT_BOUNDARY` (appended status8) at FBD4. This
represents its nonreturning wait for the next factory timer restart. It does not
represent an RTS to the interrupted frame. Existing status values remain stable.

The factory ID is captured before heartbeat activity. ID02 bypasses heartbeat;
ID03 calls only when0001.0 was already armed. Callback invocation sets that bit
before capturing the pointer. `PcmPlatform.call_address` receives the full word,
with no invented whitelist, range or alignment test. Missing execution support
returns `PCM_NO_HARDWARE` after the actual prefix. A supplied callback may mutate
canonical state or return an explicit boundary. Its unknown machine code,
return convention and effects on stack/interrupts remain external.

Upload reads the destination once. It then reads each0390..03AF source byte
immediately before its incrementing destination write. Forward overlap therefore
changes later reads; wrap is16-bit; a short accepted payload retains the remaining
old source bytes. The post-copy COM reads the current0364 value, including any
alias effects. It is not a transactional upload or a flash-programming protocol.
Logical serial-owned addresses use their existing canonical fields; mixed words
such as038E/038F require a coherent word-width provider.

The cycling route applies only to captured ID0 and3064.7. It clamps phase>4F
to0, publishes a row only when phase is divisible by16 and preserves the literal
coil-toggle conditions. All five FBF2-based rows and the default FC01 row are
read from the recorded address space. The word3FFC merge preserves its captured
high byte and unrelated low bits across the separate delay. Cycling rows use
the existing real `pcm_serial_start(FBE0)` acknowledgment path.

Every FBD6 call keeps its own minimum11-cycle delay binding. Comparisons assert
that each modeled call/RTS interval meets that floor; they do not claim identical
native C execution timing or physical device timing. The shared CPU model gives
BSR an extra nominal cycle, while the binding retains the common minimum.

Focused verification passes **2,807 C/ROM comparisons**, covering **all152
resident instruction starts** in this new scope. FA5B's SP assignment, FA82's
SWI and FBD4's infinite branch are three explicit target boundaries. Tests cover
actual qualification thresholds/timeouts, every phase byte, all output rows,
overlapping/serial-alias/wrapped uploads, callback pointers, missing bindings,
captured-ID mutation,30 real serial-accept joins,512 timer joins,128 retained
histories and397 selected failed prefixes. Every provider, mask, delay, entry
and callback operation of representative paths is failed separately.

The fixture records logical operand width/order, including upload accesses into
the private stack-address region. Implicit HC11 push/pull traffic and final
private stack bytes are excluded; their ABI effects are not claimed equivalent.
Instruction fetch is distinguished from data. Callback code and entry checks
are supplied test bindings. Arbitrary interrupt interleavings, target entry/RTI,
physical thresholds/output timing and the full repository regression remain
separate. The latter is deferred until the requested "pull and merge" step.
