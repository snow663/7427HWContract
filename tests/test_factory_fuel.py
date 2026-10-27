from __future__ import annotations

import csv
import json
from pathlib import Path
import random
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from factory_fuel import FuelModel,base_values,multiply
from factory_fuel_replay import FuelReplay
import verify_factory_fuel as proof
from build_factory_scheduler import recorded_rom


class FactoryFuelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence=json.loads(proof.EVIDENCE.read_text())
        with (proof.OUT/'factory_fuel_memory_accesses.csv').open() as source:rows=list(csv.DictReader(source))
        cls.input_bytes=sorted({int(r['address'],16)+i for r in rows if r['address'] and int(r['address'],16)<0x1000 and 'R' in r['access']
                                and r['scope'] in {'running_fuel_and_delivery','asynchronous_output_helper'} for i in range(int(r['width_bits'])//8)})

    def compare(self,replay,start=0x7FD8):
        model=FuelModel(bytes(replay.memory.mem),replay.memory.samples).run(start)
        replay.cpu.s.d=replay.memory.read16(0x024E) if start==0x83B1 else 0
        replay.run(start)
        actual=replay.writes()
        if actual!=model.writes:
            for i in range(max(len(actual),len(model.writes))):
                a=actual[i] if i<len(actual) else None;b=model.writes[i] if i<len(model.writes) else None
                if a!=b:self.fail(f'first differing state write #{i}: actual={a}, model={b}; stages={model.stages}')
        for _,a,_,width in actual:
            self.assertEqual(replay.memory.mem[a:a+width//8],model.mem[a:a+width//8],f'{a:04X}')
        self.assertEqual(replay.cpu.s.sp,0x03F4)
        return model

    def test_recorded_evidence_and_review_vectors_reproduce(self):
        for name,content in proof.build(recorded_rom(self.evidence)).items():
            self.assertEqual((proof.OUT/name).read_text(),content,name)
        replay=FuelReplay()
        for name,start,inputs in proof.review_cases():
            with self.subTest(case=name):
                replay.prepare(inputs);self.compare(replay,start)

    def test_saved_integer_quotient_high_byte_controls_base_saturation(self):
        replay=FuelReplay()
        for air,flow,afr in [(0,7008,145),(1,7008,145),(65535,1,1),(65535,256,1),
                              (65535,0,1),(65535,7008,0),(65535,7008,255)]:
            replay.prepare(proof.defaults());replay.word(0x0234,air)
            replay.word(0x4D92,flow);replay.memory.mem[0x024A]=afr
            replay.run(0x8010,0x8032)
            q=65535 if afr==0 or air>>2>=afr<<8 else ((air>>2)<<16)//(afr<<8)
            expected=65535 if flow==0 else min(65535,(q<<8)//flow)
            self.assertEqual(replay.memory.read16(0x024E),expected,(air,flow,afr))
            self.assertEqual(replay.cpu.s.sp,0x03F4)

    def test_base_fixed_point_divides_and_all_normalization_stores_match_ROM(self):
        replay=FuelReplay();rng=random.Random(0x31B453)
        cases=[(d,t,v,e,p,a,f) for d,t in [(0,0),(1,1),(1,2),(65535,65535),(65535,1)]
               for v,e,p,a,f in [(206,180,2000,145,7008),(255,255,0,0,0),(0,0,1,1,1),(255,255,1,1,256)]]
        cases.extend((rng.randrange(65536),rng.randrange(65536),rng.randrange(256),rng.randrange(256),
                      rng.randrange(65536),rng.randrange(256),rng.randrange(65536)) for _ in range(512))
        for density,temp,volume,ve,period,afr,flow in cases:
            replay.prepare(proof.defaults())
            for a,v in [(0x0257,density),(0x0236,temp),(0x01E8,period),(0x4D92,flow)]:replay.word(a,v)
            for a,v in [(0x4D94,volume),(0x0231,ve),(0x024A,afr)]:replay.memory.mem[a]=v
            initial=bytes(replay.memory.mem);model=FuelModel(initial);expected=model.base();replay.run(0x7FD8,0x8032)
            self.assertEqual(replay.writes(),model.writes)
            for a,key in [(0x0238,'displaced'),(0x0234,'air'),(0x0232,'air_rate'),(0x024E,'pulse')]:
                self.assertEqual(replay.memory.read16(a),expected[key])
            self.assertEqual(replay.cpu.s.sp,0x03F4)

    def test_BLM_128_is_neutral_until_the_explicit_double_saturation_boundary(self):
        replay=FuelReplay()
        for pulse in [0,1,127,128,32767,32768,65535]:
            for blm in [0,1,100,127,128,129,255]:
                replay.prepare(proof.defaults());replay.word(0x024E,pulse);replay.cpu.s.a=blm
                replay.cpu._push16(0x0200);replay.run(0x80EE,0x0200)
                expected=multiply(blm,min(pulse*2,65535))
                self.assertEqual(replay.memory.read16(0x024E),expected)
                if blm==128:self.assertEqual(expected,min(pulse,32768))
                self.assertEqual(replay.cpu.s.sp,0x03F4)

    def test_EGR_rounding_and_PE_suppression_of_lean_BLM_match_ROM(self):
        replay=FuelReplay()
        for pulse in [0,1,127,32767,32768,65535]:
            for egr in [0,127,128,32767,65535]:
                for blm,pe in [(100,False),(100,True),(128,True),(255,True)]:
                    replay.prepare(proof.defaults());replay.word(0x024E,pulse);replay.word(0x01B2,egr)
                    replay.memory.mem[0x0248]=blm;replay.memory.mem[0x3D]=32 if pe else 0
                    model=FuelModel(replay.memory.mem);model.egr_and_blm();replay.run(0x8032,0x8058)
                    self.assertEqual(replay.writes(),model.writes)

    def test_INT_is_a_signed_saturating_adder_and_MAP_AE_is_a_separate_adder(self):
        replay=FuelReplay()
        for correction in range(256):
            for pulse in [0,1,127,128,32767,65407,65535]:
                replay.prepare(proof.defaults());replay.word(0x024E,pulse)
                replay.memory.mem[0x026F]=correction;replay.memory.mem[0x023E]=173
                signed=correction-256 if correction&128 else correction
                expected=min(65535,max(0,pulse+signed))
                replay.run(0x8380,0x83B1)
                writes=replay.writes()
                self.assertEqual(writes[0],(0x839C,0x024E,expected,16))
                self.assertEqual(replay.memory.read16(0x024E),min(65535,expected+173))
                self.assertEqual(replay.memory.read16(0x0254),min(65535,expected+173))

    def test_two_dimensional_lookup_uses_two_rounded_column_interpolations_then_rows(self):
        replay=FuelReplay();rng=random.Random(0x31F4DE)
        for _ in range(1024):
            replay.prepare(proof.defaults())
            for i in range(100):replay.memory.mem[0x49AD+i]=rng.randrange(256)
            a,b=rng.randrange(256),rng.randrange(256)
            model=FuelModel(replay.memory.mem);expected=model.lookup2(a,b,0x49AA)
            replay.cpu.s.a,replay.cpu.s.b,replay.cpu.s.x=a,b,0x49AA
            replay.cpu._push16(0x0200);replay.run(0xF4DE,0x0200)
            self.assertEqual(replay.cpu.s.a,expected,(a,b))
            self.assertEqual((replay.cpu.s.b,replay.cpu.s.x,replay.cpu.s.sp),(b,0x49AA,0x03F4))

    def test_every_short_correction_input_and_both_lookup_slopes_match_ROM(self):
        replay=FuelReplay()
        for descending in [False,True]:
            for pulse in range(1,256):
                replay.prepare(proof.defaults());replay.word(0x024E,pulse)
                replay.memory.mem[0x4979:0x4988]=bytes((255 if (i%2==int(descending)) else 0) for i in range(15))
                self.compare(replay,0x84BC)

    def test_every_16bit_final_PW_matches_ROM_including_offset_wrap(self):
        replay=FuelReplay()
        for pulse in range(65536):
            replay.prepare(proof.defaults());replay.word(0x024E,pulse);replay.memory.mem[0x0256]=61
            self.compare(replay,0x84BC)

    def test_sync_zero_skips_offset_but_async_zero_adds_it_and_toggles_word_bit0400(self):
        replay=FuelReplay();replay.prepare(proof.defaults());replay.memory.mem[0x0256]=61
        self.compare(replay,0x84BC)
        self.assertEqual(replay.memory.read16(0x3FCE),0)
        replay.prepare(proof.defaults());replay.memory.mem[0x0256]=61;replay.word(0x3FFC,0xA5A5)
        model=FuelModel(replay.memory.mem);model.emit_async(0)
        replay.cpu.s.d=0;replay.cpu._push16(0x0200);replay.run(0x8548,0x0200)
        self.assertEqual(replay.writes(),model.writes)
        self.assertEqual(replay.memory.read16(0x3FF2),61)
        self.assertEqual([v for _,a,v,_ in replay.writes() if a==0x3FFC],[0xA1A5,0xA5A5])

    def test_TBI_async_bypass_leaves_0250_unchanged_and_clears_only_the_integer_accumulator_word(self):
        replay=FuelReplay();inputs=proof.defaults()
        inputs['bytes']['0050']=0;inputs['words'].update({'024E':10,'0254':10,'0250':0x4567})
        replay.prepare(inputs);self.compare(replay,0x83B1)
        self.assertEqual(replay.memory.read16(0x3FCE),0)
        self.assertEqual(replay.memory.read16(0x0250),0x4567)
        replay.prepare(proof.defaults());replay.word(0x024E,500);replay.memory.mem[0x025B]=173
        self.compare(replay,0x83B1)
        self.assertEqual(replay.memory.read16(0x0259),0)
        self.assertEqual(replay.memory.mem[0x025B],173)

    def test_boundary_and_random_delivery_modes_predict_all_business_writes(self):
        replay=FuelReplay();rng=random.Random(0x3183B1)
        for n in range(1200):
            replay.prepare(proof.defaults())
            for a in self.input_bytes:replay.memory.mem[a]=rng.randrange(256)
            replay.word(0x3FC0,rng.choice([0,1,127,32767,32768,65535,rng.randrange(65536)]))
            replay.word(0x3FFC,rng.randrange(65536))
            replay.memory.mem[0x400B]=rng.choice([0,1,4,5])
            replay.memory.mem[0x400E]=rng.choice([3,0x13])
            with self.subTest(case=n):self.compare(replay,0x83B1)

    def test_random_full_running_pipeline_matches_every_explicit_RAM_and_ASIC_write(self):
        replay=FuelReplay();rng=random.Random(0x317FD8)
        modes=set()
        for n in range(2048):
            replay.prepare(proof.defaults())
            for a in self.input_bytes:replay.memory.mem[a]=rng.randrange(256)
            replay.word(0x3FC0,rng.randrange(65536));replay.word(0x3FFC,rng.randrange(65536))
            replay.memory.mem[0x400B]=rng.choice([0,1,4,5,0x84])
            replay.memory.mem[0x400E]=rng.choice([3,0x13])
            replay.memory.mem[0x400F]=rng.choice([0,1,0x10,0x80,0x81])
            with self.subTest(case=n):m=self.compare(replay);modes.update(m.stages)
        self.assertTrue({'hard_zero','decel_reduction','recover','reset','delay','TBI_async_route','async_emit'}<=modes,modes)

    def test_boot_initialization_clears_fuel_software_words_and_attempts_ASIC_zero(self):
        replay=FuelReplay();replay.prepare(proof.defaults());replay.memory.mem[0x100:0x29D]=bytes([0xA5])*413
        replay.cpu.s.sp=0x03FF;replay.run(0x7164,0x717F)
        for a in [0x0232,0x0234,0x0238,0x023A,0x024C,0x024E,0x0250,0x0252,0x0254,0x0256,0x0259,0x025A,0x025C,0x026F]:
            self.assertEqual(replay.memory.read16(a),0)
        replay.prepare();replay.word(0x3FCE,65535);replay.word(0x3FF2,65535);replay.word(0x3FFC,0xA5A5)
        replay.run(0x7156,0x7164)
        self.assertEqual(replay.memory.read16(0x3FCE),0);self.assertEqual(replay.memory.read16(0x3FF2),0)
        self.assertEqual(replay.memory.read16(0x3FFC),0xA5A5)

    def test_load_reset_path_still_decrements_the_active_decel_timer(self):
        replay=FuelReplay();replay.prepare(proof.defaults())
        for a,v in [(0x16,16),(0x6F,32),(6,255),(0x01CF,255),(0x0245,2)]:replay.memory.mem[a]=v
        model=FuelModel(replay.memory.mem);model.controls();replay.run(0x8058,0x82ED)
        self.assertIn('reset_load',model.stages)
        self.assertEqual(replay.writes(),model.writes)
        self.assertEqual(replay.memory.mem[0x0245],1)

    def test_INT_proportional_combination_keeps_direction_cap_and_signed_bias(self):
        replay=FuelReplay()
        for i in [0,1,127,128,129,254,255]:
            for p in [0,1,127,128,254,255]:
                for direction,cap in [(False,False),(True,False),(True,True)]:
                    replay.prepare(proof.defaults());replay.memory.mem[0x020F]=i;replay.memory.mem[0x027A]=p
                    replay.memory.mem[0x3E]=64 if direction else 0
                    replay.memory.mem[0x400B]=12 if cap else 4;replay.memory.mem[0x44]=2 if cap else 0
                    replay.memory.mem[0x4912]=100
                    model=FuelModel(replay.memory.mem);model.int_producer();replay.run(0x88E9,0x891D)
                    self.assertEqual(replay.writes(),model.writes)

    def test_injector_offset_voltage_lookup_matches_every_input_byte(self):
        replay=FuelReplay()
        for battery in range(256):
            replay.prepare(proof.defaults());replay.memory.mem[0xA7]=battery
            model=FuelModel(replay.memory.mem);model.offset_producer();replay.run(0xE2FB,0xE306)
            self.assertEqual(replay.writes(),model.writes)

    def test_CPI_alternative_output_scales_period_and_does_not_invent_a_3FCE_write(self):
        replay=FuelReplay()
        for multiplier in [0,1,128,255]:
            for period in [0,1,8191,32767,65535]:
                replay.prepare(proof.defaults());replay.memory.mem[0x400B]=1
                replay.memory.mem[0x4973]=multiplier;replay.word(0x005F,period);replay.word(0x024E,1000)
                model=self.compare(replay,0x84BC)
                self.assertEqual(model.w(0x081F),min(65535,4*multiply(multiplier,period)))
                self.assertFalse(any(a==0x3FCE for _,a,_,_ in replay.writes()))

    def test_device_read_samples_remain_distinct_from_stored_fixture_values(self):
        replay=FuelReplay();inputs=proof.defaults()
        inputs['bytes']['0050']=0;inputs['words'].update({'024E':10,'0254':10,'023A':1000})
        replay.prepare(inputs,samples={0x842C:{0x3FC0:17},0x8577:{0x3FFC:0xFFFF}})
        self.compare(replay,0x83B1)
        reads={(p,a):v for p,a,v in replay.memory.reads}
        self.assertEqual(reads[0x842C,0x3FC0],17)
        self.assertEqual(reads[0x8577,0x3FFC],65535)


if __name__=='__main__':unittest.main()
