"""One reproducible ROM session, with trace and GUI-friendly stepping."""
from collections import deque
from dataclasses import dataclass
import hashlib
from pathlib import Path
from .bus import Bus, BusEvent, RomWriteError
from .cpu import CPU, UnknownInstruction

@dataclass(frozen=True)
class Stop:
    reason: str
    instructions: int
    pc: int
    detail: str = ""

class Machine:
    def __init__(self):
        self.events = deque(maxlen=25000)
        self.bus = Bus(self._record)
        self.cpu = CPU(self.bus)
        self.breakpoints: set[int] = set()
        self.watch_writes: set[int] = {0x3FCE, 0x3FD0, 0x3060, 0x3067}
        self.last_rom_sha256: str | None = None
        # Virtual controls are inert until source-backed device bindings exist.
        self.engine_inputs = {"rpm":0.0,"map_kpa":100.0,"tps_pct":0.0,
                              "coolant_c":20.0,"battery_v":12.6}
        self.stop_reason = "ROM not loaded"

    def _record(self, event: BusEvent):
        if event.direction in ("W","ROM_WRITE_BLOCKED","PATCH") or (
            event.direction == "R" and event.address in self.watch_writes):
            self.events.append(event)

    def load_rom(self, path: str | Path):
        data = Path(path).read_bytes()
        self.bus.load(data)
        self.last_rom_sha256 = hashlib.sha256(data).hexdigest()
        self.reset()

    def load_bytes(self, data: bytes):
        self.bus.load(data)
        self.last_rom_sha256 = hashlib.sha256(data).hexdigest()
        self.reset()

    def reset(self):
        if not self.bus.rom_loaded:
            return
        self.events.clear()
        self.bus.reset()
        self.cpu.reset()
        self.stop_reason = "Reset complete"

    def step(self) -> Stop:
        if not self.bus.rom_loaded:
            return Stop("no_rom",0,0,"Load a BIN first")
        pc = self.cpu.r.pc
        try:
            self.cpu.step()
            return Stop("step",1,self.cpu.r.pc)
        except (UnknownInstruction,RomWriteError,ValueError) as exc:
            self.stop_reason = str(exc)
            return Stop("fault",0,pc,str(exc))

    def run(self, count: int = 1000) -> Stop:
        if count < 1:
            raise ValueError("Instruction count must be positive")
        if not self.bus.rom_loaded:
            return Stop("no_rom",0,0,"Load a BIN first")
        executed=0
        for _ in range(count):
            if self.cpu.r.pc in self.breakpoints:
                return Stop("breakpoint",executed,self.cpu.r.pc)
            step=self.step()
            if step.reason != "step":
                return Stop(step.reason,executed,step.pc,step.detail)
            executed+=1
        return Stop("limit",executed,self.cpu.r.pc)

    def irq(self, vector: int, *, maskable: bool = True) -> bool:
        if not self.bus.rom_loaded:
            return False
        if not 0xFFD6 <= vector <= 0xFFFE or vector & 1:
            raise ValueError("Unknown HC11 vector address")
        return self.cpu.interrupt(vector,maskable=maskable)

    def write_memory(self, address: int, value: int):
        self.bus.write8(address,value)

    def memory_dump(self, start: int, length: int=128) -> str:
        if not (0 <= start <= 0xFFFF) or length < 1:
            raise ValueError("Invalid dump range")
        lines=[]
        for a in range(start,min(0x10000,start+length),16):
            chunk=[self.bus.peek8(j) for j in range(a,min(a+16,0x10000,start+length))]
            lines.append(f"{a:04X}  "+ " ".join(f"{v:02X}" for v in chunk))
        return "\n".join(lines)
