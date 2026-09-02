from __future__ import annotations

from typing import Callable

from .contracts import Evidence, PCMProfile
from .devices import ADCDevice, ASICDevice, EngineInputs, TimerDevice
from .hc11_core import CPUState, HC11Memory, hi, lo, u8
from .trace import AccessRecord, OutputRecord, TraceRecorder


class ContractMemory(HC11Memory):
    """One 64K bus with relocatable HC11 internals and contract-described devices."""

    def __init__(self, profile: PCMProfile, inputs: EngineInputs, trace: TraceRecorder) -> None:
        super().__init__()
        self.profile = profile
        self.inputs = inputs
        self.trace_recorder = trace
        self.timer = TimerDevice()
        self.adc = ADCDevice(inputs)
        self.asic = ASICDevice(inputs, profile.e_clock_hz)
        self.state_provider: Callable[[], CPUState] | None = None
        self.context_pc = 0
        self.context_opcode = 0
        self.force_rom_write = False
        self._word_write_depth = 0

    def reset(self) -> None:
        super().reset()
        self.timer = TimerDevice()
        self.adc.reset()
        self.asic.reset()

    def _canonical_contract_address(self, address: int) -> int:
        if address == 0x103D:
            return 0x303D
        if self._is_internal_reg(address):
            return 0x3000 + (address - self.reg_base)
        return address & 0xFFFF

    def _bus_log(self, addr: int, data: int, rw: str, note: str = "") -> None:
        super()._bus_log(addr, data, rw, note)
        state = self.state_provider() if self.state_provider else CPUState()
        canonical = self._canonical_contract_address(addr)
        contract = self.profile.register_for(canonical)
        region = self.profile.region_for(canonical)
        self.trace_recorder.access(AccessRecord(
            cycle=self.cycle_counter,
            pc=self.context_pc,
            opcode=self.context_opcode,
            access_type=rw,
            address=addr & 0xFFFF,
            value=data & 0xFF,
            region=region.name if region else ("internal" if self._is_internal(addr) else "unmapped"),
            device=contract.subsystem if contract else "memory",
            symbol=contract.name if contract else "",
            evidence=(contract.evidence.value if contract else (region.evidence.value if region else Evidence.UNKNOWN.value)),
            a=state.a, b=state.b, d=state.d, x=state.x, y=state.y,
            sp=state.sp, ccr=state.ccr,
            engine_state=self.inputs.engine_state,
            rpm=self.inputs.rpm, map_kpa=self.inputs.map_kpa,
            tps_pct=self.inputs.tps_pct, coolant_c=self.inputs.coolant_c,
            battery_v=self.inputs.battery_v, vss_mph=self.inputs.vss_mph,
            note=note,
        ))

    def _internal_offset(self, address: int) -> int | None:
        if self._is_internal_reg(address):
            return (address - self.reg_base) & 0x3F
        return None

    def read8(self, addr: int) -> int:
        addr &= 0xFFFF
        off = self._internal_offset(addr)
        if off is not None:
            if off == 0x00:
                value = self.inputs.port_a
            elif off == 0x02:
                value = self.inputs.port_c
            elif off == 0x08:
                value = self.inputs.port_e
            elif 0x0E <= off <= 0x27:
                value = self.timer.read(off)
            elif 0x30 <= off <= 0x34:
                value = self.adc.read(off)
            else:
                return super().read8(addr)
            self._bus_log(addr, value, "R", "internal-device")
            self._watch(addr, "R", value)
            return value
        if 0x3FC0 <= addr <= 0x3FFF:
            value = self.asic.read8(addr)
            self._bus_log(addr, value, "R", "7427-asic-window")
            self._watch(addr, "R", value)
            return value
        return super().read8(addr)

    def write8(self, addr: int, value: int) -> None:
        addr &= 0xFFFF
        value = u8(value)
        off = self._internal_offset(addr)
        if off is not None:
            handled = False
            if off == 0x00:
                self.inputs.port_a = value
                handled = True
            elif off == 0x02:
                self.inputs.port_c = value
                handled = True
            elif off == 0x08:
                self.inputs.port_e = value
                handled = True
            elif 0x0E <= off <= 0x27:
                handled = self.timer.write(off, value)
            elif off == 0x30:
                self.adc.start(value)
                handled = True
            if handled:
                self._bus_log(addr, value, "W", "internal-device")
                self._watch(addr, "W", value)
                if self._word_write_depth == 0:
                    self._record_output(addr, value, 8)
                return
        if 0x3FC0 <= addr <= 0x3FFF:
            self.asic.write8(addr, value)
            self._bus_log(addr, value, "W", "7427-asic-window")
            self._watch(addr, "W", value)
            if self._word_write_depth == 0:
                self._record_output(addr, value, 8)
            return
        if self.profile.is_rom(addr) and not self.force_rom_write:
            self._bus_log(addr, value, "W", "rom-write-blocked")
            self.trace_recorder.event("rom_write_blocked", self.cycle_counter, address=addr, value=value, pc=self.context_pc)
            return
        super().write8(addr, value)

    def write16(self, addr: int, value: int) -> None:
        self._word_write_depth += 1
        try:
            self.write8(addr, hi(value))
            self.write8((addr + 1) & 0xFFFF, lo(value))
        finally:
            self._word_write_depth -= 1
        self._record_output(addr & 0xFFFF, value & 0xFFFF, 16)

    def _record_output(self, address: int, value: int, width: int) -> None:
        canonical = self._canonical_contract_address(address)
        contract = self.profile.register_for(canonical)
        if contract is None or "W" not in contract.access:
            return
        if contract.behavior not in {"output", "timer_output", "latch", "watchdog"}:
            return
        self.trace_recorder.output(OutputRecord(
            cycle=self.cycle_counter,
            pc=self.context_pc,
            address=address,
            value=value,
            width=width,
            name=contract.name,
            subsystem=contract.subsystem,
            evidence=contract.evidence.value,
            note=contract.notes,
        ))

    def debug_write8(self, address: int, value: int, allow_rom: bool = False) -> None:
        previous = self.force_rom_write
        self.force_rom_write = allow_rom
        try:
            self.write8(address, value)
        finally:
            self.force_rom_write = previous

    def debug_read8(self, address: int) -> int:
        """Non-destructive, trace-free debugger read."""
        address &= 0xFFFF
        off = self._internal_offset(address)
        if off is not None:
            if off == 0x00:
                return self.inputs.port_a
            if off == 0x02:
                return self.inputs.port_c
            if off == 0x08:
                return self.inputs.port_e
            if 0x0E <= off <= 0x27:
                return self.timer.read(off)
            if 0x30 <= off <= 0x34:
                return self.adc.read(off)
            if off == 0x3D:
                return self.init_value
            if off == 0x3F:
                return self.config_value
            if 0x2B <= off <= 0x2E:
                return self.sci.read(off)
            if off == 0x2F:
                return self.sci.rx_fifo[0] if self.sci.rx_fifo else 0
            return self.internal_regs[off]
        if self._is_internal_ram(address):
            return self.internal_ram[address - self.ram_base]
        if 0x3FC0 <= address <= 0x3FFF:
            return self.asic.read8(address)
        return self.mem[address]

    def tick(self, cycles: int) -> None:
        # HC11Memory.tick advances cycle_counter and calls this TimerDevice.
        super().tick(cycles)
        self.adc.tick(cycles)
        self.asic.tick(cycles)

    def pending_interrupt_vector(self) -> int | None:
        if self.asic.consume_ref_irq():
            return 0xFFF2
        return self.timer.pending_vector()
