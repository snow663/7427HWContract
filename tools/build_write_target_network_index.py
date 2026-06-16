#!/usr/bin/env python3
"""Build the whole-ROM write-target network index for the 7427/$31 source.

This is a static analysis/index artifact only. It does not create runtime ASM,
relax hardware gates, or prove bench behavior.
"""
from __future__ import annotations

import argparse
import csv
import re
from collections import Counter, defaultdict, deque
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

SOURCE_CANDIDATES = [
    Path("source/31/BMHM_HAC_ORG_7100_to_end.asm"),
    Path("31_HAC_from_ORG_7100_to_end_NOWRAP.asm"),
]
OUT_CSV = Path("maps/contracts/write_target_network_index.csv")
OUT_MD = Path("docs/contracts/WRITE_TARGET_NETWORK_INDEX.md")
OUT_TEST = Path("docs/tests/WRITE_TARGET_NETWORK_INDEX_TEST.md")

WRITE_OPS = {
    "STAA", "STAB", "STD", "STS", "STX", "STY",
    "BSET", "BCLR", "CLR", "INC", "DEC", "COM", "NEG",
    "ASL", "LSL", "LSR", "ROL", "ROR",
}
BRANCH_OPS = {
    "BRA", "BRN", "BHI", "BLS", "BCC", "BCS", "BNE", "BEQ", "BVC", "BVS",
    "BPL", "BMI", "BGE", "BLT", "BGT", "BLE", "BRSET", "BRCLR", "JMP", "JSR",
}
ACCUMULATORS = {"A", "B", "D", "X", "Y", "SP"}
LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)\s*(.*?)\s*(?:;\s*(.*))?$")
LABEL_RE = re.compile(r"^\s*(L[0-9A-Fa-f]{4})\s+")
HEX_DIRECT_RE = re.compile(r"^\$([0-9A-Fa-f]{1,4})$")
HEX_INDEXED_RE = re.compile(r"^\$([0-9A-Fa-f]{1,4}),([XY])$")
SYMBOL_DIRECT_RE = re.compile(r"^(L[0-9A-Fa-f]{4})$")
SYMBOL_INDEXED_RE = re.compile(r"^(L[0-9A-Fa-f]{4}),([XY])$")
IMM_HEX_RE = re.compile(r"^#\$([0-9A-Fa-f]{1,4})$")
IMM_DEC_RE = re.compile(r"^#([0-9]+)$")


@dataclass
class ParsedLine:
    pc: str
    label: str
    op: str
    operands: str
    comment: str
    raw: str


def choose_source(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    for path in SOURCE_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("No source file found; pass --source")


def strip_comment_operands(operands: str) -> str:
    return operands.split(";", 1)[0].strip()


def split_operands(operands: str) -> list[str]:
    # BSET/BCLR often use target,#mask,target; preserve comma-index X/Y as part of operand.
    parts: list[str] = []
    current = ""
    for chunk in operands.split(","):
        chunk = chunk.strip()
        if chunk in {"X", "Y"} and current:
            current += "," + chunk
        else:
            if current:
                parts.append(current)
            current = chunk
    if current:
        parts.append(current)
    return parts


def parse_source(path: Path) -> list[ParsedLine]:
    rows: list[ParsedLine] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = LINE_RE.match(raw)
        if not m:
            continue
        pc, label, op, operands, comment = m.groups()
        rows.append(ParsedLine(pc.upper(), label or "", op.upper(), strip_comment_operands(operands or ""), comment or "", raw.rstrip()))
    return rows


def symbol_to_addr(symbol: str) -> int | None:
    m = SYMBOL_DIRECT_RE.match(symbol)
    if m:
        return int(m.group(1)[1:], 16)
    m = HEX_DIRECT_RE.match(symbol)
    if m:
        return int(m.group(1), 16)
    return None


def resolve_target(target: str, x_base: int | None, y_base: int | None) -> tuple[int | None, str, str, str]:
    target = target.strip()
    x_base_text = f"${x_base:04X}" if x_base is not None else ""
    y_base_text = f"${y_base:04X}" if y_base is not None else ""

    m = SYMBOL_DIRECT_RE.match(target)
    if m:
        return int(m.group(1)[1:], 16), m.group(1).upper(), x_base_text, y_base_text
    m = HEX_DIRECT_RE.match(target)
    if m:
        addr = int(m.group(1), 16)
        return addr, f"L{addr:04X}" if addr < 0x10000 else target, x_base_text, y_base_text
    m = HEX_INDEXED_RE.match(target)
    if m:
        offset = int(m.group(1), 16)
        idx = m.group(2)
        base = x_base if idx == "X" else y_base
        if base is not None:
            addr = (base + offset) & 0xFFFF
            return addr, f"L{addr:04X}", x_base_text, y_base_text
        return None, target.upper(), x_base_text, y_base_text
    m = SYMBOL_INDEXED_RE.match(target)
    if m:
        offset = int(m.group(1)[1:], 16)
        idx = m.group(2)
        base = x_base if idx == "X" else y_base
        if base is not None:
            addr = (base + offset) & 0xFFFF
            return addr, f"L{addr:04X}", x_base_text, y_base_text
        return None, target.upper(), x_base_text, y_base_text
    return None, target.upper(), x_base_text, y_base_text


def width_for(op: str) -> str:
    if op in {"STD", "STS", "STX", "STY"}:
        return "16"
    if op in {"BSET", "BCLR"}:
        return "bit"
    return "8"


def value_source_for(op: str, operands: list[str]) -> tuple[str, str]:
    if op == "STAA":
        return "A", ""
    if op == "STAB":
        return "B", ""
    if op == "STD":
        return "D", ""
    if op == "STS":
        return "SP", ""
    if op == "STX":
        return "X", ""
    if op == "STY":
        return "Y", ""
    if op in {"BSET", "BCLR"}:
        mask = operands[1] if len(operands) > 1 else ""
        return f"{op} mask", mask
    if op == "CLR":
        return "zero", ""
    return "read_modify_write", ""


def target_operand(op: str, operands: list[str]) -> str | None:
    if not operands:
        return None
    if op in {"STAA", "STAB", "STD", "STS", "STX", "STY", "CLR", "INC", "DEC", "COM", "NEG", "ASL", "LSL", "LSR", "ROL", "ROR", "BSET", "BCLR"}:
        return operands[0]
    return None


def is_memory_target(target: str | None) -> bool:
    if not target:
        return False
    t = target.strip().upper()
    if not t or t in ACCUMULATORS:
        return False
    if t.startswith("#"):
        return False
    return True


def classify_role(addr: int | None, symbol: str, op: str) -> tuple[str, str, str]:
    s = symbol.upper()
    if addr is None:
        return "unknown", "low", "unresolved target; indexed/base tracking may be required"
    if s == "L3FCE":
        return "hardware sink:fuel pulsewidth", "high", "known EFI pulsewidth command sink"
    if s in {"L3FE8", "L3FE6", "L3FDC", "L3FF6", "L3FEC", "L3FE4"}:
        return "hardware sink/state:spark stock handoff", "medium", "spark stock handoff / rolling-state candidate"
    if s in {"L3062", "L3060", "L3FFC"}:
        return "hardware sink/state:IAC candidate", "medium", "IAC port/phase/enable/park candidate"
    if s == "L303A":
        return "hardware sink:watchdog/COP", "high", "COP reset register candidate"
    if 0x3000 <= addr <= 0x30FF:
        return "hardware register/ASIC/CPU peripheral", "medium", "mapped hardware register range"
    if op in {"BSET", "BCLR"}:
        return "mode flag/safety gate/state latch", "medium", "bit mutation"
    if addr < 0x0400:
        return "RAM state/calculation/shadow", "medium", "internal RAM write"
    return "ROM/data? unexpected write target", "low", "write target outside normal RAM/hardware ranges"


def branch_context(history: Iterable[str]) -> str:
    return " | ".join(history)


def derive_read_counts(rows: list[ParsedLine]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for row in rows:
        operands = split_operands(row.operands)
        for operand in operands:
            token = operand.strip().upper()
            # Skip immediate, pure branch labels, and store/bset first target are still counted elsewhere by symbol counts only.
            if token.startswith("#"):
                continue
            direct = token.split(",", 1)[0]
            if SYMBOL_DIRECT_RE.match(direct) or HEX_DIRECT_RE.match(direct):
                addr = symbol_to_addr(direct)
                if addr is not None:
                    counts[f"L{addr:04X}"] += 1
    return counts


def build_rows(parsed: list[ParsedLine]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    x_base: int | None = None
    y_base: int | None = None
    routine = ""
    branches: deque[str] = deque(maxlen=4)
    read_counts = derive_read_counts(parsed)

    for row in parsed:
        if row.label:
            routine = row.label.upper()
        operands = split_operands(row.operands)

        if row.op in {"LDX", "LDY"} and operands:
            m = IMM_HEX_RE.match(operands[0].upper()) or IMM_DEC_RE.match(operands[0].upper())
            if m:
                try:
                    base = int(m.group(1), 16 if operands[0].startswith("#$") else 10)
                    if row.op == "LDX":
                        x_base = base
                    else:
                        y_base = base
                except ValueError:
                    pass

        if row.op in BRANCH_OPS:
            branches.append(f"{row.pc}:{row.op} {row.operands}".strip())

        if row.op not in WRITE_OPS:
            continue
        target = target_operand(row.op, operands)
        if not is_memory_target(target):
            continue
        addr, symbol, x_text, y_text = resolve_target(target or "", x_base, y_base)
        role, conf, note = classify_role(addr, symbol, row.op)
        value_source, bitmask = value_source_for(row.op, operands)
        out.append({
            "pc": row.pc,
            "routine_label": routine,
            "instruction": row.op,
            "target_address": f"${addr:04X}" if addr is not None else "",
            "target_symbol": symbol,
            "write_width": width_for(row.op),
            "bitmask": bitmask,
            "value_source": value_source,
            "x_base": x_text,
            "y_base": y_text,
            "call_context": routine,
            "nearby_branch_conditions": branch_context(branches),
            "candidate_role": role,
            "confidence": conf,
            "reads_observed_for_target_symbol": str(read_counts.get(symbol, 0)),
            "notes": note,
        })
    return out



def aggregate_by_target(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["target_symbol"]].append(row)
    out: list[dict[str, str]] = []
    for symbol, members in sorted(grouped.items()):
        first = members[0]
        op_counts = Counter(r["instruction"] for r in members)
        role_counts = Counter(r["candidate_role"] for r in members)
        source_counts = Counter(r["value_source"] for r in members)
        bitmasks = sorted(set(r["bitmask"] for r in members if r["bitmask"]))
        bases = sorted(set((r["x_base"] or r["y_base"]) for r in members if r["x_base"] or r["y_base"]))
        contexts = sorted(set(r["call_context"] for r in members if r["call_context"]))
        sites = ";".join(f"{r['pc']}:{r['instruction']}" for r in members[:20])
        if len(members) > 20:
            sites += f";...+{len(members) - 20}"
        out.append({
            "target_symbol": symbol,
            "target_address": first["target_address"],
            "write_count": str(len(members)),
            "first_pc": first["pc"],
            "first_routine_label": first["routine_label"],
            "representative_instruction": first["instruction"],
            "write_widths": " ".join(sorted(set(r["write_width"] for r in members))),
            "bitmasks": " ".join(bitmasks),
            "value_sources": " | ".join(f"{k}:{v}" for k, v in source_counts.most_common()),
            "x_y_bases_seen": " ".join(bases),
            "call_contexts": " | ".join(contexts[:10]),
            "nearby_branch_conditions_sample": first["nearby_branch_conditions"],
            "candidate_role": role_counts.most_common(1)[0][0],
            "confidence": first["confidence"],
            "reads_observed_for_target_symbol": first["reads_observed_for_target_symbol"],
            "write_sites_sample": sites,
            "notes": first["notes"],
        })
    return out

def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict[str, str]], source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    role_counts = Counter(r.get("candidate_role", "") for r in rows)
    op_counts = Counter(r.get("representative_instruction", "") for r in rows)
    target_counts = Counter({r["target_symbol"]: int(r.get("write_count", "0") or 0) for r in rows})
    high_value_targets = ["L3FCE", "L3FE8", "L3FE6", "L3FDC", "L3FF6", "L3FEC", "L3FE4", "L3062", "L3060", "L3FFC", "L303A"]

    lines = []
    lines.append("# WRITE_TARGET_NETWORK_INDEX")
    lines.append("")
    lines.append("## Purpose")
    lines.append("")
    lines.append("Whole-ROM static sweep of write targets. This starts from mutations instead of subsystem names so that RAM, hardware, shadows, mode flags, safety gates, rolling state, and dispatcher selectors can be separated by read/write network context.")
    lines.append("")
    lines.append("This is a static analysis artifact only. It does not implement runtime ASM, relax bench gates, or prove hardware behavior.")
    lines.append("")
    lines.append("## Source")
    lines.append("")
    lines.append(f"- source file: `{source}`")
    lines.append(f"- target dossier rows emitted: `{len(rows)}`")
    lines.append("")
    lines.append("## Write op coverage")
    lines.append("")
    for op, count in sorted(op_counts.items()):
        lines.append(f"- `{op}`: {count}")
    lines.append("")
    lines.append("## Candidate role counts")
    lines.append("")
    for role, count in role_counts.most_common():
        lines.append(f"- `{role}`: {count}")
    lines.append("")
    lines.append("## High-value target dossier seeds")
    lines.append("")
    lines.append("| target | writes observed | role seed | note |")
    lines.append("|---|---:|---|---|")
    for target in high_value_targets:
        writes = target_counts.get(target, 0)
        matching = next((r for r in rows if r["target_symbol"] == target), None)
        role = matching["candidate_role"] if matching else "not written in sweep"
        note = matching["notes"] if matching else "no write row emitted"
        lines.append(f"| `{target}` | {writes} | `{role}` | {note} |")
    lines.append("")
    lines.append("## Indexing limitations")
    lines.append("")
    lines.append("- Indexed writes are resolved only when the linear pass can see a recent immediate `LDX`/`LDY` base.")
    lines.append("- Branch context is nearby static context, not a full path-sensitive proof.")
    lines.append("- Read counts are symbol-token observations and are intended as triage hints, not complete dataflow proof.")
    lines.append("- A target is not safe to delete merely because its role is unknown or low confidence.")
    lines.append("")
    lines.append("## Deletion rule")
    lines.append("")
    lines.append("Do not delete a variable because it looks unimportant. Delete only after the read/write network proves it does not feed hardware, safety, dispatch, or a preserved stock driver.")
    lines.append("")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_test(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = """# WRITE_TARGET_NETWORK_INDEX_TEST

## Scope

Static test definition for the write-target network index.

This test must verify that the artifact:

- sweeps mutation instructions across the source
- includes indexed write forms where resolvable
- records PC, routine label, instruction, target, write width, bitmask, value source, base tracking, branch context, role, confidence, and notes
- treats unresolved or low-confidence targets as retained-for-review, not removable
- does not create runtime ASM
- does not relax fuel, spark, or IAC hardware gates

## Required output files

```text
maps/contracts/write_target_network_index.csv
docs/contracts/WRITE_TARGET_NETWORK_INDEX.md
```

## Required write op coverage

```text
STAA STAB STD STS STX STY BSET BCLR CLR INC DEC COM NEG ASL/LSL LSR ROL ROR
```

Accumulator-only shifts/rotates must not be counted as memory writes unless an operand target exists.

## Required interpretation

A write proves only that a target is mutated. It does not prove target importance. Importance is determined by read/use/downstream routing.

## Non-relaxation clause

This artifact must not permit deleting a target, creating a hardware writer, bypassing bench proof, or changing any subsystem gate.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build write-target network index")
    parser.add_argument("--source", default=None)
    args = parser.parse_args()
    source = choose_source(args.source)
    parsed = parse_source(source)
    raw_rows = build_rows(parsed)
    rows = aggregate_by_target(raw_rows)
    write_csv(OUT_CSV, rows)
    write_md(OUT_MD, rows, source)
    write_test(OUT_TEST)
    print(f"wrote {len(rows)} target dossier rows from {len(raw_rows)} write rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
