"""Execute selected factory masked intervals and complete REF/SCI handlers.

Nominal instruction costs are independent of the CPU core's accounting.
Peripheral samples and interrupt arrivals remain supplied test inputs.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_factory_scheduler import recorded_rom
from factory_hc11_cycle_subset import cycles
from factory_rom_decode import decode
from verify_factory_ownership import EVIDENCE
import verify_factory_masked_timing as proof
from test_factory_stack_and_shared_state import Replay


class Meter(Replay):
    def __init__(self,rom):
        super().__init__(rom)
        self.e=0
        self.invocations=[]

    def step(self):
        i=decode(self.rom.read,self.cpu.s.pc)
        super().step()
        self.e+=cycles(i)

    def irq(self,vector,before_step=None):
        start=self.e
        self.e+=12
        super().irq(vector,before_step)
        self.invocations.append((vector,self.e-start))


class FactoryMaskedTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=recorded_rom(json.loads(EVIDENCE.read_text()))
        cls.generated=proof.build(cls.rom)
        cls.masked={int(r['start'],16):r for r in csv.DictReader(io.StringIO(cls.generated[proof.FILES[0]]))}
        cls.irqs={(int(r['entry'],16),r['contract']):r for r in csv.DictReader(io.StringIO(cls.generated[proof.FILES[1]]))}

    def test_all_sei_sites_and_distinct_other_irq_handlers_are_accounted_for(self):
        for name,content in self.generated.items():
            self.assertEqual((proof.OUT/name).read_text(),content,name)
        meta=json.loads(self.generated[proof.FILES[3]])
        self.assertEqual(meta['SEI_sites'],29)
        self.assertEqual(meta['ordinary_SEI_rows'],27)
        self.assertEqual(meta['ordinary_max_start_pcs'],['7AB7'])
        self.assertEqual(meta['ordinary_masked_max_E'],709)
        self.assertEqual(self.masked[0xF616]['scope'],'stock_schedule_excludes')
        self.assertEqual(len({entry for entry,contract in self.irqs}),8)
        self.assertEqual(meta['REF_latch_set_only_writer_pcs'],['7725','7742','775B'])
        self.assertEqual(meta['SCI_root_chains']['51BF'],['51BF','53A8','53C9'])
        self.assertEqual(meta['SCI_root_chains']['FBD7'],['FBD7','FBE0','FBE9'])

    def test_complete_adc_wrapper_reaches_709_cycle_envelope_with_three_timeouts(self):
        f=Meter(self.rom)
        f.memory.adc_ready=False
        f.call(0x7AB7)
        self.assertEqual(f.e,709)
        self.assertEqual(f.trace.count(0xF267),36)
        self.assertEqual(f.trace.count(0xF26E),3)
        self.assertEqual(f.cpu.s.sp,0x03F4)
        self.assertEqual(f.cpu.s.ccr&0x10,0)
        self.assertEqual(f.memory.mem[0x3A]&1,1)
        self.assertEqual(f.trace[-2:],[0x7ABB,0x7ABC])

    def test_refresh_async_and_output_intervals_include_the_instruction_after_cli(self):
        for start,stop in [(0x7483,0x7473),(0x84A9,0x84B1),(0xF3EE,0x7000)]:
            f=Meter(self.rom)
            f.cpu.s.x=0x0050
            f.cpu.s.d=0x0100
            f.word(0x3FFC,0xB93E)
            if start==0xF3EE:
                f.call(start)
            else:
                f.run(start,stop)
            self.assertLessEqual(f.e,int(self.masked[start]['nominal_upper_E']))
            self.assertEqual(f.cpu.s.ccr&0x10,0)
            self.assertEqual(f.trace[-1],int(self.masked[start]['unmask_end_instructions'],16))
            if start==0x7483:
                self.assertEqual(f.e,97)

    def test_complete_ref_handlers_stay_below_the_conservative_envelope(self):
        high=int(self.irqs[(0x74EA,'resident_handler')]['including_IRQ_entry12_E'])
        for qualification,bypass,period in [(0,0,0),(255,0,0x0700),(255,0x10,0x0700)]:
            f=Meter(self.rom)
            f.memory.mem[0x2CD],f.memory.mem[0x4F]=qualification,bypass
            f.word(0x3FC0,period)
            for _ in range(3):
                f.irq(0xFFF2)
                self.assertLessEqual(f.invocations[-1][1],high)
                self.assertEqual(f.cpu.s.sp,0x03F4)
            self.assertEqual(f.trace.count(0x77C6),3)
            self.assertNotIn(0x7AA5,f.trace)

    def test_complete_normal_service_exchange_stays_within_the_11_byte_copy_envelope(self):
        f=Meter(self.rom)
        f.memory.mem[0x302D]=0x26
        reply=f.exchange([4,*range(10)])
        self.assertEqual(sum(reply)&255,0)
        high=int(self.irqs[(0xF7EA,'normal_session_copy_le11')]['including_IRQ_entry12_E'])
        observed=max(cost for vector,cost in f.invocations)
        self.assertEqual(observed,487)
        self.assertLessEqual(observed,high)
        self.assertEqual(high,493)
        self.assertEqual(f.trace.count(0xFA18),11)
        self.assertEqual(f.cpu.s.sp,0x03F4)

    def test_complete_factory_receive_exchange_stays_within_the_34_byte_copy_envelope(self):
        f=Meter(self.rom)
        f.memory.mem[0x302D]=0x26
        f.memory.mem[0x50]=8
        payload=list(range(34))
        reply=f.exchange(payload,ident=3)
        self.assertEqual(sum(reply)&255,0)
        self.assertEqual(len(reply),27)
        high=int(self.irqs[(0xF7EA,'stock_typed_descriptors_RX_N_le34')]['including_IRQ_entry12_E'])
        observed=max(cost for vector,cost in f.invocations)
        self.assertEqual(observed,932)
        self.assertLessEqual(observed,high)
        self.assertEqual(high,976)
        self.assertEqual(f.trace.count(0xFA18),34)
        self.assertEqual(bytes(f.memory.mem[0x038E:0x03B0]),bytes(payload))
        self.assertEqual(f.cpu.s.sp,0x03F4)


if __name__=='__main__':unittest.main()
