# EGR control and output contract

The stock BMHM image is the byte authority (SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`).
This group closes two resident controller boundaries. It preserves factory
behavior for the pseudo-source; it makes no tuning-image or EGR-delete change.

| C entry | Stock range | Scope |
|---|---|---|
| `pcm_egr_control` | D1F6..D2B1 | Inhibition, direct-duty selection, signed error, integral and proportional words, final duty. |
| `pcm_egr_output` | CDF7..CE0F | Output inhibition, running duty, stopped-engine override and literal F0xx word publication. |
| Private scaled lookup | F4B6 entry and existing interpolation body | Scale byte, adjacent-knot word and fresh base-knot byte transactions. |

The initial0070.2 inhibit clears error01BA, integral01BC, proportional01BE
and duty01AF. It does not clear the006D.3 direction flag. With400D.1 clear,
the direct route copies demand01AE to duty01AF while retaining error and both
PI words. The003B.4/0393.1 service admission bypasses the later0070.0 and
0072.5 inhibits, while the initial inhibit retains priority.

The linear route stores the absolute demand/position error and its separate
direction. A fresh zero-demand read clears the PI words and duty while retaining
that error. An empty integral is seeded through the48A9 scaled curve. The48AF
gain/error product is saved at084F before the integral update. The48B5 product
is doubled for the proportional term; overflow selects **FF00**, not FFFF.
Integral updates and final composition saturate at0000/FFFF. Only the final
command high byte reaches01AF.

Demand, error, direction, integral and saved product reads remain distinct where
the ROM rereads them. Each scaled curve samples its scale, captures neighboring
knots as one word and rereads the base knot after rounded interpolation. Large
coordinates retain their actual neighboring-ROM reads rather than being clamped
to an invented table boundary.

Output first checks0051.4. If allowed and004F.7 is set, it consumes saved duty.
Otherwise0071.7 selects FF or00. Every successful path writes one word to3FD8
with high byteF0, including inhibitedF000 and stopped-engine forcedF0FF.

The existing fast dispatcher already calls these named routines; those calls
now enter their resident bodies. Demand at CF16 and flow at D03E were ported in
the following group; see the [EGR producer contract](egr_producers_contract.md)
for joined checks and remaining boundaries. The broad scheduled fuel wrapper
remains separate work.

Focused verification passes **2,662 compiled-C/actual-ROM comparisons**:

| Cases | Checked behavior |
|---:|---|
| 4 | Individual bodies and real feedback/control/output joins. |
| 256 | Inhibit priority, service admission, direct mode and zero-demand resets. |
| 1,620 | Error direction, integral bounds and retained-state mutation. |
| 162 | Scaled lookup coordinates, live backing and proportional overflow. |
| 64 | Output gates, running duty and stopped-engine override. |
| 256 | Real ADC/timeout feedback through control and hardware command. |
| 172 | Every provider/mask failed-operation prefix on representative paths. |
| 128 | Retained feedback/control/output histories without controller task stubs. |

All90 newly scoped instruction starts inD1F6..D2B1, CDF7..CE0F and theF4B6
entry are exercised. This count excludes the already shared interpolation tail
and feedback body; those execute in the joined cases. Kernel and hardware
contracts pass, as do the shared controller-boot fixture's2,773 comparisons.
All332 production/calibration files compile with strict C11 warnings as errors.

The fixture binds shared native fields to the logical provider, following the
[controller boot contract](boot_controllers_contract.md). Traces compare ordered
logical operand widths, values and literal interrupt-mask assignments, with the
same failed-attempt semantics as the boot fixture. Private HC11 stack traffic
is excluded. No target ABI, physical peripheral timing or whole-firmware
equivalence is asserted. The full project suite, PR and merge remain deferred
until the user's requested "pull and merge" step.
