"""Check functional grouping, fixed-operand scope and recorded context anchors."""
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from explain_revb_bin import SHA
from explain_revb_functions import CONTEXT, fixed_references, make_groups, partition, read_context
from factory_rom_decode import decode
from manual_idle_asm import assemble


def instruction(pc, hexbytes):
    data = bytes.fromhex(hexbytes)
    return decode(lambda a, n: data[a-pc:a-pc+n], pc)


class FunctionalReader(unittest.TestCase):
    def test_partition_covers_gaps_and_each_instruction_once(self):
        decoded = {0x7100: instruction(0x7100, "01"),
                   0x7101: instruction(0x7101, "39"),
                   0x7110: instruction(0x7110, "39")}
        entries = {0x7100: {"title": "Entry", "purpose": "First path", "source": "test"},
                   0x7110: {"title": "Other", "purpose": "Separate tail", "source": "test"}}
        groups = partition(decoded, entries)
        self.assertEqual([[i.pc for i in g["instructions"]] for g in groups], [[0x7100, 0x7101], [0x7110]])

    def test_missing_chapter_context_does_not_get_guessed(self):
        with self.assertRaisesRegex(ValueError, "without functional context"):
            partition({0x7100: instruction(0x7100, "39")}, {})

    def test_indexed_offset_is_not_a_fixed_sensor_address(self):
        rows = [instruction(0x7000, "A6 06"), instruction(0x7002, "FC 01 D9"), instruction(0x7005, "FD 02 9D")]
        reads, writes, indexed = fixed_references(rows)
        self.assertEqual(reads, [(0x1d9, 16)])
        self.assertEqual(writes, [(0x29d, 16)])
        self.assertEqual(indexed, ["7000"])

    def test_wrong_image_is_rejected_before_generation(self):
        with self.assertRaisesRegex(ValueError, "exact released"):
            make_groups(bytes(65536))

    def test_every_authored_boundary_is_recorded_as_a_real_instruction(self):
        context = read_context()
        evidence = json.loads((ROOT / "maps/maintenance/revb_function_boundaries.json").read_text())
        self.assertEqual(evidence["image_sha256"], SHA)
        self.assertEqual(evidence["context_sha256"], hashlib.sha256(CONTEXT.read_bytes()).hexdigest())
        self.assertEqual(sum(row["instructions"] for row in evidence["groups"]), 6449)
        starts = {row["address"] for row in evidence["groups"]}
        self.assertEqual(len(starts), len(evidence["groups"]))
        self.assertTrue(set(context["by_address"]) <= starts)
        for group in evidence["groups"]:
            for row in (group["first"], group["last"]):
                i = instruction(int(row["address"], 16), row["bytes"])
                self.assertEqual((i.op + " " + i.operand).strip(), row["operation"])

    def test_custom_boundary_bytes_match_the_reviewed_assembly(self):
        evidence = json.loads((ROOT / "maps/maintenance/revb_function_boundaries.json").read_text())
        sources = [assemble(ROOT / "source/manual_idle/manual_idle.asm"),
                   assemble(ROOT / "source/manual_idle/decel_spark_gate.asm")]
        memory = {a: b for source in sources for a, b in source.memory.items()}
        checked = 0
        for group in evidence["groups"]:
            for row in (group["first"], group["last"]):
                pc = int(row["address"], 16)
                if pc in memory:
                    data = bytes.fromhex(row["bytes"])
                    self.assertEqual(data, bytes(memory[a] for a in range(pc, pc+len(data))))
                    checked += 1
        self.assertGreaterEqual(checked, 60)
        for address, data in evidence["calibration_excerpts"].items():
            pc = int(address, 16)
            if pc in memory:
                data = bytes.fromhex(data)
                self.assertEqual(data, bytes(memory[a] for a in range(pc, pc+len(data))))


if __name__ == "__main__":
    unittest.main()
