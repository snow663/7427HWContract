#!/usr/bin/env python3
"""Build a contract slice for an HC11 math helper.

First target: LF550, the 8x16 fixed-point multiply helper used by the spark
unit-conversion path. The tool is intentionally simple: it extracts helper body,
callers, nearby caller context, and emits contract-oriented CSV/Markdown files.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)?\s*(.*?)\s*(?:;\s*(.*))?$")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
    return p if p.is_absolute() else repo_root() / p


def parse_pc(value: str) -> int:
    value = value.strip().lower()
    if value.startswith("0x"):
        return int(value, 16)
    if value.startswith("$"):
        return int(value[1:], 16)
    return int(value, 16)


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


def operation_class(row: dict[str, str]) -> str:
    mn = row["mnemonic"]
    ops = row["operands"].upper()
    comment = row["comment"].lower()
    if row["pc"] == "0xF550": return "load_input"
    if mn in {"LDAB", "LDAA"} and ",X" in ops: return "read_pointed_operand"
    if mn == "MUL": return "multiply_step"
    if mn == "ADCA" and "#$00" in ops or mn == "ADCA" and "#0" in ops: return "rounding_or_carry_propagation"
    if mn in {"PSHA", "PULB", "PSHX", "PULX", "INS", "TSX"}: return "stack_scratch"
    if mn == "ADDB": return "add_accumulate"
    if mn == "RTS": return "return_value"
    if "overflow" in comment or mn in {"BEQ", "BNE", "BCS", "BCC"}: return "branch_or_saturation_check"
    return "unknown"


def access_type(row: dict[str, str]) -> str:
    mn = row["mnemonic"]
    ops = row["operands"].upper()
    if mn in {"LDAA", "LDAB", "LDD", "LDX", "LDY"} and ",X" in ops:
        return "R"
    if mn in {"STAA", "STAB", "STD", "STX", "STY", "CLR"} and ",X" in ops:
        return "W"
    return "REG_STACK"


def effective_address(row: dict[str, str]) -> str:
    ops = row["operands"].upper().replace(" ", "")
    if ops in {"0,X", "$00,X"}: return "X+0"
    if ops in {"1,X", "$01,X"}: return "X+1"
    if ops in {"2,X", "$02,X"}: return "X+2"
    if ops in {"4,X", "$04,X"}: return "X+4"
    if ops in {"6,X", "$06,X"}: return "X+6"
    return ""


def register_reads(row: dict[str, str]) -> str:
    mn = row["mnemonic"]
    if mn == "MUL": return "A,B"
    if mn in {"ADCA", "ADDB"}: return "A/B,CCR"
    if mn == "PSHA": return "A"
    if mn == "PULB": return "stack"
    if mn == "LDAB" and ",X" in row["operands"].upper(): return "X,memory"
    if mn == "LDAA" and ",X" in row["operands"].upper(): return "X,memory"
    return ""


def register_writes(row: dict[str, str]) -> str:
    mn = row["mnemonic"]
    if mn == "MUL": return "D,CCR"
    if mn == "ADCA": return "A,CCR"
    if mn == "ADDB": return "B,CCR"
    if mn == "LDAB": return "B"
    if mn == "LDAA": return "A"
    if mn == "PULB": return "B,SP"
    if mn == "PSHA": return "SP/memory"
    if mn == "PSHX": return "SP/memory"
    if mn == "PULX": return "X,SP"
    if mn == "TSX": return "X"
    if mn == "INS": return "SP"
    return ""


def helper_rows(source_rows: list[dict[str, str]], start: int, end: int | None) -> list[dict[str, str]]:
    out = []
    for row in source_rows:
        pc = row["pc_int"]
        if pc >= start and (end is None or pc <= end):
            out.append(row)
            if end is None and pc > start and row["mnemonic"] == "RTS":
                break
    return out


def caller_rows(source_rows: list[dict[str, str]], helper: str, context: int = 4) -> list[dict[str, str]]:
    out = []
    helper = helper.upper()
    for i, row in enumerate(source_rows):
        if row["mnemonic"] == "JSR" and helper in row["operands"].upper():
            lo = max(0, i - context)
            hi = min(len(source_rows), i + context + 1)
            for ctx in source_rows[lo:hi]:
                copy = dict(ctx)
                copy["caller_pc"] = row["pc"]
                copy["caller_context"] = row["routine_label"]
                out.append(copy)
    return out


def write_csv(helper_body: list[dict[str, str]], callers: list[dict[str, str]], out: Path, helper: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["helper","pc","mnemonic","operands","access_type","effective_address","address_class","register_read","register_write","memory_read","memory_write","operation_class","input_candidate","output_candidate","scale_candidate","caller_pc","caller_context","notes","confidence"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for row in helper_body:
            ea = effective_address(row)
            opcls = operation_class(row)
            w.writerow({
                "helper": helper,
                "pc": row["pc"],
                "mnemonic": row["mnemonic"],
                "operands": row["operands"],
                "access_type": access_type(row),
                "effective_address": ea,
                "address_class": "pointed_operand" if ea.startswith("X+") else "register_or_stack",
                "register_read": register_reads(row),
                "register_write": register_writes(row),
                "memory_read": ea if row["mnemonic"] in {"LDAA", "LDAB"} and ea else "",
                "memory_write": ea if row["mnemonic"].startswith("ST") and ea else "",
                "operation_class": opcls,
                "input_candidate": "A=8-bit multiplier; X=&16-bit multiplicand" if row["pc"] == "0xF550" else "",
                "output_candidate": "D=rounded upper 16 bits of A*[X:X+1]" if row["mnemonic"] == "RTS" else "",
                "scale_candidate": "out=(A*M+0x80)>>8" if row["mnemonic"] in {"MUL", "ADCA", "ADDB", "RTS"} else "",
                "caller_pc": "",
                "caller_context": "",
                "notes": row["comment"] or row["raw"],
                "confidence": "high_static_source_comment",
            })
        for row in callers:
            w.writerow({
                "helper": helper,
                "pc": row["pc"],
                "mnemonic": row["mnemonic"],
                "operands": row["operands"],
                "access_type": "CALL_CONTEXT" if row["mnemonic"] != "JSR" else "CALL",
                "effective_address": "",
                "address_class": "caller_context",
                "register_read": "",
                "register_write": "",
                "memory_read": "",
                "memory_write": "",
                "operation_class": "caller_setup_or_use" if row["mnemonic"] != "JSR" else "helper_call",
                "input_candidate": "caller sets A and X before call" if row["mnemonic"] == "JSR" else "",
                "output_candidate": "caller uses D/A/B after call" if row["mnemonic"] != "JSR" else "",
                "scale_candidate": "out=(A*M+0x80)>>8",
                "caller_pc": row.get("caller_pc", ""),
                "caller_context": row.get("caller_context", ""),
                "notes": row["comment"] or row["raw"],
                "confidence": "medium_context",
            })


def write_md(helper_body: list[dict[str, str]], callers: list[dict[str, str]], out: Path, helper: str) -> None:
    caller_pcs = []
    for row in callers:
        if row["mnemonic"] == "JSR" and row["pc"] not in caller_pcs:
            caller_pcs.append(row["pc"])
    md = [
        "# Math Helper LF550",
        "",
        "## Purpose",
        "",
        "Classify `LF550`, the math helper used in the spark degree-to-tick conversion path.",
        "",
        "## Static Classification",
        "",
        "`LF550` is an unsigned 8×16 fixed-point multiply helper. It multiplies an 8-bit scalar in `A` by a 16-bit operand pointed to by `X`, rounds from the discarded low byte, and returns the upper 16-bit result in `D`.",
        "",
        "```text",
        "input:",
        "  A = 8-bit multiplier/scalar",
        "  X = address of 16-bit multiplicand, MSB at 0,X and LSB at 1,X",
        "",
        "output:",
        "  D = rounded upper 16 bits of the 24-bit product",
        "",
        "equation:",
        "  D = round((A * M16) / 256)",
        "  D ≈ (A * M16 + 0x80) >> 8",
        "```",
        "",
        "The source comments explicitly identify this as `8 x 16 Multiply with 16 bit result rounded to the upper 16 bits` and document the call/return register contract.",
        "",
        "## Known Spark Caller",
        "",
        "```text",
        "0xAB76  LDX #$005F",
        "0xAB79  JSR LF550",
        "```",
        "",
        "This call occurs after spark magnitude/sign handling and before latency/period-anchor subtraction. `L005F` is currently classified as the DRP/ref period basis candidate.",
        "",
        "## Questions Resolved",
        "",
        "| Question | Static answer | Confidence |",
        "|---|---|---|",
        "| What register carries the spark magnitude? | `A` at helper entry | high |",
        "| Does `X` point to a 16-bit operand? | yes, MSB at `0,X`, LSB at `1,X` | high |",
        "| Is pointed operand read as 8-bit or 16-bit? | two 8-bit reads forming a 16-bit operand | high |",
        "| Return register? | `D` / `A:B` | high |",
        "| Operation? | unsigned 8×16 fixed-point multiply | high |",
        "| Scale? | rounded upper 16 bits, equivalent to divide by 256 | high |",
        "| Sign handling? | none inside helper; caller handles sign/magnitude | high |",
        "| Saturation? | none in `LF550`; saturation belongs to different 16×16 helper at `F564` | high |",
        "| Rounding? | yes, carry from low partial product is propagated with `ADCA #$00` | high |",
        "",
        "## Helper Body",
        "",
        "| PC | Instruction | Operation class | Effect | Notes |",
        "|---|---|---|---|---|",
    ]
    for row in helper_body:
        inst = (row["mnemonic"] + " " + row["operands"]).strip()
        note = (row["comment"] or row["raw"]).replace("|", "/")
        effect = {
            "0xF550": "save multiplier A",
            "0xF551": "load multiplicand LSB into B",
            "0xF553": "A * low_byte → D",
            "0xF554": "round low partial product",
            "0xF556": "restore multiplier to B",
            "0xF557": "save rounded low-byte partial",
            "0xF558": "load multiplicand MSB into A",
            "0xF55A": "MSB * multiplier → D",
            "0xF55D": "add saved partial into low byte of high product",
            "0xF55F": "carry propagate / rounding",
            "0xF563": "return with D=result",
        }.get(row["pc"], "stack/register housekeeping")
        md.append(f"| `{row['pc']}` | `{inst}` | {operation_class(row)} | {effect} | {note} |")
    md += [
        "",
        "## Caller Inventory",
        "",
        f"Static caller count found: `{len(caller_pcs)}`.",
        "",
        "| Caller PC | Caller routine | Local context note |",
        "|---|---|---|",
    ]
    for pc in caller_pcs:
        jsr = next(r for r in callers if r["pc"] == pc and r["mnemonic"] == "JSR")
        md.append(f"| `{pc}` | `{jsr.get('caller_context') or jsr.get('routine_label')}` | {jsr.get('comment') or 'MUL 8X16 helper call'} |")
    md += [
        "",
        "## Spark-Path Interpretation",
        "",
        "For the spark conversion caller:",
        "",
        "```text",
        "A = spark magnitude / scalar after sign handling",
        "X = #$005F",
        "M16 = [L005F:L0060] = last DRP/ref period basis candidate",
        "LF550_output = round((A * M16) / 256)",
        "```",
        "",
        "This confirms that the degree-to-time bridge is a fixed-point scale of spark magnitude by period basis. The exact physical meaning still depends on the unit of the caller's `A` magnitude and the timebase represented by `L005F`.",
        "",
        "## Candidate Equation Locked By Helper",
        "",
        "```text",
        "mult = LF550(spark_mag, period_basis)",
        "mult = round((spark_mag_u8 * period_basis_u16) / 256)",
        "```",
        "",
        "This should replace the unresolved `LF550(...)` placeholder in `SPARK_TIMING_UNIT_CONVERSION.md`.",
        "",
        "## Required New-OS Impact",
        "",
        "If the bench tests confirm the upstream units, the minimal spark conversion layer can reimplement `LF550` directly as:",
        "",
        "```c",
        "uint16_t lf550(uint8_t mag, uint16_t period_basis) {",
        "    return (uint16_t)(((uint32_t)mag * (uint32_t)period_basis + 0x80u) >> 8);",
        "}",
        "```",
        "",
        "No spark writer should be created yet. `L005F`, `L3FC0`, `L0201`, and LA906 rolling-state behavior still require unit/bench classification.",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="source/31/BMHM_HAC_ORG_7100_to_end.asm")
    ap.add_argument("--map", default="maps/full/hardware_access_map_v0.3.csv", help="accepted for CLI compatibility")
    ap.add_argument("--helper", default="LF550")
    ap.add_argument("--start-pc", required=True)
    ap.add_argument("--end-pc")
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    args = ap.parse_args()

    rows = parse_source(resolve_path(args.source))
    start = parse_pc(args.start_pc)
    end = parse_pc(args.end_pc) if args.end_pc else None
    body = helper_rows(rows, start, end)
    callers = caller_rows(rows, args.helper)
    write_csv(body, callers, resolve_path(args.out_csv), args.helper)
    write_md(body, callers, resolve_path(args.out_md), args.helper)
    print(f"helper rows: {len(body)}")
    print(f"caller context rows: {len(callers)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
