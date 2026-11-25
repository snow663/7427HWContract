# HC11 target arithmetic audit

## Scope and conclusion

Audit baseline: development commit `f2f493f4df5843d37baf23d27a460dbd7d890476`.
The same nine expressions were also inspected on main commit
`56a3145477291dd7c6bfee15db98414c983b1b2f`; all nine defects are present there.
Corrections were prepared on the separate audit branch; neither `main` nor
`work/pseudo-source-development` was modified.

**Nine source sites have confirmed 16-bit-`int` arithmetic defects.** The
existing host code preserves values above 65535 until a saturation decision;
the HC11 `-mshort` code discards those bits earlier. A 32-bit argument or
destination does not widen the expression that produced it. Consequently,
even exhaustive host-C versus ROM comparisons can pass while a real target
build computes different values.

This is a language-semantics finding supported by actual BMHM saturation
instructions, not an inference from a passing differential simulator. The
audit supplies permanent, executable tests of the actual source expressions.
They produce **nine failures on the baseline and zero on the corrections**.
No native HC11 compiler was available in this audit environment. These tests
are explicitly a **C integer-width model**, not execution of native HC11
machine code, target ABI verification, or complete function equivalence.

The production syntax survey covers **468 C/header files** in `src`,
`calibration`, `platform`, and `include`, with **714 multiplication, division,
remainder, and shift expressions**, and zero parser failures. The accompanying
`target_arithmetic_inventory.json` contains each path, source hash, expression,
source line, macros, signed narrowing conversions, and pointer/layout leads.
Its rows are an inventory, not 714 claims of behaviorally verified code. The arithmetic-only snapshot had 713;
the integrated bus-aperture correction adds one bounded size-count division.

## Reference model and independent evidence

The repository itself requests `-m6811 -mshort` and checks 16-bit `unsigned`
and 16-bit pointers in `pseudo-source/native/verify_hc11_toolchain.py:21-36`.
The [GCC M68hc1x documentation](https://gcc.gnu.org/onlinedocs/gcc-4.0.0/gcc/M68hc1x-Options.html)
defines `-mshort` as a 16-bit `int` ABI. The relevant C language rules are
integer promotions, usual arithmetic conversions, unsigned modular
arithmetic, and shift-result types; see C99 TC3 clauses 6.2.5, 6.3.1.1,
6.3.1.3, 6.3.1.8, and 6.5.7 in the
[WG14 draft](https://www.open-std.org/jtc1/sc22/wg14/www/docs/n1256.pdf).

For example, `2u * pulse` has unsigned-`int` arithmetic when `pulse` is
`uint16_t` on this target. `pulse == 32768` therefore produces zero before
being passed to `mix_word(uint32_t)`. The widening must occur on an operand:

```c
/* The parameter type is too late to preserve the lost carry. */
mix_word(2u * pulse);

/* Preserve the carry until the saturating helper decides. */
mix_word((uint32_t)2u * pulse);
```

The audit checked the actual 65536-byte BMHM image with SHA-256
`6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004`.
These byte sequences were read from that image, then checked against the
addressed assembly listing and the HC11 meaning of ASLD/carry:

| Factory address | Image bytes | Arithmetic intent |
|---|---|---|
| `$739C` | `80 1A C6 97 3D C3 00 40 05 24 03 CC FF FF` | Wrapped byte subtract 26, multiply 151, add 64, double; load FFFF on carry |
| `$7E69`, `$80F2`, `$8339`, `$83F0`, `$842F` | `05 24 03 CC FF FF` | ASLD; branch past `LDD #FFFF` only when carry is clear |
| `$8360` | `05 24 03 CC FF FF 05 24 03 CC FF FF` | Two successive saturating doublings |
| `$8609` | `05 25 03 05 24 03 CC FF FF` | Two doublings; either carry saturates |
| `$8F77` | `3D 05 25 06 05 25 03 05 24 03 CC FF FF` | Byte multiply and three doublings; any carry saturates |

This evidence establishes the saturation rule needed for the fixes. It does
not establish that every caller's admission, gain interpolation, interrupt
interleaving, or hardware output behavior is correct.

## Confirmed defects and minimal reproductions

All source locations below are relative to the repository; line numbers are
unchanged by these one-line corrections. Numeric inputs are raw internal
units. They should not be read as physical injector duration or load units.
These are local arithmetic/input-state counterexamples. The audit does not
claim that every vector is reachable under unchanged stock calibration and a
particular physical engine trajectory; that requires the retained scenario
and calibration coverage described below.

| ID | Exact source location | Small reproduction | Baseline 16-bit result | Required/fixed result | Severity |
|---|---|---|---:|---:|---|
| TA-01a | `pseudo-source/src/fuel/fuel_cpi_prepare.c:15` | `corrected_pulse=32768`, doubling path admitted | 0 | 65535 | High |
| TA-01b | `pseudo-source/src/fuel/fuel_crank_prepare.c:15` | Returned crank pulse 32768, before battery gain | 0 | 65535 | High |
| TA-01c | `pseudo-source/src/fuel/fuel_blm_scale.c:7` | `corrected_pulse=32768`, before BLM gain | 0 | 65535 | High |
| TA-01d | `pseudo-source/src/fuel/fuel_crank_pulse.c:22` | Local `value=65534`, TPS `gain=64`; rounded gain result 16384 | 0 | 65535 | High |
| TA-01e | `pseudo-source/src/fuel/fuel_baro_battery.c:10` | `corrected_pulse=65535`, `gain=64`; rounded gain result 16384 | 0 | 65535 | High |
| TA-01f | `pseudo-source/src/fuel/fuel_derivative_correction.c:16` | `corrected_pulse=65535`, bounded factor `value=128`; rounded gain result 32768 | 0 | 65535 | High |
| TA-01g | `pseudo-source/src/fuel/fuel_async_accumulate.c:8` | `period=32768`, `corrected_pulse=10000` | Denominator 0; ratio 65535 | Denominator 65535; ratio 10000 | High |
| TA-02 | `pseudo-source/src/fuel/governor_internal.h:45` | `governor_sat_shift(8192,3)` | 0 | 65535 | High |
| TA-03 | `pseudo-source/src/startup/reset_controllers.c:14` | ADC `raw=255` | MAP 14 | MAP 255 | High |

### TA-01: seven saturation expressions lose the carry

The six pulse-scaling sites multiply a 16-bit value by the `unsigned int`
literal `2u` or `4u`. On the selected target ABI the product wraps at 65536.
`mix_word` cannot detect the discarded carry. The asynchronous site has the
same failure in its divisor construction, so the error propagates through
`mix_fraction` into both quotient and retained accumulator state. A zero
input pulse with period 32768 also exposes it: the intended ratio is zero,
but the baseline passes a zero divisor and returns 65535.

The correction explicitly casts the multiplicative constant to `uint32_t`
before multiplication. It preserves the existing saturated-word contract
without altering later rounding, truncation, or saturation stages.

Affected evidence includes `compare_fuel_mixture_rom.py` for crank pulse,
`compare_fuel_feedback_rom.py` for BLM/derivative/barometric corrections,
`compare_fuel_delivery_rom.py` for crank preparation/CPI/asynchronous
accumulation, and composed fuel-controller/cycle tests that invoke them.
For example, `compare_fuel_feedback_rom.py:188` enumerates all 65536 BLM pulse
values, but executes host C. That exhaustive sweep does **not** cover target
integer promotions. The defect invalidates extrapolation of those results to
a native HC11 binary; it does not retroactively make the observed host values
incorrect.

### TA-02: governor shift temporary is only 16 bits on target

Both the left operand cast and the `wide` destination were `unsigned`.
The original `wide > 65535u` test is unreachable on a 16-bit `unsigned` ABI.
Widening both to `uint32_t` preserves overflow through the decision.

`pcm_fuel_governor_rate` uses the helper with counts 3, 2, 4 for the primary,
secondary, and auxiliary corrections; `pcm_fuel_governor_lead` uses count 2.
Affected evidence is `fuel_governor_compute_contracts` and
`compare_fuel_governor_rom.py`, including its compute/lead entry cases. The
separate `gov_product` helper already used 32-bit arithmetic and was preserved.
The new regression exercises the actual helper body for counts 0 through 4;
it does not claim meaningful behavior for arbitrary shifts above 31.

### TA-03: boot MAP accumulator cannot represent saturation

For raw 255, the intentional byte subtract yields 229. The multiply/add is
`229*151+64 == 34643`; doubling should retain 69286 until saturation selects
255. A 16-bit `unsigned` retains 3750, producing 14 after the right shift.
The same bug affects raw 0 and other wrapped subtract results. The fix makes
the accumulator and the pre-multiplication cast `uint32_t`, while preserving
the deliberate `uint8_t(raw-26)` wrap.

`compare_boot_controllers_rom.py` and composed boot tests can agree with the
factory on the host yet miss this native behavior. The resulting state seeds
MAP at logical addresses `$01C0/$01C7`, so this is broader than a cosmetic ADC
conversion discrepancy. Downstream impact needs retained boot-to-run tests.

## Executable regression package

Run from the audit checkout:

```sh
python -m pip install pycparser==3.00
python -m unittest discover -s tests/audit -p test_target_arithmetic.py -v

# Run the same tests and helper against a separate baseline checkout.
AUDIT_REPO=/absolute/path/to/baseline python -m unittest discover -s tests/audit -p test_target_arithmetic.py -v

# Compile the actual C library and execute the five relevant host contracts.
python tools/audit/verify_target_arithmetic_host.py

# Regenerate the production-file and expression census.
python tools/audit/inventory_target_arithmetic.py --out docs/audit/target_arithmetic_inventory.json
```

Observed results:

| Verification | Baseline | Corrected audit source |
|---|---:|---:|
| Source-bound target arithmetic suite | 14 tests; 9 failures, 5 passes | 14 tests; 14 passes |
| Actual host translation units with `-Wall -Wextra -Wpedantic -Werror` | 424 compiled | 424 compiled |
| Actual host C contract programs | 5 passed | 5 passed |
| Native HC11 compile/link/execute | Not run | Not run |

The main baseline also produces nine failures and five passes. Machine-readable
results for all three source snapshots are in `target_arithmetic_results.json`.

The model parses actual C with `pycparser`; it evaluates each selected
expression, actual `mix_word`/`mix_fraction`/`pcm_gain_word` helper, the actual
governor helper body, and the actual boot MAP declaration and assignments.
It is therefore source-bound: removing a correction reintroduces a failing
test. Expected values come from the saturation and rounding contract, not a
second copy of the corrected source.

The tests cover threshold neighbors, distributed 16-bit inputs, seven gain
values, all 256 boot ADC values, and preservation checks for bounded byte
rounding and the already-guarded crank doubling. Three model-conformance
tests separately check promotion order, literal types, shift widths, and
rejection of signed overflow. Unsupported syntax and signed conversions
outside the representable range raise an error. This is deliberately not a
complete C interpreter; it does not execute callbacks, aliasing, macros,
interrupts, or every path through these functions. Pcm member input types are
supplied by the tests from their declared contracts in `pcm.h`.

The host checker compiles and runs `fuel_mixture_test.c`,
`fuel_feedback_test.c`, `fuel_delivery_test.c`, `boot_controllers_test.c`, and
`fuel_governor_compute_test.c`. Those unchanged host passes are useful
regression evidence and also demonstrate the blind spot: host success alone
does not establish 16-bit target compatibility.

## Review of the remaining arithmetic and ABI risks

### Reviewed cases preserved intentionally

| Category | Reviewed examples | Finding |
|---|---|---|
| Rounded byte products | `mixture_internal.h:12`, `math/lookup16.c:8`, `math/lookup2d.c:5`, `idle/iac_cold.c:4` | The explicit `uint16_t` operand selects unsigned 16-bit arithmetic on HC11. The maximum, `255*255+128`, is 65153, so the intermediate fits. |
| Word scaling that needs more than 16 bits | `math/gain_word.c:5`, `fuel/fuel_base.c:4-22`, `fuel/fuel_base_publish.c:6-24`, `spark/spark_load.c:4-21` | These already cast before multiplication/left-shift or use guarded divisions. No width defect established in the reviewed expressions. |
| Deliberate word wrap | `sensors/vss_calculate.c:12`, `fuel/fuel_finalize.c:19-21`, `spark/spark_rpm_filters.c:13` | Casts preserve factory-width operations. Widening the final result or changing a wrap into saturation would change behavior. |
| Guard before doubling/quadrupling | `fuel/fuel_crank_pulse.c:17-18`, `idle/iac_follower.c:4`, `fuel/fuel_governor_vss_gate.c:22/44` | A threshold test prevents overflow before the multiply. These were not changed. |
| Byte-to-high-word shifts | `idle/iac_drive_limit.c:9-12`, `idle/iac_seed_cells.c:11-15`, `idle/iac_cold.c:38-40` | The shifted locals are `uint16_t`, not bare `uint8_t`; target promotions therefore stay unsigned 16-bit. Apparent signed-shift concerns do not apply. |
| Other byte shifts | ADC mux, interpolation fractions, reference age, diagnostic bits | Reviewed shifts are at most 4 positions and fit signed 16-bit values before the explicit byte truncation. |
| Byte sums in `unsigned` | Governor finish, BLM learning, oxygen bands, purge multiplier | Their reviewed ranges are at most 510 or similarly bounded values; 16-bit `unsigned` is sufficient. |
| Acceleration reservoir | `fuel/fuel_acceleration_reservoir.c:8-21` | The `unsigned value` is capped to 255 before its byte gain; the product fits 16 bits and the final reservoir addition intentionally wraps. |
| Signed filters | `math/lag8.c:6-8`, `math/lag16.c:6-11`, `service/diagnostic_internal.h:11-13` | Explicit `int32_t` intermediates preserve range. Lag8 explicitly floors negative division; lag16 shifts an unsigned difference before applying the signed correction. No negative signed right shift was found in these paths. |

The census also includes transmission, diagnostics, serial, and platform
expressions. The review prioritized engine/fuel/spark/idle/startup; it does
not replace subsystem dynamic coverage or claim every calibration combination
was enumerated.

### Strongly supported portability concern, not a confirmed HC11 failure

`pseudo-source/src/fuel/fuel_governor_lead.c:35` uses
`(int8_t)derivative <= 0`. Converting a byte above 127 to a signed 8-bit value is
implementation-defined in C99. A normal two's-complement GCC implementation
produces the intended signed test, so this audit does **not** label it a
confirmed wrong-HC11-value defect. It can be made independent of that
implementation choice using `derivative == 0 || (derivative & 0x80u)`.
Confirm the factory branch and add native byte-domain execution before
changing it. No silent correction was made.

### Pointer, layout, endianness, and volatile-state boundaries

The design mostly avoids native structure overlays on factory addresses.
`PcmPlatform` explicitly assigns logical RAM ownership to callbacks
(`include/pcm.h:47-59`). Word assembly and stores use shifts/high/low bytes:
`platform/hc11_native_mmio.c:21-29,48-54`, serial ownership helpers, and
`system/fuel_ram_owner_read8.c`/`write8.c`. This avoids assuming that a host
pointer layout or host endian order matches the factory image. The MMIO
primitive rejects a word beginning at `$FFFF` and otherwise accesses the high
byte before the low byte.

That source organization is useful evidence, but not native validation.
Outstanding requirements include the actual compiler's function-pointer
representation, enum/bool size, alignment and structure layout, memory-model
and linker placement, stack consumption, library helper routines, and
the compatibility of C/assembly call and interrupt frames. The native probe
creates `sizeof` symbols but currently asks reviewers to inspect their values;
host `sizeof(Pcm)` is not a substitute. `Pcm` and calibration structures must
fit the specifically verified target memory map and execution model.

`volatile uint16_t` fields also do not prove atomicity on an 8-bit target.
An interrupt may run between byte accesses unless the target instruction
sequence and masking discipline establish the needed guarantee. The widened
arithmetic fixes preserve values; they do not close torn-state, device-latch,
read-order, or interrupt-interleaving questions. No existing missing hardware
behavior was replaced by an invented default in this audit.

## Staged follow-up

1. Keep the nine corrections and source-bound regressions on the isolated
   audit branch. Run the regression package against both the pinned baseline
   and proposed source. Do not promote a semantic-model pass to a native pass.
2. Establish a reproducible real MC68HC11 `-mshort` compiler toolchain, pin its
   exact version and runtime libraries, run the repository's all-source ABI
   probe, and archive object/ELF/disassembly/link-map identities. Add build-time
   type-width and layout assertions for the actual ABI boundary.
3. Compile the same minimal vectors as a native HC11 test image. Execute it
   on the independently instruction-validated emulator and, later, hardware.
   Compare actual memory result records with the mathematical expected values.
   The C-width model is a useful additional guard, not the native oracle.
4. Rerun the affected ROM/C suites after CPU-core corrections; then rerun
   with the reconstructed target BIN. Include calibration extremes, the
   recorded overflow neighbors, and persistent CPI/async state sequences.
5. Exercise boot MAP through boot-to-run transitions and injector/governor
   outputs. Add interrupt injection at relevant state loads/stores. Use
   separate state mapping for equivalent logical variables; do not equate
   physical C layout with factory RAM addresses.

After these corrections, confidence is stronger that these particular
saturation operations preserve target values. Confidence in whole-firmware
native execution remains unestablished until those compile/link/execute and
retained-state gates have actual evidence.
