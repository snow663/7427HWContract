"""Native ASM11/C boot binding; synthetic machine bytes only."""
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
for name in ("compose_hc11_rom","compose_hc11_linked_boot"):
    s=importlib.util.spec_from_file_location(name,ROOT/(name+".py"))
    m=importlib.util.module_from_spec(s)
    sys.modules[name]=m
    s.loader.exec_module(m)
from compose_hc11_rom import ImageError,srecords

def record(a,data):
    payload=bytes(data)
    count=len(payload)+3
    chk=(255-((count+(a>>8)+(a&255)+sum(payload))&255))&255
    return f"S1{count:02X}{a:04X}"+payload.hex().upper()+f"{chk:02X}"

WORDS=b"".join((0x7110 if a==0xfffe else 0x7120).to_bytes(2,"big")
               for a in range(0xffc0,0x10000,2))
def assembler():
    return srecords("\n".join([
      record(0x7110,[0x0f,0x39]),record(0x7120,[0x0f,0x20,0xfe]),
      record(0x7130,[0x71,0x35]), # original ISR unbound target
      record(0x7140,[0,0,0,0,0,0x71,0x48]), # token, state words, reset unbound
      record(0x7148,[0x7e,0x71,0x20]), # safe unbound jump to trap
      *[record(0xffc0+i*16,WORDS[i*16:i*16+16]) for i in range(4)]
    ]))
def compiled():
    return srecords(record(0x9000,[0x39,0x39]))
def fields():
    return {"schema":"7427-asm11-native-c-boot-bind-v1",
        "authority":"verified ASM11 listing fixture",
        "isr_call_word":"0x7130","expected_isr_unbound":"0x7135",
        "boot_token":"0x7140",
        "boot_state_start_word":"0x7141",
        "boot_state_end_word":"0x7143",
        "boot_reset_call_word":"0x7145",
        "expected_boot_reset_unbound":"0x7148"}
def evidence():
    return {"schema":"7427-linked-c-image-inspection-v1",
        "native_architecture":"MC68HC11","flash_ready":False,
        "source_authority":"MC68HC11 linker section test",
        "linked_entry":"0x9000",
        "linked_reset_entry":"0x9001",
        "state_first":"0x0600",
        "state_end_exclusive":"0x0640",
        "state_bytes":0x40,"state_capacity":0x200}
NM="00009000 T pcm_hc11_c_entry\n00009001 T pcm_hc11_c_entry_reset"

class NativeBootBinding(unittest.TestCase):
    def join(self,*,asm=None,code=None,symbols=NM,report=None,bindings=None):
        return sys.modules["compose_hc11_linked_boot"].compose_boot(
            asm if asm is not None else assembler(),
            code if code is not None else compiled(),
            symbols,report if report is not None else evidence(),
            bindings if bindings is not None else fields())
    def test_qualified_link_and_all_32_vectors_unchanged(self):
        image,report=self.join()
        def addr(a):return image[a-0x4000]
        self.assertEqual(len(image),0xc000)
        self.assertEqual(addr(0x7130)*256+addr(0x7131),0x9000)
        self.assertEqual(addr(0x7140),0xc3)
        self.assertEqual(image[0x7141-0x4000:0x7145-0x4000],
                         bytes.fromhex("06000640"))
        self.assertEqual(image[0x7145-0x4000:0x7147-0x4000],
                         bytes.fromhex("9001"))
        self.assertEqual(image[0xffc0-0x4000:0x10000-0x4000],WORDS)
        self.assertFalse(report["flash_ready"])
    def test_existing_token_or_wrong_unbound_rejected(self):
        edited=fields();edited["expected_boot_reset_unbound"]="0x7135"
        with self.assertRaises(ImageError):self.join(bindings=edited)
        changed=assembler()
        # Overwrite one token byte by an independent SRecord replacement
        image=[]
        for segment in changed:
            if segment.address==0x7140:
                image.append(type(segment)(segment.address,bytes([0xc3])+segment.data[1:]))
            else:image.append(segment)
        with self.assertRaises(ImageError):self.join(asm=image)
    def test_word_collision_and_code_spill_rejected(self):
        edit=fields();edit["boot_reset_call_word"]="0x7143"
        with self.assertRaises(ImageError):self.join(bindings=edit)
        edit=fields();edit["boot_token"]="0x9000"
        with self.assertRaises(ImageError):self.join(bindings=edit)
    def test_report_drift_and_missing_reset_code_rejected(self):
        edit=evidence();edit["state_bytes"]=65
        with self.assertRaises(ImageError):self.join(report=edit)
        edit=evidence();edit["linked_reset_entry"]="0x9002"
        with self.assertRaises(ImageError):self.join(report=edit)
        edit=evidence();edit["state_first"]=None
        with self.assertRaises(ImageError):self.join(report=edit)
        with self.assertRaises(ImageError):self.join(symbols="00009000 T pcm_hc11_c_entry")
    def test_untrusted_or_stale_authority_rejected(self):
        edit=fields();edit["authority"]=""
        with self.assertRaises(ImageError):self.join(bindings=edit)
        edit=evidence();edit["source_authority"]=""
        with self.assertRaises(ImageError):self.join(report=edit)

if __name__=="__main__":unittest.main()
