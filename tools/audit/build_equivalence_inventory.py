#!/usr/bin/env python3
"""Build a conservative, reproducible inventory, NOT an equivalence certificate.

Run from any directory. --check reports stale/missing committed output. No ROM is
downloaded and no production module is imported or executed by this census.
Source anchors identify claimed implementations; range overlap and test-source
references are retained separately and NEVER promoted to execution coverage.
"""
from __future__ import annotations

import argparse
import ast
import csv
import hashlib
import io
import json
from pathlib import Path
import re
from collections import Counter, defaultdict, deque

ROOT = Path(__file__).resolve().parents[2]
OUT = "maps/audit"
BASE_MAIN = "56a3145477291dd7c6bfee15db98414c983b1b2f"
BASE_DEV = "2696d9d1a58d55fa913a967e18761d051e0b87b2"
FROZEN_AUDIT = "8dce2cf9a492e0366213877491de7957953b361d"
GENERATOR = "tools/audit/build_equivalence_inventory.py"
STRUCT = "maps/structure/"
CORE = "hac31_romsim/romsim/hc11_core.py"
NEW_CORE = "7427_simulator/sim7427/cpu.py"
CLASSIFICATIONS = {
    "fully_implemented_behaviorally_verified",
    "implemented_insufficiently_verified",
    "outline_or_partial",
    "intentionally_excluded_or_replaced",
    "unresolved_or_missing",
}
MISSING_GROUPS = {
    0xAEA4: "transmission_input_prefix",
    0xB018: "transmission_input_prefix",
    0xB089: "transmission_input_prefix",
    0xC483: "transmission_input_prefix",
    0xB1F0: "transmission_input_prefix",
    0xB23C: "transmission_input_prefix",
    0xB2C9: "transmission_input_prefix",
    0xB2ED: "transmission_input_prefix",
    0xB56B: "pressure_tcc",
}
PREFIX_ENTRIES = {0xAEA4, 0xB018, 0xB089, 0xC483, 0xB1F0, 0xB23C, 0xB2C9, 0xB2ED}
PREFIX_SOURCE = "pseudo-source/src/transmission/transmission_input_prefix.c"
# Reviewed non-bijective mappings, not guesses based on a containing range.
# A callable HC11 entry can be an inlined C expression or one parameterized body.
OVERRIDES = {
    0x77F7: ("pcm_reference_timer_arm", "implemented_insufficiently_verified",
             "source explicitly implements 77C7 and77F7 with bank_b parameter"),
    0x9222: ("pcm_iac_service", "implemented_insufficiently_verified",
             "A407 sole direct caller explicitly inlines raw9222 setter; larger disable wrapper is not substituted"),
    0x923C: ("pcm_iac_service", "implemented_insufficiently_verified",
             "A407 sole direct caller explicitly inlines raw923C setter; larger enable wrapper is not substituted"),
    0x9240: ("pcm_iac_boot", "implemented_insufficiently_verified",
             "LDX004C/BSET10 helper is inlined as final sys_update(004C,0,10)"),
    0x9247: ("pcm_iac_error", "implemented_insufficiently_verified",
             "carry result from004D.7 becomes the input_shadow bit80 predicate"),
    0xD8F0: ("pcm_transmission_gear_select", "implemented_insufficiently_verified",
             "source names D8F0; select_threshold inlines descriptor/column lookup"),
    0xD94B: ("pcm_transmission_temperature_gain", "implemented_insufficiently_verified",
             "only rooted direct caller D92E inlines gain selection before scaling; no standalone C ABI required"),
    0xF49A: ("pcm_lookup_capped", "implemented_insufficiently_verified",
             "shared cap/interpolate tail represented by input argument rather than HC11 accumulator placement"),
    0xF5CF: ("pcm_slot_03", "implemented_insufficiently_verified",
             "source explicitly folds optional1806 then0F00=F7 into slot03"),
    0xCF15: ("pcm_slot_00", "intentionally_excluded_or_replaced",
             "single RTS is explicitly folded into slot00 normal return"),
    0xF3ED: ("pcm_board_latch", "intentionally_excluded_or_replaced",
             "single RTS delay represented by explicit11-cycle backend calls; backend timing remains unverified"),
    0xFBD6: ("pcm_factory_outputs", "intentionally_excluded_or_replaced",
             "literal RTS delay replaced by explicit minimum11-cycle backend delay; timing/device interleaving remain separate"),
}


def read_csv(root: Path, path: str) -> list[dict[str, str]]:
    with (root / path).open(newline="") as stream:
        return list(csv.DictReader(stream))


def csv_text(rows: list[dict[str, object]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, list(rows[0]), lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def packed(values) -> str:
    return ";".join(sorted(set(str(x) for x in values if x != "")))


def anchors(reference: str) -> tuple[set[int], list[tuple[int, int]]]:
    """Parse explicit start addresses, not arbitrary numbers in prose.

    References are uppercase hex, sometimes joined to English (and9250).
    A leading vector address is harmless: only rooted instruction starts map.
    """
    ranges = [(int(a, 16), int(b, 16)) for a, b in
              re.findall(r"([0-9A-F]{4})\.\.([0-9A-F]{4})", reference)]
    starts = {a for a, _ in ranges}
    leading = re.match(r"([0-9A-F]{4})(?=[:., ]|$)", reference)
    if leading:
        starts.add(int(leading.group(1), 16))
    starts.update(int(a, 16) for a in
                  re.findall(r"->\s*([0-9A-F]{4})(?=[:., ]|$)", reference))
    return starts, ranges


def source_location(root: Path, path: str, pattern: str) -> str:
    for lineno, line in enumerate((root / path).read_text().splitlines(), 1):
        if re.search(pattern, line):
            return f"{path}:{lineno}"
    return path


def cmake_commands(text: str, name: str):
    # The repository uses simple add_test/add_executable declarations. Balanced
    # parentheses preserve generator expressions and multiline native contracts.
    for match in re.finditer(r"\b" + name + r"\s*\(", text, re.I):
        start = pos = match.end()
        depth, quoted = 1, False
        while depth:
            char = text[pos]
            if char == '"':
                quoted = not quoted
            elif not quoted and char == "(":
                depth += 1
            elif not quoted and char == ")":
                depth -= 1
            pos += 1
        yield re.sub(r"#[^\n]*", "", text[start:pos - 1]).split()


class PythonLineage:
    """Resolve local imports and the repo's explicit exec(with_name(...)) chain.

    This is source dependency evidence, not proof every imported line executes.
    Unknown dynamic imports are not guessed. CPU identity for ROM suites is a
    required gate, so a suite with an unrecognized route causes a review failure.
    """
    def __init__(self, root: Path):
        self.root = root
        self.memo = {}
        self.direct_memo = {}
        self.search = [root / "tools", root / "tests", root / "pseudo-source/tests",
                       root / "hac31_romsim", root / "7427_simulator",
                       root / "pseudo-source/native", root / "tools/audit", root / "tests/audit"]

    def resolve(self, module: str, parent: Path):
        stem = module.replace(".", "/")
        for base in [parent.parent, *self.search]:
            for candidate in [base / (stem + ".py"), base / stem / "__init__.py"]:
                if candidate.is_file():
                    return candidate.relative_to(self.root).as_posix()
        return None

    def direct(self, path: str) -> set[str]:
        if path in self.direct_memo:
            return self.direct_memo[path]
        file = self.root / path
        text = file.read_text()
        tree = ast.parse(text)
        result = set()
        for node in ast.walk(tree):
            modules = []
            if isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module]
            elif isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            for module in modules:
                candidate = self.resolve(module, file)
                if candidate:
                    result.add(candidate)
            # Literal import_module calls are source-resolvable. Arbitrary
            # dynamic expressions remain unclaimed interpreter lineage.
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "import_module" and node.args
                    and isinstance(node.args[0], ast.Constant)
                    and isinstance(node.args[0].value, str)):
                candidate = self.resolve(node.args[0].value, file)
                if candidate:
                    result.add(candidate)
        for other in re.findall(r"with_name\(['\"]([^'\"]+\.py)['\"]\)", text):
            candidate = file.with_name(other)
            if candidate.is_file():
                result.add(candidate.relative_to(self.root).as_posix())
        self.direct_memo[path] = result
        return result

    def closure(self, path: str) -> set[str]:
        if path not in self.memo:
            pending, seen = [path], set()
            while pending:
                item = pending.pop()
                if item in seen:
                    continue
                seen.add(item)
                pending.extend(self.direct(item) - seen)
            self.memo[path] = seen
        return self.memo[path]

    def route(self, path: str, destination: str) -> str:
        pending = deque([(path, [path])])
        seen = set()
        while pending:
            item, route = pending.popleft()
            if item == destination:
                return " -> ".join(route)
            if item in seen:
                continue
            seen.add(item)
            pending.extend((child, route + [child]) for child in sorted(self.direct(item)))
        return ""


def suite_inventory(root: Path, routine_names: set[str]) -> list[dict[str, str]]:
    text = (root / "pseudo-source/CMakeLists.txt").read_text()
    executables = {row[0]: row[1:] for row in cmake_commands(text, "add_executable")}
    lineage = PythonLineage(root)
    result = []

    def row(name, kind, command, script="", target="", sources=()):
        source_files = ["pseudo-source/" + path for path in sources if path.endswith(".c")]
        closure = lineage.closure(script) if script else set()
        code = (root / script).read_text() if script else ""
        scope = (ast.get_docstring(ast.parse(code)) or "").replace("\n", " ") if code else ""
        core = CORE if CORE in closure else NEW_CORE if NEW_CORE in closure else ""
        is_rom = kind == "ctest" and "/compare" in script
        if is_rom:
            evidence = "factory_instructions_vs_host_C"
            independence = "distinct_ROM_bytes_and_C_algorithm; shared_legacy_CPU_and_fixture_contract; not_dual_BIN"
            if core != CORE:
                raise ValueError(f"unreviewed interpreter dependency for {name}")
        elif kind == "ctest":
            evidence = "host_or_source_or_image_contract"
            independence = "no_factory_instruction_equivalence_established_by_this_test"
        elif script.startswith("pseudo-source/native/"):
            evidence = "synthetic_image_tooling_contract"
            independence = "synthetic_ELF_Srecord_or_compiler_fixture; no_reconstructed_BIN_execution"
        elif script == "tests/test_factory_structure.py":
            evidence = "ROM_structural_decode_and_evidence_contract"
            independence = "no_CPU_execution_or_C_equivalence"
        elif script.startswith("tests/test_factory_"):
            evidence = "factory_instructions_vs_model_or_scoped_contract" if core else "structural_or_model_contract"
            independence = "stock_ROM_executed_when_replay_used; Python_model_or_contract_not_reconstructed_C_BIN"
        elif script == "hac31_romsim/tests/test_real_bmhm_optional.py":
            evidence = "optional_real_factory_ROM_smoke"
            independence = "requires_matching_external_BIN; may_skip; boot_execution_not_C_equivalence"
        elif script.startswith(("hac31_romsim/", "7427_simulator/")):
            evidence = "CPU_or_simulator_synthetic_contract"
            independence = "synthetic_programs_or_UI_contract; not_full_firmware_equivalence"
        elif script == "tests/audit/test_hc11_isa.py":
            evidence = "manual_derived_CPU_conformance_contract"
            independence = "independent_expected_semantics_for_both_CPU_implementations; no_whole_firmware_equivalence"
        elif script == "tests/audit/test_interrupt_scheduling.py":
            evidence = "interrupt_coordinator_synthetic_contract"
            independence = "coordinator_and_CPU_synthetic_state; not_physical_timer_or_whole_firmware_execution"
        elif script in ("tests/audit/test_target_arithmetic.py", "tests/audit/test_output_timer_arithmetic.py"):
            evidence = "source_expression_target_width_contract"
            independence = "bounded_C_integer_semantics_model; no_native_HC11_compilation_or_ABI_proof"
        elif script == "tests/audit/test_dual_bin.py":
            evidence = "synthetic_dual_BIN_comparator_contract"
            independence = "separate_environments_share_legacy_CPU; synthetic_BINs_and_fixture_IO; no_factory_vs_reconstructed_BIN_run"
        elif script == "tests/audit/test_equivalence_inventory.py":
            evidence = "inventory_integrity_contract"
            independence = "checks_census_omission_provenance_and_classification; no_firmware_execution"
        elif script == "tests/audit/test_artifact_integrity.py":
            evidence = "synthetic_native_artifact_and_host_bus_contract"
            independence = "synthetic_code_reports_and_host_compiled_bus_probe; no_native_compiler_or_physical_EEPROM_proof"
        elif script in ("tests/test_manual_idle.py", "tests/test_manual_idle_release.py"):
            evidence = "custom_idle_C_and_emitted_HC11_vs_recorded_excerpt"
            independence = "custom_RevA_RevB_work_not_complete_stock_BMHM_C_reconstruction"
        else:
            evidence = "artifact_structure_or_documentation_contract"
            independence = "no_factory_C_equivalence_established"
        all_text = "\n".join((root / p).read_text() for p in sorted(closure)) if closure else code
        refs = set()
        for file in source_files:
            refs |= set(re.findall(r"\bpcm_[a-z0-9_]+\b", (root / file).read_text())) & routine_names
        boundaries = [p for p in source_files if p.endswith("_boundary.c")]
        # These observations are intentionally named source signals: no branch or
        # event coverage is inferred from the existence of a literal or a loop.
        signals = []
        for needle, label in [(r"\bretained\b|\.update\(.*state", "retained_state_witness_source"),
                              (r"\.interrupt\(", "explicit_interrupt_injection_source"),
                              (r"\.s\.pc\s*=\s*0x7aa5", "redirect_to_RTS_source"),
                              (r"\bcoverage\b|executed\.add|covered\.add", "instruction_set_tracking_source"),
                              (r"\bfail\b|\bfailure\b", "failure_injection_source")]:
            if re.search(needle, all_text, re.I):
                signals.append(label)
        result.append({
            "suite": name, "registration": kind, "evidence_class": evidence,
            "command": command, "script": script, "host_target": target,
            "host_fixture_sources": packed(source_files),
            "linked_replacement_boundaries": packed(boundaries),
            "interpreter": core,
            "all_source_resolved_interpreters_not_executed": packed(
                item for item in (CORE, NEW_CORE) if item in closure),
            "interpreter_route": lineage.route(script, core) if core else "",
            "local_python_dependencies": packed(closure - {script}),
            "scope_from_suite_docstring": scope,
            "independence_assessment": independence,
            "C_routine_references_not_coverage": packed(refs),
            "source_signals_not_coverage": packed(signals),
            "global_limit": "no_whole_controller_dual_BIN_or_physical_device_equivalence",
        })

    for tokens in cmake_commands(text, "add_test"):
        assert tokens[0] == "NAME" and tokens[2] == "COMMAND", tokens
        name, args = tokens[1], tokens[3:]
        script = next(("pseudo-source/" + a.split("${CMAKE_CURRENT_SOURCE_DIR}/", 1)[1]
                       for a in args if a.endswith(".py") and "${CMAKE_CURRENT_SOURCE_DIR}/" in a), "")
        target = next((re.search(r"TARGET_FILE:([^>]+)", a).group(1)
                       for a in args if "TARGET_FILE:" in a), "")
        if not target and args and args[0] in executables:
            target = args[0]
        row(name, "ctest", " ".join(args), script, target, executables.get(target, ()))
    for directory in ("tests", "tests/audit", "hac31_romsim/tests", "7427_simulator/tests", "pseudo-source/native/tests"):
        for file in sorted((root / directory).glob("test*.py")):
            script = file.relative_to(root).as_posix()
            row("python:" + script, "python_module", "python -m unittest " + script, script)
    return sorted(result, key=lambda item: (item["registration"], item["suite"]))


def build(root: Path = ROOT) -> dict[str, str]:
    routines = read_csv(root, "pseudo-source/routine_index.csv")
    by_name = {r["routine"]: r for r in routines}
    if len(by_name) != len(routines):
        raise ValueError("duplicate indexed C routine")
    for routine in routines:
        source = root / "pseudo-source" / routine["file"]
        if not source.is_file() or not re.search(r"\b" + routine["routine"] + r"\s*\(", source.read_text()):
            raise ValueError("missing indexed C body: " + routine["routine"])
    instruction_rows = read_csv(root, STRUCT + "factory_global_instructions.csv")
    instructions = {int(r["pc"], 16): r for r in instruction_rows}
    instruction_lines = {int(r["pc"], 16): index for index, r in enumerate(instruction_rows, 2)}
    edges = read_csv(root, STRUCT + "factory_global_control_edges.csv")
    vectors = read_csv(root, STRUCT + "factory_global_vectors.csv")
    roles, callers = defaultdict(set), defaultdict(set)
    for vector in vectors:
        roles[int(vector["target"], 16)].add("vector:" + vector["name"])
    for edge in edges:
        if edge["kind"] in ("call", "reviewed16_word_dispatch"):
            target = int(edge["target"], 16)
            roles[target].add(edge["kind"])
            callers[target].add(edge["pc"])
    for path in ("factory_global_call_bindings.csv", "factory_dte_roots.csv", "factory_idle_governor_roots.csv"):
        for item in read_csv(root, STRUCT + path):
            address = int(item["entry"], 16)
            if address in instructions:
                roles[address].add("reviewed_root:" + path)
    entries = set(roles) & set(instructions)
    # Keep local successor reachability separate from direct/tail call edges.
    local, calls = defaultdict(set), defaultdict(set)
    for edge in edges:
        pc, target = int(edge["pc"], 16), int(edge["target"], 16)
        if edge["kind"] in ("call", "reviewed16_word_dispatch"):
            calls[pc].add(target)
        elif edge["kind"] != "software_interrupt":
            local[pc].add(target)
    frontier_source = read_csv(root, STRUCT + "factory_global_frontiers.csv")
    frontier_by_pc = {int(row["pc"], 16): row["target"] for row in frontier_source}
    entry_calls, local_counts, local_frontiers = {}, {}, {}
    for entry in sorted(entries):
        seen, destinations, pending = set(), set(), [entry]
        while pending:
            pc = pending.pop()
            if pc in seen or pc not in instructions:
                continue
            if pc != entry and pc in entries:
                destinations.add(pc)  # shared/tail entry, not inferred new body
                continue
            seen.add(pc)
            destinations.update(calls[pc])
            pending.extend(local[pc] - seen)
        entry_calls[entry] = destinations
        local_counts[entry] = len(seen)
        local_frontiers[entry] = {f"{pc:04X}->{frontier_by_pc[pc]}" for pc in seen if pc in frontier_by_pc}
    owners = defaultdict(set)
    for entry, group in MISSING_GROUPS.items():
        pending, seen = [entry], set()
        while pending:
            pc = pending.pop()
            if pc in seen:
                continue
            seen.add(pc)
            owners[pc].add(group)
            pending.extend(entry_calls.get(pc, set()) - seen)
    suites = suite_inventory(root, set(by_name))
    routine_tests = defaultdict(set)
    for suite in suites:
        if suite["evidence_class"] == "factory_instructions_vs_host_C":
            for name in suite["C_routine_references_not_coverage"].split(";"):
                routine_tests[name].add(suite["suite"])
    claim, intervals = defaultdict(list), {}
    source_rows = []
    for index, routine in enumerate(routines, 2):
        starts, spans = anchors(routine["reference"])
        intervals[routine["routine"]] = spans
        for start in starts:
            if start in instructions:
                claim[start].append(routine)
        source_rows.append({
            "routine": routine["routine"], "source": "pseudo-source/" + routine["file"],
            "index_status_not_audit_verdict": routine["status"], "reference": routine["reference"],
            "rooted_claimed_starts": packed(f"{p:04X}" for p in starts if p in instructions),
            "nonrooted_or_noninstruction_claimed_starts": packed(f"{p:04X}" for p in starts if p not in instructions),
            "known_entry_matches": packed(f"{p:04X}" for p in starts if p in entries),
            "index_evidence": f"pseudo-source/routine_index.csv:{index}",
            "ROM_suite_C_references_not_coverage": packed(routine_tests[routine["routine"]]),
            "limit": "source_claim_and_test_reference_do_not_prove_instruction_branch_or_state_coverage",
        })
    function_rows = []
    for entry in sorted(entries):
        candidates = claim[entry]
        mapped = [r["routine"] for r in candidates]
        classification = "unresolved_or_missing"
        reason = "no_exact_source_entry_mapping; containing_ranges_are_candidates_only"
        if candidates:
            implemented = [r for r in candidates if r["status"].startswith("implemented_")]
            if implemented:
                classification = "implemented_insufficiently_verified"
                reason = "explicit_entry_claim_and_C_body_present; complete_behavior_not_independently_certified"
            else:
                reason = "only_dependency_boundary_body; actual_required_body_unsupplied"
        if entry in OVERRIDES:
            routine, classification, reason = OVERRIDES[entry]
            mapped.append(routine)
        if entry == 0x7100:
            classification = "outline_or_partial"
            reason = "C_reset_boundary_plus_native_startup_scaffold; no_verified_compiled_reset_to_runtime_execution"
        elif entry == 0xAE85:
            classification = "outline_or_partial"
            reason = "resident_F781_F64E_tail_present; eight_preceding_transmission_bodies_supplied_as_one_boundary"
        elif entry == 0xF5DC:
            classification = "outline_or_partial"
            reason = "signature_probe_resident_body_present; enabled180C_module_and_machine_ABI_unsupplied"
        elif entry in PREFIX_ENTRIES and classification == "unresolved_or_missing":
            prefix = (root / PREFIX_SOURCE).read_text()
            if f"{entry:04X}" not in prefix or "PCM_TRANSMISSION_INPUT_PREFIX" not in prefix:
                raise ValueError("reviewed eight-callee prefix boundary changed; re-review its entry mapping")
            reason = "explicit_callee_supplied_by_pcm_transmission_input_prefix; resident_body_unsupplied"
        elif instructions[entry]["mnemonic"] == "RTS" and entry not in OVERRIDES:
            if instructions[entry]["bytes_hex"] != "39":
                raise ValueError("RTS classification lacks matching raw39 opcode")
            classification = "intentionally_excluded_or_replaced"
            reason = "stock_entry_is_single_RTS; no_algorithmic_state_effect_after_normal_return; native_stack_timing_separate"
        if classification == "intentionally_excluded_or_replaced" and instructions[entry]["bytes_hex"] != "39":
            raise ValueError("reviewed replacement no longer has the literal RTS body")
        ranges = [name for name, spans in intervals.items()
                  if name not in mapped and any(a <= entry <= b for a, b in spans)]
        evidence = [source_location(root, "pseudo-source/" + by_name[name]["file"],
                                    r"\b" + name + r"\s*\(") for name in sorted(set(mapped))]
        evidence.append(f"{STRUCT}factory_global_instructions.csv:{instruction_lines[entry]}")
        if entry in (0x7875, 0x78D9):
            evidence += ["pseudo-source/include/hc11_vector_map.def",
                         "pseudo-source/platform/hc11_vector_contract.c",
                         "docs/analysis/FACTORY_OUTPUT_TIMER_IMPLEMENTATION.md",
                         "maps/structure/factory_output_timer_validation.json"]
        if entry in PREFIX_ENTRIES:
            evidence.append(PREFIX_SOURCE)
        if classification == "unresolved_or_missing":
            gap_kind = ("explicit_unsupplied_boundary" if entry in PREFIX_ENTRIES or mapped
                        else "unresolved_nested_entry_mapping")
        elif classification == "outline_or_partial":
            gap_kind = "partial_implementation_or_execution_boundary"
        else:
            gap_kind = "no_missing_body_claim"
        source_dirs = [by_name[name]["file"].split("/")[1] for name in mapped]
        function_rows.append({
            "entry": f"{entry:04X}", "entry_roles": packed(roles[entry]),
            "classification": classification, "reason": reason,
            "implementation_gap_kind": gap_kind,
            "implementation_mapping": packed(mapped),
            "containing_range_candidates_not_mapping": packed(ranges),
            "subsystem_candidates": packed(source_dirs),
            "source_evidence": packed(evidence),
            "incoming_call_or_dispatch_sites": packed(callers[entry]),
            "local_CFG_instruction_starts_not_execution": local_counts[entry],
            "direct_or_tail_entry_dependencies": packed(f"{p:04X}" for p in entry_calls[entry]),
            "reachable_from_missing_group_not_ownership": packed(owners[entry]),
            "ROM_suite_C_references_not_execution_coverage": packed(
                suite for name in mapped for suite in routine_tests[name]),
            "confidence": "structural_entry_confirmed; implementation_evidence_scoped; equivalence_unestablished",
        })
    entry_classification = {int(row["entry"], 16): row["classification"] for row in function_rows}
    for row in function_rows:
        pending, seen, unknown, external = [int(row["entry"], 16)], set(), set(), set()
        while pending:
            entry = pending.pop()
            if entry in seen:
                continue
            seen.add(entry)
            if entry_classification.get(entry) == "unresolved_or_missing":
                unknown.add(f"{entry:04X}")
            external.update(local_frontiers.get(entry, set()))
            pending.extend(entry_calls.get(entry, set()) - seen)
        row["transitive_unresolved_resident_entries"] = packed(unknown)
        row["transitive_external_frontiers"] = packed(external)
    frontier_rows = []
    for item in frontier_source:
        frontier_rows.append({**item, "classification": "unresolved_or_missing",
                              "limit": "conditional_external_dependency; neither_noop_nor_whitelist_assumed"})
    missing = [row for row in function_rows if row["classification"] in
               ("unresolved_or_missing", "outline_or_partial")]
    counts = Counter(row["classification"] for row in function_rows)
    input_paths = {
        "pseudo-source/routine_index.csv", "pseudo-source/CMakeLists.txt",
        STRUCT + "factory_global_instructions.csv", STRUCT + "factory_global_control_edges.csv",
        STRUCT + "factory_global_vectors.csv", STRUCT + "factory_global_frontiers.csv",
        STRUCT + "factory_global_call_bindings.csv", STRUCT + "factory_dte_roots.csv",
        STRUCT + "factory_idle_governor_roots.csv", STRUCT + "factory_global_alternate_entries.csv",
    }
    input_paths.update("pseudo-source/" + item["file"] for item in routines)
    # Include C helpers and headers behind indexed wrappers as well as public
    # bodies. A helper change must not leave the content identity unchanged.
    for directory in ("pseudo-source/src", "pseudo-source/include", "pseudo-source/platform"):
        input_paths.update(path.relative_to(root).as_posix()
                           for path in (root / directory).rglob("*")
                           if path.is_file() and path.suffix in {".c", ".h", ".def"})
    for suite in suites:
        for field in ("script", "host_fixture_sources", "local_python_dependencies"):
            input_paths.update(path for path in suite[field].split(";") if path)
    # Evidence references are not execution proof, but their exact content is
    # still part of this inventory's reviewed snapshot.
    for row in function_rows:
        input_paths.update(re.sub(r":\d+$", "", path) for path in row["source_evidence"].split(";"))
    input_hashes = {path: hashlib.sha256((root / path).read_bytes()).hexdigest()
                    for path in sorted(input_paths)}
    generator_hash = hashlib.sha256((root / GENERATOR).read_bytes()).hexdigest()
    snapshot_hash = hashlib.sha256(json.dumps(
        {"generator_sha256": generator_hash, "input_sha256": input_hashes},
        sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
    summary = {
        "schema": "7427-independent-equivalence-inventory-v2",
        "reference_main": BASE_MAIN, "development_starting_commit": BASE_DEV,
        "historical_audit_commit": FROZEN_AUDIT,
        "snapshot_policy": "content_hash_snapshot_of_available_source_including_working_tree_edits; revision_anchors_do_not_assert_clean_or_committed_content",
        "generator": GENERATOR,
        "generator_sha256": generator_hash,
        "content_snapshot_sha256": snapshot_hash,
        "rooted_instruction_starts_not_execution_coverage": len(instructions),
        "known_resident_entries": len(function_rows),
        "entry_definition": "vector targets; direct call targets; resolved16slot targets; rooted reviewed CFG roots",
        "unknown_entry_universe": "arbitrary RAM[038E] callback; conditional absent external modules; alternate unrooted candidates",
        "classification_counts": dict(sorted(counts.items())),
        "independent_whole_entry_certificates": 0,
        "unresolved_entry_detail_counts": dict(sorted(Counter(
            row["implementation_gap_kind"] for row in function_rows
            if row["classification"] == "unresolved_or_missing").items())),
        "indexed_C_routines": len(routines),
        "source_index_status_counts_not_completeness": dict(sorted(Counter(r["status"] for r in routines).items())),
        "external_frontiers": len(frontier_rows),
        "alternate_unrooted_instruction_starts": len(read_csv(root, STRUCT + "factory_global_alternate_entries.csv")),
        "ctests": sum(r["registration"] == "ctest" for r in suites),
        "factory_ROM_vs_host_C_suites": sum(r["evidence_class"] == "factory_instructions_vs_host_C" for r in suites),
        "factory_ROM_vs_host_C_suites_with_linked_replacements": sum(
            r["evidence_class"] == "factory_instructions_vs_host_C" and bool(r["linked_replacement_boundaries"]) for r in suites),
        "additional_python_modules": sum(r["registration"] == "python_module" for r in suites),
        "verdict": "no_whole_firmware_equivalence_certificate; counts_are_not_percent_complete",
        "input_sha256": input_hashes,
    }
    validate(function_rows, frontier_rows, suites, entries)
    return {
        OUT + "/factory_function_inventory.csv": csv_text(function_rows),
        OUT + "/missing_implementation_inventory.csv": csv_text(missing),
        OUT + "/external_frontier_inventory.csv": csv_text(frontier_rows),
        OUT + "/unrooted_alternate_inventory.csv": csv_text(read_csv(root, STRUCT + "factory_global_alternate_entries.csv")),
        OUT + "/C_source_claim_inventory.csv": csv_text(source_rows),
        OUT + "/equivalence_test_inventory.csv": csv_text(suites),
        OUT + "/equivalence_inventory_summary.json": json.dumps(summary, indent=2, sort_keys=True) + "\n",
    }


def validate(functions, frontiers, suites, expected_entries):
    entries = [int(row["entry"], 16) for row in functions]
    if len(entries) != len(set(entries)) or set(entries) != set(expected_entries):
        raise ValueError("known rooted entries omitted, duplicated, or invented")
    for row in functions:
        if row["classification"] not in CLASSIFICATIONS:
            raise ValueError("unknown classification")
        if row["classification"] == "fully_implemented_behaviorally_verified":
            raise ValueError("independent whole-entry behavioral certificate not supplied")
        if row["classification"] == "implemented_insufficiently_verified" and not row["implementation_mapping"]:
            raise ValueError("containing range cannot substitute for implementation mapping")
    if not any("038E" in row["target"] for row in frontiers):
        raise ValueError("arbitrary factory callback frontier was dropped")
    if len({row["suite"] for row in suites}) != len(suites):
        raise ValueError("duplicate test inventory key")
    for row in suites:
        if row["evidence_class"] == "factory_instructions_vs_host_C" and not row["interpreter_route"]:
            raise ValueError("ROM comparison missing interpreter lineage")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--require-complete", action="store_true",
                        help="readiness gate: fail while an entry lacks an independent behavioral certificate or an external frontier is unresolved")
    args = parser.parse_args()
    outputs = build()
    stale = []
    for name, content in outputs.items():
        path = ROOT / name
        if args.check:
            if not path.is_file() or path.read_text() != content:
                stale.append(name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
    if stale:
        parser.exit(1, "Inventory drift; review inputs and regenerate:\n" + "\n".join(stale) + "\n")
    if args.require_complete:
        summary = json.loads(outputs[OUT + "/equivalence_inventory_summary.json"])
        outstanding = sum(value for name, value in summary["classification_counts"].items()
                          if name not in {"fully_implemented_behaviorally_verified", "intentionally_excluded_or_replaced"})
        if outstanding or summary["external_frontiers"]:
            parser.exit(1, "FAIL: complete functional equivalence is not established. "
                        f"{summary['known_resident_entries']} known resident entries; "
                        f"{summary['classification_counts'].get('unresolved_or_missing', 0)} unresolved/missing; "
                        f"{summary['external_frontiers']} external frontiers. See missing_implementation_inventory.csv.\n")
    print("equivalence inventory: " + ("checked" if args.check else "generated") + f" {len(outputs)} artifacts")


if __name__ == "__main__":
    main()
