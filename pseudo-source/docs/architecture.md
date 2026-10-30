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
The future normal-spark consumer must preserve the factory atomic read/clear
ownership when consuming those observations. See the
[OC1 contract](../reference/oc1_knock_contract.md).

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
