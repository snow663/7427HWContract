#!/usr/bin/env python3
"""Build dispatcher / indirect-control-flow reverse map for 7427/$31 source."""
from __future__ import annotations

import argparse
import csv
import re
from collections import defaultdict
from pathlib import Path

SOURCE_CANDIDATES = [Path("source/31/BMHM_HAC_ORG_7100_to_end.asm"), Path("31_HAC_from_ORG_7100_to_end_NOWRAP.asm")]
OUT_CSV = Path("maps/contracts/dispatcher_reverse_map.csv")
OUT_MD = Path("docs/contracts/DISPATCHER_REVERSE_MAP.md")
OUT_TEST = Path("docs/tests/DISPATCHER_REVERSE_MAP_TEST.md")
LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)\s*(.*?)\s*(?:;\s*(.*))?$")
ORG_RE = re.compile(r"\bORG\s+\$?([0-9A-Fa-f]{4})")
TABLE_ROW_RE = re.compile(r"^\s*(L[0-9A-Fa-f]{4})\s+FCB\s+\$?([0-9A-Fa-f]{4})\s*(?:;\s*(.*))?$")
IMM_LDX_RE = re.compile(r"LDX\s+#\$?([0-9A-Fa-f]{4})")
SYMBOL_RE = re.compile(r"L([0-9A-Fa-f]{4})")


def choose_source(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    for path in SOURCE_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError("No source file found; pass --source")


def parse_lines(source: Path):
    parsed = []
    raw_lines = source.read_text(encoding="utf-8", errors="ignore").splitlines()
    current_label = ""
    for idx, raw in enumerate(raw_lines):
        m = LINE_RE.match(raw)
        if m:
            pc, label, op, operands, comment = m.groups()
            if label:
                current_label = label.upper()
            parsed.append({"lineno": idx + 1, "pc": pc.upper(), "label": (label or "").upper(), "routine": current_label, "op": op.upper(), "operands": (operands or "").split(";", 1)[0].strip(), "comment": comment or "", "raw": raw.rstrip()})
    return raw_lines, parsed


def table_entries(raw_lines: list[str], table_addr: str) -> list[dict[str, str]]:
    entries = []
    capture = False
    for raw in raw_lines:
        if re.search(rf"\bORG\s+\$?{table_addr}\b", raw, re.I):
            capture = True
            continue
        if capture:
            if re.search(r"\bORG\s+\$?[0-9A-Fa-f]{4}\b", raw):
                break
            m = TABLE_ROW_RE.match(raw)
            if m:
                label, target, comment = m.groups()
                entries.append({"entry_label": label.upper(), "entry_value": f"${int(target,16):04X}", "resolved_target": f"L{int(target,16):04X}", "entry_comment": comment or ""})
            elif entries and raw.strip() and not raw.strip().startswith(";") and ":" in raw:
                break
    return entries


def find_target_writes(parsed: list[dict[str, str]], target_addr: str, window_end_pc: int | None = None) -> str:
    # Coarse landing-routine write-target summary: collect direct writes in the next 80 parsed instructions after target label.
    start_index = None
    target_label = f"L{target_addr.upper().lstrip('$').lstrip('L')}"
    for i, row in enumerate(parsed):
        if row.get("label") == target_label or row.get("pc") == target_label[1:]:
            start_index = i
            break
    if start_index is None:
        return ""
    write_ops = {"STAA", "STAB", "STD", "STS", "STX", "STY", "BSET", "BCLR", "CLR", "INC", "DEC"}
    writes = []
    for row in parsed[start_index:start_index + 80]:
        if row["op"] in write_ops:
            target = row["operands"].split(",", 1)[0].strip()
            if target:
                writes.append(target)
    return " ".join(sorted(set(writes)))[:500]


def classify_subsystem(text: str) -> tuple[str, str]:
    t = text.upper()
    if any(x in t for x in ["IAC", "L3062", "L3060", "L3FFC"]):
        return "iac/idle-air candidate", "medium"
    if any(x in t for x in ["FUEL", "BPW", "INJ", "L3FCE"]):
        return "fuel candidate", "medium"
    if any(x in t for x in ["SPARK", "EST", "L3FE8", "L3FE6"]):
        return "spark candidate", "medium"
    if any(x in t for x in ["ALDL", "OUTPUT", "DEVICE ID"]):
        return "ALDL/output-control dispatcher", "high"
    if "MAJOR LOOP" in t:
        return "major-loop scheduler", "high"
    return "unknown/mixed", "low"


def build_dispatchers(raw_lines: list[str], parsed: list[dict[str, str]]) -> list[dict[str, str]]:
    rows = []
    for i, row in enumerate(parsed):
        if row["op"] not in {"JMP", "JSR"} or ",X" not in row["operands"].upper():
            continue
        context = parsed[max(0, i - 12):i]
        table_addr = ""
        index_source = ""
        index_math = []
        for c in context:
            if c["op"] in {"LDAB", "LDAA", "LDD"} and not index_source:
                index_source = f"{c['op']} {c['operands']}"
            if c["op"] in {"ANDB", "ANDA", "ASLB", "ASLA", "ABX", "ADDB", "ADDA", "LSLB", "LSLA", "LSL", "MUL"}:
                index_math.append(f"{c['pc']}:{c['op']} {c['operands']}".strip())
            m = IMM_LDX_RE.search(c["raw"])
            if m:
                table_addr = f"${int(m.group(1),16):04X}"
        notes = " | ".join(c["raw"].strip() for c in context[-6:])
        entries = table_entries(raw_lines, table_addr[1:]) if table_addr else []
        if entries:
            for n, ent in enumerate(entries):
                text = f"{row['comment']} {ent['entry_comment']} {ent['resolved_target']} {notes} {find_target_writes(parsed, ent['resolved_target'])}"
                subsystem, conf = classify_subsystem(text)
                rows.append({
                    "dispatcher_pc": row["pc"],
                    "dispatcher_label": row["routine"],
                    "index_source": index_source,
                    "index_math": " ; ".join(index_math),
                    "mask_shift_add_operations": " ; ".join(index_math),
                    "table_address": table_addr,
                    "entry_width": "16-bit target address",
                    "entry_count": str(len(entries)),
                    "entry_index": str(n),
                    "entry_value": ent["entry_value"],
                    "resolved_target": ent["resolved_target"],
                    "target_label": ent["resolved_target"],
                    "target_write_targets": find_target_writes(parsed, ent["resolved_target"]),
                    "candidate_subsystem": subsystem,
                    "confidence": conf,
                    "notes": f"{ent['entry_comment']} | context: {notes}"[:900],
                })
        else:
            subsystem, conf = classify_subsystem(f"{row['comment']} {notes}")
            rows.append({
                "dispatcher_pc": row["pc"],
                "dispatcher_label": row["routine"],
                "index_source": index_source,
                "index_math": " ; ".join(index_math),
                "mask_shift_add_operations": " ; ".join(index_math),
                "table_address": table_addr,
                "entry_width": "unknown",
                "entry_count": "unknown",
                "entry_index": "",
                "entry_value": "",
                "resolved_target": row["operands"],
                "target_label": "",
                "target_write_targets": "",
                "candidate_subsystem": subsystem,
                "confidence": conf,
                "notes": f"unresolved indirect {row['op']} {row['operands']} | context: {notes}"[:900],
            })
    return rows


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["dispatcher_pc", "dispatcher_label", "index_source", "index_math", "mask_shift_add_operations", "table_address", "entry_width", "entry_count", "entry_index", "entry_value", "resolved_target", "target_label", "target_write_targets", "candidate_subsystem", "confidence", "notes"]
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_md(path: Path, rows: list[dict[str, str]], source: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    dispatchers = sorted(set(r["dispatcher_pc"] for r in rows))
    lines = [
        "# DISPATCHER_REVERSE_MAP",
        "",
        "## Purpose",
        "",
        "Reverse-map indirect dispatch and table-driven control flow so subsystem ownership can be inferred from both selector variables and landing routines.",
        "",
        "This is a static analysis artifact only. It does not implement runtime ASM, relax hardware gates, or prove hardware behavior.",
        "",
        "## Source",
        "",
        f"- source file: `{source}`",
        f"- dispatcher rows emitted: `{len(rows)}`",
        f"- dispatcher PCs observed: `{', '.join(dispatchers)}`",
        "",
        "## Key dispatcher classes",
        "",
        "- Major-loop dispatcher: `L0002 & 0x0F -> table -> JSR 0,X`.",
        "- Output-control/ALDL dispatcher: `L038E -> JSR 0,X`; this is an indirect control block and must not be confused with production subsystem scheduling.",
        "- Other indexed `JMP/JSR` rows are retained as unresolved/mixed until selector and table semantics are proven.",
        "",
        "## Required reverse-map fields",
        "",
        "`dispatcher_pc`, `index_source`, `index_math`, `table_address`, `entry_value`, `resolved_target`, `target_write_targets`, `candidate_subsystem`, `confidence`, and `notes`.",
        "",
        "## Isolation rule",
        "",
        "A routine reached only through a dispatcher must be kept reachable if it owns hardware, safety, scheduler, rolling-state, or preserved-driver side effects. Do not delete by linear call-tree assumptions alone.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_test(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = """# DISPATCHER_REVERSE_MAP_TEST

## Scope

Static test definition for dispatcher and indirect-control-flow mapping.

The artifact must:

- identify indirect `JMP/JSR` dispatch sites
- record selector/index source when statically visible
- record mask/shift/add/index math when statically visible
- resolve table entries where table rows are statically present
- reverse-map entries to landing labels
- summarize landing routine write targets when possible
- classify subsystem role conservatively
- retain unresolved dispatchers for review

## Required output files

```text
maps/contracts/dispatcher_reverse_map.csv
docs/contracts/DISPATCHER_REVERSE_MAP.md
```

## Non-relaxation clause

This artifact must not permit removing dispatch entries, changing scheduler paths, creating runtime ASM, or relaxing any hardware-output gate.
"""
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build dispatcher reverse map")
    parser.add_argument("--source", default=None)
    args = parser.parse_args()
    source = choose_source(args.source)
    raw_lines, parsed = parse_lines(source)
    rows = build_dispatchers(raw_lines, parsed)
    write_csv(OUT_CSV, rows)
    write_md(OUT_MD, rows, source)
    write_test(OUT_TEST)
    print(f"wrote {len(rows)} dispatcher rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
