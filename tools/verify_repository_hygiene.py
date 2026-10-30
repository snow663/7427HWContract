#!/usr/bin/env python3
"""Check live navigation, retired paths, CSV schemas and untouched ROM evidence."""
from __future__ import annotations

import ast
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from build_factory_scheduler import recorded_rom
from verify_factory_ownership import EVIDENCE
from verify_factory_rom_structure import EXPECTED_SHA256


def verify(root: Path = ROOT) -> list[str]:
    errors = []
    retirement = root / "maps/maintenance/retired_artifacts.csv"
    with retirement.open(newline="", encoding="utf-8") as source:
        retired = list(csv.DictReader(source))
    paths = {row["path"] for row in retired}
    for row in retired:
        if (root / row["path"]).exists():
            errors.append("Retired artifact returned: " + row["path"])
        if not re.fullmatch("[0-9a-f]{40}", row["git_blob_sha"]):
            errors.append("Missing retirement identity: " + row["path"])
        for replacement in row["replacement"].split(";"):
            if not (root / replacement).is_file():
                errors.append("Missing replacement: " + replacement)
    if (root / "factory_c").exists():
        errors.append("Superseded unpublished factory_c draft is not part of the active tree")
    for path in (root / "maps/structure").glob(".factory_*.csv.*"):
        errors.append("Interrupted generated file: " + path.relative_to(root).as_posix())

    for path in (root / "tools").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_argument"
            ):
                continue
            for keyword in node.keywords:
                if (
                    keyword.arg == "default"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value in paths
                ):
                    errors.append("CLI default uses retired path: " + path.relative_to(root).as_posix())

    for name in ["README.md", "docs/WORKING_STATE.md", "docs/TRUCK_FIRST_RUNTIME_DECODING.md", "source/README.md"]:
        text = (root / name).read_text(encoding="utf-8")
        if "0.3.12" not in text:
            errors.append("Missing current tune scope: " + name)
        if re.search(r"current running BIN:\s*2\.bin", text, re.I):
            errors.append("Historical tune promoted to current: " + name)
        if "pseudo-source" not in text:
            errors.append("Missing active source navigation: " + name)

    for path in root.rglob("*.md"):
        if {".git", "build", "__pycache__"}.intersection(path.relative_to(root).parts):
            continue
        text = re.sub(r"^```.*?^```", "", path.read_text(encoding="utf-8"), flags=re.M | re.S)
        for target in re.findall(r"\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = unquote(target.split("#")[0].strip("<>"))
            if not (path.parent / target).exists():
                errors.append(f"Broken link: {path.relative_to(root)} -> {target}")

    for path in root.rglob("*.csv"):
        if {".git", "build", "__pycache__"}.intersection(path.relative_to(root).parts):
            continue
        with path.open(newline="", encoding="utf-8") as source:
            rows = csv.reader(source)
            header = next(rows, [])
            for number, row in enumerate(rows, 2):
                if len(row) != len(header):
                    errors.append(
                        f"CSV schema width: {path.relative_to(root)} row {number} "
                        f"has {len(row)} fields, expected {len(header)}"
                    )

    # Passive identity metadata is checked separately from modeled behavior.
    profile = json.loads((root / "hac31_romsim/romsim/profiles/gm_16197427_31.json").read_text())
    names = {register["address"]: register["name"] for register in profile["registers"]}
    if names.get("0x3002") != "PORTG" or not names.get("0x3008", "").startswith("PORTD"):
        errors.append("Simulator profile contains superseded CPU register names")
    if "current_2.bin" in profile["provenance"]["known_images"]:
        errors.append("Simulator profile promotes the historical tune to current")
    region = next(region for region in profile["regions"] if region["start"] == "0x3000")
    if region["end"] != "0x305F":
        errors.append("Simulator profile omits the F1 chip-select register offsets")
    rom = recorded_rom(json.loads(EVIDENCE.read_text()))
    if sha256(bytes([255]) * 0x4000 + rom.read(0x4000, 0xC000)).hexdigest() != EXPECTED_SHA256:
        errors.append("Stock ROM evidence identity changed")
    return errors


if __name__ == "__main__":
    failures = verify()
    if failures:
        print("\n".join(failures))
        raise SystemExit(1)
    print("Repository hygiene verified: current navigation, retired defaults, CSV schemas, links and stock evidence")
