"""Native C linker placement contract tests. No C cross compiler required."""
import importlib.util
from pathlib import Path
import sys
import unittest

FILE=Path(__file__).resolve().parents[1]/"hc11_layout.py"
SPEC=importlib.util.spec_from_file_location("hc11_layout",FILE)
MOD=importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name]=MOD
SPEC.loader.exec_module(MOD)

def plan(**changes):
    params={"asm_code_end":0x7201,"asm_ram_end":0x0050,
            "c_ram_first":0x0600,"c_ram_last":0x07FF,
            "authority":"test ASM11 symbols and independently audited free RAM"}
    params.update(changes)
    return MOD.Placement(**params)

class LayoutTests(unittest.TestCase):
    def test_source_driven_rom_and_c_state_layout(self):
        p=plan().check()
        self.assertEqual(p.code_start,0x7202)
        self.assertEqual(p.ram_length,0x200)
        ld=MOD.linker_script(p)
        self.assertIn('OUTPUT_FORMAT("elf32-m68hc11")',ld)
        self.assertIn("ORIGIN = 0x7202",ld)
        self.assertIn("ORIGIN = 0x0600",ld)
        self.assertIn("*(.softregs .softregs.*)",ld)
        self.assertIn("*(COMMON)",ld)
        self.assertIn('ASSERT(SIZEOF(.c_data)==0',ld)
        self.assertIn('ASSERT(__c_code_end <= 0xFFC0',ld)
        self.assertFalse(MOD.manifest(p)["approved_for_flash"])
    def test_reject_absent_authority(self):
        with self.assertRaises(MOD.PlacementError):plan(authority="").check()
    def test_reject_provisional_out_of_range_rom(self):
        for v in (0x7000,0xFFC0):
            with self.subTest(v=v),self.assertRaises(MOD.PlacementError):
                plan(asm_code_end=v).check()
    def test_no_stack_or_register_collision(self):
        for lo,hi in ((0x03a0,0x03c0),(0x03ff,0x0408),
                      (0x0df0,0x1000),(0x3000,0x30ff)):
            with self.subTest(lo=lo),self.assertRaises(MOD.PlacementError):
                plan(c_ram_first=lo,c_ram_last=hi).check()
    def test_no_asm_owned_overlap(self):
        with self.assertRaises(MOD.PlacementError):
            plan(c_ram_first=0x0040,c_ram_last=0x0060).check()
        with self.assertRaises(MOD.PlacementError):
            plan(c_ram_first=0x0500,c_ram_last=0x0506).check()
    def test_rom_capacity_and_approved_scratch_are_distinct(self):
        p=plan(asm_code_end=0xFEFF,c_ram_first=0x0400,c_ram_last=0x0410)
        self.assertEqual(p.code_start,0xFF00)
        self.assertEqual(MOD.manifest(p)["rom_capacity"],0xC0)
        with self.assertRaises(MOD.PlacementError):
            plan(asm_code_end=0xFFFF).check()

if __name__=="__main__":unittest.main()
