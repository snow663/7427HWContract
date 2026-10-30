from __future__ import annotations

import csv
import io
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
import factory_spark as model
from factory_spark_replay import SparkReplay
import verify_factory_spark as proof
from build_factory_scheduler import recorded_rom


class FactorySparkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=json.loads(proof.EVIDENCE.read_text())
        cls.rom=recorded_rom(cls.evidence)
        cls.table=cls.rom.read(0x454A,15)

    def check_handoff(self,replay,inputs,table=None,sp=0x03F4):
        expected=model.spark_handoff(inputs,table or self.table)
        actual=replay.handoff(inputs,table,sp)
        self.assertEqual(actual,expected["writes"],inputs)
        self.assertEqual(replay.cpu.s.sp,sp)
        self.assertEqual(replay.cpu.s.d,expected["chosen"])
        self.assertEqual(replay.memory.mem[0x4F],expected["flags4f"])
        self.assertEqual(replay.memory.read16(0x01EE),inputs.command)
        self.assertEqual(replay.memory.read16(0x01F0),inputs.command)
        self.assertEqual(replay.memory.mem[0x0201],expected["latency"])
        return expected

    def test_evidence_and_review_vectors_reproduce(self):
        for name,content in proof.build(recorded_rom(self.evidence)).items():
            self.assertEqual((proof.OUT/name).read_text(),content,name)
        replay=SparkReplay()
        for row in csv.DictReader(io.StringIO((proof.OUT/"factory_spark_handoff_vectors.csv").read_text())):
            inputs=model.HandoffInputs(**json.loads(row["inputs_json"]))
            actual=self.check_handoff(replay,inputs)
            for _,address,value in actual["writes"]:self.assertEqual(f"{value:04X}",row[f"word_{address:04X}"])

    def test_reference_term_matches_ROM_for_every_16bit_input(self):
        replay=SparkReplay()
        for period in range(65536):
            replay.prepare();replay.word(0x01E8,period)
            replay.run(0xA6B8,0xA6DC)
            actual=replay.memory.read16(0x083F)
            if actual!=model.reference_term(period):self.fail(f"reference term mismatch at {period:04X}: {actual}")

    def test_adaptive_event_decay_matches_ROM_for_every_16bit_input(self):
        replay=SparkReplay()
        for previous in range(65536):
            replay.prepare();replay.word(0x01EA,previous)
            replay.run(0xA4FB,0xA50D)
            actual=replay.memory.read16(0x01EA)
            if actual!=model.decay_adaptive(previous):self.fail(f"adaptive decay mismatch at {previous:04X}: {actual}")

    def test_adaptive_terms_match_ROM_at_borrow_clamp_and_wrap_boundaries(self):
        replay=SparkReplay();cases=[]
        for period in [0,1,38,39,40,457,458,459,1637,1638,1639,0x7FFF,0x8000,0xFFFF]:
            for now,old in [(0,1),(31,0),(32,0),(255,0),(1,255)]:
                cases.append(model.TermInputs(period,0xFFFF,0xFFFF,now,old,173,0,period))
        rng=random.Random(0x31A6)
        cases.extend(model.TermInputs(rng.randrange(65536),rng.randrange(65536),rng.randrange(65536),
                                     rng.randrange(256),rng.randrange(256),rng.randrange(256),rng.randrange(256),rng.randrange(65536)) for _ in range(512))
        for inputs in cases:
            expected=model.spark_terms(inputs)
            self.assertEqual(replay.terms(inputs),expected["writes"],inputs)
            for a,key in [(0x01EA,"adaptive"),(0x083F,"reference_term"),(0x01EC,"correction")]:
                self.assertEqual(replay.memory.read16(a),expected[key])

    def test_period_basis_scale_matches_ROM_including_zero_low_product_byte(self):
        replay=SparkReplay()
        for calibration in [0,1,4,6,8,12,16,255]:
            for period in [0,1,127,128,983,0x7FFF,0xFFFF]:
                replay.prepare();replay.word(0x3FC0,period);replay.memory.mem[0x4141]=calibration
                replay.run(0xA5E5,0xA5FE)
                self.assertEqual(replay.memory.read16(0x01E8),period)
                self.assertEqual(replay.memory.read16(0x005F),model.period_basis(period,calibration))

    def test_latency_interpolation_matches_ROM_for_all_input_bytes_and_both_slopes(self):
        replay=SparkReplay()
        tables=[self.table,bytes([192]+[20 if i%2 else 220 for i in range(14)]),bytes([192]+[220 if i%2 else 20 for i in range(14)])]
        for table in tables:
            for rpm in range(256):
                replay.prepare();replay.memory.mem[0x454A:0x4559]=table
                replay.cpu.s.a=rpm;replay.cpu.s.b=0xA5;replay.cpu.s.x=0x454A
                replay.cpu._push16(0x0200)
                replay.run(0xF499,0x0200)
                self.assertEqual(replay.cpu.s.a,model.latency_lookup(rpm,table),(rpm,table))

    def test_command_sign_low_byte_and_startup_rounding_wrap_match_ROM(self):
        replay=SparkReplay()
        for command in [0,1,127,255,256,0x7FFF,0x8000,0xFF00,0xFFFF]:
            for startup in [0,0x007F,0x0080,0x7FFF,0xFF7F,0xFF80,0xFFFF]:
                for bypass in [False,True]:
                    self.check_handoff(replay,model.HandoffInputs(command=command,startup=startup,startup_bypass=bypass,
                                                               rpm=73,basis=983,anchor_period=983,rolling1=0xF123,
                                                               work_read=315,correction1=340,flags4f=0xFE))

    def test_bridge_uses_N_bit_of_wrapped_subtraction_and_preserves_stack_word(self):
        replay=SparkReplay()
        for period in [0,1,15,16,17,0x7FFF,0xFFFF]:
            for rolling in [0,1,0x7FFF,0x8000,0xFFFF]:
                candidate=model.u16(((model.u16(-period)>>4)|0xF000)+rolling)
                for difference in [0,1,0x7FFF,0x8000,0xFFFF]:
                    saved=model.u16(candidate-difference)
                    replay.prepare();replay.cpu.s.d=saved
                    replay.word(0x3FC0,period);replay.word(0x3FF6,rolling);replay.word(0x3FDC,66);replay.word(0x01EC,79)
                    replay.run(0xAB89,0xABCB)
                    expected=model.bridge(saved,period,rolling,rolling,66,79,79)
                    actual=[(p,a,v) for p,a,v,w in replay.memory.events if w==16 and a in {0x3FE8,0x3FE6,0x3FDC,0x3FF6}]
                    self.assertEqual(actual,expected["writes"])
                    for pc,a,_ in replay.memory.reads:
                        if pc in {0xAB9A,0xAB9E,0xABA2}:self.assertEqual(a,0x03F3)
                    self.assertEqual(replay.cpu.s.sp,0x03F4)

    def test_readbacks_at_different_PCs_are_independent_inputs(self):
        replay=SparkReplay()
        for sp in [0x03B0,0x03D0,0x03F4,0x03FF]:
            inputs=model.HandoffInputs(command=0xFF9C,rpm=191,basis=321,anchor_period=1638,
                                      rolling1=0xFFFE,rolling2=0x0001,work_read=0xFFFF,
                                      correction1=300,correction2=301)
            self.check_handoff(replay,inputs,sp=sp)
            reads={(pc,a):v for pc,a,v in replay.memory.reads}
            self.assertEqual(reads[0xAB97,0x3FF6],0xFFFE)
            self.assertEqual(reads[0xABA4,0x3FF6],1)
            self.assertEqual(reads[0xABB3,0x01EC],300)
            self.assertEqual(reads[0xABB7,0x01EC],301)

    def test_random_full_handoffs_match_ROM_word_for_word(self):
        replay=SparkReplay();rng=random.Random(0x31AB)
        for _ in range(512):
            inputs=model.HandoffInputs(command=rng.randrange(65536),startup=rng.randrange(65536),
                                      startup_bypass=bool(rng.randrange(2)),rpm=rng.randrange(256),basis=rng.randrange(65536),
                                      anchor_period=rng.randrange(65536),rolling1=rng.randrange(65536),rolling2=rng.randrange(65536),
                                      work_read=rng.randrange(65536),correction1=rng.randrange(65536),correction2=rng.randrange(65536),
                                      flags4f=rng.randrange(256))
            self.check_handoff(replay,inputs)

    def test_initial_zero_writes_cover_software_terms_and_ASIC_handoff_words(self):
        replay=SparkReplay();replay.prepare()
        replay.memory.mem[0x36:0x1000]=bytes([0xA5])*(0x1000-0x36)
        replay.cpu.s.sp=0x03FF
        replay.run(0x7164,0x717F,budget=10000)
        for a in [0x005F,0x01E6,0x01E8,0x01EA,0x01EC,0x01F2,0x0201,0x083F]:
            self.assertEqual(replay.memory.read16(a),0)
        replay.prepare();replay.word(0x3FDC,0xFFFF);replay.word(0x3FF6,0xFFFF)
        replay.run(0x7156,0x7164)
        self.assertEqual(replay.memory.read16(0x3FDC),0)
        self.assertEqual(replay.memory.read16(0x3FF6),0)

    def test_first_reference_and_no_reference_paths_do_not_admit_conversion(self):
        replay=SparkReplay();replay.prepare()
        self.assertEqual(replay.run(0xA4EC,{0xA5E5,0xAC51,0xA5D7}),0xAC51)
        replay.prepare();replay.memory.mem[0x50]=0x20
        self.assertEqual(replay.run(0xA4EC,{0xA5E5,0xAC51,0xA5D7}),0xAC51)
        self.assertEqual(replay.memory.mem[0x44]&8,8)
        self.assertEqual(replay.memory.mem[0x50]&0x20,0)

    def test_qualifying_reference_count_enters_running_update(self):
        replay=SparkReplay();replay.prepare()
        replay.memory.mem[0x44]=8;replay.memory.mem[0x4F]=0x10
        threshold=int.from_bytes(replay.memory.mem[0x4133:0x4135],"big")
        count_threshold=replay.memory.mem[0x4142]
        self.assertGreater(threshold,0);self.assertGreater(count_threshold,0)
        for count in range(1,count_threshold+1):
            replay.memory.mem[0x50]|=0x20;replay.word(0x3FC0,threshold-1)
            reached=replay.run(0xA4EC,{0xA5E5,0xAC51,0xA5D7})
            self.assertEqual(reached,0xA5E5 if count==count_threshold else 0xAC51)
        self.assertEqual(replay.memory.mem[0x4F]&0x80,0x80)
        self.assertEqual(replay.memory.read16(0x01F2),0)

    def test_no_reference_timeout_is_an_explicit_reset_boundary(self):
        replay=SparkReplay();replay.prepare();replay.memory.mem[0x4F]=0x90;replay.memory.mem[0x0202]=0x17
        self.assertEqual(replay.run(0xA4EC,{0xA5E5,0xAC51,0xA5D7}),0xA5D7)
        self.assertEqual(replay.memory.mem[0x4F]&0x90,0)
        self.assertEqual(replay.memory.read16(0x005F),0xFFFF)

    def test_external_extension_is_retained_as_an_open_boundary(self):
        inputs=model.HandoffInputs(headsup=True)
        with self.assertRaisesRegex(ValueError,"180F"):model.spark_handoff(inputs,self.table)
        with self.assertRaisesRegex(ValueError,"180F"):SparkReplay().handoff(inputs)

    def test_knock_saved_byte_is_stack_local_and_subtracted_as_half_byte(self):
        replay=SparkReplay()
        for sp in [0x03B0,0x03F4,0x03FF]:
            for retard in [0,1,2,127,128,254,255]:
                for command in [0,1,0x7FFF,0x8000,0xFFFF]:
                    replay.prepare(sp);replay.cpu.s.a=retard;replay.word(0x01EE,command)
                    replay.run(0xAACB,0xAADC)
                    self.assertEqual(replay.memory.read16(0x01EE),model.u16(command-(retard>>1)))
                    self.assertEqual(replay.cpu.s.sp,sp)
                    self.assertEqual(replay.memory.mem[0x020C],retard)


if __name__=="__main__":unittest.main()
