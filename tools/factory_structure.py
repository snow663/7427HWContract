"""Source-backed structure helpers; no inferred instruction bytes or reachability.

Reviewed data ranges apply only to the listing hash in their evidence rows
(line endings normalized so Windows checkouts preserve the same evidence).
An unreviewed HAC instruction remains a candidate, never confirmed executable code.
"""
from __future__ import annotations

import csv
import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "source/31/BMHM_HAC_ORG_7100_to_end.asm"
REGIONS = ROOT / "maps/structure/reviewed_source_regions.csv"
ADDRESS_ROW = re.compile(
    r"^\s*(?:([0-9A-Fa-f]{4}):\s*(?:(L[0-9A-Fa-f]{4})\s+)?"
    r"|(L[0-9A-Fa-f]{4})\s+)(\S+)\s*(.*?)\s*$"
)
DECLARATIONS = {"FCB", "FDB", "FCC", "RMB"}
BRANCHES = set("BRA BRN BHI BLS BCC BCS BNE BEQ BVC BVS BPL BMI BGE BLT BGT BLE BHS BLO".split())
CALLS = {"JSR", "BSR"}
CONTROL = BRANCHES | CALLS | {"JMP", "BRSET", "BRCLR"}
STORES = set("STAA STAB STD STX STY STS CLR".split())
MUTATIONS = set("BSET BCLR INC DEC COM NEG ASL LSL LSR ASR ROL ROR".split())
READS = set((
    "LDAA LDAB LDD LDX LDY LDS CMPA CMPB CPD CPX CPY BITA BITB TST "
    "ADDA ADDB ADDD ADCA ADCB SUBA SUBB SUBD SBCA SBCB ANDA ANDB "
    "ORAA ORAB EORA EORB BRSET BRCLR"
).split())
WORD_OPS = set("LDD LDX LDY LDS STD STX STY STS CPD CPX CPY ADDD SUBD".split())


@dataclass(frozen=True)
class Region:
    region_id: str
    start: int
    end: int
    evidence_pcs: str
    reason: str


@dataclass(frozen=True)
class Statement:
    line: int
    pc: int
    label: str
    op: str
    operand: str
    comment: str


def parse_listing(source: Path) -> list[Statement]:
    rows = []
    for line_no, raw in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
        code, _, comment = raw.partition(";")
        # Two inherited branch comments use a spaced colon, not a semicolon.
        # The address colon has no preceding whitespace and is unaffected.
        colon_comment = re.split(r"\s+:\s+", code, maxsplit=1)
        if len(colon_comment) == 2:
            code = colon_comment[0]
            comment = colon_comment[1] + ("; " + comment if comment else "")
        match = ADDRESS_ROW.match(code)
        if match:
            pc, label, declaration_label, op, operand = match.groups()
            rows.append(Statement(
                line_no, int(pc or declaration_label[1:], 16),
                (label or declaration_label or "").upper(), op.upper(),
                operand.strip(), comment.strip(),
            ))
    return rows


def load_regions(source: Path = SOURCE, path: Path = REGIONS) -> list[Region]:
    digest = text_sha256(source)
    pcs = {row.pc for row in parse_listing(source)}
    regions = []
    with path.open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["source_sha256"] != digest:
                raise ValueError("Reviewed regions do not match source SHA-256; review them before reuse")
            start, end = int(row["start"], 16), int(row["end"], 16)
            if not 0 <= start <= end <= 0xFFFF:
                raise ValueError(f"Invalid reviewed region: {row['region_id']}")
            if row["classification"] != "data":
                raise ValueError("This first-pass overlay accepts reviewed data regions only")
            for anchor in row["evidence_pcs"].split(";"):
                if int(anchor, 16) not in pcs:
                    raise ValueError(f"Missing evidence PC {anchor}")
            regions.append(Region(row["region_id"], start, end, row["evidence_pcs"], row["reason"]))
    regions.sort(key=lambda region: region.start)
    for left, right in zip(regions, regions[1:]):
        if left.end >= right.start:
            raise ValueError("Overlapping reviewed regions require explicit conflict resolution")
    return regions


def text_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_text(encoding="utf-8").encode("utf-8")).hexdigest()


def data_region(pc: int, regions: list[Region]) -> Region | None:
    return next((region for region in regions if region.start <= pc <= region.end), None)


def classification(row: Statement, regions: list[Region]) -> str:
    if data_region(row.pc, regions):
        return "reviewed_embedded_data"
    if row.op in DECLARATIONS:
        return "declared_data"
    if row.op.startswith("*"):
        return "undecoded_review"
    if row.op == "TEST":
        return "test_opcode_review"
    return "instruction_candidate"


def operands(text: str) -> list[str]:
    result: list[str] = []
    for token in text.upper().split(","):
        token = token.strip()
        if token in {"X", "Y"} and result:
            result[-1] += "," + token
        else:
            result.append(token)
    return [token for token in result if token]


def number(text: str) -> int | None:
    text = text.strip().upper()
    if re.fullmatch(r"(?:\$|L)[0-9A-F]{1,4}", text):
        return int(text[1:], 16)
    if re.fullmatch(r"[0-9]+", text):
        return int(text, 10)
    return None


def memory_access(row: Statement) -> dict | None:
    args = operands(row.operand)
    if not args or args[0].startswith("#"):
        return None
    if row.op in STORES:
        access = "W"
    elif row.op in MUTATIONS:
        access = "RW"
    elif row.op in READS:
        access = "R"
    else:
        return None
    raw = args[0]
    if raw in {"A", "B", "D", "X", "Y", "SP"}:
        return None
    # Never resolve an index from a stale immediate load in another basic block.
    indexed = "," in raw
    target = None if indexed else number(raw)
    return {
        "pc": f"{row.pc:04X}", "source_line": row.line,
        "mnemonic": row.op, "operand": row.operand, "access": access,
        "width_bits": 16 if row.op in WORD_OPS else 8,
        "target_address": f"{target:04X}" if target is not None else "",
        "resolution": "direct" if target is not None else "unresolved_indexed" if indexed else "unresolved_operand",
        "bitmask": args[1] if row.op in {"BSET", "BCLR", "BRSET", "BRCLR"} and len(args) > 1 else "",
    }


def control_edge(row: Statement) -> dict | None:
    if row.op not in CONTROL:
        return None
    args = operands(row.operand)
    raw = args[-1] if row.op in {"BRSET", "BRCLR"} else args[0] if args else ""
    target = number(raw)
    return {
        "pc": f"{row.pc:04X}", "source_line": row.line,
        "mnemonic": row.op, "target_operand": raw,
        "target_address": f"{target:04X}" if target is not None else "",
        "edge_kind": "call" if row.op in CALLS else "jump" if row.op == "JMP" else "branch",
        "resolution": "direct" if target is not None else "unresolved_indirect" if "," in raw else "unresolved_direct_operand",
    }
