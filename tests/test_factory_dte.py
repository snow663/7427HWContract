"""Bounded actual-ROM checks of high-impact documentation reductions.

No full transmission/device simulation is asserted. Fixtures explicitly set
RAM and counterfactual calibration bytes where a branch boundary is tested.
The runner rejects a partial multi-bit BRSET: the existing general CPU has
an any-bit implementation, and these tests do not use it to prove that case.
"""
from __future__ import annotations

import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import verify_factory_dte as proof
from build_factory_scheduler import recorded_rom
from factory_integer_replay import IntegerMemory
from factory_rom_decode import decode
from factory_scheduler_replay import HC11CPU


def s8(n):return (n&255)-256 if n&128 else n&255
def clamp(n,lo,hi):return min(hi,max(lo,n))
def q(n,d):return (n<<16)//d if d>n else 65535
def r8(a,b):return (a*b+128)>>8


class DTEFixture:
    def __init__(self,rom):
        self.memory=IntegerMemory(rom);self.cpu=HC11CPU(self.memory)
        self.cpu.s.sp=0x03F4;self.cpu.s.ccr=0xC0

    def byte(self,a,v):self.memory.mem[a]=v&255
    def word(self,a,v):self.memory.mem[a:a+2]=(v&65535).to_bytes(2,'big')
    def readword(self,a):return self.memory.read16(a)

    def run(self,start,stop=0x0200,budget=10000):
        self.cpu.s.pc=start
        for _ in range(budget):
            pc=self.cpu.s.pc
            if pc==stop:return
            # This guard does not execute or repair the branch; it excludes
            # cases outside the existing CPU's independently usable subset.
            i=decode(lambda a,n:bytes(self.memory.read8(a+j) for j in range(n)),pc)
            if i.op=='BRSET' and i.mask.bit_count()>1:
                address=i.value
                if i.mode=='indexed_x':address=(address+self.cpu.s.x)&65535
                if i.mode=='indexed_y':address=(address+self.cpu.s.y)&65535
                selected=self.memory.read8(address)&i.mask
                if selected not in {0,i.mask}:raise AssertionError('Partial multi-bit BRSET is outside bounded CPU proof')
            self.memory.pc=pc;self.cpu.step()
        raise AssertionError(f'DTE execution budget at{self.cpu.s.pc:04X}')

    def call(self,entry):
        self.cpu._push16(0x0200);self.run(entry)


class FactoryDTETests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rom=recorded_rom(json.loads(proof.EVIDENCE.read_text()))
    def fixture(self):return DTEFixture(self.rom)

    def test_priority_descriptors_for_every_mask_and_valid_gear_column(self):
        f=self.fixture()
        for base,_ in proof.DESCRIPTORS:
            stop,stride=self.rom.read(base,2)
            for gear in range(stride//2):
                for selector in range(256):
                    expected_c=1;expected_x=None
                    for k in range(8):
                        row=base+2+2*gear+stride*k
                        if selector&(1<<k):
                            expected_x=self.rom.word(row);expected_c=int(expected_x==0);break
                        if stop&(1<<k):expected_x=row;break
                    f.cpu.s.a=selector;f.cpu.s.b=gear;f.cpu.s.x=base
                    f.call(0xD8FE)
                    self.assertEqual((f.cpu.s.x,f.cpu.s.ccr&1),(expected_x,expected_c),(base,gear,selector))
                    self.assertEqual((f.cpu.s.a,f.cpu.s.b,f.cpu.s.sp),(selector,gear,0x03F4))

    def test_capture_no_change_returns_timeout_not_saved_speed(self):
        for timeout,expected in [(5,4),(2,1),(1,0),(0,0)]:
            f=self.fixture();f.cpu.s.y=0xB9;f.cpu.s.x=3000;f.cpu.s.b=9
            f.byte(0xB9,7);f.byte(0xC1,7);f.byte(0xBC,timeout);f.word(0xBD,0x4567)
            f.call(0xE58C)
            self.assertEqual(f.cpu.s.d,expected)
            self.assertEqual(f.readword(0xBD),0x4567 if timeout>1 else 0)
            self.assertEqual(f.memory.mem[0xBC],expected)

    def test_capture_changed_batch_uses_two_fractional_divides_and_first_batch_seed(self):
        for old_timeout in [0,1,12]:
            f=self.fixture();f.cpu.s.y=0xB9;f.cpu.s.x=3000;f.cpu.s.b=9
            f.byte(0xB9,255);f.byte(0xC1,1);f.byte(0xBC,old_timeout)
            f.word(0xBA,0xFF00);f.word(0xBF,0x02E8);f.word(0xBD,0x4567)
            f.call(0xE58C)
            expected=q(q(16,3000),1000) if old_timeout else 0x4567
            self.assertEqual(f.cpu.s.d,expected)
            self.assertEqual(f.readword(0xBD),expected)
            self.assertEqual((f.memory.mem[0xB9],f.readword(0xBA),f.memory.mem[0xBC]),(1,0x02E8,9))

    def test_force_feedback_signed_deadband_fraction_and_rail(self):
        rng=random.Random(0x317C)
        cases=[(1,0,0,0,70,41),(0,1,0,3000,70,41),(57,255,-128,2,255,255),
               (255,0,127,0xDFF,255,255),(0,255,127,0xE00,255,255)]
        cases += [(rng.randrange(256),rng.randrange(256),rng.randrange(-128,128),rng.randrange(0xE01),
                   rng.randrange(256),rng.randrange(256)) for _ in range(96)]
        for reference,feedback,old_error,acc,g1,g2 in cases:
            f=self.fixture();f.byte(0x4C,0x20);f.byte(0x14D,reference);f.byte(0x14E,feedback)
            f.byte(0x14F,old_error);f.word(0x150,acc);f.byte(0x153,g1);f.byte(0x154,g2)
            e=clamp(min(reference,57)-feedback,-128,127)
            if e in {-1,1}:e=0
            delta=clamp(e*g1-old_error*g2,-32768,32767)
            expected=clamp(acc+(delta+2)//4,0,0xE00)
            f.run(0x7C13,0x7CA8)
            self.assertEqual((s8(f.memory.mem[0x14F]),f.readword(0x150)),(e,expected),(reference,feedback,old_error,acc,g1,g2))
            self.assertEqual(f.memory.mem[0x14C],min(255,(q(expected,0xE00)+128)>>8))

    def test_central_log_intersects_candidates_and_commits_only_after_threshold(self):
        f=self.fixture();f.byte(0x4F,0x80)
        f.memory.mem[0x5B00:0x5B12]=bytes([255])*18
        f.memory.mem[0x4E2E:0x4E32]=bytes([2,2,1,2])
        f.byte(0x16,0x80);f.byte(0x17,0x80)
        f.run(0xE132,0xE1C7)
        self.assertEqual((f.memory.mem[0x56],f.memory.mem[0x57]),(0x80,0x80))
        self.assertEqual(f.memory.mem[0xB],0)
        f.byte(0x17,0);f.byte(0x18,0x40)
        f.run(0xE132,0xE1C7)
        self.assertEqual((f.memory.mem[0x56],f.memory.mem[0x57],f.memory.mem[0x58]),(0x80,0,0))
        f.run(0xE132,0xE1C7)
        self.assertEqual(f.memory.mem[0xB],0)
        f.run(0xE132,0xE1C7)
        self.assertEqual(list(f.memory.mem[0xB:0x14]),[0x80]+[0]*8)
        self.assertEqual(list(f.memory.mem[0x56:0x5F]),[0]*9)
        self.assertEqual(f.memory.mem[0x15],(-sum(f.memory.mem[0xB:0x15]))&255)
        self.assertEqual(f.memory.mem[0x71]&1,1)

    def test_a_disappearing_candidate_does_not_log_a_newly_arrived_fault(self):
        f=self.fixture();f.byte(0x56,0x80);f.byte(0x16,0);f.byte(0x17,0x80)
        f.byte(0x22B,1);f.memory.mem[0x4E2E:0x4E32]=bytes([0,0,0,0])
        f.run(0xE132,0xE1C7)
        self.assertEqual(list(f.memory.mem[0xB:0x14]),[0]*9)
        self.assertEqual(list(f.memory.mem[0x56:0x5F]),[0]*9)
        f.run(0xE132,0xE1C7)
        self.assertEqual(f.memory.mem[0x57],0x80)

    def test_masked_clears_have_different_bank_and_counter_footprints(self):
        for entry,mask_address in [(0xF333,0xF377),(0xF380,0xF3DB)]:
            f=self.fixture()
            for base in [0xB,0x16,0x56]:f.memory.mem[base:base+9]=bytes([255])*9
            f.byte(0x25,71);f.byte(0x2E,83);f.byte(0x14,5)
            f.call(entry);keep=self.rom.read(mask_address,9)
            self.assertEqual(bytes(f.memory.mem[0xB:0x14]),keep)
            self.assertEqual(bytes(f.memory.mem[0x16:0x1F]),keep)
            self.assertEqual(bytes(f.memory.mem[0x56:0x5F]),keep if entry==0xF333 else bytes([255])*9)
            self.assertEqual((f.memory.mem[0x25],f.memory.mem[0x2E]),(71,83))
            self.assertEqual(f.memory.mem[0x15],(-sum(f.memory.mem[0xB:0x15]))&255)

    def test_reaction_alternate_mask_is_opposite_for_general_and_special_summary(self):
        for alternate in [0,1]:
            f=self.fixture();f.byte(0x16,1);f.byte(0x5B2B,1);f.byte(0x5B34,alternate)
            f.memory.mem[0xE717:0xE720]=bytes([255])*9
            f.memory.mem[0xE720:0xE729]=bytes([255])*9
            f.call(0xE62D)
            self.assertEqual(bool(f.memory.mem[0x98]&8),bool(alternate))
            f.call(0xE654)
            self.assertEqual(bool(f.memory.mem[0x98]&0x10),not alternate)

    def test_EGR_zero_nonlinear_and_test_phase_have_distinct_retention(self):
        for linear,test in [(False,False),(True,False),(False,True),(True,True)]:
            f=self.fixture();f.byte(0x400D,2 if linear else 0);f.byte(0x70,4 if test else 0)
            f.byte(0x1AE,0);f.byte(0x1B9,40);f.word(0x1BC,0x1234);f.word(0x1BE,0x5678)
            f.call(0xD1F6)
            self.assertEqual(f.memory.mem[0x1AF],0)
            self.assertEqual((f.readword(0x1BC),f.readword(0x1BE)),(0,0) if linear or test else (0x1234,0x5678))
            if linear and not test:self.assertEqual(f.memory.mem[0x1BA],40)

    def test_purge_phase_freeze_and_hot_shortcut_precede_DFCO(self):
        f=self.fixture();f.byte(2,0x1A);f.byte(0x1D6,123);f.byte(0x1D7,77);f.byte(0x1D8,44)
        f.call(0xD2B2)
        self.assertEqual(list(f.memory.mem[0x1D6:0x1D9]),[123,77,44])
        f.byte(2,0x0A);f.byte(0x400C,0x80);f.byte(6,101);f.byte(0x402C,100)
        f.word(0xFD,0);f.word(0x402D,5);f.byte(0x46,8)
        f.call(0xD2B2)
        self.assertEqual(list(f.memory.mem[0x1D6:0x1D9]),[255,77,44])
        self.assertEqual(f.memory.mem[0x41]&0x80,0x80)

    def test_first_high_voltage_observation_retains_outputs_second_clears(self):
        f=self.fixture();f.byte(0x400B,0);f.byte(0x400E,0);f.byte(0x400F,0)
        f.byte(0xA7,171);f.byte(0x4F,0x80);f.byte(0x46,4);f.byte(0x1D6,123)
        f.call(0xCCC1)
        self.assertEqual((f.readword(0x3FDA),f.readword(0x3FD6)),(0xDFFF,0xB000|(123<<3)))
        f.call(0xCCC1)
        self.assertEqual((f.readword(0x3FDA),f.readword(0x3FD6),f.memory.mem[0x1D6]),(0xD000,0xB000,0))

    def test_solenoid_pattern_current_enable_and_TCC_are_separate_fields(self):
        for gear,pattern in enumerate([1,0,2,3]):
            for fault in [0,8]:
                f=self.fixture();f.byte(0xD9,gear);f.byte(0x4C,0x9C);f.byte(0x99,fault)
                f.byte(0x400F,0);f.word(0x126,0x1234);f.word(0x12B,0x1000);f.byte(0x8A,4)
                f.call(0xC514)
                self.assertEqual(f.memory.mem[0x4C],0x9C|pattern|(0 if fault else 0x20))
                self.assertEqual(f.readword(0x306A),0x7F12)
                self.assertEqual(f.memory.mem[0x8B]&1,1)

    def test_TCC_basecurve_extended_arithmetic_and_service_override(self):
        for gain in [0,32,128,255]:
            for first,second in [(0,255),(255,0),(128,192)]:
                for tps in [0,7,16,255]:
                    for bias in [0,127,128,255]:
                        f=self.fixture();f.cpu.s.x=0x6DB3;f.cpu.s.y=0x10B
                        f.memory.mem[0x6E2A:0x6E2A+17]=bytes([gain])*17
                        knots=bytes([first]+[second]*16);f.memory.mem[0x6DB3:0x6DB3+17]=knots
                        f.byte(0xB2,tps);f.byte(0x10C,bias)
                        k=tps>>4;frac=(tps&15)<<4;a,b=knots[k:k+2]
                        value=a+r8(b-a,frac) if b>=a else a-r8(a-b,frac)
                        p=2*gain*(value-first)+(first<<8)
                        if p<0:p=0
                        elif p>65535:p=65535
                        else:p=min(65535,p+(p>>8)+int((p&255)+(p>>8)>255))
                        biased=(p>>8)-128+s8(bias)
                        expected=0 if biased < -128 else 65535 if biased > 127 else ((biased+128)<<8)|(p&255)
                        f.call(0xC271)
                        self.assertEqual(f.readword(0xF1),expected,(gain,first,second,tps,bias,p))
        for override in [1,100,255]:
            f=self.fixture();f.cpu.s.x=0x6DB3;f.cpu.s.y=0x10B;f.byte(0x10B,override)
            f.call(0xC271);self.assertEqual(f.readword(0xF1),override*257)


if __name__=='__main__':unittest.main()
