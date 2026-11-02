# Fuel acquisition and injector finalization

Authority is stock BMHM SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
This is the first implementation batch of the complete fuel milestone recorded
in [working state](../../docs/WORKING_STATE.md). It adds six public routines and
replaces the ADC feedback boundary: 186 routines now comprise 89 implemented
outlines, 64 algorithms and 33 explicit dependency boundaries.

| Scope | C routine | Current connection |
|---|---|---|
| 7B70..7B9A | `pcm_adc_feedback` | Resident fast service after the IAC step and before current control |
| F245..F25E | `pcm_adc_inputs` | Called by feedback; callable startup acquisition slice |
| C56F..C582 | `pcm_battery_input` | Callable battery acquisition; broader callers retain unfinished work |
| 8613..863C | `pcm_fuel_battery_state` | Callable fuel-tail ignition/capture slice |
| E2FB..E305 | `pcm_injector_offset` | Callable slot-F slice before its remaining phase-gated work |
| 84BC..84F4 | `pcm_fuel_finalize` | Callable running-fuel shaping and async bypass |
| 84F5..852B | `pcm_fuel_publish` | Shared shaped/crank publication entry; stops before scheduled tail852C |

## Acquisition and shared state

Feedback sets the interrupt mask, writes ADCTL=7, then waits for bit80 with no
factory timeout. It reads ADR1..ADR4 separately, accumulates the full sum, and
stores `(sum+2)>>2` at014E. This is current feedback, not an extra fuel quantity.
It then calls F245 and performs literal CLI. The existing separate IAC step still
precedes feedback, including busy reentry. Current control remains an explicit
task boundary; catch-up does not add a fast-service admission.

F245 uses the existing F25F twelve-poll conversion with ADCTL14. Timeout sets
001A.1 and003A.0 but still samples results. Publish TPS00A6 from ADR1; read ADR2
into raw MAP082E only when the freshly tested0050.0 is clear; publish O2 at01D5
from ADR3. A successful conversion clears timeout but retains the fault latch.
The F245 helper itself does not change the interrupt mask.

Battery acquisition selects mux2 outside SEI, retaining both PORTD reads, then
uses F25F with ADCTL1 under SEI. Read ADR4, perform CLI, then publish the latched
sample to0055. A failed CLI therefore retains the old0055. This acquisition does
not supply raw battery00A7, whose remaining producer stays explicit.

The8613 helper consumes that separate raw00A7. Below40 it sets0044.4 and clears
0050.0;40..89 retain both. At90 or above, an old0044.4 causes one3FCA word read
into0205, then the latch clears.400C.0 can set0050.0; its clear route retains
the existing sampling flag. Failed capture reads retain the latch and baseline.
These are the same owners used by REF and EST;0051.3 is a separate state.

## Offset and finalization

E2FB looks up raw00A7 at4B05 and publishes the byte0256. The separate0055 sample,
battery fuel multiplier and electrical voltage units are not substituted for it.
The new source profile checks the two496D/496F words,4973 byte and17 offset knots
against actual stock bytes (22 bytes). Existing4971/4979 and mode-byte ownership
remain in the shared reference profile.

84BC first loads corrected024E. With003E.4 set it publishes unshaped024C, clears
003F.7 and exits to the unported tail without modifying0250 or issuing3FCE. The
broader routing caller owns any earlier synchronous clear. This entry does not
invent that transaction.

On the synchronous route, original zero skips short-PW/minimum shaping and retains
the old003F.7 flag. Every nonzero pulse below0100 uses the4979 lookup with a
zero-floored subtraction of32 from its byte coordinate, adds the correction,
then subtracts4971. Borrow selects replacement496F and sets003F.7. Otherwise
clear003F.7, compare against minimum496D, and replace/set the flag if smaller.
This synchronous lookup has no400E.4 option gate. The existing async helper does.

84F5 stores the pre-offset pulse at024C. Zero emits zero without the offset.
For nonzero input add0256 with16-bit wrapping, then cap that wrapped result at
7FFF. Store0250 before any hardware publication attempt. Consequently FFFF+FF
becomes00FE before the comparison, rather than saturating the addition.

TBI400B.0 clear writes0250 directly to3FCE. The CPI/PFI alternative retains0250,
does not write3FCE here, and instead stores081F as four times the rounded F550
product of period005F and gain4973, saturating on either shift carry. The direct
84F5 entry supports the future main-task crank caller without reapplying the
running short-PW correction. No tail852C routine is silently skipped or claimed
implemented by these callable slices.

## Verification and remaining work

The new suite passes357,761 compiled-C/ROM comparisons, including1,265 selected
failure prefixes and1,024 retained history calls. It executes actual ROM instructions
and compares mapped
state, ordered typed bus transactions, literal mask assignments and successful
slice frame balance. Its149 scoped instruction starts include the acquisition,
offset, finalizer and existing async helper. Selected joins include the real REF
event body and the IAC-step/feedback prefix. Supplied ADC readiness and callbacks
are host bus fixtures, not a peripheral electrical model.

Coverage includes complete pulse-word sweeps, short-PW/minimum/offset boundaries,
delay overflow, battery hysteresis, ADC timeout and MAP gate changes, multi-sample
rounding, selected transaction failures and retained producer/consumer histories.
The current kernel tests use resident feedback with its old task binding absent,
including160-phase and busy/catch-up sequences. Both host routes now have42 tests:
21 quick contracts/provenance checks followed by21 ROM suites.

The7D4B fuel controller, upstream fuel producers, raw00A7 producer, broader
battery/slot-F callers, initialization and full fuel-tail integration remain
unfinished. The next batch closes air-charge/input producers and their actual
admissions. Target reset/interrupt assembly, backend, memory/ABI fit, ADC timing,
ASIC/injector response and delivered fuel remain separate validation work.
