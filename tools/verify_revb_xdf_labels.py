"""Replay bounded HC11 witnesses for disputed Rev B XDF labels.

No ROM is written. Recording requires exact private images; committed excerpts
allow the same instruction-level assertions to run in CI without a full BIN.
Synthetic calibration probes alter only copied fixture memory and are recorded
separately from the released calibration. These are not physical engine tests.
"""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'hac31_romsim'))
from romsim.hc11_core import HC11CPU,HC11Memory
from factory_rom_decode import decode
from trace_manual_idle import sweep

SHA='e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1'
REVA_SHA='d771e824686d086986ee0bdef37697bfc63274071a13b79fc4ba59746644923e'
XDF_SHA='788b8f5b79c646fa072b45de5f8e075c77f5d692468d39541406676a0145214e'
EVIDENCE=ROOT/'maps/maintenance/revb_xdf_label_evidence.json'
REPORT=ROOT/'maps/maintenance/revb_xdf_label_trace.json'
XDF=ROOT/'definitions/7427_0.3.12_Manual_Idle_RevB.xdf'
SCOPES=((0x5c9a,0x5cbb),(0x7765,0x7792),(0x7df1,0x7e09),(0x7f86,0x7fd8),
        (0x8d9e,0x8def),
        (0x84bc,0x852c),(0x8548,0x856c),(0x989c,0x9913),
        (0x9a44,0x9a82),(0xaaf7,0xab1a),(0xc9ad,0xc9c0),
        (0xf4b6,0xf4de),(0xf86e,0xf8e0),(0xff40,0xff60))
CAL_RANGES=((0x400b,0x400f),(0x4146,0x414a),(0x48da,0x48db),
            (0x496d,0x4989),(0x49d5,0x49d8),(0x4a88,0x4a8b),
            (0x50a2,0x50aa),(0x51bf,0x5220),(0x5b26,0x5b27),
            (0x9f00,0x9f27),(0xfe9f,0xfea0),(0xff60,0xff71),(0xff8a,0xff8c))


class Memory(HC11Memory):
    def __init__(self,contents):
        super().__init__();self.mem[:]=contents;self.reads=[];self.writes=[]
    def read8(self,address):
        self.reads.append(address&65535);return self.mem[address&65535]
    def write8(self,address,value):
        assert address<0x1000,'Unexpected hardware or ROM write'
        self.writes.append((address&65535,value&255));self.mem[address&65535]=value&255
    def tick(self,cycles):self.cycle_counter+=cycles


def put(memory,address,value):memory[address:address+2]=(value&65535).to_bytes(2,'big')
def word(memory,address):return int.from_bytes(memory[address:address+2],'big')


def execute(contents,entry,stops,d=0,x=0):
    memory=Memory(contents);cpu=HC11CPU(memory)
    cpu.s.pc=entry;cpu.s.sp=0x3ff;cpu.s.ccr=0xd0;cpu.s.d=d;cpu.s.x=x
    cpu._push16(0x7000);pcs=[]
    for _ in range(4000):
        if cpu.s.pc in stops:return memory,cpu,pcs
        pcs.append(cpu.s.pc);cpu.step()
        assert not(cpu.halted or cpu.waiting),hex(cpu.s.pc)
    raise AssertionError(f'Budget exceeded at {cpu.s.pc:04X}')


def fresh(image):
    memory=bytearray(image);memory[:0x400]=bytes(0x400)
    memory[0x800:0x900]=bytes(0x100);return memory


def run_cases(image):
    results={}
    a=[]
    for flags,tps,rpm in [(0,0,40),(1,2,200),(1,3,68),(1,4,68),(2,255,200),(3,255,200)]:
     b=fresh(image);b[0xfe9f]=flags;b[0x1d9]=tps;b[0x63]=rpm;b[0x3e]=0xa2
     m,c,pcs=execute(b,0xff40,{0xe4ff,0xe561});a.append(dict(flags=flags,tps=tps,rpm=rpm,exit=hex(c.s.pc),state=m.mem[0x3e]))
     assert (c.s.pc==0xe561)==bool(flags&2 or flags&1 and tps<=b[0xff8b])
    results['ol']=a
    a=[]
    for async_path in (False,True):
     for enabled in (False,True):
      for pulse in (64,256):
       b=fresh(image);b[0x4979:0x4988]=bytes([8])*15;put(b,0x4971,3);put(b,0x496d,1);put(b,0x496f,48)
       b[0x400b]&=~1;b[0x400e]=b[0x400e]&~16|(16 if enabled else 0);put(b,0x24e,pulse)
       m,c,pcs=execute(b,0x8548 if async_path else 0x84bc,{0x856c}if async_path else {0x84f5},d=pulse)
       expected=pulse+5 if pulse<256 and(not async_path or enabled)else pulse
       assert c.s.d==expected,(async_path,enabled,pulse,c.s.d)
       a.append(dict(path='async'if async_path else'sync',async_flag=enabled,input=pulse,result=c.s.d,lookup=0xf4bd in pcs))
    results['short_pw']=a
    a=[]
    for pulse in (0,31,32,33,256):
     b=fresh(image);put(b,0x496d,32);put(b,0x496f,48);b[0x400b]&=~1;put(b,0x24e,pulse)
     m,c,pcs=execute(b,0x84bc,{0x850b});expected=48 if 0<pulse<32 else pulse
     assert word(m.mem,0x24c)==expected,(pulse,word(m.mem,0x24c))
     a.append(dict(input=pulse,selected=word(m.mem,0x24c),timer=word(m.mem,0x250)))
    results['minimum']=a
    a=[]
    for change in (-1,0,9,10,11):
     for tps in (25,26,27):
      b=fresh(image);put(b,0x87d,100<<8);b[0x1d9]=tps
      m,c,pcs=execute(b,0x9a44,{0x7000},d=(100+change)<<8)
      eligible=change>=10 and tps<26
      assert(0x9a67 in pcs)==eligible,(change,tps)
      a.append(dict(air_delta=change,tps=tps,lookup=0x9a67 in pcs,ae=m.mem[0x87f]))
    results['iac_ae']=a
    a=[]
    for ptr in (0x24a,0xa7):
     b=fresh(image);put(b,0x5216,ptr);b[0x24a]=0x91;b[0xa7]=0x22
     m,c,pcs=execute(b,0xf86e,{0xf8e6},d=15,x=0x51ef)
     assert c.s.a==(0x91 if ptr==0x24a else 0x22)
     assert not any(p==0x24a for p,v in m.writes)
     a.append(dict(pointer=hex(ptr),output=c.s.a,pointer_read=0x5216 in m.reads,source_read=ptr in m.reads))
    results['aldl']=a
    a=[]
    for tps in(2,3,4):
     for rpm in(71,72,73):
      for capture in(0,4):
       b=fresh(image);b[0x1d9]=tps;b[0x62]=rpm;b[0x63]=min(255,rpm*2);b[0x36]=capture
       m,c,pcs=execute(b,0x7f86,{0x7fb0,0x7fc0})
       low=tps<=3 and rpm<72
       assert c.s.x==(0x4a88 if low else 0x49d5)
       a.append(dict(tps=tps,rpm25=rpm,capture=capture,header=hex(c.s.x)))
    results['ve']=a
    a=[]
    for dfco in(0,32):
     for tps in(6,7):
      for command in(-32,-18,-11,0,40):
       b=fresh(image);b[0x51]=dfco;b[0x1d9]=tps;put(b,0x1ee,command)
       m,c,pcs=execute(b,0xaaf7,{0xab1a})
       bound=-11 if dfco and tps<=6 else -18
       value=word(m.mem,0x1ee);value=value-65536 if value&0x8000 else value
       assert value==max(command,bound)
       a.append(dict(dfco=bool(dfco),tps=tps,incoming=command,floor=bound,result=value))
    results['spark_floor']=a

    # The short-pulse borrow behavior differs between the delivery paths.
    a=[]
    for async_path in (False,True):
     b=fresh(image);b[0x4979:0x4988]=bytes([8])*15;put(b,0x4971,90)
     put(b,0x496d,32);put(b,0x496f,48);put(b,0x24e,64);b[0x400e]|=16
     m,c,pcs=execute(b,0x8548 if async_path else 0x84bc,{0x856c}if async_path else{0x84f5},d=64)
     assert c.s.d==(0 if async_path else 48)
     a.append(dict(path='async'if async_path else'sync',input=64,table_added=8,subtraction=90,result=c.s.d))
    results['short_pw_borrow']=a
    # The minimum-pulse comparison precedes the byte-valued voltage offset.
    a=[]
    for pulse in (0,31,32):
     b=fresh(image);put(b,0x496d,32);put(b,0x496f,48);put(b,0x24e,pulse);b[0x256]=7
     m,c,pcs=execute(b,0x84bc,{0x850b})
     chosen=48 if 0<pulse<32 else pulse
     assert word(m.mem,0x24c)==chosen
     assert word(m.mem,0x250)==(chosen+7 if chosen else 0)
     a.append(dict(input=pulse,selected=chosen,offset=7,timer=word(m.mem,0x250)))
    results['minimum_before_offset']=a
    # Seed really initializes the integral word and clears its fractional byte.
    a=[]
    for seed in (38,45):
     b=fresh(image);b[0x9f11]=seed;put(b,0x29d,0xffff)
     m,c,pcs=execute(b,0x989c,{0x7000})
     assert word(m.mem,0x29d)==seed<<8
     assert 0x9f11 in m.reads
     a.append(dict(seed=seed,integral_word=word(m.mem,0x29d),signature=m.mem[0x2a5]))
    results['idle_seed']=a
    # Trace the normal coolant-coordinate producer and target lookup together.
    a=[]
    for coolant in(0,16,80,176,208,255):
     b=fresh(image);b[6]=coolant
     m,c,pcs=execute(b,0xc9ad,{0x7000})
     coordinate=max(0,min(192,coolant-16));assert m.mem[0x283]==coordinate
     n,c,pcs=execute(m.mem,0x98e3,{0x7000})
     assert 0x283 in n.reads and 0xff60+coordinate//16 in n.reads
     assert n.mem[0x857]==image[0xff60+coordinate//16]
     a.append(dict(coolant_byte=coolant,index=coordinate,target_raw=n.mem[0x857],target_rpm=n.mem[0x857]*12.5))
    results['coolant_index_target']=a
    return results


def historical_ae(image,excerpt):
    memory=bytearray(image)
    lo=int(excerpt['start'],16);raw=bytes.fromhex(excerpt['bytes'])
    memory[lo:lo+len(raw)]=raw
    results=[]
    for change in(-1,0,9,10,11):
        for tps in(25,26,27):
            b=fresh(memory);put(b,0x87d,100<<8);b[0x1d9]=tps
            m,c,pcs=execute(b,0x97b6,{0x97e6},d=(100+change)<<8)
            eligible=change>=10 and tps<26
            assert(0x97dd in pcs)==eligible
            results.append(dict(air_delta=change,tps=tps,lookup=0x97dd in pcs,ae=m.mem[0x87f]))
    return results


def instruction_row(pc,instruction):
    return dict(pc=f'{pc:04X}',bytes=instruction.data.hex(' '),
                op=instruction.op,operand=instruction.operand)


def record(image,baseline):
    assert len(image)==65536 and hashlib.sha256(image).hexdigest()==SHA
    assert len(baseline)==65536 and hashlib.sha256(baseline).hexdigest()==REVA_SHA
    assert hashlib.sha256(XDF.read_bytes()).hexdigest()==XDF_SHA
    assert image[0x50a2:0x50aa]==baseline[0x50a2:0x50aa]
    decoded,frontiers,roots=sweep(image)
    targets={0xfe9f,0xff8b,0x4971,0x4979,0x496d,0x496f,0x50a8,0x50a9,
             0x5216,0x49d5,0x4a88,0x48da,0x4146,0x4148,0x9f11,0xff60,0x283}
    refs={f'{a:04X}':[instruction_row(p,i) for p,i in sorted(decoded.items())
                       if i.value==a] for a in sorted(targets)}
    rows=[instruction_row(p,i) for p,i in sorted(decoded.items())
          if any(lo<=p<hi for lo,hi in SCOPES)]
    evidence=dict(image_sha256=SHA,baseline_sha256=REVA_SHA,xdf_sha256=XDF_SHA,
        scope='Recorded code/calibration excerpts, not a full executable ROM.',
        ranges=[dict(start=f'{lo:04X}',end_exclusive=f'{hi:04X}',bytes=image[lo:hi].hex())
                for lo,hi in SCOPES+CAL_RANGES],
        extra_instructions=[row for group in refs.values() for row in group],
        reva_ae_excerpt=dict(start='97B6',end_exclusive='97E6',bytes=baseline[0x97b6:0x97e6].hex()))
    cases=run_cases(image)
    historical=historical_ae(image,evidence['reva_ae_excerpt'])
    assert cases['iac_ae']==historical
    report=dict(image_sha256=SHA,baseline_sha256=REVA_SHA,xdf_sha256=XDF_SHA,
        scope='Actual emitted HC11 instruction fixtures and rooted direct references; no physical engine/PCM, interrupts, timing deadlines or unbounded indexed-pointer proof.',
        synthetic_calibration_probes='Copied fixture memory only: short curve constant 8, subtraction 3/90, minimum 1/32 and replacement 48; async option off/on; logging pointer 024A/00A7; idle seed 38/45. Released files unchanged.',
        actual_calibration=dict(ol_flags=image[0xfe9f],closed_tps=image[0xff8b],
            iac_ae_air_delta=image[0x50a8],iac_ae_tps=image[0x50a9],
            minimum=word(image,0x496d),replacement=word(image,0x496f),
            short_subtraction=word(image,0x4971),logging_pointer=f'{word(image,0x5216):04X}',
            normal_spark_floor_raw=word(image,0x4146)-65536,
            dfco_spark_floor_raw=word(image,0x4148)-65536),
        current_cases=sum(map(len,cases.values())),historical_cases=len(historical),
        cases=cases,reva_ae_cases=historical,direct_references=refs,instructions=rows,
        interpretation_corrections=[
            '50A8 may validly use 100/256 percent of normalized air-command scale. Internal air units are another representation; measured airflow percent is not established.',
            '50A9 consumes normalized TPS, so percent Flow is the wrong quantity even though the same 100/256 numeric scaling can express TPS percent.',
            'Maximum Spark Retard is defensible terminology for a negative signed angle floor; minimum commanded angle describes storage/comparison more directly. Service edits can follow the clamp.',
            'Async is incomplete as an exclusive short-pulse description, but the option bit genuinely gates only async shaping; synchronous shaping has its own unconditional nonzero-below-0100 condition.',
            'Idle VE and Desired AFR are contextual shorthand; selection rules and the ALDL pointer description must remain explicit. No wrong data address was found for these items.'
        ])
    EVIDENCE.write_text(json.dumps(evidence,indent=2)+'\n')
    REPORT.write_text(json.dumps(report,indent=2)+'\n')
    return report


def check_recorded():
    evidence=json.loads(EVIDENCE.read_text());report=json.loads(REPORT.read_text())
    assert evidence['image_sha256']==report['image_sha256']==SHA
    assert evidence['baseline_sha256']==report['baseline_sha256']==REVA_SHA
    assert evidence['xdf_sha256']==report['xdf_sha256']==hashlib.sha256(XDF.read_bytes()).hexdigest()==XDF_SHA
    image=bytearray(65536)
    for row in evidence['ranges']:
        lo,hi=int(row['start'],16),int(row['end_exclusive'],16)
        raw=bytes.fromhex(row['bytes']);assert len(raw)==hi-lo
        image[lo:hi]=raw
    for row in evidence['extra_instructions']:
        lo=int(row['pc'],16);raw=bytes.fromhex(row['bytes']);image[lo:lo+len(raw)]=raw
    for row in report['instructions']+evidence['extra_instructions']:
        pc=int(row['pc'],16)
        assert instruction_row(pc,decode(lambda a,n:image[a:a+n],pc))==row
    cases=run_cases(image);old=historical_ae(image,evidence['reva_ae_excerpt'])
    assert cases==report['cases'] and old==report['reva_ae_cases']==cases['iac_ae']
    assert sum(map(len,cases.values()))==report['current_cases']==87
    assert len(old)==report['historical_cases']==15
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom',type=Path,help='Exact released Rev B, read only')
    parser.add_argument('--baseline',type=Path,help='Exact original Rev A, read only')
    parser.add_argument('--record',action='store_true',help='Record reviewed excerpts/results; requires both images')
    parser.add_argument('--check-recorded',action='store_true',help='Replay committed excerpts without either full BIN')
    args=parser.parse_args()
    if args.record:
        if not args.rom or not args.baseline:parser.error('--record requires --rom and --baseline')
        image=args.rom.read_bytes();baseline=args.baseline.read_bytes()
        result=record(image,baseline)
        assert args.rom.read_bytes()==image and args.baseline.read_bytes()==baseline
    else:
        result=check_recorded()
        if args.rom:assert hashlib.sha256(args.rom.read_bytes()).hexdigest()==SHA
    print(json.dumps(dict(current_cases=result['current_cases'],historical_cases=result['historical_cases'],
        instruction_starts=len(result['instructions']),image_sha256=SHA,
        result='passed',rom_and_xdf_modified=False),indent=2))
