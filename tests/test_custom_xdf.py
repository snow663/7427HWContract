"""Definition semantics and reversible in-memory edits; never create a BIN."""
from __future__ import annotations
import gzip
import hashlib
import json
from pathlib import Path
import sys
import unittest
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
from build_custom_xdf import (CONTRACT,BASE,DEST,PROFILES,read_roles,build,data_element,footprint,program_fingerprint)
from verify_custom_xdf import verify,decode_scalar,encode_scalar,identify
from test_manual_idle import fixture as sparse_fixture,ASSEMBLY


class CustomXdf(unittest.TestCase):
    def items(self,profile):
        root=ET.parse(DEST/PROFILES[profile]).getroot()
        return {int(data_element(p).get('mmedaddress'),0):p for p in root
                if p.tag in ('XDFCONSTANT','XDFTABLE') and data_element(p).get('mmedaddress')}

    def test_regeneration_and_source_identity(self):
        contract=json.loads(CONTRACT.read_text()); roles=read_roles()
        self.assertEqual(hashlib.sha256(gzip.decompress(BASE.read_bytes())).hexdigest(),contract['base_xdf_sha256'])
        for profile,filename in PROFILES.items():
            generated,_=build(profile,contract,roles)
            self.assertEqual(generated,(DEST/filename).read_bytes())
        verify()

    def test_complete_manual_controls_and_units(self):
        items=self.items('manual_idle_dev'); memory=sparse_fixture(); s=ASSEMBLY.symbols
        expected={'cal_seed':38,'cal_start_air':60,'cal_start_div':4,'cal_tps_enter':2,'cal_tps_exit':3,
            'cal_rpm_enter':100,'cal_rpm_exit':200,'cal_qualify':16,'cal_deadband':25,'cal_kp':0.25,
            'cal_ki_up':0.015625,'cal_ki_down':0.015625,'cal_p_limit':24,'cal_i_limit':180,
            'cal_follower_cap':40,'cal_follower_decay':0.5,'cal_stall_error':200,'cal_stall_air':12,'cal_ac_air':5}
        for name,value in expected.items():self.assertAlmostEqual(decode_scalar(items[s[name]],memory),value,places=9,msg=name)
        for address in (s['cal_p_limit'],s['cal_i_limit'],s['cal_follower_decay']):
            e=data_element(items[address]);self.assertEqual(e.get('mmedelementsizebits'),'16');self.assertEqual(e.get('mmedtypeflags'),'0x00')
        rpm=items[0xff60]; self.assertEqual(rpm.find("XDFAXIS[@id='z']/MATH").get('equation'),'12.5 * X')
        self.assertEqual([p.get('value') for p in rpm.findall("XDFAXIS[@id='y']/LABEL")],[str(n) for n in range(0,257,16)])

    def test_word_byte_edits_round_trip_without_code_changes(self):
        items=self.items('manual_idle_dev'); m=sparse_fixture(); before=bytes(m)
        edits={0x9f11:45,0x9f16:112.5,0x9f1a:0.5,0x9f1d:24.5,0x9f22:0.75}
        for address,value in edits.items():
            encode_scalar(items[address],m,value);self.assertAlmostEqual(decode_scalar(items[address],m),value)
        self.assertEqual(m[0x9f1d:0x9f1f],bytes.fromhex('18 80'))
        self.assertEqual(m[0x9f22:0x9f24],bytes.fromhex('00 c0'))
        allowed=set().union(*(footprint(items[a]) for a in edits))
        self.assertTrue(all(a in allowed for a,(x,y) in enumerate(zip(before,m)) if x!=y))
        self.assertEqual(program_fingerprint(before,'manual_idle_dev'),program_fingerprint(m,'manual_idle_dev'))

    def test_retired_tables_and_false_enable_controls_are_absent(self):
        for profile in PROFILES:
            items=self.items(profile)
            for address in (0x428d,0x44f1,0x44f9,0x4503,0x450b,0x451b,0x46ed,0x46f0,0x48eb,0x4969,0x496a,0x4f26):
                self.assertNotIn(address,items)
            self.assertIn('RETARD',items[0x4152].findtext('title'))
            self.assertIn('Zero does not universally disable',items[0x4152].findtext('description'))
            self.assertIn('Single base spark',items[0x4169].findtext('title'))
        self.assertIn(0x4f50,self.items('reva'));self.assertNotIn(0x4f50,self.items('manual_idle_dev'))
        self.assertNotIn(0x9f00,self.items('reva'));self.assertIn(0x9f00,self.items('manual_idle_dev'))

    def test_legacy_transition_definitions_are_corrected(self):
        items=self.items('reva'); m=sparse_fixture()
        for address in (0x4f23,0x4f24,0x4f25):
            self.assertEqual(items[address].find('MATH').get('equation'),'X')
            self.assertEqual(decode_scalar(items[address],m),m[address])
        self.assertEqual(items[0x4f23].findtext('units'),'air units')
        self.assertEqual(items[0x4f24].findtext('units'),'main calls')

    def test_unknown_program_is_not_guessed(self):
        with self.assertRaisesRegex(ValueError,'65536'):identify(bytes(32768))
        with self.assertRaisesRegex(ValueError,'layout'):identify(bytes(65536))

    def test_removed_diagnostic_switches_are_not_advertised(self):
        for profile,filename in PROFILES.items():
            flags=[p.findtext('title','').lower() for p in ET.parse(DEST/filename).getroot().findall('XDFFLAG')]
            self.assertFalse(any(t.startswith(('code 16 ','code 77 ')) for t in flags))
            if profile=='manual_idle_dev':
                self.assertFalse(any(t.startswith(('code 35 ','code 36 ')) for t in flags))


if __name__=='__main__':unittest.main(verbosity=2)
