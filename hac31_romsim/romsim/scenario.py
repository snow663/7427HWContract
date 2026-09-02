from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


@dataclass(order=True)
class ScenarioEvent:
    cycle: int
    inputs: dict[str, Any] = field(default_factory=dict, compare=False)
    writes: list[dict[str, Any]] = field(default_factory=list, compare=False)
    interrupt: str | int | None = field(default=None, compare=False)
    note: str = field(default="", compare=False)


class Scenario:
    def __init__(self, events: list[ScenarioEvent] | None = None) -> None:
        self.events = sorted(events or [])
        self.cursor = 0

    @classmethod
    def load(cls, path: str | Path) -> "Scenario":
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        rows = data["events"] if isinstance(data, dict) else data
        return cls([ScenarioEvent(
            cycle=int(row["cycle"]),
            inputs=dict(row.get("inputs", {})),
            writes=list(row.get("writes", [])),
            interrupt=row.get("interrupt"),
            note=row.get("note", ""),
        ) for row in rows])

    def reset(self) -> None:
        self.cursor = 0

    def due(self, cycle: int) -> list[ScenarioEvent]:
        rows: list[ScenarioEvent] = []
        while self.cursor < len(self.events) and self.events[self.cursor].cycle <= cycle:
            rows.append(self.events[self.cursor])
            self.cursor += 1
        return rows

    def next_cycle(self) -> int | None:
        if self.cursor >= len(self.events):
            return None
        return self.events[self.cursor].cycle

