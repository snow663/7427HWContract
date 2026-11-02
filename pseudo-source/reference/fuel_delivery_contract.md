# Cut/decel, enrichment reservoirs and connected fuel delivery

This batch adds16 public routines. The source now has261 routines:122 implemented
outlines,108 implemented algorithms and31 dependency boundaries. Each public
routine has its own file. The admitted calculation at7E4F now has a connected
C path through synchronous/asynchronous injector-command publication at852B.
The broad7D4B ignition/input prefix and852C scheduling tail remain separate.

## Entries and stops

| Stock scope | C entry | Behavior |
| --- | --- | --- |
| 8058..810B | `pcm_fuel_cut_gate` | Qualification, hard cut and old-count delay; reports reduction route |
| 810C..8174 | `pcm_fuel_acceleration_reservoir` | Transition/AC/TPS additions, reservoir wrap and activity holds |
| 8175..824C | `pcm_fuel_decel_gate` | Decel permission, recovery/reload and phase-gated delay |
| 821D..823A | `pcm_fuel_reduction` | Decel flags, timer reload and reduction-factor scaling |
| 824D..82EC | `pcm_fuel_enleanment` | Rounded history drops, gain calculation and reservoir/PW scaling |
| 8058..82EC | `pcm_fuel_cut_decel` | Conditional contiguous cut/AE/decel body |
| 83C4..83FA | `pcm_fuel_cpi_prepare` | Literal SEI/CLI counter update and conditional PW doubling |
| 842C..8468 | `pcm_fuel_async_accumulate` | Live period sample, /80 quotient/fraction and24-bit accumulation |
| 8476..84A8 or84B6..84BB | `pcm_fuel_packet_select` | Wrapped total, ordered limits and reservoir debit |
| 84A9..84B5 | `pcm_fuel_packet_emit` | Masked existing8548 transaction and completed-emission flags |
| 8476..84BB | `pcm_fuel_packet` | Select and conditionally emit a packet |
| 83B1..8475 | `pcm_fuel_route` | Inhibit/CPI/TBI routing and async zero-write/accumulation prefix |
| 83B1..852B | `pcm_fuel_deliver` | Packet accounting followed by the existing finalizer |
| 7EB2..83B0 | `pcm_fuel_construct` | AE, VE/base, EGR/BLM, cut/decel and post-corrections |
| 7EB2..852B | `pcm_fuel_running` | Admitted running calculation through publication |
| 7E4F..852B | `pcm_fuel_calculate` | Existing crank/authorization admission followed by running work |

The boolean gate outputs represent actual branch successors, not added RAM flags.
The packet-selector output captures the D-register word passed to the emitter.
CPI and routing entries assume D carries the current PW at entry; the C interface
uses `corrected_pulse`. The qualifying CPI path reloads PW after CLI, as the ROM
does. The running and general calculation wrappers preserve the full intervening
stages; they do not jump over the cut/decel/reservoir body.

## State and source profiles

Existing TPS/MAP histories, AE terms, PE, IAC enrichment087F, VSS, RPM, primary
faults, transmission inhibit flags and REF packet/latch owners are reused.
New fields own0053.3/0053.1,0046.4/0046.0,003D.6/.7,0041.3, qualification/cut/hold
counters, reduction/decel timers, reservoir023A and throttle drop082B.
The accumulator has one high byte0259 and one fractional word025A/025B.
Word0259 operations update the high byte and the fraction's high byte while
preserving025B. Quotient025C/025D and rounded remainder025E remain explicit.

The immutable delivery profile contains85 distinct stock bytes. Its decel
threshold caps RPM before subtracting32. The9-knot stock view includes the next
startup curve's first byte at4C9D; the enleanment load view likewise retains its
zero-weight neighbor at4B2B. The full TPS-drop curve includes its last neighbor
at4B3B. All source views, overlapping entries and17 expanded fixture bytes are
checked against the SHA256-verified BMHM image.

## Cut, recovery and enleanment

Qualification preserves its previous latch when a gate skips evaluation. Hard
cut uses the prior cut flag and fault-adjusted thresholds. The speed/RPM delay
compares the old counter; incrementing to its limit does not cut on that call.
The hard-cut zero is a local stage result: later signed/AE additions still run.

Transition, AC and TPS enrichment additions saturate as bytes. An early overflow
skips the later additions/cache updates. The reservoir addition then wraps as a
word. MAP activity can reload holds without adding a TPS reservoir term.
Inactive activity clears only its own flag; the fuel-activity hold clears on a
call finding its old count already zero.

Decel recovery adds fuel only when its active timer was nonzero. A carry selects
7FFF, notFFFF. The TPS reset skips that addition. Load-triggered reload and the
ordinary delay route both age a nonzero active timer. Delay decrements use
`phase & 0E == 0`; they do not compare the complete phase byte. Direct reduction
entries preserve the earlier branch priority and skip ordinary enleanment.

Ordinary enleanment first clears the DFCO flag and restores factorFF. Rounded
history bytes saturate before subtraction. TPS/load threshold tests retain the
stock latch bypass and strict comparisons. Curve addition saturates before the
three-shift gain; the optional slow-speed product rounds separately. The byte
negation creates the multiplier; zero takes the inactive exit. Reservoir and PW
use the same rounded multiplier through their separate stores.

## Routing, accumulation and packet publication

The inhibit route stores a local zero and enters finalization. An existing async
route can still bypass a synchronous write. CPI's count saturates at255 under a
literal SEI/CLI pair; its qualifying path latches the existing REF flags before
reloading/doubling PW. TBI uses the previous async-route bit to select its word
threshold and load/RPM pair. Synchronous selection clears word0259 while retaining
025B, then optionally services an already pending packet.

Asynchronous selection writes zero to3FCE, preserves the nominal11-cycle
JSR/RTS gap through the delay backend, then samples3FC0 once. The bounded double,
FDIV, integer division by80 and rounded fraction reproduce the stock increment.
The low accumulator word is stored before the high carry byte. No floating-point
or saturating24-bit replacement is used.

Packet totals wrap at16 bits. Maximum is tested before minimum, including
contradictory supplied limits. A maximum packet borrows from the reservoir only
when its accumulator subtraction borrows. Selection commits these debits before
SEI. The packet word is captured before the mask callback; offset and helper
inputs retain their own consuming positions. Emission calls the existing8548
helper, then CLI, then sets/clears the completion flags. A failure preserves the
completed RAM/bus prefix and literal IRQ mask. A suppressed packet retains its
fraction/reservoir and updates only the specified flags.

Callback witnesses change state at the zero write,11-cycle gap, live-period read,
and both mask assignments. Repeated delivery and REF joins exercise retained
fractions, packet remainder, fresh post-CLI PW loads and finalizer routing.

## Verification and remaining integration

The suite contains665,548 C/ROM comparisons across368 reachable instruction
starts, with one defensive guard bounded as described below. It includes1,343
selected failure prefixes,1,024 retained-history calls and85 distinct profile
bytes (86 read-view entries) plus17 expanded curve bytes.
The ROM suite checks the new ranges, complete construction/delivery and7E4F
crank/running joins, configuration errors, typed transactions, failed prefixes
and retained histories. One instruction at844F is excluded from execution
coverage with an explicit arithmetic bound: division by80 leaves remainder0..79,
whose rounded fraction cannot carry. The defensive increment remains in C.

Both host routes contain50 checks:25 quick contracts/provenance checks and25 ROM
suites. These establish source-level calculations and command ordering. The
7D4B ignition/input/governor prefix,852C scheduled tail, required EGR producers,
remaining slow-slot admissions/initialization and target backend remain work.
The kernel's broad fuel task is still an explicit dependency until those callers
are complete. Target ABI, interrupt timing, bus coherency and delivered fuel are
separate validation obligations.

Publish after local checks, report GitHub CI as pending, and check the completed
results before a later merge. Do not wait for Actions in the implementation turn.
