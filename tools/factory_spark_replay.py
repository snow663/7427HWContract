"""Execute captured spark instructions on the existing CPU, independently of equations."""
from __future__ import annotations

import json
from build_factory_scheduler import recorded_rom
from factory_scheduler_replay import HC11CPU
from factory_integer_replay import IntegerMemory as SparkMemory
from verify_factory_spark import EVIDENCE
from romsim.hc11_core import CPUState


class SparkReplay:
    def __init__(self):
        self.memory=SparkMemory(recorded_rom(json.loads(EVIDENCE.read_text())))
        self.cpu=HC11CPU(self.memory)
        self.stock_latency=bytes(self.memory.mem[0x454A:0x4559])
        self.stock_scale=self.memory.mem[0x4141]

    def prepare(self,sp=0x03F4):
        self.memory.mem[:0x4000]=bytes(0x4000)
        self.memory.mem[0x454A:0x4559]=self.stock_latency
        self.memory.mem[0x4141]=self.stock_scale
        self.cpu.s=CPUState(sp=sp,ccr=0xC0)
        self.cpu.halted=self.cpu.waiting=False
        self.cpu.exec_trace.clear();self.memory.writes.clear();self.memory.events.clear();self.memory.reads.clear()
        self.memory.pc=None;self.memory.samples={}

    def word(self,address,value):
        self.memory.mem[address:address+2]=(value&0xFFFF).to_bytes(2,"big")

    def run(self,start,stops,budget=3000):
        self.cpu.s.pc=start
        stops={stops} if isinstance(stops,int) else set(stops)
        for _ in range(budget):
            pc=self.cpu.s.pc
            if pc in stops:return pc
            if 0x1800<=pc<=0x1815:raise ValueError(f"External hook reached at {pc:04X}")
            self.memory.pc=pc
            self.cpu.step()
        raise RuntimeError(f"Spark replay budget exhausted at {self.cpu.s.pc:04X}")

    def handoff(self,inputs,table=None,sp=0x03F4):
        self.prepare(sp)
        if table is not None:self.memory.mem[0x454A:0x454A+len(table)]=table
        self.cpu.s.d=inputs.command
        for address,value in [(0x01F2,inputs.startup),(0x005F,inputs.basis),(0x01EC,inputs.correction1),
                              (0x3FC0,inputs.anchor_period),(0x3FF6,inputs.rolling1),(0x3FDC,inputs.work_read)]:self.word(address,value)
        self.memory.mem[0x51]=0x40 if inputs.startup_bypass else 0
        self.memory.mem[0x4F]=inputs.flags4f
        self.memory.mem[0x86]=0x40 if inputs.headsup else 0
        self.memory.mem[0x62]=inputs.rpm
        self.memory.samples={0xAB8E:{0x3FC0:inputs.anchor_period},0xAB97:{0x3FF6:inputs.rolling1},
                             0xABA4:{0x3FF6:inputs.rolling1 if inputs.rolling2 is None else inputs.rolling2},
                             0xABB0:{0x3FDC:inputs.work_read},0xABB3:{0x01EC:inputs.correction1},
                             0xABB7:{0x01EC:inputs.correction1 if inputs.correction2 is None else inputs.correction2}}
        self.run(0xAB3E,0xABCB)
        return [(pc,a,v) for pc,a,v,w in self.memory.events if w==16 and a in {0x3FE8,0x3FE6,0x3FDC,0x3FF6}]

    def terms(self,inputs):
        self.prepare()
        for a,v in [(0x01E8,inputs.period),(0x01E6,inputs.previous_period),(0x01EA,inputs.adaptive),(0x3FC0,inputs.limit_period)]:self.word(a,v)
        for a,v in [(0x01C0,inputs.load_now),(0x01C2,inputs.load_old),(0x01C1,inputs.load_latch),(0xA7,inputs.battery)]:self.memory.mem[a]=v
        self.run(0xA687,0xA706)
        return [(pc,a,v,w) for pc,a,v,w in self.memory.events if a in {0x01EA,0x01E6,0x083F,0x01EC,0x01C2}]
