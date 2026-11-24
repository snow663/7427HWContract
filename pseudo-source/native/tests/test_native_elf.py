"""MC68HC11 ELF layout validation using synthetic objdump/nm evidence."""
from pathlib import Path
import importlib.util
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
for name in ("hc11_layout","verify_native_elf"):
    spec=importlib.util.spec_from_file_location(name,ROOT/(name+".py"))
    module=importlib.util.module_from_spec(spec)
    sys.modules[name]=module
    spec.loader.exec_module(module)
from hc11_layout import Placement
from verify_native_elf import NativeImageError, validate

PLAN=Placement(0x7201,0x0050,0x0600,0x07ff,
               "assembly-listing + audited C scratch memory")
ARCH="runtime.elf: file format elf32-m68hc11\narchitecture: m68hc11, flags 0x00000112\n"
SYMBOL="00007208 T pcm_hc11_c_entry"
HEADER="""Sections:
Idx Name          Size      VMA       LMA       File off  Algn
  0 .c_code       00000120  00007202  00007202  00000080  2**1
                  CONTENTS, ALLOC, LOAD, READONLY, CODE
  1 .c_state      00000040  00000600  00000600  00000000  2**1
                  ALLOC
  2 .comment      00000011  00000000  00000000  00000000  2**0
                  CONTENTS, READONLY
"""
def replace_once(src,old,new):
    assert old in src
    return src.replace(old,new,1)

class PostLinkTests(unittest.TestCase):
    def test_approved_machine_code_and_noinit_state(self):
        evidence=validate(PLAN,ARCH,HEADER,SYMBOL)
        self.assertEqual(evidence["code_first"],"0x7202")
        self.assertEqual(evidence["code_bytes"],0x120)
        self.assertEqual(evidence["state_bytes"],0x40)
        self.assertFalse(evidence["flash_ready"])
        self.assertFalse(evidence["bss_reset_initializer_verified"])
    def test_host_or_hc12_elf_rejected(self):
        for label in ("elf64-x86-64","elf32-m68hc12"):
            with self.subTest(label=label), self.assertRaises(NativeImageError):
                validate(PLAN,ARCH.replace("elf32-m68hc11",label),HEADER,SYMBOL)
    def test_noncode_entry_rejected(self):
        with self.assertRaises(NativeImageError):
            validate(PLAN,ARCH,HEADER,"00000600 B pcm_hc11_c_entry")
    def test_code_vector_overlap_rejected(self):
        data=replace_once(HEADER,"00000120  00007202","00009000  00007202")
        with self.assertRaises(NativeImageError):
            validate(PLAN,ARCH,data,SYMBOL)
    def test_stack_and_scratch_spill_rejected(self):
        data=replace_once(HEADER,"00000040  00000600","00000220  00000600")
        with self.assertRaises(NativeImageError):
            validate(PLAN,ARCH,data,SYMBOL)
        data=replace_once(HEADER,"00000040  00000600  00000600",
                         "00000040  000003D0  000003D0")
        with self.assertRaises(NativeImageError):
            validate(PLAN,ARCH,data,SYMBOL)
    def test_unplanned_allocations_and_initialized_data_rejected(self):
        data=HEADER+"\n  3 .softregs  0000000A  00000680  00000680  00000200 2**0\n                  ALLOC\n"
        with self.assertRaises(NativeImageError):
            validate(PLAN,ARCH,data,SYMBOL)
        data=replace_once(HEADER,".c_state      00000040",".c_data       00000040")
        with self.assertRaises(NativeImageError):
            validate(PLAN,ARCH,data,SYMBOL)
        data=replace_once(HEADER,"                  ALLOC\n","                  CONTENTS, ALLOC, LOAD\n")
        with self.assertRaises(NativeImageError):
            validate(PLAN,ARCH,data,SYMBOL)
    def test_provenance_required(self):
        bad=Placement(PLAN.asm_code_end,PLAN.asm_ram_end,
                      PLAN.c_ram_first,PLAN.c_ram_last,"")
        with self.assertRaises(ValueError):
            validate(bad,ARCH,HEADER,SYMBOL)

if __name__=="__main__":unittest.main()
