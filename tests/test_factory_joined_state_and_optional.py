"""Joined stock service/mode transitions and explicit optional-code fixtures.

All resident instructions are stock BMHM. Supplied RAM handlers are tiny test
programs, never claims about the absent GM module. ASIC values and IRQ times
are fixture inputs; caller fragments have explicit start/stop boundaries.
"""
from __future__ import annotations

import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from build_factory_scheduler import recorded_rom
from verify_factory_ownership import EVIDENCE
import verify_factory_joined_state as proof
from test_factory_masked_timing import Meter


class Overlay:
    def __init__(self,stock,memory):self.stock=stock;self.memory=memory
    def read(self,a,n):
        if a>=0x4000:return self.stock.read(a,n)
        return bytes(self.memory.read8(a+k) for k in range(n))
    def word(self,a):return int.from_bytes(self.read(a,2),'big')


class ModuleFixture(Meter):
    def __init__(self,rom):
        super().__init__(rom)
        self.rom=Overlay(rom,self.memory)
        self.provided=set();self.entered=[]
        self.memory.mem[0x302D]=0x26
        self.word(0x3FFC,0xB93E)

    def supply(self,address,body):
        data=bytes.fromhex(body) if isinstance(body,str) else bytes(body)
        self.memory.mem[address:address+len(data)]=data
        self.provided.update(range(address,address+len(data)))

    def module(self,handlers=None):
        handlers=handlers or {}
        for n,entry in enumerate(range(0x1800,0x1818,3)):
            body=0x1880+n*16
            self.supply(entry,bytes([0x7E,body>>8,body&255]))
            self.supply(body,handlers.get(entry,'39'))

    def step(self):
        p=self.cpu.s.pc
        if p<0x4000:
            assert p in self.provided,f'Unprovided optional instruction at{p:04X}'
            if p in range(0x1800,0x1818,3) or p in {0x1900,0x1910}:
                s=self.cpu.s;self.entered.append((p,s.a,s.b,s.x,s.y,s.sp,s.ccr))
        super().step()

    def packet(self,payload,ident=0xF4):
        reply=self.exchange(payload,ident)
        assert sum(reply)&255==0
        return reply

    def stage(self,payload,ident=0xF4):
        request=[ident,0x55+len(payload),*payload]
        checksum=(-sum(request))&255
        for value in request:
            self.memory.mem[0x302E]=0x20;self.memory.mem[0x302F]=value;self.irq(0xFFD6)
        return checksum

    def accept_checksum(self,checksum):
        self.memory.mem[0x302E]=0x20;self.memory.mem[0x302F]=checksum;self.irq(0xFFD6)

    def factory(self):
        self.memory.mem[0x44]|=1
        self.memory.adc_samples={1:0x30,3:0x20}
        self.run(0xFA5B,0xFBD4)


def engine_payload(*,requests=0,aux=0,aux_value=0,flags=0,position=0,afr=0,spark=0):
    return [4,0,0,requests,0,aux,aux_value,flags,position,afr,spark]


class FactoryJoinedStateOptionalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.rom=recorded_rom(json.loads(EVIDENCE.read_text()))
    def fixture(self):return ModuleFixture(self.rom)

    def test_recorded_joined_state_contracts_match_rom_and_execution_inventory(self):
        for name,content in proof.build(self.rom).items():
            self.assertEqual((proof.OUT/name).read_text(),content,name)

    def test_changing_selector_and_a_short_packet_keep_active_engine_overrides(self):
        f=self.fixture();f.packet(engine_payload(flags=5,position=42,afr=0x96));f.call(0xF64E)
        f.packet([4]);f.call(0xF64E)
        self.assertEqual(f.memory.mem[0x3B]&0x10,0x10)
        self.assertEqual((f.memory.mem[0x395],f.memory.mem[0x396],f.memory.mem[0x397]),(5,42,0x96))
        f.packet([1]);f.call(0xF64E)
        self.assertEqual(f.memory.mem[0x38E],1)
        self.assertEqual(f.memory.mem[0x3B]&0x10,0x10)
        f.memory.mem[0x24A]=0x80;f.run(0x8C53,0x8C73)
        self.assertEqual(f.memory.mem[0x24B],0x96)
        f.memory.mem[7],f.memory.mem[8]=9,3;f.call(0x93D0)
        self.assertEqual(f.memory.mem[8],42)
        self.assertEqual(f.cpu.s.sp,0x03F4)

    def test_session_release_can_precede_a_pending_engine_clear_edge(self):
        f=self.fixture();f.packet(engine_payload());f.call(0xF64E)
        f.packet(engine_payload(requests=0x40));f.packet([0])
        self.assertEqual((f.memory.mem[0x42]&1,f.memory.mem[0x3B]&0x12),(0,0x10))
        before=f.trace.count(0xF333);f.call(0xF64E)
        self.assertEqual(f.trace.count(0xF333)-before,1)
        self.assertEqual(f.memory.mem[0x3B]&0x10,0)
        self.assertEqual(f.memory.mem[0x391],0x40)
        self.assertEqual(f.memory.mem[0x45]&0x80,0x80)
        self.assertLess(f.trace.index(0xF74C),f.trace.index(0xF777))

    def test_idle_expiry_leaves_an_override_until_cleanup_and_raw_aux_survives_cleanup(self):
        f=self.fixture();f.packet(engine_payload(aux=8,aux_value=0xA5,flags=4,afr=0x92));f.call(0xF64E)
        f.memory.mem[0x24A]=0x80;f.run(0x8C53,0x8C73)
        self.assertEqual(f.memory.mem[0x24B],0x92)
        f.memory.mem[0x367]=199;f.cpu._push16(0x7000);f.run(0xAE85,0xAEA0)
        self.assertEqual((f.memory.mem[0x42]&3,f.memory.mem[0x38E],f.memory.mem[0x3B]&0x10),(0,0,0x10))
        f.run(0xAEA0,0x7000)
        self.assertEqual(f.memory.mem[0x3B]&0x10,0)
        self.assertEqual(f.memory.mem[0x24B],0x92)
        f.memory.mem[0x24A]=0x80;f.run(0x8C53,0x8C73)
        self.assertEqual(f.memory.mem[0x24B],0x80)
        f.run(0xCD90,0xCDCE)
        self.assertEqual(f.readword(0x3FD4),0x7A50)

    def test_cooldown_discards_engine_selector_but_retains_an_inactive_transmission_request(self):
        f=self.fixture();f.packet(engine_payload());f.call(0xAE85)
        f.packet(engine_payload(requests=0x10))
        checksum=f.stage([4,0,0,0,0,0x80,77,0,91,0,0],0xF5)
        f.word(0x368,0xFFFE);f.cpu._push16(0x7000);f.run(0xAE85,0xAEA0)
        self.assertEqual((f.readword(0x36A),f.memory.mem[0x3B]&0x18),(1,0x10))
        f.accept_checksum(checksum);f.run(0xAEA0,0x7000)
        self.assertIn(0xF280,f.trace)
        self.assertEqual((f.memory.mem[0x38E],f.memory.mem[0x399],f.memory.mem[0x3B]&0x18),(0,4,0))
        f.call(0xAE85)
        self.assertEqual((f.readword(0x36A),f.readword(0x368)),(0,0))
        self.assertEqual(f.memory.mem[0x3B]&0x18,8)
        self.assertEqual((f.memory.mem[0x10A],f.memory.mem[0x111]),(77,91))

    def test_service_duration_triggers_shared_cooldown_then_cleanup(self):
        f=self.fixture();f.packet(engine_payload());f.packet([4],0xF5);f.call(0xAE85)
        self.assertEqual(f.memory.mem[0x3B]&0x18,0x18)
        self.assertEqual((self.rom.word(0x51BB),self.rom.word(0x51BD)),(0xFFFF,0))
        f.word(0x368,0xFFFE);f.cpu._push16(0x7000);f.run(0xAE85,0xAEA0)
        self.assertEqual((f.readword(0x368),f.readword(0x36A)),(0xFFFF,1))
        f.run(0xAEA0,0x7000)
        self.assertEqual(f.memory.mem[0x3B]&0x18,0)
        self.assertEqual((f.memory.mem[0x38E],f.memory.mem[0x399]),(0,0))
        self.assertEqual(f.memory.mem[0x42]&3,3)
        f.call(0xAE85)
        self.assertEqual((f.readword(0x368),f.readword(0x36A)),(0,0))

    def test_idle_expiry_rearms_held_engine_clear_but_does_not_repeat_blm_reset(self):
        f=self.fixture();f.packet(engine_payload(requests=0x50));f.call(0xAE85)
        self.assertEqual((f.trace.count(0xF280),f.trace.count(0xF333)),(1,1))
        f.memory.mem[0x367]=199;before=len(f.trace);f.call(0xAE85)
        self.assertEqual((f.trace.count(0xF280),f.trace.count(0xF333)),(1,2))
        path=f.trace[before:]
        self.assertLess(path.index(0xF79C),path.index(0xF74C))
        self.assertLess(path.index(0xF74C),path.index(0xF777))
        self.assertEqual(f.memory.mem[0x3B]&0x10,0)

    def test_blm_reset_edge_rearms_only_when_its_admitted_request_is_low(self):
        f=self.fixture();f.packet(engine_payload(requests=0x10));f.call(0xF64E)
        self.assertEqual(f.memory.mem[0x2B3],0x80)
        f.memory.mem[0x2B3]=0xA1
        f.packet([1]);f.call(0xF64E)
        self.assertEqual(f.memory.mem[0x45]&0x10,0x10)
        f.packet(engine_payload(requests=0x10));f.call(0xF64E)
        self.assertEqual((f.trace.count(0xF280),f.memory.mem[0x2B3]),(1,0xA1))
        f.packet(engine_payload());f.call(0xF64E)
        f.packet(engine_payload(requests=0x10));f.call(0xF64E)
        self.assertEqual((f.trace.count(0xF280),f.memory.mem[0x2B3]),(2,0x80))

    def test_raw_current_enable_selector_survives_transmission_session_release(self):
        f=self.fixture();f.packet([4,0x40,0x40,0,0,0,0,0,0,0,0],0xF5);f.call(0xF64E)
        f.packet([0],0xF5);f.call(0xF64E)
        self.assertEqual((f.memory.mem[0x3B]&8,f.memory.mem[0x399]),(0,0))
        f.memory.mem[0x99]|=8;f.call(0xC514)
        self.assertEqual(f.memory.mem[0x4C]&0x20,0x20)
        f.call(0xF3EE)
        self.assertEqual(f.memory.mem[0x3062]&0x20,0x20)

    def test_special_mode_can_ack_clear_without_admitting_the_clear_consumer(self):
        for phase in range(16):
            f=self.fixture();f.packet([0x0A]);f.memory.mem[0x1A]=0x20;f.memory.mem[2]=phase
            f.memory.mem[0xA7]=128;f.memory.mem[0x4F]=4
            f.run(0x7989,0x7A51)
            self.assertNotIn(0xF64E,f.trace)
            self.assertNotIn(0xF333,f.trace)
            self.assertEqual((f.memory.mem[0x1A]&0x20,f.memory.mem[0x3B]&2),(0x20,2))
        f.call(0xF333)
        self.assertEqual(f.memory.mem[0x1A]&0x20,0)

    def test_connection_hook_runs_while_disabled_and_can_enable_later_hooks(self):
        f=self.fixture();f.module({0x180C:'14 86 40 39',0x1806:'7C 02 B0 86 11 39'})
        f.call(0xF5CF)
        self.assertEqual(f.memory.mem[0x2B0],0)
        f.call(0xF5DC)
        self.assertEqual(f.memory.mem[0x86]&0x40,0x40)
        self.assertEqual([x[3] for x in f.entered if x[0]==0x180C],[0x7E18])
        f.call(0xF5CF)
        self.assertEqual((f.memory.mem[0x2B0],f.memory.mem[0xF00]),(1,0xF7))
        f.supply(0x18C0,'15 86 40 39');f.call(0xF5DC);f.call(0xF5CF);f.call(0xF5DC)
        self.assertEqual(f.memory.mem[0x2B0],1)
        self.assertEqual(sum(x[0]==0x180C for x in f.entered),3)

    def test_afr_service_bypasses_hook_and_hook_requires_a_ram_result(self):
        f=self.fixture();f.module({0x1800:'86 12 39'});f.memory.mem[0x86]=0x40
        f.memory.mem[0x24A]=0x80;f.run(0x8C53,0x8C73)
        self.assertEqual(f.memory.mem[0x24B],0x80)
        f.supply(0x1880,'86 91 B7 02 4A 86 12 39');f.run(0x8C53,0x8C73)
        self.assertEqual(f.memory.mem[0x24B],0x91)
        before=len(f.entered);f.memory.mem[0x3B]=0x10;f.memory.mem[0x395]=4;f.memory.mem[0x397]=0xA3
        f.run(0x8C53,0x8C73)
        self.assertEqual(f.memory.mem[0x24B],0xA3)
        self.assertEqual(len(f.entered),before)

    def test_iac_hook_precedes_resident_service_and_immediate_flag_clear(self):
        f=self.fixture();f.module({0x1803:'14 38 40 86 33 97 08 39'})
        f.memory.mem[0x86]=0x40;f.memory.mem[0x3B]=0x10;f.memory.mem[0x395]=1;f.memory.mem[0x396]=42
        f.call(0x93D0)
        self.assertEqual((f.memory.mem[0x38]&0x40,f.memory.mem[8]),(0,42))
        self.assertNotIn(0x93E1,f.trace)
        self.assertEqual(f.cpu.s.sp,0x03F4)

    def test_governor_carry_selects_scalar_result(self):
        for body,takes in [('86 A5 0D 39',True),('86 A5 0C 39',False)]:
            f=self.fixture();f.module({0x1809:body});f.memory.mem[0x86]=0x40;f.cpu.s.a=17;f.memory.mem[0x293]=17
            f.run(0x8EDB,0x8EE4 if not takes else 0x8EC8)
            if takes:self.assertEqual(f.memory.mem[0x299],0xA5)
            else:self.assertNotIn(0x8EC5,f.trace)

    def test_egr_hook_uses_ram_and_service_has_later_precedence(self):
        for body,expected in [('86 A5 39',0),('86 91 B7 01 AE 86 A5 39',0x91)]:
            f=self.fixture();f.module({0x1815:body});f.memory.mem[0x86]=0x40;f.memory.mem[0x1AE]=0
            f.call(0xD025);self.assertEqual(f.memory.mem[0x1AE],expected)
            f.memory.mem[0x3B]=0x10;f.memory.mem[0x393]=2;f.memory.mem[0x394]=0x63
            f.call(0xD025);self.assertEqual(f.memory.mem[0x1AE],0x63)

    def test_spark_factor_hook_a_survives_the_resident_lookup(self):
        f=self.fixture();f.module({0x180F:'86 40 39'});f.memory.mem[0x86]=0x40;f.word(0x5F,0x0800)
        f.run(0xAB62,0xAB7C)
        self.assertEqual(f.cpu.s.d,0x0200)
        self.assertEqual(f.cpu.s.sp,0x03F4)

    def test_spark_command_hook_uses_ram_and_service_edits_follow_the_limits(self):
        for body,expected in [('CC 01 23 39',0x300),('CC 03 21 FD 01 FD CC 01 23 39',0x321)]:
            f=self.fixture();f.module({0x1812:body});f.memory.mem[0x86]=0x40;f.word(0x1FD,0x300)
            f.run(0xA9E0,0xAA1A);self.assertEqual(f.readword(0x1FD),expected)
            f.packet(engine_payload(flags=0x28,spark=77));f.call(0xF64E)
            f.run(0xA9E0,0xAB44)
            self.assertEqual((f.readword(0x1EE),f.readword(0x1F0)),(0xFFB3,0xFFB3))

    def test_connection_activation_is_seen_by_the_same_pass_profiling_tail(self):
        f=self.fixture();f.module({0x180C:'14 86 40 39'})
        f.memory.mem[2]=6;f.memory.mem[0x4F]=4;f.memory.mem[0xA7]=128
        f.word(0x300E,1000);f.word(0x301A,900)
        f.run(0x7989,0x7A84)
        self.assertEqual(f.memory.mem[2],7)
        self.assertEqual(f.readword(0x2E1),919)
        self.assertEqual([x[0] for x in f.entered],[0x180C])
        f.supply(0x18C0,'15 86 40 39');f.call(0x7B1B)
        f.word(0x300E,2000);f.run(0x7A51,0x7A84)
        self.assertEqual(f.memory.mem[0x86]&0x40,0)
        self.assertEqual(f.readword(0x2E1),919)

    def test_signature_loss_does_not_clear_the_separate_hook_enable_latch(self):
        f=self.fixture();f.module({0x180C:'14 86 40 39',0x1806:'7C 02 B0 39'})
        f.call(0xF5DC);f.memory.mem[0x1800:0x1802]=bytes(2)
        f.call(0xF5DC);f.call(0xF5CF)
        self.assertEqual(sum(x[0]==0x180C for x in f.entered),1)
        self.assertEqual((f.memory.mem[0x86]&0x40,f.memory.mem[0x2B0]),(0x40,1))

    def test_one_checksum_irq_can_change_value_after_the_controller_samples_old_enable(self):
        f=self.fixture();f.packet(engine_payload(flags=4,afr=0x90));f.call(0xF64E)
        checksum=f.stage(engine_payload(flags=0,afr=0xA3))
        self.assertEqual((f.memory.mem[0x395],f.memory.mem[0x397]),(4,0x90))
        f.memory.mem[0x24A]=0x80;f.run(0x8C53,0x8C5E)
        f.accept_checksum(checksum)
        self.assertEqual((f.memory.mem[0x395],f.memory.mem[0x397]),(0,0xA3))
        f.run(0x8C5E,0x8C73)
        self.assertEqual(f.memory.mem[0x24B],0xA3)
        f.memory.mem[0x24A]=0x80;f.run(0x8C53,0x8C73)
        self.assertEqual(f.memory.mem[0x24B],0x80)

    def test_extension_status_changes_closed_loop_gate_only_when_enabled(self):
        for enabled,status,allowed in [(0,3,True),(0x40,0,True),(0x40,3,False)]:
            f=self.fixture();f.memory.mem[0x86]=enabled;f.memory.mem[0x801]=status;f.memory.mem[0x50]=2
            f.run(0xE4F1,0xE561)
            self.assertEqual(bool(f.memory.mem[0x46]&0x80),allowed)
            self.assertEqual(bool(f.memory.mem[0x3E]&0x20),allowed)

    def test_factory_short_upload_reuses_source_suffix_and_forward_overlap_is_literal(self):
        f=self.fixture();f.memory.mem[0x50]=8
        pattern=list(range(1,33));f.packet([0x20,0,*pattern],1);f.factory()
        self.assertEqual(bytes(f.memory.mem[0x2000:0x2020]),bytes(pattern))
        self.assertEqual(f.memory.mem[0x364],0xFE)
        f.packet([0x21,0],1);f.factory()
        self.assertEqual(bytes(f.memory.mem[0x2100:0x2120]),bytes(pattern))
        f.packet([3,0x91,*pattern],1);f.factory()
        self.assertEqual(bytes(f.memory.mem[0x390:0x3B1]),bytes([1])*33)

    def test_factory_callback_arm_is_not_bound_to_one_pointer(self):
        f=self.fixture();f.memory.mem[0x50]=8
        f.supply(0x1900,'7C 02 B0 39');f.supply(0x1910,'7C 02 B1 39')
        f.packet([0x19,0],3);f.factory();self.assertEqual(f.memory.mem[0x2B0],0)
        f.packet([0x19,0],2);f.factory();f.factory()
        self.assertEqual(f.memory.mem[0x2B0],2)
        self.assertEqual(f.memory.mem[1]&1,1)
        f.packet([0x19,0x10],3);f.factory()
        self.assertEqual((f.memory.mem[0x2B0],f.memory.mem[0x2B1]),(2,1))
        f.packet([0x20,0],1);f.factory()
        self.assertEqual(f.memory.mem[1]&1,0)
        f.packet([0x19,0x10],3);f.factory();self.assertEqual(f.memory.mem[0x2B1],1)

    def test_factory_timer_abandons_an_upload_and_restarts_its_unconsumed_action(self):
        f=self.fixture();f.memory.mem[0x50]=8;f.memory.mem[0x44]=1;f.memory.adc_samples={1:0x30,3:0x20}
        pattern=list(range(1,33));f.packet([0x20,0,*pattern],1)
        f.run(0xFA5B,0xFABC)
        for _ in range(5):
            f.step();f.run(f.cpu.s.pc,0xFABC)
        self.assertEqual(bytes(f.memory.mem[0x2000:0x2005]),bytes(pattern[:5]))
        self.assertTrue(f.cpu.interrupt(0xFFE4));f.run(0x793D,0xFBD4)
        writes=[a for pc,a,v,w in f.memory.events if 0x2000<=a<0x2020]
        self.assertEqual(len(writes),37)
        self.assertEqual(bytes(f.memory.mem[0x2000:0x2020]),bytes(pattern))
        self.assertEqual((f.cpu.s.sp,f.memory.mem[0x364]),(0x03FF,0xFE))

    def test_callback_samples_pointer_before_an_accepting_checksum_retargets_the_next_loop(self):
        f=self.fixture();f.memory.mem[0x50]=8
        f.supply(0x1900,'7C 02 B0 39');f.supply(0x1910,'7C 02 B1 39')
        f.packet([0x19,0],2);f.factory()
        checksum=f.stage([0x19,0x10],3)
        f.run(0xFA5B,0x1900)
        self.assertEqual(f.cpu.s.x,0x1900)
        f.accept_checksum(checksum)
        self.assertEqual((f.cpu.s.pc,f.cpu.s.x,f.readword(0x38E)),(0x1900,0x1900,0x1910))
        f.run(0x1900,0xFBD4)
        self.assertEqual((f.memory.mem[0x2B0],f.memory.mem[0x2B1]),(2,0))
        f.factory()
        self.assertEqual((f.memory.mem[0x2B0],f.memory.mem[0x2B1]),(2,1))

    def test_factory_upload_can_supply_a_vector_block_then_reset_probe_activates_it(self):
        f=self.fixture();f.memory.mem[0x50]=8
        program=[]
        for entry in range(0x1800,0x1818,3):program.extend([0x7E,0x18,0x18 if entry==0x180C else 0x1C])
        program.extend(bytes.fromhex('14 86 40 39 39 00 00 00'))
        f.provided.update(range(0x1800,0x1820))
        f.packet([0x18,0,*program],1);f.factory()
        self.assertEqual(bytes(f.memory.mem[0x1800:0x1820]),bytes(program))
        f.cpu.s.ccr=0xD0;f.run(0x7100,0x7467)
        self.assertEqual((f.memory.mem[0x86]&0x40,f.memory.mem[0x44]&1),(0,0))
        self.assertEqual(bytes(f.memory.mem[0x1800:0x1820]),bytes(program))
        f.call(0x7B1B)
        self.assertEqual(f.memory.mem[0x86]&0x40,0x40)
        self.assertTrue(any(x[0]==0x180C for x in f.entered))


if __name__=='__main__':unittest.main()
