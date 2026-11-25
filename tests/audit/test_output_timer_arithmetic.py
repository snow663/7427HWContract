"""Source-bound output-timer saturation checks for the HC11 16-bit-int ABI.

The actual pulse declaration, conditional += and width initializer are parsed
from output_timer_internal.h. A bounded C integer-semantics model evaluates
them; independent arithmetic and literal witnesses supply expected results.
This is not native HC11 execution, timing or whole-handler verification.

Run: python -m unittest discover -s tests/audit -p test_output_timer_arithmetic.py -v
AUDIT_REPO may select another checkout containing the output-timer helper.
This new suite is deliberately separate from the pinned preimplementation
baseline's original 14-method arithmetic suite.
"""
from copy import deepcopy
import os
from pathlib import Path
import sys
import unittest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
REPO = Path(os.environ.get("AUDIT_REPO", HARNESS_ROOT)).resolve()
sys.path.insert(0, str(HARNESS_ROOT / "tools" / "audit"))
from c_integer_model import IntegerModel, c_ast, function, nodes, parse_source, spelling

SOURCE = Path("pseudo-source/src/interrupts/output_timer_internal.h")
BOUNDARIES = (0, 1, 2, 0x3FFF, 0x4000, 0x7FFE, 0x7FFF,
              0x8000, 0x8001, 0xFFFE, 0xFFFF)


class OutputTimerArithmetic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        body = function(parse_source(REPO / SOURCE), "output_timer_irq")
        declarations = nodes(body, c_ast.Decl)
        pulses = [node for node in declarations if node.name == "pulse"]
        widths = [node for node in declarations if node.name == "width"]
        additions = [node for node in nodes(body, c_ast.Assignment)
                     if spelling(node.lvalue) == "pulse"]
        if len(pulses) != 1 or len(widths) != 1 or len(additions) != 1:
            raise AssertionError("Expected one actual pulse declaration, addition and width declaration")
        cls.pulse, cls.width, cls.addition = pulses[0], widths[0], additions[0]
        if cls.addition.op != "+=" or not isinstance(cls.addition.lvalue, c_ast.ID):
            raise AssertionError("Expected scalar pulse += expression in the actual helper")
        guards = [node for node in nodes(body, c_ast.If) if node.iftrue is cls.addition]
        if len(guards) != 1:
            raise AssertionError("Expected the actual conditional pulse-addition guard")
        cls.guard = guards[0].cond

    def evaluate_width(self, pulse, reservoir, consume, *, int_bits=16,
                       accumulator_type=None):
        model = IntegerModel(int_bits)
        env = {
            "pcm->reference.timer_pulse": model.value(pulse, "uint16_t"),
            "pcm->fuel.acceleration_reservoir": model.value(reservoir, "uint16_t"),
            "consume": model.value(int(consume), "unsigned"),
        }
        declaration = deepcopy(self.pulse)
        if accumulator_type is not None:
            # Negative controls mutate only this in-memory AST. The production
            # file and shared IntegerModel are never changed.
            scalar = declaration.type
            if not isinstance(scalar, c_ast.TypeDecl) or not isinstance(scalar.type, c_ast.IdentifierType):
                raise AssertionError("Pulse accumulator is no longer a scalar declaration")
            scalar.type.names = [accumulator_type]
        model.statement(declaration, env)
        if model.evaluate(self.guard, env).number:
            # For an ID lvalue, C's pulse += rhs is equivalent to
            # pulse = pulse + rhs, including conversion back to pulse's type.
            # This adapter uses the source's actual lvalue and RHS AST.
            expanded = c_ast.Assignment(
                "=", deepcopy(self.addition.lvalue),
                c_ast.BinaryOp("+", deepcopy(self.addition.lvalue),
                               deepcopy(self.addition.rvalue)))
            model.statement(expanded, env)
        model.statement(self.width, env)
        return env["width"].number

    def test_literal_factory_carry_and_saturation_witnesses(self):
        # 788D/78F1 ADDD carry and 7892/78F6 ASLD carry both select FFFF.
        # The base-only route also saturates its ASLD at 78AA/790E.
        witnesses = (
            (0, 0, False, 0),
            (1, 0xFFFF, False, 2),
            (0x7FFF, 0, False, 0xFFFE),
            (0x8000, 0, False, 0xFFFF),
            (1, 1, True, 4),
            (0x7FFF, 1, True, 0xFFFF),
            (0xFFFF, 1, True, 0xFFFF),
            (0xFFFF, 0xFFFF, True, 0xFFFF),
        )
        for pulse, reservoir, consume, expected in witnesses:
            with self.subTest(pulse=pulse, reservoir=reservoir, consume=consume):
                self.assertEqual(self.evaluate_width(pulse, reservoir, consume), expected)

    def test_actual_expression_boundaries_under_both_int_widths(self):
        for int_bits in (16, 32):
            for consume in (False, True):
                for pulse in BOUNDARIES:
                    for reservoir in BOUNDARIES:
                        # Mathematical saturation, independent of the parsed
                        # comparison/conditional expression and its C types.
                        total = pulse + (reservoir if consume else 0)
                        expected = min(65535, total * 2)
                        with self.subTest(int_bits=int_bits, consume=consume,
                                          pulse=pulse, reservoir=reservoir):
                            self.assertEqual(self.evaluate_width(
                                pulse, reservoir, consume, int_bits=int_bits), expected)

    def test_uint16_accumulator_mutation_loses_add_carry(self):
        for int_bits in (16, 32):
            with self.subTest(int_bits=int_bits):
                mutant = self.evaluate_width(0xFFFF, 1, True, int_bits=int_bits,
                                             accumulator_type="uint16_t")
                self.assertEqual(mutant, 0)
                # The same saturation witness must fail for the narrowed AST.
                with self.assertRaises(AssertionError):
                    self.assertEqual(mutant, 0xFFFF)

    def test_unsigned_accumulator_mutation_is_hidden_on_host(self):
        host = self.evaluate_width(0xFFFF, 1, True, int_bits=32,
                                   accumulator_type="unsigned")
        target = self.evaluate_width(0xFFFF, 1, True, int_bits=16,
                                     accumulator_type="unsigned")
        self.assertEqual(host, 0xFFFF)
        self.assertEqual(target, 0)
        with self.assertRaises(AssertionError):
            self.assertEqual(target, 0xFFFF)


if __name__ == "__main__":
    unittest.main()
