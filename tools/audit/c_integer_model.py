"""Source-bound C integer expression checks for the HC11 -mshort ABI.

This is a deliberately limited C-semantics model, NOT a native HC11 compiler,
instruction simulator, or proof of a whole function. Unsupported syntax and
undefined/implementation-defined signed arithmetic fail rather than being
silently approximated. pycparser supplies syntax only; types below supply the
target's 8-bit char, 16-bit int/short, and 32-bit long arithmetic.

References: C99 TC3 6.2.5, 6.3.1.1, 6.3.1.3, 6.3.1.8, 6.4.4.1, 6.5.7;
https://gcc.gnu.org/onlinedocs/gcc-4.0.0/gcc/M68hc1x-Options.html
"""

from dataclasses import dataclass
from pathlib import Path
import re

try:
    from pycparser import c_ast, c_generator, c_parser
except ImportError as exc:
    raise RuntimeError("Target arithmetic tests require pycparser: python -m pip install pycparser") from exc


@dataclass(frozen=True)
class CType:
    bits: int
    signed: bool
    rank: int

    @property
    def maximum(self):
        return (1 << (self.bits - self.signed)) - 1

    def convert(self, value):
        if not self.signed:
            return value % (1 << self.bits)
        if not -(1 << (self.bits - 1)) <= value <= self.maximum:
            raise ValueError(f"Undefined arithmetic or implementation-defined signed conversion: {value} to {self}")
        return value


@dataclass(frozen=True)
class Value:
    number: int
    type: CType


GENERATOR = c_generator.CGenerator()


def spelling(node):
    return GENERATOR.visit(node)


def parse_source(path):
    """Parse real expressions, without expanding unrelated platform macros.

    Pcm types are opaque here; tests must supply types for member lvalues they
    exercise. Preprocessor directives are removed with newlines preserved.
    Source coordinates are therefore the real line plus one typedef line.
    """
    text = Path(path).read_text()
    text = re.sub(r"/\*.*?\*/|//[^\n]*", lambda m: "\n" * m[0].count("\n"), text, flags=re.S)
    lines, continuation = [], False
    for line in text.splitlines(keepends=True):
        directive = continuation or line.lstrip().startswith("#")
        continuation = directive and line.rstrip().endswith("\\")
        lines.append("\n" if directive else line)
    text = "".join(lines)
    names = sorted(set(re.findall(r"\b(?:Pcm|Hc11)[A-Za-z_0-9]*\b", text)))
    prefix = ("typedef unsigned char uint8_t; typedef unsigned short uint16_t; "
              "typedef unsigned long uint32_t; typedef signed char int8_t; "
              "typedef signed short int16_t; typedef signed long int32_t; "
              "typedef int bool; typedef unsigned size_t; typedef unsigned uintptr_t; "
              + " ".join(f"typedef int {name};" for name in names) + "\n")
    return c_parser.CParser().parse(prefix + text, filename=str(path))


def nodes(root, cls):
    found = []

    class Visitor(c_ast.NodeVisitor):
        def generic_visit(self, node):
            if isinstance(node, cls):
                found.append(node)
            super().generic_visit(node)

    Visitor().visit(root)
    return found


def function(tree, name):
    found = [n for n in nodes(tree, c_ast.FuncDef) if n.decl.name == name]
    if len(found) != 1:
        raise AssertionError(f"Expected exactly one source definition of {name}, got {len(found)}")
    return found[0]


class Returned(Exception):
    def __init__(self, value):
        self.value = value


class IntegerModel:
    def __init__(self, int_bits=16):
        self.int = CType(int_bits, True, 3)
        self.uint = CType(int_bits, False, 3)
        self.long = CType(32, True, 4)
        self.ulong = CType(32, False, 4)
        self.types = {
            "int": self.int, "unsigned": self.uint, "unsigned int": self.uint,
            "long": self.long, "long int": self.long,
            "unsigned long": self.ulong, "unsigned long int": self.ulong,
            "uint8_t": CType(8, False, 1), "int8_t": CType(8, True, 1),
            "uint16_t": CType(16, False, 2), "int16_t": CType(16, True, 2),
            "uint32_t": self.ulong, "int32_t": self.long,
        }
        self.functions = {}

    def value(self, number, type_name):
        t = self.types[type_name]
        return Value(t.convert(number), t)

    def declared_type(self, node):
        while isinstance(node, (c_ast.Decl, c_ast.Typename, c_ast.TypeDecl)):
            node = node.type
        if not isinstance(node, c_ast.IdentifierType):
            raise TypeError(f"Unsupported scalar type: {type(node).__name__}")
        return self.types[" ".join(node.names)]

    def promote(self, t):
        if t.rank < self.int.rank:
            return self.int if t.maximum <= self.int.maximum else self.uint
        return t

    def common(self, a, b):
        a, b = self.promote(a), self.promote(b)
        if a == b:
            return a
        if a.signed == b.signed:
            return max((a, b), key=lambda t: t.rank)
        u, s = (b, a) if a.signed else (a, b)
        if u.rank >= s.rank:
            return u
        if s.maximum >= u.maximum:
            return s
        return CType(s.bits, False, s.rank)

    def constant(self, text):
        suffix = re.search(r"[uUlL]*$", text)[0].lower()
        digits = text[:len(text)-len(suffix)] if suffix else text
        number = int(digits, 16 if digits.lower().startswith("0x") else 8 if len(digits)>1 and digits.startswith("0") else 10)
        ll, ull = CType(64, True, 5), CType(64, False, 5)
        if "u" in suffix:
            candidates = [self.uint, self.ulong, ull]
        elif digits.lower().startswith("0x") or (len(digits)>1 and digits.startswith("0")):
            candidates = [self.int, self.uint, self.long, self.ulong, ll, ull]
        else:
            candidates = [self.int, self.long, ll]
        min_rank = 5 if suffix.count("l") == 2 else 4 if "l" in suffix else 3
        t = next(t for t in candidates if t.rank >= min_rank and number <= t.maximum)
        return Value(number, t)

    def type_of(self, node, env):
        if isinstance(node, c_ast.Constant):
            return self.constant(node.value).type
        if isinstance(node, (c_ast.ID, c_ast.StructRef, c_ast.ArrayRef)):
            return env[spelling(node)].type
        if isinstance(node, c_ast.Cast):
            return self.declared_type(node.to_type)
        if isinstance(node, c_ast.BinaryOp):
            if node.op in ("==", "!=", "<", "<=", ">", ">=", "&&", "||"):
                return self.int
            if node.op in ("<<", ">>"):
                return self.promote(self.type_of(node.left, env))
            return self.common(self.type_of(node.left, env), self.type_of(node.right, env))
        if isinstance(node, c_ast.TernaryOp):
            return self.common(self.type_of(node.iftrue, env), self.type_of(node.iffalse, env))
        if isinstance(node, c_ast.FuncCall):
            return self.declared_type(self.functions[node.name.name].decl.type.type)
        raise TypeError(f"Unsupported expression type: {type(node).__name__}")

    def evaluate(self, node, env):
        if isinstance(node, c_ast.Constant):
            return self.constant(node.value)
        if isinstance(node, (c_ast.ID, c_ast.StructRef, c_ast.ArrayRef)):
            return env[spelling(node)]
        if isinstance(node, c_ast.Cast):
            t = self.declared_type(node.to_type)
            return Value(t.convert(self.evaluate(node.expr, env).number), t)
        if isinstance(node, c_ast.FuncCall):
            return self.call(node.name.name, [self.evaluate(a, env) for a in node.args.exprs])
        if isinstance(node, c_ast.TernaryOp):
            branch = node.iftrue if self.evaluate(node.cond, env).number else node.iffalse
            t = self.type_of(node, env)
            return Value(t.convert(self.evaluate(branch, env).number), t)
        if not isinstance(node, c_ast.BinaryOp):
            raise TypeError(f"Unsupported expression: {type(node).__name__}")
        a = self.evaluate(node.left, env)
        if node.op == "&&" and not a.number:
            return Value(0, self.int)
        if node.op == "||" and a.number:
            return Value(1, self.int)
        b = self.evaluate(node.right, env)
        t = self.type_of(node, env)
        if node.op in ("<<", ">>"):
            a = Value(t.convert(a.number), t)
            if not 0 <= b.number < t.bits:
                raise ValueError("Undefined shift count")
            if a.number < 0:
                raise ValueError("Negative signed shift is undefined or implementation-defined")
            result = a.number << b.number if node.op == "<<" else a.number >> b.number
        else:
            common = self.common(a.type, b.type)
            x, y = common.convert(a.number), common.convert(b.number)
            if node.op == "+": result = x + y
            elif node.op == "-": result = x - y
            elif node.op == "*": result = x * y
            elif node.op in ("/", "%"):
                if y == 0: raise ValueError("Undefined division by zero")
                quotient = (abs(x) // abs(y)) * (-1 if (x < 0) != (y < 0) else 1)
                result = quotient if node.op == "/" else x - quotient * y
            elif node.op == "|": result = x | y
            elif node.op == "&": result = x & y
            elif node.op == "^": result = x ^ y
            elif node.op == ">": result = x > y
            elif node.op == ">=": result = x >= y
            elif node.op == "<": result = x < y
            elif node.op == "<=": result = x <= y
            elif node.op == "==": result = x == y
            elif node.op == "!=": result = x != y
            elif node.op == "&&": result = bool(x) and bool(y)
            elif node.op == "||": result = bool(x) or bool(y)
            else: raise TypeError(f"Unsupported operator {node.op}")
        return Value(t.convert(int(result)), t)

    def statement(self, node, env):
        if isinstance(node, c_ast.Compound):
            for item in node.block_items or []:
                self.statement(item, env)
        elif isinstance(node, c_ast.Decl):
            t = self.declared_type(node)
            env[node.name] = Value(t.convert(self.evaluate(node.init, env).number), t)
        elif isinstance(node, c_ast.Assignment) and node.op == "=":
            name = spelling(node.lvalue)
            t = env[name].type
            env[name] = Value(t.convert(self.evaluate(node.rvalue, env).number), t)
        elif isinstance(node, c_ast.Return):
            raise Returned(self.evaluate(node.expr, env))
        else:
            raise TypeError(f"Unsupported statement: {type(node).__name__}")

    def call(self, name, args):
        definition = self.functions[name]
        params = definition.decl.type.args.params
        if len(args) != len(params):
            raise AssertionError("Argument count mismatch")
        env = {}
        for param, arg in zip(params, args):
            t = self.declared_type(param)
            env[param.name] = Value(t.convert(arg.number), t)
        try:
            self.statement(definition.body, env)
        except Returned as returned:
            t = self.declared_type(definition.decl.type.type)
            return Value(t.convert(returned.value.number), t)
        raise AssertionError(f"No return in scalar helper {name}")
