#!/usr/bin/env python3
"""Build DISPATCHER_REVERSE_MAP for 7427/$31.

Static-only artifact. Identifies indirect JMP/JSR dispatch sites and table-driven
control flow. It does not create runtime ASM or relax hardware-output gates.
"""
from __future__ import annotations

import argparse, csv, re
from pathlib import Path

SOURCE = Path("source/31/BMHM_HAC_ORG_7100_to_end.asm")
OUT_CSV = Path("maps/contracts/dispatcher_reverse_map.csv")
OUT_MD = Path("docs/contracts/DISPATCHER_REVERSE_MAP.md")
OUT_TEST = Path("docs/tests/DISPATCHER_REVERSE_MAP_TEST.md")
LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)\s*(.*?)\s*(?:;\s*(.*))?$")
TABLE_RE = re.compile(r"^\s*(L[0-9A-Fa-f]{4})\s+FCB\s+\$?([0-9A-Fa-f]{4})\s*(?:;\s*(.*))?$")


def parse(source: Path):
    raw_lines = source.read_text(encoding="utf-8", errors="ignore").splitlines()
    rows = []
    cur = ""
    for i, raw in enumerate(raw_lines):
        m = LINE_RE.match(raw)
        if not m:
            continue
        pc, label, op, operands, comment = m.groups()
        if label:
            cur = label.upper()
        rows.append({"lineno": i+1, "pc": pc.upper(), "label": (label or "").upper(), "routine": cur, "op": op.upper(), "operands": (operands or "").split(';',1)[0].strip(), "comment": comment or "", "raw": raw.rstrip()})
    return raw_lines, rows


def major_loop_entries(raw_lines: list[str]) -> list[dict[str,str]]:
    out = []
    capture = False
    for raw in raw_lines:
        if "ORG  $7A85" in raw or "ORG     $7A85" in raw:
            capture = True
            continue
        if capture:
            m = TABLE_RE.match(raw)
            if m:
                label, target, comment = m.groups()
                out.append({"entry_label": label.upper(), "entry_value": f"${int(target,16):04X}", "resolved_target": f"L{int(target,16):04X}", "entry_comment": comment or ""})
            elif out and raw.strip() and raw.lstrip().startswith("7AA5:"):
                break
    return out


def build(raw_lines, parsed):
    out = []
    for i, row in enumerate(parsed):
        if row["op"] in {"JMP", "JSR"} and ",X" in row["operands"].upper():
            context = " | ".join(r["raw"].strip() for r in parsed[max(0, i-8):i])
            if row["pc"] == "7A4F":
                entries = major_loop_entries(raw_lines)
                for n, e in enumerate(entries):
                    out.append({
                        "dispatcher_pc": row["pc"],
                        "dispatcher_label": "major_loop_dispatcher",
                        "index_source": "LDAB L0002",
                        "index_math": "ANDB #$0F; ASLB; ABX; LDX 0,X; JSR 0,X",
                        "mask_shift_add_operations": "mask 0x0F; multiply entry index by 2; add to $7A85",
                        "table_address": "$7A85",
                        "entry_width": "16-bit target address",
                        "entry_count": str(len(entries)),
                        "entry_index": str(n),
                        "entry_value": e["entry_value"],
                        "resolved_target": e["resolved_target"],
                        "target_label": e["resolved_target"],
                        "target_write_targets": "pending landing-routine write-network join",
                        "candidate_subsystem": "major-loop scheduler",
                        "confidence": "high",
                        "notes": e["entry_comment"] or "major-loop table entry",
                    })
            else:
                out.append({
                    "dispatcher_pc": row["pc"],
                    "dispatcher_label": row["routine"],
                    "index_source": "static context required",
                    "index_math": "unresolved indexed dispatch",
                    "mask_shift_add_operations": "unresolved",
                    "table_address": "",
                    "entry_width": "unknown",
                    "entry_count": "unknown",
                    "entry_index": "",
                    "entry_value": "",
                    "resolved_target": row["operands"],
                    "target_label": "",
                    "target_write_targets": "pending",
                    "candidate_subsystem": "ALDL/output-control or mixed indirect dispatcher" if row["pc"] == "FAA5" else "unknown/mixed",
                    "confidence": "medium" if row["pc"] == "FAA5" else "low",
                    "notes": context,
                })
    return out


def write_csv(path: Path, rows: list[dict[str,str]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader(); w.writerows(rows)


def write_md(path: Path, rows: list[dict[str,str]], source: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    pcs = ', '.join(sorted(set(r['dispatcher_pc'] for r in rows)))
    path.write_text(f"""# DISPATCHER_REVERSE_MAP

## Purpose

Reverse-map indirect dispatch and table-driven control flow so subsystem ownership can be inferred from selector variables and landing routines.

This is a static analysis artifact only. It does not implement runtime ASM, change scheduling, or relax hardware-output gates.

## Source

- source file: `{source}`
- dispatcher rows emitted: `{len(rows)}`
- dispatcher PCs observed: `{pcs}`

## Required model

Forward direction:

```text
state bits / math result / mode byte -> index -> table -> computed jump/call
```

Reverse direction:

```text
dispatch entry -> landing routine -> write targets -> candidate subsystem
```

## Known dispatcher seeds

- `7A4F`: major-loop dispatcher using `L0002 & 0x0F` and table `$7A85`.
- `FAA5`: output-control block dispatcher through `L038E`; likely ALDL/output-control and not production subsystem scheduling.

## Isolation rule

Do not trust a linear call tree where computed dispatch exists. Keep dispatcher-selected routines reachable until the selector, table, landing routine, and write-target network prove they are removable.
""", encoding='utf-8')


def write_test(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("# DISPATCHER_REVERSE_MAP_TEST\n\nStatic test definition. The builder must identify indirect `JMP/JSR` sites, table/index math where visible, landing targets where resolvable, and must not change scheduler paths, create ASM, or relax hardware gates.\n", encoding='utf-8')


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument('--source')
    args = ap.parse_args(); source = Path(args.source) if args.source else SOURCE
    raw, parsed = parse(source)
    rows = build(raw, parsed)
    write_csv(OUT_CSV, rows); write_md(OUT_MD, rows, source); write_test(OUT_TEST)
    print(f"wrote {len(rows)} dispatcher rows")
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
