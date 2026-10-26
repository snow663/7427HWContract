"""Regression checks for data/code confusion and exact direct access indexing."""
from __future__ import annotations

import csv
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_dispatcher_reverse_map as dispatch
import build_factory_structure as structure
import build_full_rom_write_target_sweep as sweep
import build_write_target_network_index as network
from factory_structure import (
    SOURCE, REGIONS, Statement, control_edge, data_region, load_regions, memory_access,
    parse_listing,
)


class FactoryStructureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.regions = load_regions()
        cls.outputs = structure.build()

    def rows(self, name):
        return list(csv.DictReader(io.StringIO(self.outputs[structure.OUT / name])))

    def test_reviewed_tables_are_bounded_and_pinned_to_source(self):
        self.assertEqual(sum(r.end - r.start + 1 for r in self.regions), 308)
        self.assertIsNone(data_region(0xC2D5, self.regions))
        self.assertIsNone(data_region(0xC40A, self.regions))
        with tempfile.TemporaryDirectory() as tmp:
            different = Path(tmp) / "changed.asm"
            different.write_bytes(SOURCE.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                load_regions(different, REGIONS)

    def test_line_endings_do_not_invalidate_source_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            windows = Path(tmp) / "windows.asm"
            windows.write_bytes(SOURCE.read_bytes().replace(b"\n", b"\r\n"))
            self.assertEqual(load_regions(windows, REGIONS), self.regions)

    def test_no_false_dispatchers_and_real_dispatchers_survive(self):
        raw, parsed = dispatch.parse_lines(SOURCE)
        rows = dispatch.build_dispatchers(raw, parsed)
        self.assertEqual({r["dispatcher_pc"] for r in rows}, {"7A4F", "FAA5"})
        self.assertEqual(sum(r["dispatcher_pc"] == "7A4F" for r in rows), 16)
        self.assertFalse(any(0xC2D6 <= int(r["pc"], 16) <= 0xC409 for r in parsed))

    def test_table_bytes_are_not_mutations_in_either_legacy_index(self):
        rows = sweep.build(SOURCE)
        self.assertFalse(any(0xC2D6 <= int(r["pc"], 16) <= 0xC409 for r in rows))
        self.assertIn("8512", {r["pc"] for r in rows if r["target_symbol"] == "L3FCE"})
        raw = network.build_rows(network.parse_source(SOURCE))
        self.assertFalse(any(0xC2D6 <= int(r["pc"], 16) <= 0xC409 for r in raw))

    def test_bit_branch_reads_state_and_has_a_separate_control_target(self):
        row = Statement(1, 0x1000, "", "BRSET", "L004F,#$01,LAB84", "")
        access = memory_access(row)
        edge = control_edge(row)
        self.assertEqual((access["access"], access["target_address"], access["bitmask"]), ("R", "004F", "#$01"))
        self.assertEqual(edge["target_address"], "AB84")

    def test_immediate_values_and_call_targets_are_not_variable_reads(self):
        for op, operand in [("LDD", "#$024E"), ("JSR", "LF550"), ("BRA", "L024E")]:
            self.assertIsNone(memory_access(Statement(1, 0, "", op, operand, "")))

    def test_indexed_accesses_are_retained_without_fabricated_addresses(self):
        access = memory_access(Statement(1, 0, "", "STD", "$04,X", ""))
        self.assertEqual(access["resolution"], "unresolved_indexed")
        self.assertEqual(access["target_address"], "")

    def test_source_label_typo_is_not_mistaken_for_an_indirect_jump(self):
        edge = control_edge(Statement(1, 0xA40B, "", "BRSET", "L0009,#$01,LA4656", ""))
        self.assertEqual(edge["resolution"], "unresolved_direct_operand")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "colon.asm"
            path.write_text("A588: BCC LA596  : BR IF RPM GT THRESH\n")
            parsed = parse_listing(path)
            self.assertEqual(control_edge(parsed[0])["target_address"], "A596")

    def test_word_accesses_include_both_state_bytes(self):
        rows = {r["byte_address"]: r for r in self.rows("factory_state_index.csv")}
        self.assertIn("8508", rows["0250"]["write_pcs"].split(";"))
        self.assertIn("8508", rows["0251"]["write_pcs"].split(";"))
        accesses = {r["pc"]: r for r in self.rows("factory_memory_accesses.csv")}
        self.assertEqual(accesses["8512"]["access"], "W")
        self.assertEqual(accesses["8512"]["width_bits"], "16")
        self.assertEqual(accesses["8381"]["target_address"], "026F")
        self.assertEqual(accesses["8381"]["access"], "R")

    def test_reset_and_scheduler_entries_are_sourced_not_guessed(self):
        entries = {r["entry_address"]: r for r in self.rows("factory_entry_points.csv")}
        self.assertIn("FFFE", entries["FC29"]["source_pcs"].split(";"))
        self.assertIn("major_loop_word_table", entries["7AA6"]["entry_evidence"])
        self.assertNotIn("C39E", entries)

    def test_summary_makes_no_whole_program_completion_claim(self):
        summary = json.loads(self.outputs[structure.OUT / "factory_structure_summary.json"])
        self.assertEqual(summary["direct_control_into_reviewed_data"], [])
        self.assertEqual(set(summary["unresolved_indirect_control_sites"]), {"7A4F", "FAA5"})
        self.assertIn("not_semantic_completion", summary["scope"])


if __name__ == "__main__":
    unittest.main()
