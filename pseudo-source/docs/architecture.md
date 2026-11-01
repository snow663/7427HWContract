# Source structure and execution contract

The design retains the factory-style event and phase scheduling strategy while
making each logical routine independently editable. The first profile retains
the stock schedule as a reference. Selecting the final manual-transmission
feature set is a later explicit change, including every removed producer's
remaining consumers.

## Routine ownership

Each public routine has one implementation file and a declaration in its
subsystem header. The dispatcher owns busy/pending lifecycle. Phase advancement
owns phase, epoch and run-counter bookkeeping. A controller owns its working
state and publishes a command; the future actuator driver owns the transaction
sequence that consumes that command. Calibration fields are read-only inputs.

The current state names correspond to documented factory fields, but allocation
is ours. `volatile` marks fields intended to be shared across interrupt contexts;
it does not establish compound atomicity, coherent snapshots or mask protection.
Hardware entry code must preserve the real CPU frame and ABI. C return values
are source-development outcomes, not instructions replacing RTI or STOP.

## Tick and pass order

`pcm_periodic_irq()` advances the old OC3 compare, acknowledges its flag, and
sets the seen flag. Factory mode ends at an explicit boundary. Ordinary entry
opens the modeled mask and requires a stack-check binding. Fast service always
precedes the busy test. A busy arrival snapshots phase and sets one pending bit.

An owner dispatches main passes. Each pass applies the service mirror, advances
phase, recomputes the shared monitor gate under literal mask assignments,
executes the selected fast group, then selects a slow slot. The tail masks,
clears busy, optionally profiles, and consumes pending. Catch-up opens the mask
before reasserting busy. It repeats main work without another fast service.

The source preserves a place for the real tail gap and pre-busy reentry; the
host tests exercise selected busy coalescing, not every possible interrupt
boundary. The platform model supplies transactions and explicit task returns.
It does not simulate HC11 arbitration, CLI delay, stack frames or physical time.
See the [factory timing contract](../../docs/analysis/FACTORY_INTERRUPT_AND_TIMING_CLOSURE.md).

## Hardware and unfinished code

The four read/write entry points preserve transaction width. A word callback
does not assert coherent hardware readback or one indivisible physical bus
operation. The target backend must retain the documented byte order, masking
and strobes for each driver. Zero is not declared a universally inactive output.
Actuator-enable policy belongs to the real initialization/driver port.

An unfinished routine has an explicit task binding. This allows selected
scheduler testing while making missing implementations detectable. A target
build may replace the boundary wrapper with direct implementation code; there
is no requirement to retain a runtime callback table for completed routines.
Returning an error ends the host call at its current prefix. Target trap,
recovery and output dispositions remain to be specified at that failure point.

Reset CPU/board writes and output initialization now retain their stock
transaction order in C. The early reset precondition is a separate required
assembly boundary. The REF prefix now calls an implemented event body, split into
crank, running, decay, filter and individual output/timer routines. ADC sampling
requires a backend delay binding. See the
[REF event contract](../reference/ref_event_contract.md).

The remaining reset stages are coarse ownership boundaries rather than a
complete boot translation. Early boot unmasking, retained-state branches,
factory redirection,
SP assignments and trap loops must be implemented before target execution.
The stock stack guards cannot simply be copied onto a different C call graph.

The OC1 observer owns its sample baseline and pending-observation accumulator.
It reuses the REF RPM coordinate and retains both table gates and saturations.
The implemented normal-spark consumer uses literal SEI/read/clear/CLI to
consume observations. Slot8 directly calls the implemented phase-gated decay
and mux/ADC diagnostic. ADC timeout sets flags but still reaches ADR4, and
callback failures preserve the current prefix and mask. See the
[OC1 contract](../reference/oc1_knock_contract.md) and
[knock control contract](../reference/knock_control_contract.md).
Burst, low-octane learning/scaling and gain/cap production now have checked C
routines. Slot6 preserves the CB15 input dependency before the learner, which
samples the full phase after that dependency returns. The prior whole-slot6
binding is replaced by the narrower AC/switch owner. Other broad roots retain
their unfinished work; callable slices do not silently replace their remaining
callees. See the [adaptive spark contract](../reference/adaptive_spark_contract.md).
The new A700..A84D body now constructs the base/environmental composite word,
and CA6B..CB14 is a complete callable auxiliary producer. They use immutable
matrix descriptors with explicit backing lengths; table offsets/stride retain
the ROM arithmetic while out-of-bounds profiles return BAD_CONFIGURATION.
Profiles and arrays can live in ROM; descriptor pointers are not a serialized
EEPROM format. See the [spark terms contract](../reference/spark_terms_contract.md).
Idle/transient/decel corrections now extend the contiguous body through A9DF.
Idle direction uses unsigned target/RPM borrow; transient error is saved before
filter update, and recovery shares the startup01F2 word and applies its final
correction on the latch-clearing call. See the
[modifier contract](../reference/spark_modifiers_contract.md).
The A9E0..AB43 command wrapper now preserves the optional 1812 dependency,
resident override, signed upper limit, knock corrections, signed lower limit
and post-limit service edits in order. Both RAM command stores happen even
when service is inactive; they are not physical output writes. The module gate
reuses the profiling 0086.6 flag. Callback fixtures establish host state effects,
not the unknown 1812 machine ABI. See the
[command contract](../reference/spark_command_contract.md).
The A466..A5E4 prelude is now callable with an explicit normal-route output.
It preserves independent fuel/spark run states, first-reference alternate
admission, word/byte ages and literal CLI. AC51 now runs its resident body. The timeout
commits state and 3060 RMW, then returns TRAP_BOUNDARY before SWI; target trap
handling is not replaced by a normal C return. See the
[admission contract](../reference/spark_admission_contract.md).
The A5E5..A6FF normal period/RPM and adaptive timing body is now implemented.
The word-lag helper returns both its intermediate and final values; REF006A
and normal-load0068 preserve both stores. A conditional full builder joins
admission through AB43 and marks completion only after a successful normal
command. It does not publish physical EST output. See the
[period/RPM contract](../reference/spark_period_contract.md).
The output body now covers AB44..ABCA, with explicit180F argument/result
transport and four ordered peripheral writes. The two rolling reads and both
correction samples stay separate; the second correction is latched before the
3FE6 write. The alternate body shares the pure coordinate helper while retaining
normal filter state. See the [output contract](../reference/spark_output_contract.md).
The ABCB monitor now retains counter qualification, fault latches and the ordered
3FEC→3FE4 handoff. The resident spark/alternate adapters call implemented code
directly from the dispatcher. Their old task IDs remain reserved but are unused
by production. Earlier slice suites alone substitute the alternate adapter at
link time; the new full-controller and kernel tests use the real code. See the
[controller contract](../reference/spark_controller_contract.md).

Slot7 now calls C514 output construction and F5DC signature probing before the
explicit9E99 background-IAC dependency, then the real CA6B producer and explicit
ACA7 shift-lamp dependency. The old whole-slot7 task ID remains reserved.
A matching1800 signature calls the180C dependency independently of0086.6; the
same pass's profiling tail sees any resulting flag change. The raw gear-index
profile has explicit backing, independent of target placement. See the
[slot7 contract](../reference/slot7_contract.md).

## Freedom to change algorithms

Fuel calculation, injector scheduling, spark calculation, spark scheduling and
idle control will have independent interfaces and files. The first base-fuel
function is a pure integer calculation with explicit inputs/outputs. Larger
factory task roots currently remain boundaries until their internal routines
are separated and implemented. No claim is made that one broad factory task
root corresponds to only one final algorithm file.

Source calibration definitions are independent from placement. A serialized
calibration format will define version, widths, byte order, scaling, lengths
and integrity checks explicitly; a host compiler's native struct layout will
not be treated as that storage format.
