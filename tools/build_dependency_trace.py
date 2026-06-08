#!/usr/bin/env python3
"""Build a focused dependency trace from source/listing text.

This is intentionally conservative. It does not claim perfect data-flow. It gathers
watched symbol/address touches, classifies likely dependency roles/domains, and
emits a contract-oriented CSV/Markdown skeleton around a sink PC/register.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)?\s*(.*?)\s*(?:;\s*(.*))?$")
WRITE_OPS = {"STAA", "STAB", "STD", "STX", "STY", "CLR", "INC", "DEC", "BSET", "BCLR"}
READ_OPS = {"LDAA", "LDAB", "LDD", "LDX", "LDY", "CMPA", "CMPB", "CPD", "CPX", "CPY", "ADDA", "ADDB", "ADDD", "SUBA", "SUBB", "SUBD", "BITA", "BITB", "BRSET", "BRCLR"}
WIDTH16 = {"LDD", "STD", "LDX", "LDY", "STX", "STY", "CPD", "CPX", "CPY", "ADDD", "SUBD"}

ROLE_HINTS = {
    "L01FD": ("final_spark", "degree_domain", "ram"),
    "L01FC": ("base_or_table_spark_adder", "degree_domain", "ram"),
    "L01EE": ("la906_entry_retard_offset", "degree_domain_until_converted", "ram"),
    "L01EC": ("timing_correction_or_latency_state", "time_tick_domain", "ram"),
    "L01EB": ("spark_delay_tick_bridge_candidate", "unknown", "ram"),
    "L0201": ("latency_correction", "time_tick_domain_or_small_count", "ram"),
    "L020B": ("low_octane_spark_retard", "degree_domain", "ram"),
    "L020C": ("knock_retard", "degree_domain", "ram"),
    "L3FC0": ("ref_period", "time_tick_domain", "asic_status"),
    "L3FF6": ("timing_domain_rolling_anchor", "time_tick_domain", "asic_register"),
    "L3FDC": ("timing_domain_rolling_state", "time_tick_domain", "asic_register"),
    "L3FE8": ("spark_timing_command_candidate", "time_tick_domain", "asic_register"),
    "L3FE6": ("spark_timing_command_candidate", "time_tick_domain", "asic_register"),
    "L3FEC": ("asic_status_source", "status_mode_domain", "asic_register"),
    "L3FE4": ("asic_mirror_ack_target", "status_mode_domain", "asic_register"),
    "L005F": ("last_drp_period_work", "time_tick_domain", "ram"),
    "L01F2": ("startup_spark", "degree_domain", "ram"),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(value: str | Path) -> Path:
    p = Path(value)
    return p if p.is_absolute() else repo_root() / p


def parse_watch(raw: str) -> str:
    raw = raw.strip().upper()
    if raw.startswith("0X"):
        return "L" + raw[2:].zfill(4)
    if raw.startswith("$"):
        return "L" + raw[1:].zfill(4)
    if re.fullmatch(r"[0-9A-F]{1,4}", raw):
        return "L" + raw.zfill(4)
    return raw


def parse_source(path: Path) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    routine = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        pc, label, mnemonic, operands, comment = m.groups()
        if label:
            routine = label.upper()
        out.append({
            "pc": "0x" + pc.upper(),
            "pc_int": str(int(pc, 16)),
            "label": (label or "").upper(),
            "routine_label": routine,
            "mnemonic": (mnemonic or "").upper(),
            "operands": (operands or "").strip(),
            "comment": (comment or "").strip(),
            "raw": line.rstrip(),
        })
    return out


def classify_access(mnemonic: str) -> str:
    if mnemonic in WRITE_OPS:
        return "W" if mnemonic not in {"BSET", "BCLR", "CLR", "INC", "DEC"} else "RMW"
    if mnemonic in READ_OPS:
        return "R"
    return ""


def symbol_in_row(row: dict[str, str], watch: set[str]) -> str:
    hay = (row["operands"] + " " + row["comment"] + " " + row["raw"]).upper()
    for sym in sorted(watch):
        if sym in hay:
            return sym
    return ""


def role_for(symbol: str, row: dict[str, str]) -> tuple[str, str, str, str]:
    base_role, domain, source_type = ROLE_HINTS.get(symbol, ("unknown_spark_dependency", "unknown", "unknown"))
    mn = row["mnemonic"]
    comment = row.get("comment", "").lower()
    role = base_role
    if symbol == "L01EE" and row["pc"] == "0xAB1A":
        role = "la906_entry_value"
    elif symbol == "L3FC0":
        role = "ref_or_drp_period_basis"
    elif symbol == "L0201":
        role = "latency_correction"
    elif "knock" in comment:
        role = "knock_retard" if "retard" in comment else "knock_status"
    elif "startup" in comment or "start up" in comment:
        role = "startup_spark_override"
    return role, domain, source_type, "variable" if mn not in {"LDAA", "LDAB", "LDD"} else "variable"


def effective_address(symbol: str) -> str:
    if symbol.startswith("L") and len(symbol) == 5:
        return "0x" + symbol[1:]
    return ""


def emit_csv(rows: list[dict[str, str]], out: Path, name: str, sink_pc: str, sink_register: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["contract_name", "sink_pc", "sink_register", "pc", "mnemonic", "operands", "access_type", "effective_address", "symbol", "width", "value_direction", "routine_label", "dependency_role_candidate", "degree_domain_or_tick_domain", "source_type", "table_or_ram", "constant_or_variable", "confidence", "notes"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def emit_md(rows: list[dict[str, str]], out: Path, name: str, sink_pc: str, sink_register: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    by_symbol: dict[str, list[dict[str, str]]] = {}
    for r in rows:
        by_symbol.setdefault(r["symbol"], []).append(r)
    md = [
        "# Spark Degree-to-Tick Dependency",
        "",
        "## Purpose",
        "",
        "Trace the upstream dependency chain that converts commanded spark/retard state into the timing-domain value consumed by `LA906`.",
        "",
        "## Sink",
        "",
        f"`LA906` timing bridge, first critical arithmetic: `{sink_pc} ADDD L3FF6` with sink register `{sink_register}`.",
        "",
        "The value in `D` at this point is the LA906 entry timing-domain input to explain.",
        "",
        "## Working Hypothesis",
        "",
        "Software spark is calculated in degree-domain RAM variables, then corrected by startup/knock/latency logic and converted to timing-domain units using REF/DRP period before `LA906` writes ASIC timing registers.",
        "",
        "## Watched Variables",
        "",
        "| Variable | Candidate role | Domain | Access rows | Confidence |",
        "|---|---|---|---:|---|",
    ]
    for sym, items in sorted(by_symbol.items()):
        role, domain, _source, _cv = role_for(sym, {"pc": "", "mnemonic": "", "comment": ""})
        md.append(f"| `{sym}` | {role} | {domain} | {len(items)} | pending/static |")
    md += [
        "",
        "## Dependency Chain — Current Static Read",
        "",
        "```text",
        "base spark / table adders / idle corrections",
        "→ L01FD final spark advance",
        "→ L01EE current retard / signed offset state",
        "→ knock and burst/low-octane/startup corrections",
        "→ absolute magnitude and sign flag L004F bit0",
        "→ latency lookup L0201 from RPM table $454A",
        "→ LF550 multiply against last DRP period basis at L005F",
        "→ subtract latency and REF/DRP period term L3FC0",
        "→ LA906 entry D at 0xAB97",
        "→ L3FE8/L3FE6/L3FF6/L3FDC/L3FEC/L3FE4 ASIC timing bridge",
        "```",
        "",
        "## Key Static Findings",
        "",
        "1. `L01FD` is labeled final spark advance and is repeatedly updated before `LA906`.",
        "2. `L01EE` is labeled current retard and becomes the direct LA906-side value at `0xAB1A LDD L01EE`.",
        "3. `L020C` is knock retard in degree domain; it is folded into `L01EE` before the timing conversion.",
        "4. `L0201` is written from the spark latency lookup and is subtracted after the DRP-period multiply.",
        "5. `L3FC0` is subtracted and shifted into the timebase expression before `ADDD L3FF6`.",
        "6. The value entering `0xAB97` is already timing-domain, not raw spark degrees.",
        "",
        "## Trace Rows",
        "",
        "| PC | Instruction | Symbol | Access | Candidate role | Domain | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        inst = (r["mnemonic"] + " " + r["operands"]).strip()
        note = r["notes"].replace("|", "/")[:100]
        md.append(f"| `{r['pc']}` | `{inst}` | `{r['symbol']}` | {r['access_type']} | {r['dependency_role_candidate']} | {r['degree_domain_or_tick_domain']} | {note} |")
    md += [
        "",
        "## Required New-OS Boundary",
        "",
        "Current static evidence favors this boundary:",
        "",
        "```text",
        "minimal OS spark math produces final spark/retard in degree-domain",
        "conversion layer converts degree-domain result using DRP/REF period and latency correction",
        "LA906-compatible bridge consumes a timing-domain value and rolling ASIC state",
        "```",
        "",
        "Do not write a spark output routine until bench testing proves the physical units and which rolling state must be maintained.",
        "",
        "## Open Questions",
        "",
        "- What is the exact physical unit of `L01EE` before multiply/latency conversion?",
        "- Is `L01FD` scaled as 256/90 degrees through the entire path?",
        "- Is knock retard always applied before conversion, or can later paths bypass it?",
        "- Is `L0201` pure latency in timer ticks or a table-scaled correction term?",
        "- Does `L3FC0` represent last REF period, DRP period, or ASIC-captured timing base in this context?",
        "- What is the exact physical unit of D at `0xAB97`?",
    ]
    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="source/31/BMHM_HAC_ORG_7100_to_end.asm")
    ap.add_argument("--map", default="maps/full/hardware_access_map_v0.3.csv", help="accepted for CLI compatibility; not required by first-pass parser")
    ap.add_argument("--name", default="SPARK_DEGREE_TO_TICK")
    ap.add_argument("--sink-pc", required=True)
    ap.add_argument("--sink-register", required=True)
    ap.add_argument("--watch", action="append", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    args = ap.parse_args()

    watch = {parse_watch(w) for w in args.watch}
    source_rows = parse_source(resolve_path(args.source))
    trace_rows: list[dict[str, str]] = []
    for row in source_rows:
        sym = symbol_in_row(row, watch)
        if not sym:
            continue
        role, domain, source_type, const_var = role_for(sym, row)
        access = classify_access(row["mnemonic"])
        if not access:
            access = "EXEC_OR_CONTEXT"
        trace_rows.append({
            "contract_name": args.name,
            "sink_pc": args.sink_pc,
            "sink_register": args.sink_register,
            "pc": row["pc"],
            "mnemonic": row["mnemonic"],
            "operands": row["operands"],
            "access_type": access,
            "effective_address": effective_address(sym),
            "symbol": sym,
            "width": "16" if row["mnemonic"] in WIDTH16 or sym in {"L01FD", "L01EE", "L01EC", "L3FC0", "L3FF6", "L3FDC"} else "8",
            "value_direction": "feeds_sink" if int(row["pc_int"]) <= int(args.sink_pc, 16) else "downstream_or_feedback",
            "routine_label": row["routine_label"],
            "dependency_role_candidate": role,
            "degree_domain_or_tick_domain": domain,
            "source_type": source_type,
            "table_or_ram": source_type,
            "constant_or_variable": const_var,
            "confidence": "medium_static" if sym in ROLE_HINTS else "low_static",
            "notes": row["comment"] or row["raw"],
        })
    emit_csv(trace_rows, resolve_path(args.out_csv), args.name, args.sink_pc, args.sink_register)
    emit_md(trace_rows, resolve_path(args.out_md), args.name, args.sink_pc, args.sink_register)
    print(f"wrote {len(trace_rows)} dependency rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
