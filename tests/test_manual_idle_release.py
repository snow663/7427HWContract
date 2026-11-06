"""Rev B gate tests execute emitted HC11, with exact Rev A reference excerpts."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'tests')]
from manual_idle_asm import assemble
from manual_idle_overlay import EXPECTED_SHA
from build_manual_idle_release import GATE_SOURCE
from test_manual_idle import fixture,execute,put,word

GATE=assemble(GATE_SOURCE)


def reference():
    m=fixture()
    evidence=json.loads((ROOT/'maps/maintenance/manual_idle_release_evidence.json').read_text())
    assert evidence['image_sha256']==EXPECTED_SHA
    for r in evidence['ranges']:
        lo,hi=int(r['start'],16),int(r['end_exclusive'],16)
        raw=bytes.fromhex(r['bytes']);assert len(raw)==hi-lo
        m[lo:hi]=raw
    return m


def candidate():
    m=reference()
    for a,v in GATE.memory.items():m[a]=v
    m[0xa97a:0xa9e0]=b'\x7e\x9f\x40'+b'\xff'*(0xa9e0-0xa97d)
    return m


class ReleaseGate(unittest.TestCase):
    def seed(self,m):
        m[0x857]=68;m[0x63]=120;m[0x46]=8;m[0x51]=0xc7
        m[0x1f9]=m[0x413c];m[0x208]=99
        put(m,0x1fd,90);put(m,0x1f2,0x5678)
        return m

    def test_active_dfco_matches_resident_math_and_latch(self):
        for coolant in (0,15,63,128,200,255):
            for bias in (0,15,128,255):
                for base in (0,43,200,255):
                    old=self.seed(reference());new=self.seed(candidate())
                    for m in (old,new):
                        m[0x1f9]=coolant;m[0x413c]=bias;m[0x4152]=base
                    a,ac,_=execute(old,0xa97a,0xa9e0)
                    b,bc,_=execute(new,0xa97a,0xa9e0)
                    self.assertEqual(a.mem[:0x300],b.mem[:0x300])
                    self.assertEqual((ac.s.d,ac.s.x),(bc.s.d,bc.s.x))

    def test_no_recovery_after_fuel_returns_and_no_startup_word_clear(self):
        for latch in (0,0x20):
            for history in (0,0x5678,0xffff):
                m=self.seed(candidate());m[0x46]=0;m[0x51]|=latch;put(m,0x1f2,history)
                a,c,pcs=execute(m,0xa97a,0xa9e0)
                self.assertEqual(word(a.mem,0x1fd),90)
                self.assertEqual(word(a.mem,0x1f2),history)
                self.assertEqual(a.mem[0x208],0)
                self.assertEqual(a.mem[0x51],m[0x51]&~0x20)
                self.assertFalse(any(0xa97d<=p<0xa9e0 for p in pcs))

    def test_target_margin_equality_and_overflow(self):
        for target in (0,1,68,112,240,255):
            for margin in (0,1,16,255):
                for rpm in (0,1,67,68,83,84,85,127,254,255):
                    m=self.seed(candidate());m[0x857]=target;m[0x9f17]=margin;m[0x63]=rpm
                    a,_,_=execute(m,0xa97a,0xa9e0)
                    active=rpm>target+margin
                    self.assertEqual(bool(a.mem[0x51]&0x20),active)
                    self.assertEqual(word(a.mem,0x1f2),0 if active else 0x5678)
                    self.assertEqual(word(a.mem,0x1fd),90-m[0x4152] if active else 90)
                    self.assertEqual(a.mem[0x208],m[0x4152] if active else 0)

    def test_near_idle_ignores_stale_retard_and_preserves_other_flag_bits(self):
        for flags in range(256):
            m=self.seed(candidate());m[0x63]=84;m[0x51]=flags
            a,_,_=execute(m,0xa97a,0xa9e0)
            self.assertEqual(a.mem[0x51],flags&~0x20)
            self.assertEqual(word(a.mem,0x1f2),0x5678)
            self.assertEqual(word(a.mem,0x1fd),90)


if __name__=='__main__':unittest.main()
