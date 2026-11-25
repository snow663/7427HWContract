"""Native build driver demands actual compiler and explicit placement."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
for name in ("hc11_layout","verify_hc11_toolchain","verify_native_elf","build_hc11_c"):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+".py"))
    mod=importlib.util.module_from_spec(spec)
    sys.modules[name]=mod
    spec.loader.exec_module(mod)

from build_hc11_c import parser
from hc11_layout import Placement,PlacementError

class BuildDriverTests(unittest.TestCase):
    def test_required_source_verified_addresses(self):
        with self.assertRaises(SystemExit):
            parser().parse_args(["--out","/tmp/nowhere"])
    def test_no_stack_or_eeprom_reuse(self):
        for a,b in ((0x03a0,0x0410),(0x0e00,0x0eff)):
            with self.subTest(first=a),self.assertRaises(PlacementError):
                Placement(0x7201,0x0070,a,b,"source").check()
    def test_machine_link_requires_native_compiler(self):
        import inspect,build_hc11_c
        code=inspect.getsource(build_hc11_c.compile_and_link)
        self.assertIn("all_sources=True",code)
        self.assertIn("validate(plan,machine,sections,symbols)",code)
        self.assertIn('"-lgcc"',code)
        self.assertIn("--only-section=.c_code",code)
        self.assertIn("resolve_command(args.cc)",code)

if __name__=="__main__":unittest.main()
