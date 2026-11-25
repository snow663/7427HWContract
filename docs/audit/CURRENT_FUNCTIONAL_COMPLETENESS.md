# Current factory-equivalence worklist — 2026-11-24

## Current finding and scope

**Whole-firmware functional equivalence remains unestablished.** The two
previously missing output-timer C bodies are now implemented and compared with
actual factory instructions. The remaining indexed worklist contains **52
unresolved resident entries and three partial entries**, together with eight
fixed external hooks and one dynamic callback frontier. The 52 entries are a
bounded set identified by the existing maps; they are not proof that only 52
algorithms remain to be written.

The target is full factory equivalence, including transmission, before feature
removal. Earlier engine-first or manual-controller priorities did not justify
omitting transmission dependencies. The [development work plan](../analysis/FACTORY_EQUIVALENCE_WORK_PLAN.md)
defines the next source and verification gates. Custom-ROM Rev B/TS00 truck work
retains its separate historical trajectory and does not become complete through
this factory-source census.

## Snapshot identity

The development starting point is
`2696d9d1a58d55fa913a967e18761d051e0b87b2`, after PRs #50 and #51. This inventory
is generated from the available source content, including the artifact/bus
integration edits in the working tree. That commit is an anchor, **not a claim
that every evaluated input is unchanged from a clean checkout of it**.

The [summary](../../maps/audit/equivalence_inventory_summary.json) records the
generator SHA-256, the SHA-256 of each structural/source/test input, and a content
snapshot SHA-256 over that manifest. C helpers and headers behind indexed
wrappers are included. Deterministic hashes identify the evaluated content
without relying on the branch name, generation time, or clean-Git assertions.
The census does not execute production code or infer successful test runs from
source files. CI execution results are separate evidence.

The [frozen independent audit](https://github.com/snow663/7427HWContract/blob/8dce2cf9a492e0366213877491de7957953b361d/docs/audit/FUNCTIONAL_COMPLETENESS.md)
continues to describe its original `f2f493f4` development snapshot. Its counts and
missing-output-IRQ findings are preserved as historical evidence.

## Denominators and current classifications

| Population | Count | What the count establishes |
|---|---:|---|
| Known resident factory entry points | 253 | Vector targets, direct call targets, 16 reviewed scheduler targets, and existing reviewed CFG roots. |
| Statically mapped instruction starts | 14,523 | A structural may-reach graph; not dynamic execution, branch feasibility or interrupt-admission coverage. |
| Indexed C routines | 415 | Public source index entries, including slices, composite routines and target interfaces; not the factory-entry denominator. |
| Resident slow scheduler slots | 16 | All reviewed table targets have resident C wrappers; their dependencies still need closure. |
| Alternate unrooted instruction starts | 44 | Separate candidate entries, not ordinary rooted coverage. |
| External execution frontiers | 9 | Eight fixed hooks and `wordRAM[$038E]`; none is silently treated as a successful no-op. |
| Registered CTests | 124 | 54 factory-ROM/host-C suites and 70 other contracts; registration does not assert a test passed. |

The vector/direct-call/dispatcher union supplies 250 of the 253 resident entries;
the reviewed roots add `$7100`, `$FA5B` and `$ABCB`. Arbitrary callback content and
conditional external modules prevent a finite, unconditional claim about all
possible executable addresses until their domains are specified.

| Requested classification | Current entries | Historical audit entries | Meaning |
|---|---:|---:|---|
| Fully implemented and behaviorally verified | **0** | 0 | No independent whole-entry behavioral certificate is supplied by this census. |
| Implemented but insufficiently verified | **190** | 188 | Explicit entry mapping and a C body, or a reviewed inline/parameterized mapping; complete behavior and dependency closure remain qualified. |
| Outline or partial implementation | **3** | 3 | Specific source or execution boundaries at `$7100`, `$AE85`, and `$F5DC`. |
| Intentionally excluded or replaced | **8** | 8 | Fixed single-RTS leaves with bounded return/delay justifications. |
| Unresolved or missing | **52** | 54 | Twelve explicitly unsupplied boundary roots and forty unresolved nested mappings. |

The change from 188/54 to 190/52 is the addition of `$7875`/`$78D9` as
`pcm_toc5_irq`/`pcm_toc4_irq`. Their actual-ROM comparison covers 80 instruction
starts, all 28 conditional outcomes and retained shared-reservoir sequences
under a declared logical I/O fixture. Native entry stubs, compiler ABI and
physical device behavior remain open, so neither entry receives an independent
whole-entry certificate. See the [output-timer contract](../analysis/FACTORY_OUTPUT_TIMER_IMPLEMENTATION.md)
and [recorded comparison evidence](../../maps/structure/factory_output_timer_validation.json).

The source index still has 235 `implemented_outline`, 171
`implemented_algorithm`, and nine `dependency_boundary` labels. These are index
labels, not the classifications above. In particular, an `implemented_outline`
often contains substantial resident logic and must not be counted as an absent
factory implementation without inspecting the body and mapping.

## The 52 unresolved current/transmission entries

| Work package | Entries | Exact indexed addresses |
|---|---:|---|
| Current control | 1 | `7C13` |
| Transmission spark and dependencies | 5 | `C40A C4E5 D9B7 DA6F DAE2` |
| Shift control and dependencies | 8 | `B32D B334 B367 B4B2 BA65 E654 F131 F1DD` |
| Pressure/TCC and dependencies | 14 | `B56B B587 B88D B91D BA38 BC77 BCC6 BE5C BEBC BF62 C00B C271 D969 E664` |
| Transmission-input prefix and dependencies | 24 | `AEA4 B018 B089 B1F0 B23C B2B2 B2C9 B2ED C483 E58C E5CF E5F1 E60B E6F5 E7C7 E808 E847 E8C8 EB81 EBC0 ECCC EF2B F420 F5A2` |

Four direct roots (`7C13`, `C4E5`, `B32D`, `B56B`) have explicit C task boundaries.
The transmission-input prefix explicitly supplies eight further factory callees
in order: `AEA4 B018 B089 C483 B1F0 B23C B2C9 B2ED`. These twelve roots have an
identified unsupplied boundary. The remaining forty nested entries have no closed
source mapping in this census. A future review may map some to inlined or shared
C algorithms rather than require forty separate new C functions.

The generated `implementation_gap_kind` column preserves that distinction.
`reachable_from_missing_group_not_ownership` is a graph relationship, not proof
of state ownership or an independent algorithm boundary. Before implementing a
nested entry, review its call context, ABI, retained state and possible existing
inline representation. A containing source range or a familiar helper name alone
does not establish equivalence.

Sources: [entry worklist](../../maps/audit/missing_implementation_inventory.csv),
[factory call graph](../../maps/structure/factory_global_control_edges.csv),
[transmission-input boundary](../../pseudo-source/src/transmission/transmission_input_prefix.c),
and [transmission analysis](../analysis/FACTORY_TRANSMISSION_CONTROL.md).

## Three partial entries require their own closure work package

| Entry | Existing implementation | Remaining obligation |
|---|---|---|
| `$7100` | `pcm_reset_entry` and native startup scaffolding | Execute the real compiled reset-to-runtime path, prove state initialization and native stack/entry ABI. A host reset witness is not target execution. |
| `$AE85` | `pcm_transmission_input` resident tail plus `pcm_transmission_input_prefix` boundary | Implement or independently map all eight prefix callees, then compare the joined prefix/tail state and ordered effects. |
| `$F5DC` | Resident signature probe in `pcm_connection_probe` | Resolve the enabled `$180C` module path and machine ABI, preserving the absent/invalid-signature paths separately. |

Closing the 52 unresolved rows alone would leave these three entries partial.
Partial-entry closure also does not automatically establish a whole-controller
image, optional-module domain, interrupt schedule or peripheral model.

## Justified replacements and external execution

The eight replacement entries are `$CF15`, `$E6E4`, `$EB17`, `$EB18`, `$EE5F`,
`$EE60`, `$F3ED`, and `$FBD6`. Each has the fixed raw `$39` RTS instruction;
none is a configuration-dependent omission of a nonempty algorithm. `$CF15` is
folded into slot 00's normal return. `$F3ED` and `$FBD6` use explicit nominal-delay
contracts. Their justification assumes a normal completed call and the declared
functional-time abstraction. Native return-stack effects, interrupt interleaving
and physical timing still require validation.

The eight fixed external targets are `$1800`, `$1803`, `$1806`, `$1809`, `$180C`,
`$180F`, `$1812`, and `$1815`. The ninth frontier is `wordRAM[$038E]`, reached by
the factory branch at `$FAA5`. A supported absent-module calibration can define a
bounded scenario domain, but it cannot justify silently dropping enabled module
behavior from a full factory claim. Specify and test the admitted module/callback
domain or supply each reachable implementation and ABI. Keep unsupported cases
visible as unresolved. See the [external-frontier inventory](../../maps/audit/external_frontier_inventory.csv).

## Test-evidence interpretation

All 54 registered C/ROM differential suites resolve to
`hac31_romsim/romsim/hc11_core.py`. They execute distinct factory bytes and C
algorithms, but share that reference interpreter and supplied hardware/state
contracts. Seventeen suites link explicit C replacement-boundary fixtures.
Their scope must be read alongside those substitutions. Source references,
coverage-variable names and loops are retained as source signals, never counted
as executed branch or state coverage.

The [test inventory](../../maps/audit/equivalence_test_inventory.csv) includes the
audit test modules as well as the existing CMake and Python registrations. It
separately labels manual-derived ISA tests, the bounded C integer model,
synthetic native-artifact/bus tests, census-integrity tests and the synthetic
dual-BIN comparator. The comparator uses isolated state with a shared legacy CPU;
it does not supply an independent second CPU or execute an actual reconstructed
BMHM C BIN. Literal `import_module` calls are resolved for source lineage;
arbitrary dynamic imports are not inferred.

The complete PR #51 integration tree passed 70 non-ROM and 54 ROM suites before
merging, as recorded in [run 45530188138](https://github.com/snow663/7427HWContract/actions/runs/45530188138).
That is execution evidence for its exact tested tree, not an automatic pass for
later source changes. Regenerate this census and rerun the relevant gates as the
implementation changes.

## Generated artifacts and safeguards

| Artifact | Purpose |
|---|---|
| [factory_function_inventory.csv](../../maps/audit/factory_function_inventory.csv) | Every known entry, implementation mapping, source evidence and direct/transitive dependencies. |
| [missing_implementation_inventory.csv](../../maps/audit/missing_implementation_inventory.csv) | The 52 unresolved and three partial entries, including boundary-versus-mapping distinctions. |
| [C_source_claim_inventory.csv](../../maps/audit/C_source_claim_inventory.csv) | All 415 indexed source claims, kept separate from the factory-entry universe. |
| [external_frontier_inventory.csv](../../maps/audit/external_frontier_inventory.csv) | Eight fixed hooks and the dynamic callback. |
| [unrooted_alternate_inventory.csv](../../maps/audit/unrooted_alternate_inventory.csv) | The 44 alternate candidate instruction starts. |
| [equivalence_test_inventory.csv](../../maps/audit/equivalence_test_inventory.csv) | Test registrations, source-resolved interpreter lineage and explicit limits. |
| [equivalence_inventory_summary.json](../../maps/audit/equivalence_inventory_summary.json) | Counts, revision anchors, source/generator hashes and content identity. |

```sh
python tools/verify_factory_global_structure.py --check-recorded
python tools/audit/build_equivalence_inventory.py
python tools/audit/build_equivalence_inventory.py --check
python -m unittest discover -s tests/audit -p test_equivalence_inventory.py -v

# Expected to return 1 while complete functional equivalence is unestablished.
python tools/audit/build_equivalence_inventory.py --check --require-complete
```

The green census tests reject omitted/duplicated entries, false fully-verified
labels, unsupported range-based mappings, hidden interpreter lineage and loss of
the dynamic callback. They also require the completed OC4/OC5 mappings and verify
that the readiness gate still fails for the documented open work. A successful
test of that expected failure is an inventory safeguard, not a green firmware
equivalence verdict. Counts and percentages cannot replace behavioral evidence.
