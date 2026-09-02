from __future__ import annotations

from dataclasses import dataclass
from html import unescape
from pathlib import Path
import re

from .contracts import Evidence


@dataclass(frozen=True)
class Symbol:
    address: int
    label: str
    text: str
    evidence: Evidence


class SymbolTable:
    """Optional annotations. HAC-derived text is always visibly non-authoritative."""

    def __init__(self) -> None:
        self.by_address: dict[int, list[Symbol]] = {}

    def add(self, symbol: Symbol) -> None:
        self.by_address.setdefault(symbol.address & 0xFFFF, []).append(symbol)

    def at(self, address: int) -> list[Symbol]:
        return self.by_address.get(address & 0xFFFF, [])

    def label(self, address: int) -> str:
        rows = self.at(address)
        return "/".join(row.label for row in rows)

    def load_hac_html(self, path: str | Path) -> int:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")
        text = unescape(re.sub(r"<[^>]+>", "", raw))
        pattern = re.compile(r"^([0-9A-Fa-f]{4}):\s*(L[0-9A-Fa-f]{4})?\s*(.*)$")
        count = 0
        for line in text.splitlines():
            match = pattern.match(line)
            if not match:
                continue
            address = int(match.group(1), 16)
            label = match.group(2) or f"L{address:04X}"
            self.add(Symbol(address, label, match.group(3).strip(), Evidence.HAC_SOURCE_HINT))
            count += 1
        return count

