#!/usr/bin/env python3
"""Build a focused spark timebase/period contract from source text.

This first-pass tool gathers readers/writers for watched symbols and classifies
candidate timebase roles. It is deliberately conservative: it does not emulate the
code or lock physical units without bench data.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)?\s*(.*?)\s*(?:;\s*(.*))?$")
READ_OPS = {"LDAA","LDAB","LDD","LDX","LDY","CMPA","CMPB","CPD","CPX","CPY","ADDA","ADDB","ADDD","SUBA","SUBB","SUBD","BITA","BITB","BRSET","BRCLR"}
WRITE_OPS = {"STAA","STAB","STD","STX","STY","CLR","INC","DEC","BSET","BCLR"}
WIDTH16 = {"LDD","STD","LDX","LDY","STX","STY","CPD","CPX","CPY","ADDD","SUBD"}

ROLE_HINTS = {
    "L005F": ("timer_ticks_or_scaled_period", "software period basis used by LF550"),
    "L0060": ("timer_ticks_or_scaled_period_low_byte", "low byte of L005F 16-bit basis"),
    "L3FC0": ("asic_period_or_event_anchor", "ASIC last DRP/ref period counter source"),
    "L0201": ("latency_ticks_or_scaled_latency", "RPM-indexed spark latency correction"),
    "L01EC": ("timing_correction_or_work_period", "timing correction/state term"),
    "L01EE": ("degree_domain_signed_retard_offset", "current retard / signed spark offset"),
    "L01F2": ("startup_spark_degree_domain", "startup spark magnitude/override"),
    "L004F": ("status_mode_domain", "bit0 sign flag for advance/retard magnitude path"),
    "L3FCA": ("hardware_event_counter", "ASIC RPM/event counter source"),
    "L3FDC": ("rolling_anchor_or_work_period", "LA906 rolling timing state"),
    "L3FF6": ("rolling_anchor", "EST fall counter / LA906 rolling anchor"),
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
    rows = []
    routine = ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = LINE_RE.match(line)
        if not m:
            continue
        pc, label, mnemonic, operands, comment = m.groups()
        if label:
            routine = label.upper()
        rows.append({
            "pc": "0x" + pc.upper(),
            "pc_int": int(pc, 16),
            "label": (label or "").upper(),
            "routine_label": routine,
            "mnemonic": (mnemonic or "").upper(),
            "operands": (operands or "").strip(),
            "comment": (comment or "").strip(),
            "raw": line.rstrip(),
        })
    return rows


def symbol_in_row(row: dict[str, str], watch: set[str]) -> str:
    hay = (row["operands"] + " " + row["comment"] + " " + row["raw"]).upper()
    for sym in sorted(watch):
        if sym in hay:
            return sym
    return ""


def access_type(mnemonic: str) -> str:
    if mnemonic in WRITE_OPS:
        return "W" if mnemonic not in {"CLR","INC","DEC","BSET","BCLR"} else "RMW"
    if mnemonic in READ_OPS:
        return "R"
    if mnemonic == "JSR":
        return "CALL"
    return "CONTEXT"


def reader_or_writer(access: str) -> str:
    if access == "W": return "writer"
    if access == "R": return "reader"
    if access == "RMW": return "read_modify_write"
    return "context"


def candidate_unit(symbol: str, row: dict[str, str]) -> str:
    if symbol in {"L005F", "L0060"}: return "timer_ticks_or_scaled_period"
    if symbol == "L3FC0": return "drp_ref_period_or_event_anchor"
    if symbol == "L0201": return "latency_ticks_or_scaled_latency"
    if symbol == "L01EC": return "timing_correction_or_rolling_period_term"
    if symbol == "L01EE": return "degree_domain_signed_offset_before_conversion"
    if symbol == "L004F": return "status_mode_domain"
    if symbol in {"L3FF6", "L3FDC"}: return "rolling_anchor"
    return "unknown"


def rpm_dependency(symbol: str, row: dict[str, str]) -> str:
    text = (row["comment"] + " " + row["raw"]).lower()
    if "rpm" in text or symbol in {"L005F", "L3FC0", "L0201"}:
        return "yes_candidate"
    return "unknown"


def spark_dependency(symbol: str, row: dict[str, str]) -> str:
    text = (row["comment"] + " " + row["raw"]).lower()
    if "spark" in text or "spk" in text or symbol in {"L01EE", "L0201", "L01EC"}:
        return "yes_candidate"
    return "unknown"


def hardware_dependency(symbol: str, row: dict[str, str]) -> str:
    if symbol.startswith("L3F"):
        return "yes_asic_window"
    return "software_ram_or_status"


def value_source(row: dict[str, str]) -> str:
    mn = row["mnemonic"]
    if mn in {"STD", "STX", "STY", "STAA", "STAB"}:
        return mn[2:] if mn != "STD" else "D"
    if mn in {"LDD", "LDX", "LDY", "LDAA", "LDAB"}:
        return "memory_to_register"
    if mn in {"ADDD", "SUBD", "ADDB", "SUBB"}:
        return mn
    return ""


def physical_meaning(symbol: str, row: dict[str, str]) -> str:
    if symbol == "L005F":
        return "software copy/work value for DRP/ref period basis used as LF550 multiplicand"
    if symbol == "L3FC0":
        return "ASIC timing/period source; comments call it last DRP/ref period counter"
    if symbol == "L0201":
        return "RPM-indexed latency correction subtracted before LA906 sink"
    if symbol == "L01EC":
        return "timing correction/work-period state used after LA906 command candidates"
    if symbol == "L01EE":
        return "degree-domain signed retard/spark offset before time conversion"
    return ROLE_HINTS.get(symbol, ("unknown", "unknown"))[1]


def collect(rows: list[dict[str, str]], watch: set[str], name: str) -> list[dict[str, str]]:
    out = []
    for row in rows:
        sym = symbol_in_row(row, watch)
        if not sym:
            continue
        acc = access_type(row["mnemonic"])
        out.append({
            "contract_name": name,
            "symbol": sym,
            "address": "0x" + sym[1:] if sym.startswith("L") and len(sym) == 5 else "",
            "pc": row["pc"],
            "mnemonic": row["mnemonic"],
            "operands": row["operands"],
            "access_type": acc,
            "width": "16" if row["mnemonic"] in WIDTH16 or sym in {"L005F","L3FC0","L01EC","L01EE","L3FF6","L3FDC"} else "8",
            "routine_label": row["routine_label"],
            "reader_or_writer": reader_or_writer(acc),
            "value_source": value_source(row),
            "used_by": "LF550 multiplicand" if sym == "L005F" and "#$005F" in row["operands"].upper() else ("LA906 conversion" if row["pc_int"] >= 0xAB1A and row["pc_int"] <= 0xABC8 else "period/spark support"),
            "candidate_unit": candidate_unit(sym, row),
            "candidate_physical_meaning": physical_meaning(sym, row),
            "rpm_dependency": rpm_dependency(sym, row),
            "spark_dependency": spark_dependency(sym, row),
            "hardware_dependency": hardware_dependency(sym, row),
            "confidence": "medium_static" if sym in ROLE_HINTS else "low_static",
            "notes": row["comment"] or row["raw"],
        })
    return out


def write_csv(rows: list[dict[str, str]], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["contract_name","symbol","address","pc","mnemonic","operands","access_type","width","routine_label","reader_or_writer","value_source","used_by","candidate_unit","candidate_physical_meaning","rpm_dependency","spark_dependency","hardware_dependency","confidence","notes"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader(); w.writerows(rows)


def write_md(rows: list[dict[str, str]], out: Path, name: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    counts = {}
    for r in rows:
        counts.setdefault(r["symbol"], {"R":0,"W":0,"RMW":0,"CONTEXT":0,"CALL":0})
        counts[r["symbol"]][r["access_type"]] = counts[r["symbol"]].get(r["access_type"], 0) + 1
    md = [
        "# Spark Timebase / Period Contract",
        "",
        "## Purpose",
        "",
        "Classify the timebase variables used between final spark degrees and the `LA906` timing bridge.",
        "",
        "## Known Math",
        "",
        "`LF550` is confirmed:",
        "",
        "```text",
        "LF550(A, M16) = round((A * M16) / 256)",
        "```",
        "",
        "Spark path:",
        "",
        "```text",
        "A = spark_mag_u8",
        "M16 = [L005F:L0060]",
        "mult = round((spark_mag_u8 * L005F) / 256)",
        "```",
        "",
        "## Variables",
        "",
        "| Symbol | Static role | Candidate unit | R | W | Confidence |",
        "|---|---|---|---:|---:|---|",
    ]
    for sym in sorted(counts):
        role = physical_meaning(sym, {"comment":"", "raw":"", "operands":"", "mnemonic":"", "pc_int":0})
        unit = candidate_unit(sym, {"comment":"", "raw":""})
        md.append(f"| `{sym}` | {role} | {unit} | {counts[sym].get('R',0)} | {counts[sym].get('W',0)} | medium/static |")
    md += [
        "",
        "## Required Equation",
        "",
        "Provisional:",
        "",
        "```text",
        "mult = round((spark_mag_u8 * period_basis) / 256)",
        "D_AB97 ≈ ((mult - latency - period_anchor) >> 4) with sign/high-nibble tagging",
        "```",
        "",
        "Expanded current candidate:",
        "",
        "```text",
        "period_basis = L005F/L0060",
        "latency = L0201",
        "period_anchor = L3FC0/L3FC1",
        "timing_work = L01EC",
        "spark_mag_u8 = magnitude/sign-transformed L01EE or startup L01F2 path",
        "```",
        "",
        "## Static Findings",
        "",
        "1. `L005F` is the direct `LF550` multiplicand in the spark path because `0xAB76 LDX #$005F` immediately precedes `0xAB79 JSR LF550`.",
        "2. `L005F` is written from period/RPM support code and comments identify it as `LAST DRP PERIOD` / `LAST DRP PERIOD VAL` in the `LA5E5` area.",
        "3. `L3FC0` is read in multiple RPM/period contexts and is explicitly used at `0xAB8E SUBD L3FC0` immediately before the LA906 sink.",
        "4. `L0201` is written by the RPM-indexed latency lookup and subtracted at `0xAB84 SUBB L0201` before the period-anchor subtraction.",
        "5. `L01EC` is a time-domain work/correction term used before and after LA906 command writes; it is not raw spark degrees.",
        "6. `L01EE` remains the signed degree-domain offset before sign/magnitude conversion and LF550 scaling.",
        "",
        "## Critical Rows",
        "",
        "| Symbol | PC | Instruction | Access | Candidate meaning | Notes |",
        "|---|---|---|---|---|---|",
    ]
    critical = {"L005F","L3FC0","L0201","L01EC","L01EE"}
    for r in rows:
        if r["symbol"] not in critical:
            continue
        if r["pc"] not in {"0xA5CF","0xA5E5","0xA5E8","0xA5FC","0xA5FE","0xA6EC","0xA6EF","0xA6F5","0xA6FA","0xA6FD","0xAB1A","0xAB72","0xAB76","0xAB84","0xAB8E","0xABB3","0xABB7"}:
            continue
        inst = (r["mnemonic"] + " " + r["operands"]).strip()
        note = r["notes"].replace("|", "/")
        md.append(f"| `{r['symbol']}` | `{r['pc']}` | `{inst}` | {r['access_type']} | {r['candidate_physical_meaning']} | {note} |")
    md += [
        "",
        "## Current Classification",
        "",
        "```text",
        "TB-A:",
        "  supported statically. L005F behaves like a raw or scaled REF/DRP period basis.",
        "",
        "TB-B:",
        "  possible. L005F also appears in RPM/work-value code, so it may be filtered or derived rather than a direct hardware copy.",
        "",
        "TB-C:",
        "  not currently supported; L005F clearly functions as the period multiplicand for LF550.",
        "",
        "LAT-A:",
        "  likely. L0201 is subtracted directly from the LF550 output path before LA906.",
        "",
        "LAT-B:",
        "  still possible because the later >>4/high-nibble packing step may mean L0201 is pre-shift or scaled.",
        "",
        "ANCHOR-A:",
        "  supported. L3FC0 is used as a hardware period/event anchor in the conversion path.",
        "```",
        "",
        "## Questions",
        "",
        "- Does `L005F` represent time for 90°, 180°, 360°, or 720°?",
        "- Is `L005F` a direct copy of `$3FC0`, a filtered copy, or a separately scaled period basis?",
        "- Does `L3FC0` represent current period, prior period, or hardware event anchor?",
        "- Is `L0201` in the same unit as `mult`, or does the later shift/packing alter interpretation?",
        "- Is the `>>4` a unit conversion, ASIC packing step, or fractional discard?",
        "",
        "## Stop Condition",
        "",
        "Do not write `SPARK_WRITE` until this contract can answer:",
        "",
        "```text",
        "For X degrees at Y RPM/ref period, what LA906 input value should be produced?",
        "```",
    ]
    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="source/31/BMHM_HAC_ORG_7100_to_end.asm")
    ap.add_argument("--map", default="maps/full/hardware_access_map_v0.3.csv", help="accepted for CLI compatibility")
    ap.add_argument("--name", default="SPARK_TIMEBASE_PERIOD")
    ap.add_argument("--watch", action="append", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    args = ap.parse_args()
    watch = {parse_watch(w) for w in args.watch}
    rows = collect(parse_source(resolve_path(args.source)), watch, args.name)
    write_csv(rows, resolve_path(args.out_csv))
    write_md(rows, resolve_path(args.out_md), args.name)
    print(f"wrote {len(rows)} timebase rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
