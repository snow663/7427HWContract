"""Instrumented flat fixture for bounded execution of captured factory bytes.

Device words are coherent fixture samples keyed by read PC. This records bus
values and instruction accounting, without inventing peripheral time behavior.
"""
from factory_scheduler_replay import FixtureMemory


class IntegerMemory(FixtureMemory):
    def __init__(self,rom):
        super().__init__(rom)
        self.pc=None;self.samples={};self.events=[];self.reads=[];self.in_word=False

    def read8(self,address):
        for base,value in self.samples.get(self.pc,{}).items():
            if address==base:return value>>8
            if address==base+1:return value&255
        return super().read8(address)

    def read16(self,address):
        value=super().read16(address)
        self.reads.append((self.pc,address,value))
        return value

    def write16(self,address,value):
        self.in_word=True
        try:super().write16(address,value)
        finally:self.in_word=False
        self.events.append((self.pc,address,value&0xFFFF,16))

    def write8(self,address,value):
        super().write8(address,value)
        if not self.in_word:self.events.append((self.pc,address,value&255,8))

