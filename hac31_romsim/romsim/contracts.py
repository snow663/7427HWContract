from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path
from typing import Any, Iterable


class Evidence(str, Enum):
    """What supports a name or behavior; never a claim of physical proof."""

    CONTRACT_HIGH = "contract_high"
    CONTRACT_TEST_ITEM = "contract_test_item"
    HAC_SOURCE_HINT = "hac_source_hint"
    MODELED = "modeled"
    BENCH_PROVEN = "bench_proven"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class RegionContract:
    start: int
    end: int
    name: str
    kind: str
    writable: bool
    evidence: Evidence
    notes: str = ""

    def contains(self, address: int) -> bool:
        return self.start <= (address & 0xFFFF) <= self.end


@dataclass(frozen=True)
class RegisterContract:
    address: int
    name: str
    width: int = 8
    access: str = "RW"
    behavior: str = "storage"
    subsystem: str = "unknown"
    evidence: Evidence = Evidence.UNKNOWN
    notes: str = ""


@dataclass
class PCMProfile:
    profile_id: str
    title: str
    e_clock_hz: int
    reset_vector: int
    rom_ranges: list[tuple[int, int]]
    regions: list[RegionContract]
    registers: dict[int, RegisterContract]
    provenance: dict[str, Any] = field(default_factory=dict)
    timing: dict[str, Any] = field(default_factory=dict)

    def region_for(self, address: int) -> RegionContract | None:
        for region in self.regions:
            if region.contains(address):
                return region
        return None

    def register_for(self, address: int) -> RegisterContract | None:
        address &= 0xFFFF
        hit = self.registers.get(address)
        if hit is not None:
            return hit
        previous = self.registers.get((address - 1) & 0xFFFF)
        if previous and previous.width == 16:
            return previous
        return None

    def is_rom(self, address: int) -> bool:
        address &= 0xFFFF
        return any(lo <= address <= hi for lo, hi in self.rom_ranges)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PCMProfile":
        regions = [
            RegionContract(
                start=_number(row["start"]),
                end=_number(row["end"]),
                name=row["name"],
                kind=row["kind"],
                writable=bool(row.get("writable", True)),
                evidence=Evidence(row.get("evidence", "unknown")),
                notes=row.get("notes", ""),
            )
            for row in data.get("regions", [])
        ]
        registers: dict[int, RegisterContract] = {}
        for row in data.get("registers", []):
            contract = RegisterContract(
                address=_number(row["address"]),
                name=row["name"],
                width=int(row.get("width", 8)),
                access=row.get("access", "RW"),
                behavior=row.get("behavior", "storage"),
                subsystem=row.get("subsystem", "unknown"),
                evidence=Evidence(row.get("evidence", "unknown")),
                notes=row.get("notes", ""),
            )
            registers[contract.address] = contract
        return cls(
            profile_id=data["profile_id"],
            title=data["title"],
            e_clock_hz=int(data["e_clock_hz"]),
            reset_vector=_number(data.get("reset_vector", "0xFFFE")),
            rom_ranges=[(_number(a), _number(b)) for a, b in data["rom_ranges"]],
            regions=regions,
            registers=registers,
            provenance=data.get("provenance", {}),
            timing=data.get("timing", {}),
        )

    @classmethod
    def load(cls, path: str | Path) -> "PCMProfile":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


def _number(value: int | str) -> int:
    if isinstance(value, int):
        return value
    return int(value, 0)


def infer_bin_base(size: int) -> int:
    """Infer only conventional complete CPU-space images; ambiguity is rejected."""
    bases = {0x10000: 0x0000, 0xC000: 0x4000, 0x8000: 0x8000}
    if size not in bases:
        raise ValueError(
            f"cannot infer load base for {size} byte BIN; specify --base explicitly"
        )
    return bases[size]

