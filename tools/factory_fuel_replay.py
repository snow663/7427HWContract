"""Execute captured fuel instructions using the CPU, independently of equations."""
from __future__ import annotations

import json
from build_factory_scheduler import recorded_rom
from factory_scheduler_replay import HC11CPU
from factory_integer_replay import IntegerMemory
from factory_rom_decode import decode
from verify_factory_fuel import EVIDENCE,seed_memory
from romsim.hc11_core import CPUState


class FuelReplay:
    def __init__(self):
        self.rom=recorded_rom(json.loads(EVIDENCE.read_text()))
        self.memory=IntegerMemory(self.rom);self.cpu=HC11CPU(self.memory)
        self.stock=bytes(self.memory.mem)
        self.business_pcs=set();pc=0x7FD8
        for start,end in [(0x7FD8,0x852C),(0x8548,0x858B),(0x88E9,0x891E),(0xE2FB,0xE306)]:
            pc=start
            while pc<end:
                ins=decode(self.rom.read,pc);access=ins.access()
                if access and 'W' in access['access']:self.business_pcs.add(pc)
                pc=ins.next_pc

    def prepare(self,inputs=None,sp=0x03F4,samples=None):
        self.memory.mem[:]=self.stock
        if inputs is not None:
            seed_memory(self.memory.mem,inputs)
        self.cpu.s=CPUState(sp=sp,ccr=0xC0)
        self.cpu.halted=self.cpu.waiting=False
        self.cpu.exec_trace.clear();self.memory.writes.clear();self.memory.events.clear();self.memory.reads.clear()
        self.memory.pc=None;self.memory.samples=samples or {};self.executed=[]

    def word(self,address,value):self.memory.mem[address:address+2]=(value&65535).to_bytes(2,'big')

    def run(self,start=0x7FD8,stop=0x852C,budget=10000):
        self.cpu.s.pc=start
        for _ in range(budget):
            pc=self.cpu.s.pc
            if pc==stop:return self
            if 0x1800<=pc<=0x1815:raise ValueError(f'External hook {pc:04X}')
            self.memory.pc=pc;self.executed.append(pc);self.cpu.step()
        raise RuntimeError(f'Fuel budget exhausted at {self.cpu.s.pc:04X}')

    def writes(self):return [e for e in self.memory.events if e[0] in self.business_pcs]
