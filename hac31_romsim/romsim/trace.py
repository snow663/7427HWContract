from __future__ import annotations

from dataclasses import asdict, dataclass
from collections import deque
import json
from pathlib import Path
from typing import Any


@dataclass
class AccessRecord:
    cycle: int
    pc: int
    opcode: int
    access_type: str
    address: int
    value: int
    region: str
    device: str
    symbol: str
    evidence: str
    a: int
    b: int
    d: int
    x: int
    y: int
    sp: int
    ccr: int
    engine_state: str
    rpm: float
    map_kpa: float
    tps_pct: float
    coolant_c: float
    battery_v: float
    vss_mph: float
    note: str = ""


@dataclass
class OutputRecord:
    cycle: int
    pc: int
    address: int
    value: int
    width: int
    name: str
    subsystem: str
    evidence: str
    note: str = ""


class TraceRecorder:
    def __init__(self, max_records: int = 250_000) -> None:
        self.max_records = max_records
        self.accesses: list[AccessRecord] = []
        self.outputs: list[OutputRecord] = []
        self.events: list[dict[str, Any]] = []
        self.timeline: deque[dict[str, Any]] = deque(maxlen=max_records)
        self._stream = None

    def clear(self) -> None:
        self.accesses.clear()
        self.outputs.clear()
        self.events.clear()
        self.timeline.clear()

    def _emit(self, row: dict[str, Any]) -> None:
        self.timeline.append(row)
        if self._stream is not None:
            self._stream.write(json.dumps(row) + "\n")

    def access(self, row: AccessRecord) -> None:
        self.accesses.append(row)
        if len(self.accesses) > self.max_records:
            del self.accesses[: len(self.accesses) - self.max_records]
        self._emit({"record": "bus", **asdict(row)})

    def output(self, row: OutputRecord) -> None:
        self.outputs.append(row)
        if len(self.outputs) > self.max_records:
            del self.outputs[: len(self.outputs) - self.max_records]
        self._emit({"record": "output", **asdict(row)})

    def event(self, kind: str, cycle: int, **fields: Any) -> None:
        row = {"kind": kind, "cycle": cycle, **fields}
        self.events.append(row)
        self._emit({"record": "event", **row})

    def start_stream(self, path: str | Path) -> None:
        self.close_stream()
        self._stream = Path(path).open("w", encoding="utf-8")

    def close_stream(self) -> None:
        if self._stream is not None:
            self._stream.close()
            self._stream = None

    def write_jsonl(self, path: str | Path) -> None:
        with Path(path).open("w", encoding="utf-8") as handle:
            for row in self.timeline:
                handle.write(json.dumps(row) + "\n")
