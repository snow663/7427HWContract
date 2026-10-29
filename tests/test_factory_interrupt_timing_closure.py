"""Join real stock handlers to source flags, priority and nominal time.

Instruction-end timer writes avoid equality/inhibition border claims. ASIC
words remain explicit samples. The counter drives admission; no IRQ is
inserted at a selected current-calculation instruction.
"""
from __future__ import annotations

import csv
import heapq
import io
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_factory_scheduler import recorded_rom
from factory_integer_replay import IntegerMemory
from factory_rom_decode import decode
from factory_hc11_cycle_subset import cycles
from factory_scheduler_replay import HC11CPU
from verify_factory_ownership import EVIDENCE
import verify_factory_interrupt_timing_closure as proof
from test_factory_stack_and_shared_state import Replay
from test_factory_masked_timing import Meter


class SourceMemory(IntegerMemory):
    def __init__(self,rom):
        super().__init__(rom)
        self.e=0;self.flags=0;self.toc={1:0,3:819,4:0,5:0}
        self.pending_ref=False;self.edges=[];self.edge_log=[];self.matches=[]
        self.adc_due=None
        self.control=0x26;self.scsr=0xC0;self.rdr=0;self.status_seen=0
        self.rx=[];self.tx_wire=[];self.tdr=None;self.shift=None;self.shift_due=None
        self.idle_since=0;self.characters=[]

    def read8(self,a):
        if a in {0x300E,0x300F}:
            value=(self.e//16)&65535
            return value>>8 if a==0x300E else value&255
        if a==0x3023:return self.flags
        if a==0x302E:self.status_seen|=self.scsr;return self.scsr
        if a==0x302F:
            value=self.rdr;self.scsr&=~(self.status_seen&0x2E);self.status_seen=0
            return value
        for channel,base in [(1,0x3016),(3,0x301A),(4,0x301C),(5,0x301E)]:
            if a in {base,base+1}:return self.toc[channel]>>(8 if a==base else 0)&255
        if a==0x3030:
            return (self.mem[a]&127)|(128 if self.adc_due is not None and self.e>=self.adc_due else 0)
        return super().read8(a)

    def advance(self,n):
        for _ in range(n):
            self.e+=1
            if self.control&2 and self.e-self.idle_since>=2560:
                self.control&=~2;self.mem[0x302D]=self.control
            while self.rx and self.rx[0][0]<=self.e:
                when,value=heapq.heappop(self.rx);self.idle_since=self.e
                self.characters.append((self.e,'RX'))
                if self.control&4 and not self.control&2:
                    if self.scsr&0x20:self.scsr|=8
                    else:self.rdr=value
                    self.scsr|=0x20
            if self.shift_due==self.e:
                self.characters.append((self.e,'TX'))
                if isinstance(self.shift,int):self.tx_wire.append(self.shift)
                self.shift=None;self.shift_due=None
                if self.tdr is not None and self.control&8:
                    self.shift=self.tdr;self.tdr=None;self.shift_due=self.e+2560;self.scsr|=0x80
                else:self.scsr|=0xC0
            if self.e%16==0:
                counter=(self.e//16)&65535
                for channel,bit in [(1,128),(3,32),(4,16),(5,8)]:
                    if counter==self.toc[channel]:
                        self.flags|=bit;self.matches.append((self.e,channel,counter))
            while self.edges and self.edges[0]<=self.e:
                when=heapq.heappop(self.edges)
                self.edge_log.append((when,self.pending_ref));self.pending_ref=True

    def commit(self,events):
        for pc,a,v,width in events:
            if a==0x3023:self.flags&=~v
            elif a==0x3030:self.adc_due=self.e+129
            elif a==0x302D:
                old=self.control;self.control=v
                if v&2 and not old&2:self.idle_since=self.e
                if v&8 and not old&8:
                    self.shift='preamble';self.shift_due=self.e+2560;self.scsr&=~0x40
            elif a==0x302F:
                assert self.tdr is None,'TDR overwrite'
                self.tdr=v;self.scsr&=~(self.status_seen&0xC0);self.status_seen=0
                if self.control&8 and self.shift is None:
                    self.shift=self.tdr;self.tdr=None;self.shift_due=self.e+2560;self.scsr|=0x80
            for channel,base in [(1,0x3016),(3,0x301A),(4,0x301C),(5,0x301E)]:
                if a==base and width==16:
                    if channel==3:
                        distance=(v-((self.e//16)&65535))&65535
                        assert 3<distance<65533,'Unmodeled compare-write equality border'
                    self.toc[channel]=v


class SourceReplay(Replay):
    def __init__(self,rom):
        super().__init__(rom)
        self.memory=SourceMemory(rom);self.cpu=HC11CPU(self.memory)
        self.cpu.s.pc,self.cpu.s.sp,self.cpu.s.ccr=0x7000,0x03F4,0xC0
        self.armed=False;self.delay=0;self.entries=[];self.ref_refills=0
        self.timeline=[]

    def choose(self,ignore_mask=False):
        if not ignore_mask and (self.cpu.s.ccr&0x10 or self.delay):return None
        m=self.memory
        if m.pending_ref:return 0xFFF2
        for bit,vector in [(128,0xFFE8),(32,0xFFE4),(16,0xFFE2),(8,0xFFE0)]:
            if m.flags&m.mem[0x3022]&bit:return vector
        c,s=m.control,m.scsr
        if c&0x20 and not c&2 and s&0x28 or c&0x80 and s&0x80 or c&0x40 and s&0x40:return 0xFFD6
        return None

    def step(self):
        m=self.memory
        vector=self.choose() if self.armed else None
        if vector is not None:
            old_pc=self.cpu.s.pc
            if vector==0xFFF2:m.pending_ref=False
            assert self.cpu.interrupt(vector)
            m.advance(12)
            # Real HC11 vector priority resolves during stacking. These
            # selected examples exclude a higher source arriving anywhere
            # in that span, rather than guess a sub-instruction phase.
            rank={0xFFF2:1,0xFFE8:6,0xFFE4:8,0xFFE2:9,0xFFE0:10,0xFFD6:15}
            late=self.choose(ignore_mask=True)
            assert late is None or rank[late]>=rank[vector],'Late priority change outside selected entry model'
            self.entries.append((m.e,vector,old_pc,self.cpu.s.sp))
            if vector==0xFFF2 and self.ref_refills:
                heapq.heappush(m.edges,m.e+16);self.ref_refills-=1
        i=decode(self.rom.read,self.cpu.s.pc);start=len(m.events)
        self.timeline.append((m.e,i.pc))
        super().step();m.advance(cycles(i));m.commit(m.events[start:])
        if i.op=='CLI':self.delay=1
        elif self.delay:self.delay-=1

    def finish_irqs(self,budget=30000):
        for _ in range(budget):
            if self.cpu.s.pc==0x7000 and self.entries and self.choose() is None:return
            self.step()
        raise AssertionError(f'Event replay budget at{self.cpu.s.pc:04X}')


class FactoryInterruptTimingClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=recorded_rom(json.loads(EVIDENCE.read_text()))
        cls.generated=proof.build(cls.rom)
        cls.meta=json.loads(cls.generated[proof.FILES[3]])
        cls.bounds={int(r['entry'],16):r for r in csv.DictReader(io.StringIO(cls.generated[proof.FILES[2]]))}

    def current_fixture(self):
        f=SourceReplay(self.rom)
        for a,v in [(0x4F,4),(0x4C,0x20),(0xA7,128),(0x14D,20),(0xB5,40),(0x2CD,255)]:f.memory.mem[a]=v
        f.word(0x150,0x400);f.word(0x3FC0,0x0700);f.call(0xB2ED)
        f.trace.clear();f.memory.events.clear();return f

    def test_all_sources_loops_and_own_work_boundaries_reproduce(self):
        for name,content in self.generated.items():self.assertEqual((proof.OUT/name).read_text(),content,name)
        self.assertEqual(self.meta['stock_live_vectors'],['FFD6','FFE4','FFE8','FFF2'])
        self.assertEqual(self.meta['stock_REF_upper_own_E'],723)
        self.assertEqual(self.meta['local_cyclic_components'],46)
        self.assertEqual(self.meta['procedure_envelopes'],254)
        self.assertEqual(self.meta['conditional_deadline']['sum_E'],12860)
        self.assertEqual(self.meta['conditional_deadline']['strict_extra_wait_limit_E'],244)

    def test_complete_stock_ref_paths_cannot_enable_oc4_or_oc5(self):
        for flags in [0,4,0x10,0x14]:
            for qualification in [0,255]:
                f=Meter(self.rom);f.memory.mem[0x4F]=flags;f.memory.mem[0x2CD]=qualification
                f.memory.mem[0x3022]=0xA0;f.memory.mem[0x73]=0x40
                f.word(0x3FC0,0x0700);f.irq(0xFFF2)
                self.assertLessEqual(f.invocations[-1][1],735)
                self.assertEqual(f.memory.mem[0x3022],0xA0)
                self.assertFalse(set(f.trace)&{0x77DF,0x780F})

    def test_ref_priority_coalescing_and_oc1_then_oc3_order(self):
        f=self.current_fixture();m=f.memory
        m.mem[0x3022]=0xA0;m.flags=0xA0;m.pending_ref=True
        # Multiple edges while I1 coalesce into one hardware latch.
        f.cpu.s.ccr|=0x10;heapq.heappush(m.edges,m.e+1);heapq.heappush(m.edges,m.e+3)
        m.advance(4);self.assertTrue(m.pending_ref)
        self.assertEqual([duplicate for when,duplicate in m.edge_log],[True,True])
        f.cpu.s.ccr&=~0x10;f.armed=True;f.finish_irqs()
        self.assertEqual([v for e,v,p,sp in f.entries[:3]],[0xFFF2,0xFFE8,0xFFE4])
        self.assertEqual(m.flags&0xA0,0)
        self.assertEqual(f.cpu.s.sp,0x03F4)

    def test_one_main_pass_and_long_bounded_controller_work_execute_within_own_envelopes(self):
        for entry in [0xB99F,0xB9EE,0xE62D,0xF333,0xF380]:
            f=Meter(self.rom);f.memory.mem[0x11A]=0xC0;f.call(entry)
            self.assertLessEqual(f.e,int(self.bounds[entry]['conditional_nominal_own_upper_E']),f'{entry:04X}')
        for phase in range(16):
            f=Meter(self.rom);f.memory.mem[2]=phase;f.memory.mem[0x4F]=4
            f.memory.mem[0xA7]=128;f.word(0x3FFC,0xB93E)
            f.run(0x7989,0x7A51)
            self.assertLessEqual(f.e,int(self.bounds[0x7989]['conditional_nominal_own_upper_E']),phase)
            self.assertNotIn(0x7AA5,f.trace)

    def test_tail_gap_admits_a_new_owner_and_guard_limits_accepted_owner_frames(self):
        f=SourceReplay(self.rom);m=f.memory
        f.cpu.s.sp=0x03F6;f.cpu.s.pc=0x7A51;f.memory.mem[0x4F]=4;f.memory.mem[0x3A]=0x20
        m.mem[0x3022]=0x20;m.flags=0x20;f.armed=True
        # The flag is pending while SEI/tail clears busy. CLI's following JMP
        # completes, then the source chooses a new non-busy owner at7989.
        f.cpu.s.ccr|=0x10
        for _ in range(100):
            f.step()
            if f.entries:break
        self.assertEqual(f.entries[0][1:3],(0xFFE4,0x7989))
        self.assertEqual(f.memory.mem[0x4F]&4,0)
        for owners in range(1,10):
            g=Replay(self.rom);g.cpu.s.sp=0x03FF-9*owners;g.cpu.s.pc=0x7958
            g.run(0x7958,0x797A)
            if owners<=8:
                self.assertEqual(g.cpu.s.sp,0x03FF-9*owners)
                self.assertEqual(g.memory.mem[0x3A]&8,0)
            else:
                self.assertEqual(g.cpu.s.sp,0x03F6)
                self.assertEqual(g.memory.mem[0x3A]&8,8)
        # An entry consumes its frame before checking the lower limit. A
        # REF can also preempt the rejected prefix after its PSHX.
        g=Replay(self.rom);g.cpu.s.sp=0x03A2;g.low_sp=0x03A2
        g.memory.mem[0x4F]=4;g.memory.mem[0x2CD]=255;g.word(0x3FC0,0x0700)
        self.assertTrue(g.cpu.interrupt(0xFFE4));g.run(0x793D,0x795B)
        self.assertEqual(g.cpu.s.sp,0x0397)
        g.irq(0xFFF2)
        self.assertEqual(g.low_sp,0x0385)
        self.assertGreaterEqual(g.low_sp,int(self.meta['guard_stack']['peak_low_SP'],16))
        g.run(g.cpu.s.pc,0x797A);self.assertEqual(g.cpu.s.sp,0x03F6)

    def test_clean_sci_exchange_is_driven_by_character_time_and_releases_the_driver(self):
        f=self.current_fixture();m=f.memory;m.mem[0x302D]=0x26;m.mem[0x3022]=0xA0
        payload=[4,*range(10)];request=[0xF4,0x55+len(payload),*payload]
        request.append((-sum(request))&255)
        origin=m.e
        for n,value in enumerate(request):heapq.heappush(m.rx,(origin+5120+2560*n,value))
        f.armed=True
        for _ in range(200000):
            if f.choose() is not None or f.cpu.s.pc!=0x7000:f.step()
            else:m.advance(1)
            if m.tx_wire and m.control==0x26 and f.cpu.s.pc==0x7000:break
        else:self.fail('Clocked SCI did not finish')
        self.assertEqual(bytes(m.tx_wire),bytes([0xF4,0x56,4,0xB2]))
        self.assertEqual(m.mem[0x3FFD]&4,0)
        self.assertEqual(f.cpu.s.sp,0x03F4)
        entries=[e for e,v,p,sp in f.entries if v==0xFFD6]
        self.assertTrue(entries)
        self.assertLessEqual(max(sum(t<=u<t+13104 for u in entries) for t in entries),8)
        self.assertFalse(any(v&0x0C==0x0C for pc,a,v,w in m.events if a==0x302D))

    def test_ref_burst_can_starve_timer_service_beyond_the_normal_input_envelope(self):
        f=self.current_fixture();m=f.memory;m.mem[0x3022]=0xA0
        m.pending_ref=True;f.ref_refills=200;f.armed=True
        while m.e<32768:f.step()
        self.assertGreater(len(f.entries),40)
        self.assertEqual({v for e,v,p,sp in f.entries},{0xFFF2})
        self.assertTrue(m.flags&0x20)
        self.assertFalse(any(a==0x303A for pc,a,v,w in m.events))

    def test_source_arbitration_can_produce_late_current_overwrite_without_supplying_entry_lateness(self):
        def run(edge_times=None):
            f=self.current_fixture();m=f.memory
            m.e=13104-658;m.mem[0x3022]=0xA0
            f.cpu._push16(0x7000);f.cpu.s.pc=0x7AB7
            if edge_times is None:
                heapq.heappush(m.edges,13104);f.ref_refills=22
            else:
                for when in edge_times:heapq.heappush(m.edges,when)
            f.armed=True;f.finish_irqs();return f
        first=run()
        # Freeze the actual external edge times and replay with no adaptive
        # refill. Hardware priority and timer equality choose both entries.
        edge_times=[when for when,duplicate in first.memory.edge_log]
        self.assertEqual(len(edge_times),23)
        f=run(edge_times);m=f.memory
        timers=[(e-13104,p) for e,v,p,sp in f.entries if v==0xFFE4]
        self.assertEqual(timers,[(12414,0x7000),(13149,0x7C9D)])
        self.assertEqual([v for pc,a,v,w in m.events if a==0x3068],[0x066A,0x0660])
        self.assertEqual(f.readword(0x150),1489)
        self.assertEqual(f.cpu.s.sp,0x03F4)
        self.assertNotIn(0x7AA5,f.trace)
        self.assertFalse(any(duplicate for when,duplicate in m.edge_log))

    def test_spaced_ref_edges_and_clocked_sci_keep_busy_timer_entries_separate(self):
        f=self.current_fixture();m=f.memory;m.mem[0x3022]=0xA0;m.mem[0x302D]=0x26
        origin=m.e;payload=[4,*range(10)];request=[0xF4,0x55+len(payload),*payload]
        request.append((-sum(request))&255)
        for n,value in enumerate(request):heapq.heappush(m.rx,(origin+5120+2560*n,value))
        for when in range(origin+1000,origin+60000,2184):heapq.heappush(m.edges,when)
        f.armed=True
        for _ in range(200000):
            if f.choose() is not None or f.cpu.s.pc!=0x7000:f.step()
            else:m.advance(1)
            if m.e>=origin+65000 and f.cpu.s.pc==0x7000 and f.choose() is None:break
        else:self.fail('Spaced-source replay did not finish')
        timer_entries=[(e,p) for e,v,p,sp in f.entries if v==0xFFE4]
        self.assertGreaterEqual(len(timer_entries),4)
        self.assertTrue(all(p==0x7000 for e,p in timer_entries))
        self.assertEqual(bytes(m.tx_wire),bytes([0xF4,0x56,4,0xB2]))
        self.assertEqual(f.cpu.s.sp,0x03F4)

    def test_supplied_or_only_status_is_a_nonprogress_boundary_for_the_character_envelope(self):
        f=SourceReplay(self.rom);m=f.memory;m.control=0x24;m.mem[0x302D]=0x24;m.scsr=8
        f.armed=True
        while len(f.entries)<4:f.step()
        self.assertEqual({v for e,v,p,sp in f.entries},{0xFFD6})
        self.assertEqual(m.scsr,8)
        self.assertNotIn(0xF90B,f.trace)
        self.assertEqual(m.characters,[])
        # This supplies an OR-only state; it does not claim clean framed
        # traffic reaches that state or model a status/data bus race.

    def test_selected_cold_boot_unmasks_before_timer_arm_and_can_accept_ref_during_initialization(self):
        f=Meter(self.rom);f.run(0x7100,0xC57F)
        self.assertEqual(f.cpu.s.ccr&0x10,0x10)
        self.assertEqual(f.memory.mem[0x302D],0x26)
        self.assertEqual(f.memory.mem[0x3022],0)
        self.assertFalse(any(self.rom.read(p,1)==b'\x0E' for p in f.trace))
        f.step();f.step()  # CLI and its following instruction.
        self.assertEqual(f.cpu.s.ccr&0x10,0)
        old=f.state();f.irq(0xFFF2);self.assertEqual(f.state(),old)
        self.assertEqual(f.memory.mem[0x50]&0x20,0x20)
        f.run(f.cpu.s.pc,0x7467)
        self.assertEqual(f.cpu.s.ccr&0x10,0)
        self.assertEqual(f.cpu.s.sp,0x03FF)


if __name__=='__main__':unittest.main()
