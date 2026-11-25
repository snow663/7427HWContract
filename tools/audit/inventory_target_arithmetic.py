#!/usr/bin/env python3
"""Inventory production C arithmetic syntax; this is NOT a semantic verifier.

Lists every C/header file and multiplication, division, modulo, and shift
expression in src, calibration, platform, and include. Marks review leads,
not proven defects. Macros are recorded separately and not expanded.
"""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re

from c_integer_model import c_ast, nodes, parse_source, spelling


def inventory(repo):
    paths = sorted(p for directory in ("src", "calibration", "platform", "include")
                   for p in (repo / "pseudo-source" / directory).rglob("*") if p.suffix in (".c", ".h"))
    files, expressions, failures = [], [], []
    for path in paths:
        relative = path.relative_to(repo).as_posix()
        source = path.read_text()
        record = {"path": relative, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                  "assessment": "syntax survey only; no whole-function verification implied",
                  "macro_definitions": [i for i, line in enumerate(source.splitlines(), 1) if re.match(r"\s*#\s*define\b", line)],
                  "signed_narrowing_lines": [i for i, line in enumerate(source.splitlines(), 1) if re.search(r"\(\s*int(?:8|16)_t\s*\)", line)],
                  "layout_or_pointer_lines": [i for i, line in enumerate(source.splitlines(), 1) if re.search(r"\b(?:sizeof|offsetof|uintptr_t|memcpy|memset)\b", line)]}
        try:
            tree = parse_source(path)
            row_expr = []
            for node in nodes(tree, c_ast.BinaryOp):
                if node.op not in ("*", "/", "%", "<<", ">>"):
                    continue
                row = {"path": relative, "line": node.coord.line - 1, "operator": node.op,
                       "expression": spelling(node), "status": "surveyed expression; see report for reviewed classes"}
                row_expr.append(row)
            expressions.extend(row_expr)
            record["operator_counts"] = dict(Counter(r["operator"] for r in row_expr))
            record["parsed"] = True
        except Exception as exc:
            record["parsed"] = False
            failures.append({"path": relative, "error": str(exc)})
        files.append(record)
    return {"schema": 1, "scope": "production C syntax survey, not native compilation or complete range analysis",
            "source_file_count": len(files), "expression_count": len(expressions), "parse_failures": failures,
            "files": files, "expressions": expressions}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(os.environ.get("AUDIT_REPO", Path(__file__).resolve().parents[2])))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.repo.resolve())
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")
    print(f"{result['source_file_count']} files; {result['expression_count']} expressions; {len(result['parse_failures'])} parse failures")
    if result["parse_failures"]:
        raise SystemExit(1)
