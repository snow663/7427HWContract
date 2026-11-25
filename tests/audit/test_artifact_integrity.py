"""Independent negative tests for native artifacts and HC11 bus apertures.

Set AUDIT_REPO to a baseline checkout to demonstrate the pre-fix failures.
All code bytes here are synthetic; these tests do not qualify firmware.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(os.environ.get("AUDIT_REPO", Path(__file__).resolve().parents[2]))
NATIVE = ROOT / "pseudo-source/native"
sys.path.insert(0, str(NATIVE))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    sys.modules[name] = result
    spec.loader.exec_module(result)
    return result


ROM = module("compose_hc11_rom", NATIVE / "compose_hc11_rom.py")
BOOT = module("compose_hc11_linked_boot", NATIVE / "compose_hc11_linked_boot.py")


def asm_image():
    vectors = b"".join((0x7110 if a == 0xFFFE else 0x7120).to_bytes(2, "big")
                       for a in range(0xFFC0, 0x10000, 2))
    return [ROM.Segment(a, bytes(b)) for a, b in (
        (0x7110, [0x0F, 0x39]), (0x7120, [0x0F, 0x20, 0xFE]),
        (0x7130, [0x71, 0x35]),
        (0x7140, [0, 0, 0, 0, 0, 0x71, 0x48]),
        (0x7148, [0x7E, 0x71, 0x20]), (0xFFC0, vectors))]


CODE = [ROM.Segment(0x9000, b"\x39\x39")]
NM = "00009000 T pcm_hc11_c_entry\n00009001 T pcm_hc11_c_entry_reset\n"
FIELDS = {
    "schema": "7427-asm11-native-c-boot-bind-v1",
    "authority": "synthetic audit fixture; no target proof",
    "isr_call_word": "0x7130", "expected_isr_unbound": "0x7135",
    "boot_token": "0x7140", "boot_state_start_word": "0x7141",
    "boot_state_end_word": "0x7143", "boot_reset_call_word": "0x7145",
    "expected_boot_reset_unbound": "0x7148",
}


def report_fixture():
    report = {
        "schema": "7427-linked-c-image-inspection-v1",
        "native_architecture": "MC68HC11", "flash_ready": False,
        "source_authority": "synthetic audit fixture; no target proof",
        "linked_entry": "0x9000", "linked_reset_entry": "0x9001",
        "state_first": "0x0600", "state_end_exclusive": "0x0640",
        "state_bytes": 0x40, "state_capacity": 0x200,
        "linked_elf_sha256": "0" * 64,
    }
    # Independent implementation of the documented binding format. The
    # baseline ignores this binding, which is precisely the negative test.
    code_bytes = b"".join((s.address + i).to_bytes(2, "big") + bytes([v])
                          for s in CODE for i, v in enumerate(s.data))
    report["artifact_binding"] = {
        "schema": "7427-native-artifact-binding-v1",
        "code_sha256": hashlib.sha256(code_bytes).hexdigest(),
        "nm_sha256": hashlib.sha256(NM.encode("utf-8")).hexdigest(),
        "inspection_sha256": hashlib.sha256(json.dumps(
            report, sort_keys=True, separators=(",", ":"),
            ensure_ascii=True).encode("ascii")).hexdigest(),
    }
    return report


class NativeArtifactIntegrity(unittest.TestCase):
    def compose(self, *, asm=None, code=None, nm=NM, report=None):
        return BOOT.compose_boot(asm_image() if asm is None else asm,
                                 CODE if code is None else code, nm,
                                 report_fixture() if report is None else report,
                                 FIELDS)

    def test_valid_synthetic_bundle_still_composes(self):
        image, report = self.compose()
        self.assertEqual(image[0x9000 - 0x4000:0x9002 - 0x4000], b"\x39\x39")
        self.assertFalse(report["flash_ready"])

    def test_missing_reset_body_rejected(self):
        with self.assertRaises(ROM.ImageError):
            self.compose(asm=[s for s in asm_image() if s.address != 0x7110])

    def test_missing_trap_body_rejected(self):
        with self.assertRaises(ROM.ImageError):
            self.compose(asm=[s for s in asm_image() if s.address != 0x7120])

    def test_code_changed_without_new_inspection_rejected(self):
        with self.assertRaises(ROM.ImageError):
            self.compose(code=[ROM.Segment(0x9000, b"\x01\x39")])

    def test_nm_changed_without_new_inspection_rejected(self):
        with self.assertRaises(ROM.ImageError):
            self.compose(nm=NM + "00009000 T unexpected_symbol\n")

    def test_consistent_but_stale_bss_report_rejected(self):
        report = report_fixture()
        report.update(state_first="0x0700", state_end_exclusive="0x0740")
        with self.assertRaises(ROM.ImageError):
            self.compose(report=report)

    def test_unbound_report_rejected(self):
        report = report_fixture()
        del report["artifact_binding"]
        with self.assertRaises(ROM.ImageError):
            self.compose(report=report)


BUS_PROBE = r'''
#include "hc11_bus.h"
#include <stdio.h>
static PcmStatus r8(void *c, uint16_t a, uint8_t *v)
{ (void)c; (void)a; *v=0; return PCM_OK; }
int main(void) {
    PcmHc11Bus bus={0}; PcmPlatform p={0}; PcmHc11Io io={0};
    io.read8=r8;
    PcmHc11Window invalid={0x0400,0x1fff,PCM_HC11_EXTERNAL_GEN,PCM_HC11_R8};
    PcmStatus s=pcm_hc11_bus_bind(&bus,&p,&io,&invalid,1);
    if(s!=PCM_BAD_CONFIGURATION) {
        fprintf(stderr,"accepted 0400..1fff across conditional EEPROM 0e00..0fff\n");
        return 1;
    }
    if(p.context!=NULL || p.read8!=NULL) return 2;
    PcmHc11Window valid[]={
        {0x0400,0x0dff,PCM_HC11_EXTERNAL_GEN,PCM_HC11_R8},
        {0x0e00,0x0fff,PCM_HC11_CONDITIONAL_EEPROM,PCM_HC11_R8},
        {0x1000,0x1fff,PCM_HC11_EXTERNAL_GEN,PCM_HC11_R8}};
    if(pcm_hc11_bus_bind(&bus,&p,&io,valid,3)!=PCM_OK) return 3;
    uint8_t v=99;
    if(p.read8(p.context,0x0e00,&v)!=PCM_OK || v!=0) return 4;
    return 0;
}
'''


class BusApertureIntegrity(unittest.TestCase):
    def test_every_address_in_a_window_has_the_declared_resource(self):
        cc = shutil.which(os.environ.get("CC", "cc"))
        self.assertIsNotNone(cc, "a host C compiler is required for this audit")
        with tempfile.TemporaryDirectory() as directory:
            d = Path(directory)
            (d / "probe.c").write_text(BUS_PROBE)
            subprocess.run([cc, "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-I", str(ROOT / "pseudo-source/include"),
                            str(d / "probe.c"),
                            str(ROOT / "pseudo-source/platform/hc11_bus.c"),
                            "-o", str(d / "probe")], check=True,
                           capture_output=True, text=True)
            result = subprocess.run([str(d / "probe")], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
