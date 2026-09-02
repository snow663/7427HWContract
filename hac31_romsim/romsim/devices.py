from __future__ import annotations

from dataclasses import dataclass, field
from math import inf
from typing import Callable

from .hc11_core import hi, lo, u8, u16


@dataclass
class EngineInputs:
    engine_state: str = "KEY_ON"
    rpm: float = 0.0
    map_kpa: float = 30.0
    tps_pct: float = 0.0
    coolant_c: float = 20.0
    battery_v: float = 12.6
    vss_mph: float = 0.0
    adc: list[int] = field(default_factory=lambda: [0] * 8)
    port_a: int = 0
    port_c: int = 0
    port_e: int = 0

    def set_value(self, name: str, value: str | int | float) -> None:
        key = name.strip().lower()
        if key.startswith("adc."):
            channel = int(key.split(".", 1)[1], 0)
            if not 0 <= channel < 8:
                raise ValueError("ADC channel must be 0..7")
            self.adc[channel] = u8(int(_as_number(value)))
            return
        if key in {"engine_state", "state"}:
            self.engine_state = str(value).upper()
            return
        aliases = {
            "map": "map_kpa", "map_kpa": "map_kpa",
            "tps": "tps_pct", "tps_pct": "tps_pct",
            "coolant": "coolant_c", "cts": "coolant_c", "coolant_c": "coolant_c",
            "battery": "battery_v", "battery_v": "battery_v",
            "vss": "vss_mph", "vss_mph": "vss_mph",
            "rpm": "rpm",
        }
        if key in aliases:
            setattr(self, aliases[key], float(_as_number(value)))
            return
        ports = {"port_a": "port_a", "porta": "port_a", "port_c": "port_c",
                 "portc": "port_c", "port_e": "port_e", "porte": "port_e"}
        if key in ports:
            setattr(self, ports[key], u8(int(_as_number(value))))
            return
        raise KeyError(f"unknown input {name!r}")

    def summary(self) -> str:
        adc = " ".join(f"{n}:{v:02X}" for n, v in enumerate(self.adc))
        return (
            f"STATE={self.engine_state} RPM={self.rpm:g} MAP={self.map_kpa:g}kPa "
            f"TPS={self.tps_pct:g}% CTS={self.coolant_c:g}C BAT={self.battery_v:g}V "
            f"VSS={self.vss_mph:g}mph ADC[{adc}]"
        )


def _as_number(value: str | int | float) -> float:
    if isinstance(value, str):
        try:
            return float(int(value, 0))
        except ValueError:
            return float(value)
    return float(value)


class ADCDevice:
    """Generic HC11 four-result ADC. Semantic sensor/channel bindings stay external."""

    CCF = 0x80
    SCAN = 0x20
    MULT = 0x10

    def __init__(self, inputs: EngineInputs, conversion_cycles: int = 32) -> None:
        self.inputs = inputs
        self.conversion_cycles = conversion_cycles
        self.control = 0
        self.results = [0, 0, 0, 0]
        self.remaining = 0

    def reset(self) -> None:
        self.control = 0
        self.results[:] = [0, 0, 0, 0]
        self.remaining = 0

    def start(self, value: int) -> None:
        self.control = u8(value) & ~self.CCF
        self.remaining = self.conversion_cycles

    def tick(self, cycles: int) -> None:
        if self.remaining <= 0:
            return
        self.remaining -= cycles
        if self.remaining > 0:
            return
        channel = self.control & 0x07
        if self.control & self.MULT:
            self.results[:] = [self.inputs.adc[(channel + i) & 7] for i in range(4)]
        else:
            self.results[:] = [self.inputs.adc[channel]] * 4
        self.control |= self.CCF
        if self.control & self.SCAN:
            self.remaining = self.conversion_cycles

    def read(self, offset: int) -> int:
        if offset == 0x30:
            return self.control
        if 0x31 <= offset <= 0x34:
            return self.results[offset - 0x31]
        raise KeyError(offset)


class TimerDevice:
    """Functional HC11 timer subset: TCNT, OC compares, masks, and W1C flags."""

    COMPARE_OFFSETS = {1: 0x16, 2: 0x18, 3: 0x1A, 4: 0x1C, 5: 0x1E}
    FLAG_BITS = {1: 0x80, 2: 0x40, 3: 0x20, 4: 0x10, 5: 0x08}
    VECTORS = {1: 0xFFE8, 2: 0xFFE6, 3: 0xFFE4, 4: 0xFFE2, 5: 0xFFE0}

    def __init__(self) -> None:
        self.counter = 0
        self.regs = bytearray(0x28)

    def reset(self) -> None:
        self.counter = 0
        self.regs[:] = bytes(len(self.regs))

    def _word(self, off: int) -> int:
        return (self.regs[off] << 8) | self.regs[off + 1]

    @staticmethod
    def _crossed(old: int, new: int, target: int, elapsed: int) -> bool:
        if elapsed >= 0x10000:
            return True
        distance = (target - old) & 0xFFFF
        return 0 < distance <= elapsed

    def tick(self, cycles: int) -> None:
        cycles = max(0, int(cycles))
        old = self.counter
        self.counter = (self.counter + cycles) & 0xFFFF
        for channel, off in self.COMPARE_OFFSETS.items():
            if self._crossed(old, self.counter, self._word(off), cycles):
                self.regs[0x23] |= self.FLAG_BITS[channel]
        if old + cycles > 0xFFFF:
            self.regs[0x25] |= 0x80

    def read(self, offset: int) -> int:
        if offset == 0x0E:
            return hi(self.counter)
        if offset == 0x0F:
            return lo(self.counter)
        return self.regs[offset]

    def write(self, offset: int, value: int) -> bool:
        value = u8(value)
        if offset in {0x0E, 0x0F}:
            return True
        if offset == 0x23 or offset == 0x25:
            self.regs[offset] &= ~value
            return True
        if 0 <= offset < len(self.regs):
            self.regs[offset] = value
            return True
        return False

    def pending_vector(self) -> int | None:
        active = self.regs[0x22] & self.regs[0x23]
        for channel in range(1, 6):
            if active & self.FLAG_BITS[channel]:
                return self.VECTORS[channel]
        if (self.regs[0x24] & self.regs[0x25] & 0x80) != 0:
            return 0xFFDE
        return None


class ASICDevice:
    """7427 external register window with only contract-backed active behavior."""

    def __init__(self, inputs: EngineInputs, e_clock_hz: int) -> None:
        self.inputs = inputs
        self.e_clock_hz = int(e_clock_hz)
        self.storage = bytearray(0x40)
        self.asic_ticks = 0
        self.ref_phase_cycles = 0.0
        self.ref_irq_pending = False
        self.last_ref_period = 0xFFFF

    def reset(self) -> None:
        self.storage[:] = bytes(len(self.storage))
        self.asic_ticks = 0
        self.ref_phase_cycles = 0.0
        self.ref_irq_pending = False
        self.last_ref_period = 0xFFFF
        self._store_word(0x00, self.last_ref_period)

    def _store_word(self, offset: int, value: int) -> None:
        value = u16(value)
        self.storage[offset] = hi(value)
        self.storage[offset + 1] = lo(value)

    def tick(self, cycles: int) -> None:
        self.asic_ticks = (self.asic_ticks + max(0, cycles)) & 0xFFFF_FFFF
        self._store_word(0x0A, (self.asic_ticks // 32) & 0xFFFF)
        rpm = max(0.0, self.inputs.rpm)
        if rpm <= 0.0:
            self.ref_phase_cycles = 0.0
            return
        # Contract formula implies 4 reference events/rev and ASIC E/32 ticks.
        interval = self.e_clock_hz * 60.0 / (4.0 * rpm)
        self.ref_phase_cycles += cycles
        while self.ref_phase_cycles >= interval:
            self.ref_phase_cycles -= interval
            self.last_ref_period = max(1, min(0xFFFF, round(983040.0 / rpm)))
            self._store_word(0x00, self.last_ref_period)
            self.ref_irq_pending = True

    def read8(self, address: int) -> int:
        return self.storage[(address & 0xFFFF) - 0x3FC0]

    def write8(self, address: int, value: int) -> None:
        self.storage[(address & 0xFFFF) - 0x3FC0] = u8(value)

    def consume_ref_irq(self) -> bool:
        pending = self.ref_irq_pending
        self.ref_irq_pending = False
        return pending
