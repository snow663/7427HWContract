"""Fail-closed composition tests; synthetic bytes are NOT a firmware proof."""
import importlib.util
from pathlib import Path
import unittest

PATH=Path(__file__).resolve().parents[1]/"native/compose_hc11_rom.py"
SPEC=importlib.util.spec_from_file_location("compose_hc11_rom",PATH)
MOD=importlib.util.module_from_spec(SPEC)
import sys
sys.modules[SPEC.name]=MOD
SPEC.loader.exec_module(MOD)

def s1(address,data):
    payload=address.to_bytes(2,"big")+bytes(data)
    count=len(payload)+1
    checksum=(~(count+sum(payload)))&255
    return "S1"+(bytes([count])+payload+bytes([checksum])).hex().upper()[2:]

# The formatter below is intentionally independent from the ROM builder.
def record(address,data):
    b=bytes(data)
    count=len(b)+3
    check=(255-((count+(address>>8)+(address&255)+sum(b))&255))&255
    return f"S1{count:02X}{address:04X}"+b.hex().upper()+f"{check:02X}"

def stock():
    # One safe reset entry, one common trap for 31 reserved/other vectors.
    words=b"".join((0x7110 if x==0xfffe else 0x7120).to_bytes(2,"big")
                   for x in range(0xffc0,0x10000,2))
    return "\n".join([
        record(0x7100,[0xBD,0x71,0x30]),
        record(0x7110,[0x0F,0x3B]),
        record(0x7120,[0x0F,0x20,0xFE]),
        record(0x7130,[0x71,0x35]), # default unbound
        *[record(0xffc0+i*16,words[i*16:i*16+16]) for i in range(4)],
        "S9030000FC"
    ])
def native():
    return record(0x9000,[0x39])+"\nS9030000FC\n"
class CompositionTests(unittest.TestCase):
    def join(self,asm=None,compiled=None,nm="00009000 T pcm_hc11_c_entry",**kw):
        return MOD.compose(MOD.srecords(asm if asm is not None else stock()),
            MOD.srecords(compiled if compiled is not None else native()),
            nm,symbol="pcm_hc11_c_entry",link_address=kw.get("addr",0x7130),
            expected_unbound=kw.get("expected",0x7135))
    def test_linked_bytes_and_engine_off_vectors(self):
        image,report=self.join()
        self.assertEqual(len(image),0xc000)
        self.assertEqual(image[0x7130-0x4000:0x7132-0x4000],bytes.fromhex("9000"))
        self.assertEqual(image[0x9000-0x4000],0x39)
        self.assertEqual(report["non_reset_vectors"],"all engine-off safe trap")
        self.assertFalse(report["flash_ready"])
        self.assertEqual(image[0xfffe-0x4000:0x10000-0x4000],bytes.fromhex("7110"))
    def test_mismatched_assembly_word_rejected(self):
        with self.assertRaises(MOD.ImageError):self.join(expected=0x7199)
    def test_colliding_compiled_c_rejected(self):
        with self.assertRaises(MOD.ImageError):self.join(compiled=record(0x7110,[0x39]))
    def test_code_in_vector_region_rejected(self):
        with self.assertRaises(MOD.ImageError):self.join(compiled=record(0xffd6,[0x39]))
    def test_missing_or_fabricated_nm_symbol_rejected(self):
        with self.assertRaises(MOD.ImageError):self.join(nm="")
        with self.assertRaises(MOD.ImageError):self.join(nm="00009001 T pcm_hc11_c_entry")
    def test_unapproved_vector_rejected(self):
        orig=stock()
        original=record(0xffd0,[0x71,0x20]*8)
        changed=record(0xffd0,[0x90,0x00]+[0x71,0x20]*7)
        with self.assertRaises(MOD.ImageError):self.join(asm=orig.replace(original,changed))
    def test_corrupt_srec_checksum_and_duplicate_bytes_rejected(self):
        with self.assertRaises(MOD.ImageError):MOD.srecords("S10490003900")
        with self.assertRaises(MOD.ImageError):self.join(
           compiled=record(0x9000,[0x39])+"\n"+record(0x9000,[0x39]))
    def test_empty_records_and_address_range_rejected(self):
        with self.assertRaises(MOD.ImageError):MOD.srecords("")
        with self.assertRaises(MOD.ImageError):self.join(compiled=record(0x3000,[0x39]))

if __name__=="__main__":unittest.main()
