# Independent HC11 execution audit

## Scope and result

The original reference CPU is not a sufficiently trustworthy equivalence oracle without correction. This audit found reproducible defects in preserved condition codes, legal prebyte decoding, interrupt admission, reset state, operand read side effects, and aggregate instruction clocks. The fixes are isolated to the audit branch and accompanied by tests that fail against the pinned development baseline.

The baseline is `f2f493f4df5843d37baf23d27a460dbd7d890476` (`work/pseudo-source-development`). The legacy `hac31_romsim/romsim/hc11_core.py` file is identical in `main` at `56a3145477291dd7c6bfee15db98414c983b1b2f`, so its source defects apply to both inspected branches. The newer `7427_simulator/sim7427/cpu.py` is present only on development. This document uses **legacy** and **newer** to distinguish those implementations.

The corrected legacy implementation covers 304 of 307 normal-mode instruction encodings in the independent catalogue. `DAA`, `BRN`, and `STOP` remain explicitly unsupported. The newer implementation covers 35 encodings and has no reviewed clock accounting. A passing instruction suite improves confidence in the implemented architectural semantics; it is not a certification of all HC11 hardware behavior or firmware equivalence.

## Authority and independence

The authority is the [Motorola/Freescale M68HC11 Reference Manual, revision 6.1](https://www.nxp.com/docs/en/reference-manual/M68HC11RM.pdf), especially Appendix A, §5.3.1.1, §5.5, §5.7.2, and §5.9.3. The [M68HC11E Programming Reference Guide, revision 2.1](https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf), Table 1, supplies a second presentation of the encoding/CCR tables and the explicit `12 + n + 2` WAI clock split. Page numbers below are printed document pages.

`tests/audit/hc11_isa_spec.py` is a manually transcribed test catalogue. Neither production CPU imports it. `tests/audit/test_hc11_isa.py` uses a flat, separately implemented 64 KiB memory and a mathematical state oracle that does not import the production flag or addressing helpers. Signed overflow is checked by whether the signed mathematical result lies in range, rather than by reusing either CPU's bitwise overflow expression. Minimal literal expected-state cases supplement the general oracle.

The test catalogue includes all four opcode pages, including illegal slots. Special-test-mode `$00 TEST` is not counted as a normal-mode instruction. `hc11_opcode_matrix.json` and `hc11_opcode_matrix_baseline.json` each contain 1,024 rows: page 0 plus pages `$18`, `$1A`, and `$CD`, with normal-mode legality, implemented status, preserved/modified CCR bits, addressing mode, byte count, manual page, and cycle probes. A prebyte selector is distinguished from a complete instruction.

## Confirmed defects and reproductions

Locations in the following table are **baseline locations**, so they remain stable when the fixes shift lines. `L` means `hac31_romsim/romsim/hc11_core.py`; `N` means `7427_simulator/sim7427/cpu.py`. All examples use flat memory and one instruction unless a sequence is shown. Hex values are prefixed with `$`.

| ID / priority | Baseline location | Confirmed failure and smallest counterexample | Correction / permanent test |
|---|---|---|---|
| CPU-01 / P1 | L:904–922 | `$08 INX`, `$09 DEX`, `$18 08 INY`, `$18 09 DEY` call a helper that changes N. Only Z may change. `INX`, X=`$7FFF`, CCR=`$00` produces X=`$8000`, CCR=`$08`; expected CCR=`$00`. `DEX`, X=`$8000`, CCR=`$08` incorrectly clears N. RM pp. 540–541, 547–548. | Update register modulo 65536 and Z only. Per-encoding tests plus `test_all_ccr_values_index_and_stack_transfers` check every initial CCR and sign/wrap boundaries. |
| CPU-02 / P1 | L:1062–1071 | `$30 TSX` and `$18 30 TSY` incorrectly change N/Z. `TSX`, SP=`$7FFF`, CCR=`$00` yields CCR=`$08`; expected unchanged `$00`. RM pp. 594–595. | Copy SP+1 with 16-bit wrap and no CCR helper. Literal, all-CCR, and generated tests. |
| CPU-03 / P1 | L:815–820; N:181–191 | Indexed `$1C/$1D` and `$18 1C/$18 1D` BSET/BCLR in legacy leave NZV unchanged; newer direct `$14/$15` and indexed-X `$1D` do likewise. `1C 00 01`, X=`$2000`, M[$2000]=0, CCR=`$04` leaves Z set after writing 1; expected NZV=000. `1D 00 01` with memory=1/CCR=0 must set Z after clearing. C/H/I/X/S must be preserved. RM pp. 503, 522. | Derive NZ from the byte written, clear V. All implemented forms receive independent vectors; a conditional branch can expose the difference immediately. |
| CPU-04 / P1 | L:1217–1223, 1253–1259, 1291–1301 | `$4D/$5D/$6D/$7D/$18 6D` TST and `$4F/$5F/$6F/$7F/$18 6F` CLR fail to clear C. `TSTA`, A=1, CCR=1 leaves CCR 1; expected 0. `CLRA`, CCR=1 leaves 5; expected 4. RM pp. 529, 593. | Explicit C clear in every form. The generic oracle checks both result and all unaffected CCR bits; literal reproductions show the failure without C/ROM infrastructure. |
| CPU-05 / P1 | L:894–898,1137–1145; N:230–236 | `$06 TAP` and `$3B RTI` allow X to change from 0 to 1 through software. `TAP`, A=`$40`, CCR=0 produces `$40`; expected 0. For RTI, current X=0 with stacked CCR=`$40` similarly cannot set X. RM pp. 572, 589. | Software restoration uses old-X AND restored-X. Reset and accepted XIRQ retain their distinct authority to set X. All encodings and explicit interrupt round trips tested. |
| CPU-06 / P1 | L:779–789; generic groups at 1336–1573 | Prebytes act as generic modifiers in multiple groups. 318 undocumented prefixed encodings execute. `18 86 01` is accepted as LDAA immediate although `$18 86` is not a legal HC11 encoding. | Validate the selected page before operand side effects. Exhaustive illegal-slot test fails against the baseline in 318 separate subtests. Corrected core rejects all those encodings explicitly. Hardware illegal-opcode vector entry remains unimplemented, as discussed below. |
| CPU-07 / P2 | L:827,1268–1310,1374–1573 | 135 implemented encodings have an incorrect returned clock count, elapsed clock count, or both (including WAI's pre-wait phase). Examples: `B6 20 00` LDAA extended costs 2 instead of 4; `8B 01` ADDA immediate ticks 2 but returns 4; direct JSR (`$9D`) costs 6 instead of 5; BSR (`$8D`) costs 7 instead of 6; Y-indexed BSET costs 7 instead of 8; X-indexed BRSET costs 8 instead of 7. Appendix A per-mode tables. | Correct per-mode/prefix counts and return/tick agreement. Every implemented legacy encoding has cycle assertions. Matrix records every baseline mismatch. This does not establish cycle-by-cycle bus timing. |
| CPU-08 / P1 | L:469–488; N:110–126 | XIRQ admission incorrectly depends on caller `maskable`/I, without always enforcing X. X=1 plus `interrupt($FFF4, maskable=False)` is accepted instead of rejected. I=1/X=0 with default maskable flag is rejected instead of accepted. Legacy also omits setting X on accepted XIRQ entry. RM §5.5 pp. 176–178. | Use X for XIRQ admission, independent of I; stack old CCR and then set I/X. Tests enumerate I/X combinations, stack byte order, wrap, and RTI. |
| CPU-09 / P1 | N:31,49–52 | Newer reset CCR is `$50`, omitting S. Reset must set S, X, and I; other initial register values are not assumed specified. RM §5.3.1.1 p. 162. | Include S in reset state. `test_reset_sets_s_x_i_and_fetches_big_endian_vector` requires only the defined mask bits and vector byte order. |
| CPU-10 / P2 | L:481–488,1165–1178 | WAI charges 14 clocks before waiting, then the interrupt charges another 12 despite the pre-stacked frame. With zero explicit idle ticks that totals 26; the reference guide specifies 12 before waiting plus 2 vector-fetch clocks, total 14+n. | Charge 12 at WAI and 2 on wake; ordinary hardware entry remains 12. Test includes seven explicit idle clocks, verifies total 21 before RTI, unchanged CCR before wake, and one frame only. |
| CPU-11 / P1 | L:894–898,944–948,469–488; N:138–139, 110–126 | After CLI or TAP changes I from 1 to 0, a pending maskable IRQ is admitted before the following instruction. `CLI; SEI; BRA loop` can incorrectly be interrupted. This is functional interleaving, not a cycle-accuracy issue. RM §5.7.2 p. 192 and CLI p. 528. | Track the one-following-instruction inhibit state on actual 1→0 transitions. Tests cover CLI/NOP, CLI/SEI, CLI/WAI, TAP, immediate post-RTI admission, already-clear I, and XIRQ bypass. State is reset on CPU reset. |
| CPU-12 / P1 | N:173–180 | Newer CLR extended `$7F` and indexed `$6F` write without the preceding operand read. A read-sensitive peripheral flag therefore stays pending. RM §5.9.3 p. 196 explicitly discusses CLR's read completing an SCI status-clear sequence. Appendix A p. 529 shows the read before write. | Read the effective address before writing zero. `test_clr_reads_operand_before_write_for_peripheral_side_effects` observes read→write and a side-effect flag for both forms in both cores. Legacy already had the read. |

The simulator coordinator also had a masked FIFO-head interrupt blocking an eligible XIRQ queued behind it. That is a separate coordinator defect, fixed and tested by the parent audit work in `hac31_romsim/romsim/simulator.py`; it must not be conflated with CPU-08. Full hardware arbitration and HPRIO behavior remain outside the demonstrated coverage.

Two pre-existing newer-simulator test fixtures were corrected: `7427_simulator/tests/test_core.py:25` expected PC `$710B` although the byte sequence loops at `$710D`; line 62 assigned 11 bytes to a 10-byte image slice, growing the image to 65,537 bytes before IRQ execution. The old suite did not pass as committed. These are fixture corrections, not evidence of CPU accuracy by themselves.

A third fixture expectation became visible once IRQ deferral was implemented: the IRQ-frame test requested entry immediately after `LDS; CLI`. The parent audit corrects it to require rejection at that boundary, execute the following NOP, then accept IRQ and return to `$7005`. That change tests the documented admission rule rather than preserving the previous simulator's behavior.

## Reproduction and verification record

From the corrected audit checkout:

```sh
python tests/audit/test_hc11_isa.py
AUDIT_REPO=/path/to/pinned-f2f493f4-checkout python tests/audit/test_hc11_isa.py
```

`--repo /path/to/checkout` is equivalent to `AUDIT_REPO`. The baseline checkout is read only; the tests/oracle always come from the audit checkout. For a small standalone failure:

```sh
AUDIT_REPO=/path/to/pinned-f2f493f4-checkout python tests/audit/test_hc11_isa.py \
  ISAConformance.test_literal_minimal_flag_reproductions
python tests/audit/test_hc11_isa.py \
  ISAConformance.test_literal_minimal_flag_reproductions
```

The final suite has **357 methods**. The corrected implementation passes all 357. The pinned baseline fails **493 assertions/subtests**; that count is not 493 independent defect classes. The individual known failures are grouped above. `hc11_validation_results.json` stores exact commands, source hashes, result counts, and the failed test names.

There are **676 end-to-end boundary vectors for each of 304 legacy and 35 newer implemented encodings**, including values from both 8-bit and 16-bit boundary sets, both accumulator byte sources, varying X/Y/SP sources, all four initial CCR patterns, and direct/indexed/extended/prefixed forms. That is 229,164 generated instruction vectors. Arithmetic helpers additionally cover every 8-bit operand pair, carry/borrow input, and two initial preserved-flag patterns: 524,288 calls. The suite also checks all 256 initial CCRs for index/stack transfers; all implemented branch predicates over signed-offset and PC-wrap cases; unsigned index offsets; word wrapping; JSR/RTS fetch and SP wrap; interrupt frames; WAI; reset; and IRQ interleaving.

These are bounded architectural tests. They do not exhaust all 16-bit operand pairs, all instruction sequences, all memory/device states, or asynchronous event schedules. Defined divide results and flags are tested; the remainder after zero division or FDIV overflow is deliberately excluded because the manual leaves it indeterminate. A deterministic simulator value for that remainder is not hardware evidence.

The existing legacy suite passed 21 methods, including both optional stock-ROM tests with `HAC31_BMHM_BIN` supplied, after the first CPU corrections. The newer suite initially passed 8 methods after its first two fixture corrections; implementing IRQ deferral then exposed the third invalid fixture expectation described above. Final existing-suite and C/ROM rerun results belong to the main audit's integration record; no final integration result is inferred from these instruction tests alone.

## Which ROM comparisons are exposed?

All 53 `pseudo-source/tests/compare*.py` suites have an import or literal `exec`-include dependency on the legacy CPU. `tools/audit/inventory_hc11_exposure.py` records each dependency chain in `hc11_rom_exposure.json`. It also maps corrected opcode families to the committed 14,523-row rooted instruction map:

The affected-consumer distinction for each defect is explicit below. A dependency
means the suite belongs in the corrected-reference regression run; it does not
assert that every suite executes the faulty operation or produces a different
selected output. The evidence JSON names all 53 consumers and their import chains.

| Defect | Existing consumers requiring revalidation | Observed or bounded exposure |
|---|---|---|
| CPU-01 | All 53 legacy-core C/ROM suites | 95 static index-operation sites; per-suite dynamic exposure not established here. |
| CPU-02 | All 53 legacy-core C/ROM suites | `compare_rom.py` actually executes affected TSX sites; other suites have dependency/static evidence only. |
| CPU-03 | All 53 legacy-core C/ROM suites; newer-core simulator tests for its affected forms | `compare_hardware_rom.py` actually executes affected indexed-bit sites. |
| CPU-04 | All 53 legacy-core C/ROM suites | `compare_rom.py` actually executes affected TST/CLR sites. |
| CPU-05 | All 53 legacy-core C/ROM suites; newer-core RTI tests | 18 static TAP/RTI sites; a wrong X transition in each suite is not established. |
| CPU-06 | All 53 legacy-core C/ROM suites as decoder consumers | No illegal encoding appears in the committed rooted map. Failures are independently reproduced invalid-encoding cases, not observed factory paths. |
| CPU-07 | All 53 legacy-core C/ROM suites | 4,857 static sites use encodings with baseline clock discrepancies; device/output impact depends on the suite's time model. |
| CPU-08 | Legacy/newer interrupt consumers; all 53 suites for reference regression | XIRQ admission/frame defects are directly reproduced; per-suite factory XIRQ execution was not established. |
| CPU-09 | Newer-core reset and simulator tests | No existing factory comparison suite uses this newer core. |
| CPU-10 | Legacy WAI/interrupt consumers; all 53 suites for reference regression | Pre-stacked wake timing is directly reproduced; factory WAI exposure was not established. |
| CPU-11 | Legacy/newer interrupt consumers; all 53 suites for reference regression | 39 static CLI/TAP sites. The integration rerun exposed `compare_knock_rom.py` consuming a rejected post-CLI request; its corrected boundary witness explicitly checks rejection at AA89 and admission at AA8D. |
| CPU-12 | Newer-core CLR/device tests | No existing factory comparison suite uses this newer core; legacy already performs the operand read. |

| Defect family | Static instruction sites |
|---|---:|
| INX/DEX/INY/DEY N preservation | 95 |
| TSX/TSY CCR preservation | 37 |
| Indexed BSET/BCLR NZV | 24 |
| TST/CLR C clear | 495 |
| TAP/RTI software X restriction | 18 |
| CLI/TAP interrupt-enable transition | 39 |
| Encodings with baseline clock mismatches | 4,857 |

These are **static may-reach sites**, not proof that each suite executes each site or that every stored output changes. The matrix found no illegal encoding in that committed rooted instruction map. The only mapped legal instruction unsupported by legacy is STOP at `$7D8D`.

Actual execution was also recorded for two representative suites with `tools/audit/trace_hc11_suite.py`, which wraps the CPU step boundary without adding device reads or changing state. The trace records source/executable hashes, exact PCs, opcode counts, and instances where applying the old CCR rule to the observed step would give a different CCR:

| Existing suite | Existing result with corrected core | Actual exposure to defective CCR behavior |
|---|---|---|
| `compare_rom.py` / base fuel | 532 cases passed; 40,960 instructions, 64 unique sites | TSX at `$7FE0` and `$F55C`: 881 instances with different old/new CCR. TSTA/CLRB at `$8003`, `$8016`, `$8028`: 11 instances.|
| `compare_hardware_rom.py` | 128 startup plus 4,112 REF cases passed; 107,744 instructions, 98 unique sites | Indexed BCLR/BSET at `$7115`, `$7509`, `$750C`: 4,246 instances with different old/new CCR.|

The JSON traces are in `docs/audit/traces/`. These passing selected-output comparisons are concrete demonstrations that a wrong internal reference CCR can coexist with a passing differential test. They do **not** demonstrate that the selected C outputs are wrong. The defects invalidate treating earlier passes as independent CPU validation; each subsystem conclusion needs the corrected replay results and an honest statement of which outputs/state were compared.

`tools/factory_hc11_cycle_subset.py` is a separate nominal timing table, not another execution core. All 284 encodings handled by that timing subset agree with the manual-derived table; 23 catalogue encodings are explicitly outside its reviewed subset. It deliberately does not use the emulator's clock accounting. `tools/factory_state_flow.py` is an abstract data-flow analysis that widens unknown effects; it is not a concrete behavioral oracle. `slot_rom_replay.CPU` and replay helper classes derive from the legacy CPU, so they are not independent CPU implementations.

## Remaining gaps and explicit boundaries

1. **STOP is reachable in the committed structural map and deliberately intercepted by tests.** At `$7D86` the ROM loads D=`$5008`, writes B to `$3039`, executes TAP at `$7D8C`, then `$CF STOP` at `$7D8D`. The resulting S=0 enables stop mode. `compare_fuel_ignition_rom.py:60–64` calls CF an illegal/terminal byte and returns status 10 before executing it; CF is actually a documented legal STOP. `compare_fuel_cycle_rom.py:66–67` also intercepts it, and `compare_fuel_controller_rom.py:219` excludes `$7D8C–$7D8E` from required coverage. A terminal abstraction can be valid only with an explicit boundary that excludes wake/restart behavior; it is not execution equivalence for STOP. No DAA or BRN sites were found in that map, but that does not prove all calibration/module paths exclude them.

2. **Illegal-opcode handling is fail-closed, not a hardware trap model.** The corrected core raises `UnknownOpcode` on illegal pages. Real hardware enters its illegal-opcode trap via `$FFF8`. Unsupported legal instructions and illegals are still represented by a similar software exception. The audit prevents false acceptance, but does not claim the exception reproduces hardware trap/return behavior.

3. **Individual bus reads/writes are not comprehensively modeled.** The new CLR operand-read regression closes a real side-effect defect. Dummy reads, prefetches, `$FFFF` bus policy, exact bus ordering, transient CCR visibility, and externally stretched accesses remain unqualified. The principal instruction matrix checks architectural registers, relevant CCR preservation, write order, and aggregate legacy clocks. It is not a bus-cycle conformance suite.

4. **Interrupt correctness extends beyond the CPU frame.** CLI/TAP delay, RTI readmission, XIRQ masks, and WAI pre-stacking now have independent tests. Full HPRIO selection, all simultaneous sources, source deassertion, edge/level behavior, pending-request lifetimes, watchdog/reset causes, and every peripheral's flag-clear rules need separate tests. The parent coordinator fixes cover specific reproduced failures, not the entire interrupt controller.

5. **No hardware-backed independent execution backend has been established here.** Both BINs running in separate instances of this corrected CPU still share its implementation errors. Before declaring whole-program equivalence, run the same independent ISA vectors against a separately developed CPU backend or real HC11 single-step harness, then qualify the PCM device model and semantic state/output projections. Undefined instruction outcomes should be represented as constrained unknowns, not matched simulator constants.

6. **Broader firmware completeness is separate evidence.** Address coverage, runtime/calibration boundaries, retained RAM, optional modules, and whole-controller integration are covered by the main audit inventory. Correcting a CPU cannot turn an outline, fixture callee, or unimplemented device into verified firmware behavior.

## Immediate remediation order

First make the independent ISA gate mandatory and rerun every existing stock replay against the corrected CPU. Preserve any newly exposed C/ROM mismatch as a separate executable test and investigate factory behavior before changing C. Second, qualify the minimum peripheral reads/writes and interrupt scheduling needed for engine, injector, spark, idle, startup, and ALDL paths. Third, give STOP, illegal traps, and optional-module interfaces explicit contracts, including whether they are excluded from a particular experiment. Finally, run dual-BIN experiments with independent CPU state, separate memory/devices, deterministic common stimuli, defined state/output normalization, and first-divergence traces. A second CPU implementation or hardware ISA conformance record is required to reduce common-mode reference risk.
