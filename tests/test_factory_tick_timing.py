"""Conditional timing of complete stock BMHM busy timer handlers.

The independent timing subset, F1-style divide-by16 compare, ADC completion
and CLI delay supply an explicitly scoped test environment. Register writes
commit at instruction endpoints; cases avoid compare-write equality borders.
There is no competing-source, bus-stretch, watchdog, STOP or reset model.
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
from factory_integer_replay import IntegerMemory
from factory_rom_decode import decode
from factory_scheduler_replay import HC11CPU
from verify_factory_ownership import EVIDENCE
import verify_factory_tick_timing as proof
from test_factory_stack_and_shared_state import Replay


class Clock:
    def __init__(self):
        self.e=0
        self.toc=0
        self.flag=True  # A supplied prior match at E=0 is already pending.
        self.matches=[(0,0)]

    def advance(self,n):
        for _ in range(n):
            self.e+=1
            if (self.e//16)&65535 == self.toc and not self.flag:
                self.flag=True
                self.matches.append((self.e,self.toc))


class TimedMemory(IntegerMemory):
    def __init__(self,rom):
        super().__init__(rom)
        self.clock=Clock()
        self.adc_due=None

    def read8(self,address):
        if address == 0x3030:
            return (self.mem[address]&127)|(128 if self.adc_due is not None and self.clock.e>=self.adc_due else 0)
        if address in {0x301A,0x301B}:
            return self.clock.toc>>8 if address==0x301A else self.clock.toc&255
        if address == 0x3023:
            return 0x20 if self.clock.flag else 0
        return super().read8(address)


class TimedReplay(Replay):
    def __init__(self,rom):
        super().__init__(rom)
        self.memory=TimedMemory(rom)
        self.cpu=HC11CPU(self.memory)
        self.cpu.s.pc,self.cpu.s.sp,self.cpu.s.ccr=0x7000,0x03F4,0xC0
        self.armed=False
        self.delay=0
        self.entries=[]
        self.timeline=[]

    def step(self):
        if not self.armed:
            return super().step()
        m=self.memory
        if m.clock.flag and m.mem[0x3022]&0x20 and not self.cpu.s.ccr&0x10 and not self.delay:
            interrupted=self.cpu.s.pc
            assert self.cpu.interrupt(0xFFE4)
            m.clock.advance(12)
            self.entries.append((m.clock.e,interrupted,self.cpu.s.sp))
        i=decode(self.rom.read,self.cpu.s.pc)
        before=len(m.events)
        self.timeline.append((m.clock.e,i.pc))
        super().step()
        m.clock.advance(cycles(i))
        for pc,address,value,width in m.events[before:]:
            if address==0x301A and width==16:
                # Endpoints far from the equality boundary make the selected
                # event ordering independent of the high/low bus-write phase.
                distance=(value-((m.clock.e//16)&65535))&65535
                assert 3<distance<65533
                m.clock.toc=value
            elif address==0x3023 and value&0x20:
                m.clock.flag=False
            elif address==0x3030:
                m.adc_due=m.clock.e+proof.ADC_READY_AFTER_WRITE_E
        if i.op=='CLI':
            self.delay=1
        elif self.delay:
            self.delay-=1

    def run_pending(self,first_instruction_lateness):
        assert first_instruction_lateness>=12
        self.memory.clock.e=first_instruction_lateness-12
        self.memory.mem[0x3022]=0xA0
        self.armed=True
        old=(self.cpu.s.pc,self.cpu.s.sp)
        for _ in range(5000):
            self.step()
            if self.entries and (self.cpu.s.pc,self.cpu.s.sp)==old:
                return
        raise AssertionError(f'Timed handler budget at {self.cpu.s.pc:04X}')


class FactoryTickTimingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=recorded_rom(json.loads(EVIDENCE.read_text()))
        cls.generated=proof.build(cls.rom)
        cls.bounds={r['contract']:r for r in csv.DictReader(io.StringIO(cls.generated[proof.FILES[0]]))}

    def fixture(self):
        f=TimedReplay(self.rom)
        for a,v in [(0x4F,4),(0x4C,0x20),(0xA7,128),(0x14D,20),(0xB5,40)]:
            f.memory.mem[a]=v
        f.word(0x150,0x400)
        f.call(0xB2ED)
        self.assertEqual(tuple(f.memory.mem[0x153:0x155]),(64,35))
        f.trace.clear()
        return f

    def issued(self,f):
        return [v for pc,a,v,w in f.memory.events if a==0x3068]

    def test_timing_artifacts_reproduce_and_every_selected_instruction_has_reviewed_cost(self):
        for name,content in self.generated.items():
            self.assertEqual((proof.OUT/name).read_text(),content,name)
        rows=list(csv.DictReader(io.StringIO(self.generated[proof.FILES[1]])))
        self.assertTrue(rows)
        self.assertFalse({'7971','7974','7977'} & {r['pc'] for r in rows})
        self.assertEqual(proof.PERIOD_E,13104)
        self.assertLess(int(self.bounds['busy_entry_through_RTI']['nominal_upper_E']),1100)
        self.assertEqual(proof.ADC4_POLLS,12)
        self.assertEqual(proof.ADC7_POLLS,20)
        meta=json.loads(self.generated[proof.FILES[2]])
        self.assertEqual(meta['reset_handler_to_prescaler_write_E'],{'FFFA':39,'FFFE':36})

    def test_nominal_adc_busy_handler_finishes_well_before_its_next_compare(self):
        f=self.fixture()
        f.run_pending(12)
        self.assertEqual(len(f.entries),1)
        self.assertEqual(f.memory.clock.toc,819)
        self.assertEqual(self.issued(f),[0x0660])
        self.assertEqual(f.readword(0x150),1344)
        self.assertEqual(f.cpu.s.sp,0x03F4)
        self.assertEqual(f.memory.clock.matches,[(0,0)])
        bound=int(self.bounds['busy_entry_through_RTI']['nominal_upper_E'])
        self.assertLessEqual(f.memory.clock.e-12,bound)
        self.assertLess(f.memory.clock.e,proof.PERIOD_E)
        # Both ADC starts consume actual clock time; no always-ready fixture.
        self.assertGreater(f.trace.count(0x7B79),1)
        self.assertGreater(f.trace.count(0xF267),1)

    def test_late_arrival_below_the_conservative_limit_still_cannot_self_nest(self):
        limit=proof.PERIOD_E-int(self.bounds['busy_entry_through_RTI']['nominal_upper_E'])
        f=self.fixture()
        f.run_pending(limit-1)
        self.assertEqual(len(f.entries),1)
        self.assertLess(f.memory.clock.e,proof.PERIOD_E)
        self.assertEqual(self.issued(f),[0x0660])

    def test_counter_driven_compare_and_nominal_adc_can_admit_a_late_entry_inside_the_current_window(self):
        # Only the initial lateness is supplied. Counter equality, pending
        # status, mask and CLI delay choose the nested interrupted instruction.
        for late,pc,acc,issued in [(12425,0x7C7D,1344,[0x0654,0x0660]),
                                    (12417,0x7C96,1344,[0x0654,0x0660]),
                                    (12412,0x7C99,1489,[0x066A,0x0660]),
                                    (12358,0x7CA5,1489,[0x066A,0x0660])]:
            f=self.fixture()
            f.run_pending(late)
            self.assertEqual(f.entries,[(late,0x7000,0x03EB),(13116,pc,0x03DE)])
            self.assertEqual(f.readword(0x150),acc)
            self.assertEqual(self.issued(f),issued)
            self.assertEqual(f.memory.clock.matches,[(0,0),(13104,819)])
            self.assertEqual(f.memory.clock.toc,1638)
            self.assertEqual(f.memory.mem[0x3A]&0x28,0x20)
            self.assertEqual(f.cpu.s.sp,0x03F4)

    def test_programming_an_already_passed_next_compare_does_not_queue_elapsed_periods(self):
        f=self.fixture()
        f.run_pending(proof.PERIOD_E+100)
        self.assertEqual(len(f.entries),1)
        self.assertEqual(f.memory.clock.toc,819)
        self.assertEqual(self.issued(f),[0x0660])
        # Counter-only continuation: no assertion that the board survives the
        # interval without COP/reset or other events, which are not modeled.
        clock=f.memory.clock
        next_match=65536*16+proof.PERIOD_E
        clock.advance(next_match-clock.e-1)
        self.assertFalse(clock.flag)
        clock.advance(1)
        self.assertTrue(clock.flag)
        self.assertEqual(clock.matches[-1],(next_match,819))


if __name__=='__main__':
    unittest.main()
