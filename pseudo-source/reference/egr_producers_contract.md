# EGR demand and fraction contract

The stock BMHM image remains the byte authority (SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`).
This group ports the remaining demand/flow bodies and joins them to the
[feedback](boot_controllers_contract.md) and [control/output](egr_control_contract.md)
bodies. It does not change a truck calibration or generate a BIN.

| C entry | Stock range | Scope |
|---|---|---|
| `pcm_egr_demand` | CF16..D03D | Ordered MAT/coolant/fault/load/TPS/RPM/VSS/vacuum/AFR gates, two surfaces, output inhibits and service override. |
| `pcm_egr_flow` | D03E..D14D | Backpressure and position branches, flow scaling/division, BARO correction and filtered fraction word. |
| Private matrix lookup | F4DE..F54F | Live header reads, wrapped row stride, lower/upper interpolation and final row interpolation. |
| Private offset entry | F4BD..F4C0 | Floor BARO minus 96 before the existing raw curve lookup. |

Demand preserves the factory gate order. A failed early gate leaves later
hysteresis bits unchanged. MAP and low TPS require a strict greater-than result;
RPM, speed and the selected vacuum/coolant limits retain their individual
equality admissions. The 006F mask24 TPS fault bypass retains the TPS hysteresis
bit. An admitted route samples the load selector at470A twice where the source
does, caps RPM at160 and applies both doubled products without replacing them
with rounded byte multiplications.

The demand byte01AE is written before optional1815. If0086.6 is set, the
platform's `call_address` callback must execute or explicitly reject that hook;
an absent callback returns `PCM_NO_HARDWARE` after retaining the published byte.
No replacement module implementation or machine calling convention is invented.
The003B.4/0393.1 service route runs after that call and writes0394 to01AE,
overriding the earlier demand and output inhibits. A failed hook prevents that
later service stage, matching ordered failure-prefix semantics.

Flow first selects the400D.5/.2 branch, preserving separate reads. Both branches
clear006E.7 before their own admission tests. Test paths may calculate a fraction
without setting that bit. Normal position flow preserves its distinct idle,
position and full-word run-timer checks; the nonlinear route uses the duty
threshold. Position, duty, demand and the resulting fraction retain separate
meanings. Both vacuum coordinate compressions preserve their exact caps.

The position route writes flow byte01B1, multiplies it by47E4, and halves the
full product with carry rounding. FDIV overflow returnsFFFF when the divisor
0232 is zero or no larger than its numerator. In particular, a zero flow byte
with a zero divisor still givesFFFF. The quotient high byte is rounded using
its low byte, with no increment beyondFF. BARO correction and the lag curve
then produce the retained fraction word01B2. The backpressure route bypasses
the flow-byte/division stage and retains its old01B0/01B1 state.

Matrix accesses remain provider transactions. The row-index/stride product wraps
to a byte before address addition; the second row uses a fresh stride read.
The lower row is interpolated first. Adjacent knots are captured as a word and
their base byte is reread before composition. Neighboring ROM backing is
retained for large coordinates rather than replaced by invented table bounds.

The logical provider binds006E.7 to `spark.egr_active`,01B2 to
`spark.egr_fraction_high`, and01B3 to `fuel.egr_fraction_low`. A single word store
updates both fraction owners before a native consumer runs. The fixture checks
the real8032 EGR/BLM fuel consumer and the realA792 spark EGR consumer using
these owners. It also checks explicit demand→feedback→control→flow→output
sequences. These are joined calls; they do not substitute for the intervening
whole-scheduler input pipeline or physical timing.

Focused verification passes **8,950 compiled-C/actual-ROM comparisons**, covering
**all 323 newly scoped instruction starts**:

| Cases | Checked behavior |
|---:|---|
| 5 | Individual entries and real fuel/spark consumption. |
| 246 | Demand equality edges, hysteresis retention and output-inhibit order. |
| 1,800 | Fresh/captured load selection, RPM caps, BARO and doubled products. |
| 512 | Flow branch priority, test/fault gates, idle and duty qualifications. |
| 30 | Linear position and full-word run-timer edges. |
| 1,024 | Every vacuum byte in both compressed coordinate paths. |
| 2 | Backpressure RPM cap and below-offset BARO floor. |
| 490 | Carry-rounded half product, FDIV zero/overflow and quotient rounding. |
| 144 | Matrix offsets, wrapped stride and live backing/stride mutation. |
| 2,560 | All shared flag bytes and fresh option/MAP/airflow reads. |
| 64 | Optional1815 publication, failures and final service priority. |
| 1,536 | Real EGR controller/output and fuel/spark consumer joins. |
| 409 | Every failed provider/mask/module operation on representative paths. |
| 128 | Retained complete EGR histories. |

The earlier EGR control suite still passes2,662 cases. Kernel/hardware contracts
and five affected historical IAC/input contract fixtures pass. The latter
retain an explicit test-only CF16 boundary to preserve their original scope;
97 focused slot9 comparisons, including historical failure prefixes, also pass.
Production code and the new EGR fixture link the real demand and flow bodies.
All332 production/calibration files compile with strict C11 warnings as errors.

The follow-up kernel witness executes a full160-phase cycle with real EGR
bodies. It observes10 demand publications,40 fraction-word publications and80
hardware command writes, with zero EGR task callbacks. The fixture binds both
byte and word views of01B2/01B3 and the006E.7 owner coherently. A real flow call
then feeds the native fuel consumer; independent native edits also read back
through the provider without overwriting the adjacent fraction byte. All eight
kernel contract groups pass, including the existing busy/catch-up and stack
recovery checks. This is a host admission/ownership witness, not target timing.

Traces compare logical operand widths, order, values, literal IRQ masks and
completed failure prefixes. Native fuel/spark consumers contribute actual state
rather than fabricated provider events. Private HC11 stack traffic is excluded.
Optional1815, complete scheduler/REF interleaving, target ABI, device timing and
the broad scheduled fuel wrapper remain separate work. Full regression, PR and
merge remain deferred until the requested "pull and merge" step.
