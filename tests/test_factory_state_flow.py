from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import build_factory_state_flow as nested
import build_factory_scheduler as scheduler
from factory_rom_decode import decode
from factory_state_flow import (Effect, Ref, State, Value, add_constant, analyze,
                                byte_part, substitute, word)
from factory_scheduler_replay import FixtureMemory
from romsim.hc11_core import HC11CPU


class ByteROM:
    def __init__(self):
        self.data=bytearray(65536)
        self.reads=[]

    def read(self,address,length):
        self.reads.append((address,length))
        return bytes(self.data[address:address+length])

    def program(self,address,hex_bytes):
        data=bytes.fromhex(hex_bytes)
        self.data[address:address+len(data)]=data
        instructions={};pc=address
        while pc<address+len(data):
            ins=decode(self.read,pc);instructions[pc]=ins;pc=ins.next_pc
        return instructions


class FactoryStateFlowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=json.loads(nested.EVIDENCE.read_text())
        cls.rom=scheduler.recorded_rom(cls.evidence)
        cls.flow=list(csv.DictReader(io.StringIO((nested.OUT/"factory_indexed_flow.csv").read_text())))
        cls.effects=list(csv.DictReader(io.StringIO((nested.OUT/"factory_nested_memory_effects.csv").read_text())))

    def real_instructions(self,entry):
        return scheduler.walk_callee(self.rom,entry,[])[0]

    def run_real_helper(self,entry,ram=None,x=0x0800,d=0,y=0xBEEF):
        memory=FixtureMemory(scheduler.recorded_rom(self.evidence))
        if ram is not None:memory.mem[:len(ram)]=ram
        cpu=HC11CPU(memory);cpu.s.sp=0x03FF;cpu.s.x=x;cpu.s.y=y;cpu.s.d=d
        cpu._push16(0x0200);cpu.s.pc=entry
        written_before=len(memory.writes)
        for _ in range(30000):
            if cpu.s.pc==0x0200:break
            cpu.step()
        else:self.fail(f"Helper ${entry:04X} did not return")
        return cpu,memory,memory.writes[written_before:]

    def test_recorded_nested_outputs_reproduce_and_baseline_is_accounted_for(self):
        outputs=nested.build(scheduler.recorded_rom(self.evidence))
        for name,content in outputs.items():self.assertEqual((nested.OUT/name).read_text(),content,name)
        self.assertEqual(sum(self.evidence["baseline_resolution_counts"].values()),262)
        self.assertEqual(sum(r["in_previous_262_rows"]=="1" for r in self.flow),262)
        self.assertEqual(self.evidence["mapped_routine_entries"],234)
        self.assertEqual(self.evidence["external_hook_targets"],[f"{a:04X}" for a in range(0x1800,0x1818,3)])

    def test_branches_join_addresses_instead_of_using_last_linear_load(self):
        rom=ByteROM();ins=rom.program(0x7200,"CE 40 00 C1 01 27 03 CE 50 00 A6 00 39")
        result=analyze(rom,0x7200,ins,{})
        self.assertEqual(next(e.address.ints() for e in result.local.values() if e.pc==0x720A),{0x4000,0x5000})

    def test_opaque_call_clobbers_pointer_and_does_not_disappear_from_effect_scope(self):
        rom=ByteROM();ins=rom.program(0x7200,"CE 40 00 BD 18 00 A6 00 39")
        result=analyze(rom,0x7200,ins,{})
        self.assertEqual(result.opaque,{0x7203})
        self.assertIsNone(next(e.address.items for e in result.local.values() if e.pc==0x7206))
        self.assertIsNone(result.outputs["SP"].items)

    def test_unknown_branch_dominates_a_known_pointer_at_merge(self):
        rom=ByteROM();ins=rom.program(0x7200,"CE 40 00 D6 00 26 03 BD 18 00 A6 00 39")
        result=analyze(rom,0x7200,ins,{})
        self.assertIsNone(next(e.address.items for e in result.local.values() if e.pc==0x720A))

    def test_RAM_load_does_not_read_padding_or_treat_previous_store_as_constant(self):
        rom=ByteROM();rom.data[0x024E:0x0250]=bytes.fromhex("40 00")
        ins=rom.program(0x7200,"CE 02 4E CC 40 00 ED 00 EE 00 A6 00 39")
        result=analyze(rom,0x7200,ins,{})
        self.assertFalse(any(address==0x024E for address,_ in rom.reads))
        self.assertIsNone(next(e.address.items for e in result.local.values() if e.pc==0x720A))
        store=next(e for e in result.local.values() if e.pc==0x7206)
        self.assertEqual(nested.target_bytes(store),{0x024E,0x024F})

    def test_carry_change_invalidates_old_compare_predicate(self):
        rom=ByteROM();ins=rom.program(0x7200,"86 00 81 01 0C 24 05 CE 50 00 20 03 CE 40 00 A6 00 39")
        result=analyze(rom,0x7200,ins,{})
        self.assertEqual(next(e.address.ints() for e in result.local.values() if e.pc==0x720F),{0x4000})

    def test_byte_parameter_is_zero_extended_before_address_arithmetic(self):
        value=Value.of(16,[Ref("B",0x7A85)])
        self.assertEqual(substitute(value,{"B":Value.const(8,10)}).ints(),{0x7A8F})
        self.assertEqual(substitute(byte_part(value,"hi"),{"B":Value.const(8,10)}).ints(),{0x7A})
        self.assertIsNone(add_constant(Value.param(8,"B"),1).items)  # Wrapped-byte expressions are widened.

    def test_reviewed_local_spark_frames_survive_call_substitution_without_becoming_absolute(self):
        from factory_state_flow import stack_address,write_value
        frame=Value.of(16,[Ref("FRAME_AB89",0xFFFF)])
        self.assertEqual(frame.text(),"SP_at_AB89-1")
        self.assertTrue(stack_address(frame))
        self.assertEqual(substitute(frame,{"SP":Value.const(16,0x03FF)}),frame)
        state=State.entry();state.stack[Ref("SP")]=Value.const(8,42)
        write_value(state,frame,Value.const(16,0))
        self.assertEqual(state.stack,{})  # Unknown relation to caller frame may alias.
        rows={r["pc"]:r for r in self.flow if r["entry"]=="A466"}
        for pc in ["AB9A","AB9E","ABA0","ABA2"]:
            self.assertEqual(rows[pc]["classification"],"stack_relative")
            self.assertEqual(rows[pc]["effective_addresses"],"SP_at_AB89-1")
            self.assertEqual(rows[pc]["target_bytes"],"")
        self.assertEqual(rows["AAD4"]["effective_addresses"],"SP_at_AACF")

    def test_possible_RAM_alias_invalidates_a_saved_stack_pointer_value(self):
        rom=ByteROM();ins=rom.program(0x7200,"3C CE 02 4E CC 00 00 ED 00 38 A6 00 39")
        result=analyze(rom,0x7200,ins,{})
        self.assertIsNone(next(e.address.items for e in result.local.values() if e.pc==0x720A))

    def test_wrapped_word_write_includes_RAM_zero_in_stack_alias_check(self):
        rom=ByteROM();ins=rom.program(0x7200,"3C CE FF FF CC 00 00 ED 00 38 A6 00 39")
        result=analyze(rom,0x7200,ins,{})
        self.assertIsNone(next(e.address.items for e in result.local.values() if e.pc==0x720A))
        store=next(e for e in result.local.values() if e.pc==0x7207)
        self.assertEqual(nested.target_bytes(store),{0xFFFF,0})

    def test_math_helpers_preserve_saved_X_Y_and_nested_word_reads_bind_to_fuel_state(self):
        helpers={}
        for entry in [0xF459,0xF4C1,0xF550]:
            result=analyze(self.rom,entry,self.real_instructions(entry),{})
            self.assertEqual(result.outputs["X"],Value.param(16,"X"))
            self.assertEqual(result.outputs["Y"],Value.param(16,"Y"))
            helpers[entry]=result
        rom=ByteROM()
        wrapper=rom.program(0x7300,"BD F5 50 39")
        helpers[0x7300]=analyze(rom,0x7300,wrapper,helpers)
        caller=rom.program(0x7200,"CE 02 4E 86 80 BD 73 00 ED 00 39")
        result=analyze(rom,0x7200,caller,helpers)
        actual={e.pc:e for e in result.effects.values() if e.pc in {0xF551,0xF558}}
        self.assertEqual(actual[0xF551].address.ints(),{0x024F})
        self.assertEqual(actual[0xF558].address.ints(),{0x024E})
        self.assertEqual(actual[0xF558].via,(0x7205,0x7300))
        self.assertEqual(next(e.address.ints() for e in result.local.values() if e.pc==0x7208),{0x024E})

    def test_real_multiply_helper_preserves_registers_in_CPU_execution(self):
        for multiplicand in [0,1,0x007F,0x0080,0x1234,0xFFFF]:
            ram=bytearray(0x1000);ram[0x0800:0x0802]=multiplicand.to_bytes(2,"big")
            for multiplier in [0,1,127,128,255]:
                cpu,_,_=self.run_real_helper(0xF550,ram,x=0x0800,d=multiplier<<8)
                self.assertEqual((cpu.s.x,cpu.s.y,cpu.s.sp),(0x0800,0xBEEF,0x03FF))
                self.assertEqual(cpu.s.d,(multiplier*multiplicand+128)>>8)

    def test_clear_call_contract_matches_actual_CPU_for_all_factory_lengths_and_edges(self):
        for length in [1,7,8,9,11,43,177,202,256,413,512]:
            with self.subTest(length=length):
                ram=bytearray([0xA5])*0x1001
                cpu,memory,_=self.run_real_helper(0xF2FD,ram,x=0x0800,d=length)
                state=State.entry();state.put("SP",Value.const(16,0x03FF));state.put("X",Value.const(16,0x0800));state.put("Y",Value.const(16,0xBEEF));state.put("D",Value.const(16,length))
                effects={}
                self.assertTrue(nested.clear_override(self.rom,state,0xF2FD,0x7200,effects))
                self.assertEqual(set().union(*(nested.target_bytes(e) for e in effects.values())),set(range(0x0800,0x0800+length)))
                self.assertEqual(memory.mem[0x0800:0x0800+length],bytes(length))
                self.assertEqual((memory.mem[0x07FF],memory.mem[0x0800+length]),(0xA5,0xA5))
                self.assertEqual(state.get("X").singleton(),cpu.s.x)
                self.assertEqual(state.get("Y").singleton(),cpu.s.y)
                self.assertEqual(state.get("D").singleton(),cpu.s.d)
        for length in [0,513,65535]:
            state=State.entry();state.put("D",Value.const(16,length))
            self.assertFalse(nested.clear_override(self.rom,state,0xF2FD,0x7200,{}))

    def test_clear_contract_does_not_assume_normal_return_when_return_frame_is_erased(self):
        state=State.entry();state.put("SP",Value.const(16,0x03FF));state.put("X",Value.const(16,0x03F0));state.put("D",Value.const(16,16))
        self.assertFalse(nested.clear_override(self.rom,state,0xF2FD,0x7200,{}))

    def test_masked_state_map_matches_actual_helper_writes_for_varied_RAM(self):
        rows=list(csv.DictReader(io.StringIO((nested.OUT/"factory_masked_state_updates.csv").read_text())))
        for entry in [0xF333,0xF380]:
            for seed in [0,1,71,255]:
                randomizer=random.Random(seed)
                ram=bytearray(randomizer.randrange(256) for _ in range(0x1000))
                original=bytes(ram)
                _,memory,writes=self.run_real_helper(entry,ram)
                expected={int(row["destination"],16):original[int(row["destination"],16)] & int(row["and_mask"],16)
                          for row in rows if row["entry"]==f"{entry:04X}"}
                for address,value in expected.items():
                    self.assertIn((address,value),writes)
                    self.assertEqual(memory.mem[address],value,hex(address))

    def test_indexed_service_write_clears_special_mode_without_a_direct_STAA(self):
        ram=bytearray([0xFF])*0x1000
        _,memory,_=self.run_real_helper(0xF333,ram)
        self.assertEqual(memory.mem[0x001A],0xD9)
        self.assertEqual(memory.mem[0x001A] & 0x20,0)
        _,memory,_=self.run_real_helper(0xF380,ram)
        self.assertEqual(memory.mem[0x001A],0xE7)
        self.assertEqual(memory.mem[0x001A] & 0x20,0x20)

    def test_checksum_loop_uses_ten_bytes_from_000B_through_0014(self):
        ram=bytearray((i*17+3)&255 for i in range(0x1000))
        cpu,_,_=self.run_real_helper(0xF326,ram)
        self.assertEqual(cpu.s.a,(-sum(ram[0x000B:0x0015]))&255)
        self.assertEqual((cpu.s.x,cpu.s.b,cpu.s.sp),(0x000A,0,0x03FF))

    def test_emitted_fuel_helper_reads_include_both_bytes_and_keep_stack_access_separate(self):
        relevant=[r for r in self.effects if r["entry"]=="7D4B" and r["call_witness"].startswith("803B")]
        self.assertEqual({r["addresses"] for r in relevant if r["access_pc"] in {"F551","F558"}},{"$024E","$024F"})
        self.assertTrue(any(r["classification"]=="stack_relative" for r in relevant))

    def test_malformed_A40B_target_matches_actual_CPU_branch(self):
        for flags in [0,1]:
            memory=FixtureMemory(scheduler.recorded_rom(self.evidence));memory.mem[9]=flags
            cpu=HC11CPU(memory);cpu.s.pc=0xA40B;cpu.step()
            self.assertEqual(cpu.s.pc,0xA465 if flags else 0xA40F)
        rows=list(csv.DictReader(io.StringIO((nested.OUT/"factory_nested_control_corrections.csv").read_text())))
        self.assertEqual((rows[0]["rom_target"],rows[0]["inherited_operand"]),("A465","LA4656"))


if __name__=="__main__":unittest.main()
