"""Executable source-bound regressions for 16-bit int arithmetic.

Run: python -m unittest discover -s tests/audit -p test_target_arithmetic.py -v
Set AUDIT_REPO=/absolute/path to test the unmodified development checkout.
These tests model C expression widths; they do NOT execute native HC11 code.
"""

from pathlib import Path
import os
import sys
import unittest

HARNESS_ROOT = Path(__file__).resolve().parents[2]
REPO = Path(os.environ.get("AUDIT_REPO", HARNESS_ROOT)).resolve()
sys.path.insert(0, str(HARNESS_ROOT / "tools" / "audit"))
from c_integer_model import IntegerModel, c_ast, c_parser, function, nodes, parse_source, spelling

FUEL = Path("pseudo-source/src/fuel")
BOUNDARIES = sorted(set(range(0, 65536, 257)) | {
    0, 1, 4095, 4096, 4097, 8191, 8192, 8193,
    16383, 16384, 16385, 32767, 32768, 32769, 65534, 65535})


def helper_model(int_bits=16):
    model = IntegerModel(int_bits)
    mixture = parse_source(REPO / FUEL / "mixture_internal.h")
    for name in ("mix_word", "mix_fraction", "mix_round"):
        model.functions[name] = function(mixture, name)
    model.functions["pcm_gain_word"] = function(parse_source(REPO / "pseudo-source/src/math/gain_word.c"), "pcm_gain_word")
    model.functions["governor_sat_shift"] = function(parse_source(REPO / FUEL / "governor_internal.h"), "governor_sat_shift")
    return model


def saturating_call(filename):
    tree = parse_source(REPO / FUEL / filename)
    calls = [n for n in nodes(tree, c_ast.FuncCall) if isinstance(n.name, c_ast.ID) and n.name.name == "mix_word"]
    if len(calls) != 1:
        raise AssertionError(f"Expected one actual mix_word call in {filename}, got {len(calls)}")
    return calls[0]


class ModelConformance(unittest.TestCase):
    """Independent microcases prevent a broken width model hiding the bugs."""

    def evaluate(self, expression, width=16):
        source = "typedef unsigned char uint8_t;typedef unsigned short uint16_t;typedef unsigned long uint32_t;unsigned f(void){return " + expression + ";}"
        expr = c_parser.CParser().parse(source).ext[-1].body.block_items[0].expr
        return IntegerModel(width).evaluate(expr, {}).number

    def test_promotions_and_conversion_order(self):
        self.assertEqual(self.evaluate("2u * (uint16_t)32768"), 0)
        self.assertEqual(self.evaluate("2u * (uint16_t)32768", 32), 65536)
        self.assertEqual(self.evaluate("(uint32_t)(2u * (uint16_t)32768)"), 0)
        self.assertEqual(self.evaluate("(uint32_t)2u * (uint16_t)32768"), 65536)
        self.assertEqual(self.evaluate("(uint16_t)65535 + 1u"), 0)
        self.assertEqual(self.evaluate("(uint8_t)255 + (uint8_t)255"), 510)

    def test_signed_overflow_is_not_silently_wrapped(self):
        with self.assertRaises(ValueError):
            self.evaluate("(uint8_t)255 * (uint8_t)255")
        with self.assertRaises(ValueError):
            self.evaluate("(uint8_t)128 << 8")
        self.assertEqual(self.evaluate("(uint16_t)255 * (uint8_t)255"), 65025)
        self.assertEqual(self.evaluate("(uint16_t)128 << 8"), 32768)

    def test_literals_and_shift_width(self):
        self.assertEqual(self.evaluate("65535 + 1"), 65536)
        self.assertEqual(self.evaluate("0xffff + 1"), 0)
        self.assertEqual(self.evaluate("(uint32_t)1 << 16"), 65536)
        with self.assertRaises(ValueError):
            self.evaluate("1u << 16")


class TargetArithmetic(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.target = helper_model(16)
        cls.host = helper_model(32)

    def assert_scaling(self, filename, factor, input_name, gain_name=None):
        node = saturating_call(filename)
        for word in BOUNDARIES:
            for gain in ((0, 1, 64, 127, 128, 192, 255) if gain_name else (None,)):
                env = {input_name: self.target.value(word, "uint16_t")}
                if gain_name:
                    env[gain_name] = self.target.value(gain, "uint8_t")
                # The oracle is the mathematical contract: rounded /256 gain,
                # then saturation. It does not reuse the parsed expression.
                scaled = word if gain is None else (word * gain + 128) // 256
                expected = min(65535, factor * scaled)
                self.assertEqual(self.host.evaluate(node, env).number, expected,
                                 f"32-bit-int regression in {filename}")
                actual = self.target.evaluate(node, env).number
                self.assertEqual(actual, expected, f"{filename}:{node.coord.line-1}, word={word}, gain={gain}; int16={actual}, mathematical={expected}")

    def test_cpi_double_saturates_before_narrowing(self):
        self.assert_scaling("fuel_cpi_prepare.c", 2, "pcm->fuel.corrected_pulse")

    def test_crank_seed_double_saturates_before_narrowing(self):
        self.assert_scaling("fuel_crank_prepare.c", 2, "pulse")

    def test_blm_double_saturates_before_narrowing(self):
        self.assert_scaling("fuel_blm_scale.c", 2, "pcm->fuel.corrected_pulse")

    def test_crank_final_quadruple_saturates_before_narrowing(self):
        self.assert_scaling("fuel_crank_pulse.c", 4, "value", "gain")

    def test_baro_quadruple_saturates_before_narrowing(self):
        self.assert_scaling("fuel_baro_battery.c", 4, "pcm->fuel.corrected_pulse", "gain")

    def test_derivative_double_saturates_before_narrowing(self):
        self.assert_scaling("fuel_derivative_correction.c", 2, "pcm->fuel.corrected_pulse", "value")

    def test_async_divisor_preserves_high_period(self):
        tree = parse_source(REPO / FUEL / "fuel_async_accumulate.c")
        declarations = [n for n in nodes(tree, c_ast.Decl) if n.name == "ratio"]
        self.assertEqual(len(declarations), 1)
        expr = declarations[0].init
        for period in BOUNDARIES:
            for pulse in (0, 1, 10000, 32767, 32768, 65534, 65535):
                denominator = min(65535, period * 2)
                expected = 65535 if denominator == 0 or pulse >= denominator else (pulse * 65536) // denominator
                env = {"period": self.target.value(period, "uint16_t"),
                       "pcm->fuel.corrected_pulse": self.target.value(pulse, "uint16_t")}
                self.assertEqual(self.target.evaluate(expr, env).number, expected,
                                 f"period={period}, pulse={pulse}; ratio expression line {expr.coord.line-1}")

    def test_governor_shift_saturates_before_narrowing(self):
        # Actual callers use 2, 3 and 4; include zero and one for boundaries.
        for count in (3, 2, 4, 0, 1):
            for word in BOUNDARIES:
                args = [self.target.value(word, "uint16_t"), self.target.value(count, "unsigned")]
                actual = self.target.call("governor_sat_shift", args).number
                self.assertEqual(actual, min(65535, word << count), f"word={word}, count={count}")

    def test_reset_map_all_adc_values(self):
        body = function(parse_source(REPO / "pseudo-source/src/startup/reset_controllers.c"), "pcm_reset_controllers").body.block_items
        declaration = [n for n in body if isinstance(n, c_ast.Decl) and n.name == "map"]
        assignments = [n for n in body if isinstance(n, c_ast.Assignment) and spelling(n.lvalue) in ("map", "value")]
        self.assertEqual(len(declaration), 1)
        self.assertEqual(len(assignments), 2)
        for raw in (255, *range(255)):
            env = {"raw": self.target.value(raw, "uint8_t"), "value": self.target.value(0, "uint8_t")}
            for statement in [declaration[0], *assignments]:
                self.target.statement(statement, env)
            expected = min(255, (2 * (((raw - 26) % 256) * 151 + 64)) // 256)
            self.assertEqual(env["value"].number, expected, f"raw={raw}, map={env['map'].number}")

    def test_bounded_byte_rounding_keeps_factory_behavior(self):
        # Counterexample to blanket widening: byte*byte+128 already fits16.
        for first in range(256):
            for second in (0, 1, 127, 128, 254, 255):
                args = [self.target.value(first, "uint8_t"), self.target.value(second, "uint8_t")]
                self.assertEqual(self.target.call("mix_round", args).number, (first * second + 128) // 256)

    def test_guarded_crank_double_keeps_factory_behavior(self):
        tree = parse_source(REPO / FUEL / "fuel_crank_pulse.c")
        assignments = [n for n in nodes(tree, c_ast.Assignment) if spelling(n.lvalue) == "value" and isinstance(n.rvalue, c_ast.Cast)]
        self.assertEqual(len(assignments), 1)
        for word in (0, 1, 16384, 32766, 32767):
            env = {"value": self.target.value(word, "uint16_t")}
            self.target.statement(assignments[0], env)
            self.assertEqual(env["value"].number, 2 * word)


if __name__ == "__main__":
    unittest.main()
