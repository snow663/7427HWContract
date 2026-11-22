# Slow fuel producers and slot1

Stock BMHM remains byte authority (SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`).
Slot1 now calls all three resident bodies in order. A separate callable slotF
suffix preserves its actual entry after the C514/C4F5 group. The **whole slotF
root remains a dependency** until that prefix is ported and joined; the suffix
is never substituted for the preceding diagnostic work. This group changes no BIN.

| C entry | Stock scope | Behavior |
|---|---|---|
| `pcm_slot_01` | 7AAD..7AB6 | BARO acquisition→transmission BARO→nonelectronic TCC. |
| `pcm_transmission_baro` | C668..C6BA | Prioritized high/low fault substitutions or scaled/offset lag into wordAC. |
| `pcm_tcc_nonelectronic` | ADAA..AE5B | TPS/VSS windows, coolant/change/RPM qualifications, countdown and0089.5. |
| `pcm_pump_feedback` | E286..E2C7 | Pump-feedback diagnostic slice; every branch joins E2C8. |
| `pcm_fuel_slow` | E286..E561 | Pump/charge temperature/offset, then phase-qualified AE/startup/closed loop. |
| `pcm_fault_primary_reaction` | E62D..E653 | Nine-bank alternate-polarity reaction and0098.3. |
| `pcm_fault_reaction_mask` | E6BC..E6E3 | Nine-bank complement-polarity reaction, returning its actual byte. |
| `pcm_fault_injection_reaction` | E6E5..E6F4 | E756..E75E mask and0099.4. |
| `pcm_slot_0f_finish` | 7B60..7B6C | Both reaction bodies→slow fuel→0051.2 refresh. |

## BARO and TCC

High BARO/MAP substitutions precede low substitutions. Separate-BARO5D02.2
suppresses the MAP alternatives while retaining the independent BARO fault paths.
The normal path forms the wrapped word02F3*C5D07+W5D08, then filters from old
wordAC with the F436 helper's separate coefficient reads. Fallbacks write their
full words directly. Both AC accumulator bytes participate in retained joins.

ADAA returns unchanged with400F.6 clear. When enabled, the old0089.5 selects its
speed/load windows and curves. Coordinate construction shifts the product high
byte with byte wrap, preserving the source's difference from doubling the whole
word. The later curve floors its wrapped coordinate minus64. TPS direction
selects separate change thresholds; speed/coolant/RPM gates keep their individual
strict or inclusive comparisons. A timer decremented to zero still unlocks on
that call; an already-zero qualifying call locks. Fresh context/TPS reads and
the final0854 snapshot remain at their own consuming positions.

## Pump, phase and fault reactions

With5B04.2 clear, the pump slice retains its local flags and counter. When
enabled it clears001A.2 before qualification. A sticky0072.0 reasserts that
fault. Stage0072.1 uses its own running/feedback test. Initial qualification
increments/stores022A as a byte **before** comparing the count, so255 wraps to0.
Battery and feedback are separate inputs. Every route then admits charge
temperature and injector offset. Phase bit4 is sampled after both: set returns;
clear continues through AE gains, startup and closed-loop admission.

Reaction scans run bank9 down to1 and stop at the first nonzero intersection.
All four byte reads on an admitted bank occur before that test. E62D uses
`alternate & reaction & live & mask`; E6BC uses the complemented alternate byte.
E6BC returns the actual intersection byte, not a boolean. The caller updates
only0099.4. Primary reaction updates only0098.3. Their RMW operations preserve
other shared owners and use fresh reads. Generic logical mask pointers retain
16-bit addition/wrap; the tests exclude target call-stack aliases. A failed
helper leaves its C output unchanged. Null output is a host configuration error.

Refresh is set only after the suffix's last producer succeeds. No earlier failure
can mark the suffix complete. Named BARO, phase, TCC context, fuel and refresh
owners are bound coherently by the test provider. The kernel also binds BARO
sample/high/fraction byte and word views before transmission BARO consumes them.

## Focused verification

The new suite passes **22,168 compiled-C/actual-ROM comparisons**, exercising
**all 234 scoped instruction starts**:

| Cases | Checked behavior |
|---:|---|
| 12 | Entries and real slot1/suffix/controller/REF joins. |
| 512 | BARO substitution priority and partial masks. |
| 1,200 | Wrapped product/offset, retained word and fresh lag/sample reads. |
| 3,888 | TCC windows, coordinates, live context and countdown. |
| 270 | Falling/rising TPS equality, coolant and selected RPM threshold. |
| 9 | Disabled TCC retention. |
| 768 | Raw TCC profiles and live curve backing. |
| 6,912 | Pump flags, masks, counter wrap and live qualification. |
| 3,456 | Every fault bank/bit truth basis and both reaction polarities. |
| 16 | Logical mask-pointer wrap and live reaction reads. |
| 3,840 | Every slow phase, producer order and suffix refresh. |
| 720 | Slot1/suffix through real fuel calculation and REF. |
| 437 | Every provider/mask/module failure on representative paths. |
| 128 | Retained histories including both AC bytes. |

The existing complete-controller suite still passes16,493 comparisons after
sharing its fixture machinery. Eight kernel and64 hardware contracts pass.
The full-phase kernel observes10 transmission-BARO word stores and zero slot1
task callbacks. All345 production/calibration files compile with strict C11
warnings as errors. The two host runners now register78 checks.

New logical routines compare RAM/calibration/I/O widths, values, order and
completed failure prefixes. Previously checked native bodies contribute real
state and I/O, with no fabricated provider events for native field operations.
Private HC11 call-stack traffic is excluded; both AC bytes remain visible here.
IRQ assignments, supplied ADC completion and nominal delays retain their earlier
contracts. These joined calls do not establish intervening whole-scheduler input
age, physical TCC/pump behavior, target ABI or interrupt/device timing.

Next complete the C4F5 diagnostic prefix and join C514 plus the suffix into the
whole slotF root, then continue slot4's alternating producer groups. Full project
regression, PR and merge remain deferred until "pull and merge".
