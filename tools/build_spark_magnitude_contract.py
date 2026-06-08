#!/usr/bin/env python3
"""Build a focused spark magnitude / degree-scale contract.

This first-pass tool extracts watched spark-degree variables from the source
listing and classifies likely scale/sign roles for the magnitude entering LF550.
It is conservative; it preserves rows and hypotheses without claiming bench
proof.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

LINE_RE = re.compile(r"^\s*([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?([A-Z][A-Z0-9]*)?\s*(.*?)\s*(?:;\s*(.*))?$")
READ_OPS = {"LDAA","LDAB","LDD","LDX","LDY","ADDA","ADDB","ADDD","SUBA","SUBB","SUBD","CMPA","CMPB","CPD","CPX","CPY","BITA","BITB","BRSET","BRCLR"}
WRITE_OPS = {"STAA","STAB","STD","STX","STY","CLR","INC","DEC","BSET","BCLR"}
WIDTH16 = {"LDD","STD","LDX","STX","LDY","STY","CPD","CPX","CPY","ADDD","SUBD"}

SCALE_256_90 = "0.3515625 deg/count (90/256) candidate"
SCALE_256_45 = "0.17578125 deg/count before /2, then 0.3515625 after LSRA"

ROLE_HINTS = {
    "L01FD": ("final_spark_advance", "degree_domain", SCALE_256_90),
    "L01FC": ("working_spark_predecessor_or_table_adder", "degree_domain", SCALE_256_90),
    "L01EE": ("signed_offset_into_conversion", "signed_offset_domain", SCALE_256_90),
    "L01F2": ("startup_spark_override", "startup_override_domain", SCALE_256_90),
    "L004F": ("status_flags_bit0_sign", "status_flag_domain", "bit0: 1=retard, 0=advance"),
    "L020B": ("low_octane_spark_retard", "retard_domain", SCALE_256_90),
    "L020C": ("knock_retard", "retard_domain", SCALE_256_45),
}


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    p = Path(path)
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
    rows: list[dict[str, str]] = []
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
            "label": (label or "").upper(),
            "routine_label": routine,
            "mnemonic": (mnemonic or "").upper(),
            "operands": (operands or "").strip(),
            "comment": (comment or "").strip(),
            "raw": line.rstrip(),
        })
    return rows


def row_symbol(row: dict[str, str], watch: set[str]) -> str:
    hay = (row["operands"] + " " + row["comment"] + " " + row["raw"]).upper()
    for sym in sorted(watch):
        if sym in hay:
            return sym
    return ""


def access_type(mnemonic: str) -> str:
    if mnemonic in WRITE_OPS:
        return "RMW" if mnemonic in {"BSET","BCLR","CLR","INC","DEC"} else "W"
    if mnemonic in READ_OPS:
        return "R"
    return "CTX"


def operation(row: dict[str, str]) -> str:
    mn = row["mnemonic"]
    ops = row["operands"].upper()
    c = row["comment"].lower()
    if mn in {"STD","STAA","STAB","STX"}: return "write_variable"
    if mn in {"LDD","LDAA","LDAB","LDX"}: return "read_variable"
    if mn in {"ADDD","ADDB","ADDA"}: return "add_modifier"
    if mn in {"SUBD","SUBB","SUBA"}: return "subtract_modifier_or_bias"
    if mn in {"BSET","BCLR","BRSET","BRCLR"}: return "flag_sign_or_state"
    if mn in {"NEGB","NEGA"}: return "sign_magnitude_transform"
    if mn in {"LSRA","LSRB","LSRD"}: return "scale_shift"
    if mn == "MUL": return "multiply_or_startup_scale"
    if "tbl" in c or "table" in c: return "table_scale_context"
    return "context"


def sign_role(row: dict[str, str], symbol: str) -> str:
    text = (row["operands"] + " " + row["comment"]).upper()
    if symbol == "L004F" and "#$01" in text:
        return "bit0: 1=retard, 0=advance"
    if symbol == "L01EE":
        return "signed two's-complement offset; BPL positive path; negative sets L004F bit0 and NEGB creates magnitude"
    return ""


def value_source(row: dict[str, str]) -> str:
    mn = row["mnemonic"]
    ops = row["operands"]
    if mn.startswith("ST"):
        return {"STD":"D","STAA":"A","STAB":"B","STX":"X","STY":"Y"}.get(mn, "register")
    if mn in {"BSET","BCLR"}:
        return ops
    return ""


def effective_address(symbol: str) -> str:
    return "0x" + symbol[1:] if symbol.startswith("L") and len(symbol) == 5 else ""


def write_csv(rows: list[dict[str, str]], out: Path, name: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ["contract_name","symbol","address","pc","mnemonic","operands","access_type","width","routine_label","reader_or_writer","value_source","operation","domain","candidate_unit","candidate_scale","sign_role","used_by","confidence","notes"]
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_md(rows: list[dict[str, str]], out: Path, name: str) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    md = [
        "# Spark Magnitude / Degree Scale Contract",
        "",
        "## Purpose",
        "",
        "Classify the degree-domain spark variables that become the unsigned magnitude input `A` to `LF550`.",
        "",
        "## Known Downstream Math",
        "",
        "```text",
        "LF550(A, L005F) = round((A * L005F) / 256)",
        "```",
        "",
        "Therefore `A` is the spark angle/magnitude scalar used for degree-to-time conversion.",
        "",
        "## Known Sink",
        "",
        "```text",
        "0xAB76  LDX #$005F",
        "0xAB79  JSR LF550",
        "```",
        "",
        "At this call:",
        "",
        "```text",
        "A = spark_mag_u8",
        "X = #L005F",
        "```",
        "",
        "## Strongest Static Scale Candidate",
        "",
        "The source contains repeated calibration comments that directly identify spark-table and bias units as `SPK ADV 256/90`.",
        "",
        "```text",
        "A8xx idle spark correction: TBL = SPK ADV 256/90",
        "CAxx WOT spark correction: TBL = (256/90) * SPK ADV DEG",
        "AA1D initial spark subtract: 3.8 Deg, INITIAL SPK (256/90)",
        "```",
        "",
        "Leading candidate:",
        "",
        "```text",
        "A_count = round(degrees * 256 / 90)",
        "degrees = A_count * 90 / 256",
        "degree_per_count = 0.3515625°",
        "```",
        "",
        "This matches the expected hardware-friendly interpretation where `A=256` would represent one 90° reference window. Bench proof is still required.",
        "",
        "## Variables",
        "",
        "| Symbol | Candidate role | Candidate unit | Confidence |",
        "|---|---|---|---|",
        "| `L01FD` | final spark advance accumulator | 256/90 degree scale | high static |",
        "| `L01FC` | working/table spark adder predecessor | 256/90 degree scale | medium-high static |",
        "| `L01EE` | signed spark offset into conversion | 256/90 degree scale, two's-complement signed | high static |",
        "| `L01F2` | startup spark override/filter value | 256/90 degree scale candidate | medium static |",
        "| `L004F bit0` | sign flag for conversion | 1=retard, 0=advance | high static |",
        "| `L020B` | low-octane spark retard | 256/90 degree scale candidate | medium-high static |",
        "| `L020C` | knock retard | likely 256/45 stored, halved before subtract into 256/90 path | medium static |",
        "",
        "## Required Chain",
        "",
        "```text",
        "base spark table / WOT spark table / idle correction tables",
        "→ spark modifiers and bias subtraction",
        "→ L01FD final spark advance",
        "→ subtract initial spark bias L4132 (256/90)",
        "→ L01EE signed offset / current retard",
        "→ burst knock / knock / torque management clamps",
        "→ serial override adjustment if active",
        "→ sign/magnitude handling using L004F bit0",
        "→ A before LF550",
        "→ LF550(A, L005F)",
        "```",
        "",
        "## Critical Static Evidence",
        "",
        "### Final spark scale and bias",
        "",
        "```text",
        "0xA7E7  LDAB L01FC        ; FROM TABLE L44BF",
        "0xA811  SUBB L020B        ; LOW OCTAINE SPK RETARD",
        "0xA81B  STD  L01FD        ; FINAL SPK ADV",
        "0xAA1A  LDD  L01FD        ; FINAL SPK ADV",
        "0xAA1D  SUBB L4132        ; 3.8 Deg, INITIAL SPK (256/90)",
        "0xAA22  STD  L01EE        ; CURRENT RETARD (2's CMP)",
        "```",
        "",
        "This says `L01FD` and `L01EE` are in the same degree-domain scale as the initial spark scalar, with `L01EE = L01FD - initial_spark_bias` before later retard/clamp logic.",
        "",
        "### Sign and magnitude handling",
        "",
        "```text",
        "0xAB44  BCLR L004F,#$01    ; clear sign, 1=retard, 0=advance",
        "0xAB47  LDD  L01EE",
        "0xAB4A  BPL  LAB50         ; positive path",
        "0xAB4C  BSET L004F,#$01    ; negative offset means retard",
        "0xAB4F  NEGB                ; magnitude from low byte",
        "0xAB50  TBA                 ; A = unsigned magnitude",
        "```",
        "",
        "So `LF550` receives an unsigned 8-bit magnitude in `A`. `L004F bit0` carries the sign convention into the later add/subtract path.",
        "",
        "### Startup override path",
        "",
        "```text",
        "0xAB55  LDAB L01F2         ; START UP SPARK",
        "0xAB60  MUL",
        "0xAB61  INCA",
        "```",
        "",
        "If the startup-path flag is active, startup spark modifies/replaces the normal magnitude before latency lookup and `LF550`.",
        "",
        "### Knock and low-octane retard",
        "",
        "```text",
        "0xA78F  STAA L020B         ; LOW OCTAINE SPK RETARD",
        "0xA811  SUBB L020B         ; LOW OCTAINE SPK RETARD",
        "0xAACB  STAA L020C         ; DEG, KNOCK RETARD",
        "0xAACE  LSRA               ; halve knock-retard value",
        "0xAAD1  LDD  L01EE",
        "0xAAD4  SUBB 0,X           ; subtract halved knock amount from L01EE",
        "0xAAD8  STD  L01EE",
        "```",
        "",
        "The WOT/knock table comments mention `SPK ADV * (256/45)`; the `LSRA` before subtracting from `L01EE` is consistent with converting a 256/45 stored value into the 256/90 path.",
        "",
        "## Trace Rows",
        "",
        "| PC | Instruction | Symbol | Operation | Domain | Scale | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        inst = (r["mnemonic"] + " " + r["operands"]).strip()
        note = r["notes"].replace("|", "/")[:100]
        md.append(f"| `{r['pc']}` | `{inst}` | `{r['symbol']}` | {r['operation']} | {r['domain']} | {r['candidate_scale']} | {note} |")
    md += [
        "",
        "## Current Candidate Scale",
        "",
        "```text",
        "MAG-A leading candidate:",
        "  A uses 90°/256 scale = 0.3515625°/count.",
        "",
        "candidate mapping:",
        "  5°  → A ≈ 14",
        "  10° → A ≈ 28",
        "  20° → A ≈ 57",
        "  30° → A ≈ 85",
        "  40° → A ≈ 114",
        "```",
        "",
        "## Current Sign Convention",
        "",
        "```text",
        "L004F bit0 = 0 → advance/non-retard sign path",
        "L004F bit0 = 1 → retard sign path",
        "A entering LF550 = unsigned magnitude of L01EE low byte after sign handling",
        "```",
        "",
        "## Open Questions",
        "",
        "- Is `L01FD` always 256/90 scale after every modifier, or do some paths add already-biased 16-bit values?",
        "- Does the `L01EE` negative path using `NEGB` rely on all practical values fitting in signed 8-bit low byte?",
        "- Does startup mode replace the normal magnitude or multiply/clamp it through `L01F2` only under a flag?",
        "- Are knock and low-octane retard always converted into the same 256/90 scale before reaching `L01EE`?",
        "- Does bench-measured A match `round(degrees * 256 / 90)` at 5°, 10°, 20°, and 30°?",
        "",
        "## Stop Condition",
        "",
        "Do not write spark output code until bench testing confirms the magnitude scale and sign convention. The next combined equation contract may use this candidate, but it must remain provisional until the A-before-LF550 values are measured.",
    ]
    out.write_text("\n".join(md), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default="source/31/BMHM_HAC_ORG_7100_to_end.asm")
    ap.add_argument("--map", default="maps/full/hardware_access_map_v0.3.csv", help="accepted for CLI compatibility")
    ap.add_argument("--name", default="SPARK_MAGNITUDE_SCALE")
    ap.add_argument("--watch", action="append", required=True)
    ap.add_argument("--out-md", required=True)
    ap.add_argument("--out-csv", required=True)
    args = ap.parse_args()

    watch = {parse_watch(w) for w in args.watch}
    source_rows = parse_source(resolve_path(args.source))
    rows: list[dict[str, str]] = []
    for row in source_rows:
        sym = row_symbol(row, watch)
        if not sym:
            continue
        role, domain, scale = ROLE_HINTS.get(sym, ("unknown", "unknown", "unknown"))
        rows.append({
            "contract_name": args.name,
            "symbol": sym,
            "address": effective_address(sym),
            "pc": row["pc"],
            "mnemonic": row["mnemonic"],
            "operands": row["operands"],
            "access_type": access_type(row["mnemonic"]),
            "width": "16" if row["mnemonic"] in WIDTH16 or sym in {"L01FD","L01EE","L01F2"} else "8/bit",
            "routine_label": row["routine_label"],
            "reader_or_writer": "writer" if access_type(row["mnemonic"]) in {"W","RMW"} else "reader_or_context",
            "value_source": value_source(row),
            "operation": operation(row),
            "domain": domain,
            "candidate_unit": "spark_angle_scaled_count" if "degree" in domain or "retard" in domain else "flag_or_unknown",
            "candidate_scale": scale,
            "sign_role": sign_role(row, sym),
            "used_by": "LF550 magnitude path" if sym in {"L01EE","L01F2","L004F"} else "spark magnitude build-up",
            "confidence": "high_static" if "256/90" in row["comment"] or sym in {"L004F","L01EE"} else "medium_static",
            "notes": row["comment"] or row["raw"],
        })
    write_csv(rows, resolve_path(args.out_csv), args.name)
    write_md(rows, resolve_path(args.out_md), args.name)
    print(f"wrote {len(rows)} spark magnitude rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
