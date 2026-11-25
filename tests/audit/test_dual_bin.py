"""Executable comparator tests; synthetic BINs are not firmware validation."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools/audit"))
from dual_bin import Snapshot, Stimulus, compare, synthetic_pair

STREAM = tuple(Stimulus(i, i * 1000, (("sample", value),))
               for i, value in enumerate((1, 2, 250)))


class DualBinTests(unittest.TestCase):
    def test_relocated_different_programs_and_retained_state_match(self):
        left, right = synthetic_pair()
        result = compare(left, right, STREAM)
        self.assertEqual(result["verdict"], "MATCHED_SCENARIOS")
        self.assertEqual(result["completed_epochs"], 3)
        self.assertNotEqual(left.identity["bin_sha256"], right.identity["bin_sha256"])
        last = result["checkpoints"][-1]
        self.assertEqual(last["left"]["state"], (("accumulator", 253),))
        self.assertNotEqual(last["left"]["diagnostics"]["cycles"],
                            last["right"]["diagnostics"]["cycles"])
        self.assertNotEqual(last["left"]["diagnostics"]["executed_pcs"],
                            last["right"]["diagnostics"]["executed_pcs"])

    def test_matching_output_with_wrong_persistent_state_is_failure(self):
        result = compare(*synthetic_pair(state_fault=True), STREAM)
        self.assertEqual(result["verdict"], "DIVERGED")
        self.assertEqual(result["first_divergence"]["epoch"], 0)
        self.assertEqual(result["first_divergence"]["category"], "retained_state")
        row = result["first_divergence"]["evidence"]
        self.assertEqual(row["left"]["outputs"], row["right"]["outputs"])
        self.assertTrue(row["right"]["diagnostics"]["trace_tail"])

    def test_repeated_output_write_is_observable(self):
        result = compare(*synthetic_pair(output_fault=True), STREAM)
        self.assertEqual(result["first_divergence"]["category"], "ordered_outputs")

    def test_limit_never_counts_as_a_match(self):
        result = compare(*synthetic_pair(), STREAM, instruction_limit=1)
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
        self.assertEqual(result["completed_epochs"], 0)
        self.assertEqual(result["first_divergence"]["category"], "incomplete_execution")

    def test_unknown_instruction_never_counts_as_a_match(self):
        left, right = synthetic_pair()
        right.memory.mem[0x9000] = 0x00
        result = compare(left, right, STREAM)
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
        self.assertIn("UnknownOpcode", result["checkpoints"][0]["right"]["reason"])
        rejected = result["checkpoints"][0]["right"]["diagnostics"]
        self.assertNotIn(0x9000, rejected["executed_pcs"])
        self.assertNotIn("00", rejected["executed_opcodes"])
        self.assertEqual(rejected["trace_tail"][-1]["pc"], 0x9000)

    def test_shared_memory_is_rejected(self):
        left, right = synthetic_pair()
        right.memory.mem = left.memory.mem
        with self.assertRaisesRegex(ValueError, "share mutable state"):
            compare(left, right, STREAM)

    def test_each_side_keeps_its_own_mutable_cpu_and_ram(self):
        left, right = synthetic_pair()
        left.cpu.s.a = 17
        left.memory.mem[0x2300] = 99
        self.assertEqual(right.cpu.s.a, 0)
        self.assertEqual(right.memory.mem[0x2300], 0)

    def test_replay_is_deterministic(self):
        self.assertEqual(compare(*synthetic_pair(), STREAM),
                         compare(*synthetic_pair(), STREAM))

    def test_invalid_schedule_is_rejected(self):
        with self.assertRaises(ValueError):
            compare(*synthetic_pair(), ())
        with self.assertRaises(ValueError):
            compare(*synthetic_pair(), (STREAM[1], STREAM[0]))

    def test_nested_mutable_input_is_copied_into_immutable_stimulus(self):
        external = [["sample", 1]]
        stimulus = Stimulus(0, 0, external)
        external[0][1] = 2
        self.assertEqual(stimulus.inputs, (("sample", 1),))
        with self.assertRaises(TypeError):
            stimulus.inputs[0][1] = 3

    def test_mutable_input_values_are_rejected(self):
        with self.assertRaises(ValueError):
            Stimulus(0, 0, (("sample", [1]),))

    def test_shared_state_adopted_during_advance_cannot_pass(self):
        shared = []
        class LazyAlias:
            identity = {"adapter": "test fixture"}
            def __init__(self): self.private = []
            def mutable_state_ids(self): return {id(self), id(self.private)}
            def advance(self, stimulus, instruction_limit):
                self.private = shared
                return Snapshot("checkpoint", True, "", (), (("a", 1),), {})
        result = compare(LazyAlias(), LazyAlias(), STREAM)
        self.assertEqual(result["verdict"], "INCONCLUSIVE")
        self.assertEqual(result["first_divergence"]["category"], "shared_mutable_state")

    def test_named_state_is_compared_by_name_not_tuple_order(self):
        left, right = synthetic_pair()
        original_left, original_right = left.advance, right.advance
        def projected(original, state):
            def advance(stimulus, limit):
                s = original(stimulus, limit)
                return Snapshot(s.checkpoint, s.complete, s.reason, s.outputs, state, s.diagnostics)
            return advance
        left.advance = projected(original_left, (("a", 1), ("b", 2)))
        right.advance = projected(original_right, (("b", 2), ("a", 1)))
        self.assertEqual(compare(left, right, STREAM)["verdict"], "MATCHED_SCENARIOS")

    def test_duplicate_state_names_are_not_accepted_as_a_match(self):
        left, right = synthetic_pair()
        def bad(stimulus, limit):
            return Snapshot("checkpoint", True, "", (), (("a", 1), ("a", 1)), {})
        left.advance = right.advance = bad
        result = compare(left, right, STREAM)
        self.assertEqual(result["verdict"], "INCONCLUSIVE")


if __name__ == "__main__":
    unittest.main()
