"""Census safeguards, not firmware-equivalence tests.

Run: python -m unittest discover -s tests/audit -p test_equivalence_inventory.py -v
Negative tests deliberately remove evidence or inflate a classification and
assert the audit rejects that change. The separate --require-complete gate is
expected to fail on the audited development snapshot.
"""
import copy
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("inventory", ROOT / "tools/audit/build_equivalence_inventory.py")
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class InventoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.outputs = inventory.build(ROOT)
        def read(name):
            return list(csv.DictReader(io.StringIO(cls.outputs["maps/audit/" + name])))
        cls.functions = read("factory_function_inventory.csv")
        cls.frontiers = read("external_frontier_inventory.csv")
        cls.suites = read("equivalence_test_inventory.csv")
        cls.by_entry = {r["entry"]: r for r in cls.functions}
        cls.expected = {int(r["entry"], 16) for r in cls.functions}

    def validate(self, functions=None, frontiers=None, suites=None):
        inventory.validate(self.functions if functions is None else functions,
                           self.frontiers if frontiers is None else frontiers,
                           self.suites if suites is None else suites, self.expected)

    def test_committed_outputs_reproduce(self):
        for path, expected in self.outputs.items():
            with self.subTest(path=path):
                self.assertEqual((ROOT / path).read_text(), expected)

    def test_all_rooted_vectors_and_direct_call_targets_have_rows(self):
        raw_vectors = inventory.read_csv(ROOT, "maps/structure/factory_global_vectors.csv")
        raw_edges = inventory.read_csv(ROOT, "maps/structure/factory_global_control_edges.csv")
        expected = {r["target"] for r in raw_vectors}
        expected |= {r["target"] for r in raw_edges if r["kind"] in {"call", "reviewed16_word_dispatch"}}
        expected = {entry for entry in expected if int(entry, 16) >= 0x7100}
        self.assertTrue(expected <= self.by_entry.keys())
        self.assertTrue({"7100", "FA5B", "ABCB"} <= self.by_entry.keys())

    def test_omitting_an_output_interrupt_is_rejected(self):
        damaged = [r for r in self.functions if r["entry"] != "7875"]
        with self.assertRaisesRegex(ValueError, "omitted"):
            self.validate(functions=damaged)

    def test_duplicate_entry_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicated"):
            self.validate(functions=self.functions + [self.functions[0]])

    def test_fully_verified_cannot_be_asserted_without_certificate(self):
        damaged = copy.deepcopy(self.functions)
        damaged[0]["classification"] = "fully_implemented_behaviorally_verified"
        with self.assertRaisesRegex(ValueError, "certificate"):
            self.validate(functions=damaged)

    def test_containing_range_is_not_implementation_mapping(self):
        damaged = copy.deepcopy(self.functions)
        damaged[0]["classification"] = "implemented_insufficiently_verified"
        damaged[0]["implementation_mapping"] = ""
        damaged[0]["containing_range_candidates_not_mapping"] = "pcm_reset_sequence"
        with self.assertRaisesRegex(ValueError, "containing range"):
            self.validate(functions=damaged)

    def test_arbitrary_factory_callback_cannot_disappear(self):
        damaged = [r for r in self.frontiers if "038E" not in r["target"]]
        with self.assertRaisesRegex(ValueError, "callback"):
            self.validate(frontiers=damaged)

    def test_shared_oracle_lineage_must_remain_visible(self):
        damaged = copy.deepcopy(self.suites)
        suite = next(r for r in damaged if r["evidence_class"] == "factory_instructions_vs_host_C")
        suite["interpreter_route"] = ""
        with self.assertRaisesRegex(ValueError, "lineage"):
            self.validate(suites=damaged)

    def test_integrated_snapshot_has_60_actual_ROM_and_70_contract_suites(self):
        ctests = [r for r in self.suites if r["registration"] == "ctest"]
        rom = [r for r in ctests if r["evidence_class"] == "factory_instructions_vs_host_C"]
        self.assertEqual(len(ctests), 130)
        self.assertEqual(len(rom), 60)
        self.assertEqual(len(ctests) - len(rom), 70)
        self.assertTrue(all(r["interpreter"] == inventory.CORE for r in rom))
        self.assertEqual(sum(bool(r["linked_replacement_boundaries"]) for r in rom), 17)

    def test_inlined_helpers_are_not_false_missing_bodies(self):
        for entry, name in {"77F7": "pcm_reference_timer_arm", "9222": "pcm_iac_service",
                            "923C": "pcm_iac_service", "9240": "pcm_iac_boot",
                            "9247": "pcm_iac_error", "D94B": "pcm_transmission_temperature_gain",
                            "F5CF": "pcm_slot_03"}.items():
            with self.subTest(entry=entry):
                self.assertIn(name, self.by_entry[entry]["implementation_mapping"])
                self.assertEqual(self.by_entry[entry]["classification"], "implemented_insufficiently_verified")

    def test_completed_output_IRQs_are_mapped_without_claiming_full_equivalence(self):
        for entry, routine in (("7875", "pcm_toc5_irq"), ("78D9", "pcm_toc4_irq")):
            with self.subTest(entry=entry):
                self.assertEqual(self.by_entry[entry]["classification"], "implemented_insufficiently_verified")
                self.assertEqual(self.by_entry[entry]["implementation_mapping"], routine)
                self.assertIn("output_timer_rom_differential", self.by_entry[entry]["ROM_suite_C_references_not_execution_coverage"])
                self.assertNotIn("UNBOUND_OUTPUT_TIMER", self.by_entry[entry]["reason"])

    def test_partial_and_prefix_dependencies_remain_explicit(self):
        self.assertEqual(self.by_entry["AE85"]["classification"], "outline_or_partial")
        partials = {r["entry"] for r in self.functions if r["classification"] == "outline_or_partial"}
        self.assertEqual(partials, {"7100", "AE85", "F5DC"})
        for entry in ("AEA4", "B018", "B089", "C483", "B1F0", "B23C", "B2C9", "B2ED"):
            self.assertEqual(self.by_entry[entry]["classification"], "unresolved_or_missing")
            self.assertEqual(self.by_entry[entry]["implementation_gap_kind"], "explicit_unsupplied_boundary")
            self.assertIn(inventory.PREFIX_SOURCE, self.by_entry[entry]["source_evidence"])

    def test_dispatch_and_optional_dependencies_are_not_erased(self):
        slots = {r["entry"] for r in self.functions if "reviewed16_word_dispatch" in r["entry_roles"]}
        self.assertEqual(len(slots), 16)
        self.assertIn("A9E4->1812", self.by_entry["A466"]["transitive_external_frontiers"])
        self.assertIn("AB66->180F", self.by_entry["A466"]["transitive_external_frontiers"])
        self.assertIn("FAA5->wordRAM[038E]", self.by_entry["FA5B"]["transitive_external_frontiers"])

    def test_no_percentage_or_machine_certificate_from_counts(self):
        summary = json.loads(self.outputs["maps/audit/equivalence_inventory_summary.json"])
        self.assertEqual(summary["known_resident_entries"], 253)
        self.assertEqual(summary["indexed_C_routines"], 436)
        self.assertEqual(summary["classification_counts"], {
            "implemented_insufficiently_verified": 214,
            "intentionally_excluded_or_replaced": 8,
            "outline_or_partial": 3,
            "unresolved_or_missing": 28,
        })
        self.assertEqual(summary["unresolved_entry_detail_counts"], {
            "explicit_unsupplied_boundary": 9,
            "unresolved_nested_entry_mapping": 19,
        })
        self.assertEqual(summary["independent_whole_entry_certificates"], 0)
        self.assertNotIn("fully_implemented_behaviorally_verified", summary["classification_counts"])
        self.assertIn("not_percent_complete", summary["verdict"])

    def test_content_provenance_covers_helpers_and_current_source(self):
        summary = json.loads(self.outputs["maps/audit/equivalence_inventory_summary.json"])
        self.assertEqual(summary["development_starting_commit"], inventory.BASE_DEV)
        self.assertEqual(summary["historical_audit_commit"], inventory.FROZEN_AUDIT)
        self.assertIn("working_tree_edits", summary["snapshot_policy"])
        self.assertNotIn("reviewed_development", summary)
        self.assertEqual(summary["generator_sha256"], hashlib.sha256((ROOT / inventory.GENERATOR).read_bytes()).hexdigest())
        for path in ("pseudo-source/src/interrupts/output_timer_internal.h",
                     "pseudo-source/platform/hc11_bus.c", inventory.CORE,
                     "tests/audit/test_equivalence_inventory.py"):
            with self.subTest(path=path):
                self.assertEqual(summary["input_sha256"][path], hashlib.sha256((ROOT / path).read_bytes()).hexdigest())
        expected = hashlib.sha256(json.dumps({
            "generator_sha256": summary["generator_sha256"],
            "input_sha256": summary["input_sha256"],
        }, sort_keys=True, separators=(",", ":")).encode("ascii")).hexdigest()
        self.assertEqual(summary["content_snapshot_sha256"], expected)

    def test_comparator_and_ISA_test_evidence_are_not_promoted_to_firmware_equivalence(self):
        by_script = {row["script"]: row for row in self.suites}
        isa = by_script["tests/audit/test_hc11_isa.py"]
        self.assertEqual(set(isa["all_source_resolved_interpreters_not_executed"].split(";")),
                         {inventory.CORE, inventory.NEW_CORE})
        comparator = by_script["tests/audit/test_dual_bin.py"]
        self.assertEqual(comparator["evidence_class"], "synthetic_dual_BIN_comparator_contract")
        self.assertIn("share_legacy_CPU", comparator["independence_assessment"])

    def test_readiness_gate_remains_red_for_this_snapshot(self):
        result = subprocess.run([sys.executable, str(ROOT / inventory.GENERATOR),
                                 "--require-complete", "--check"], cwd=ROOT,
                                text=True, capture_output=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("FAIL: complete functional equivalence is not established.", result.stderr)
        self.assertIn("28 unresolved/missing; 9 external frontiers", result.stderr)
        self.assertNotIn("Inventory drift", result.stderr)


if __name__ == "__main__":
    unittest.main()
