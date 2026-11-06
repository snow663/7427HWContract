"""Apply authored functional context to every rooted operation in exact Rev B.

Reading groups describe surviving operation sequences, not guaranteed standalone
functions. Assembly bytes, branches, fixed-operand relationships and stock byte
comparisons are machine-derived; purpose text is reviewed reference context.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import html
import json
from pathlib import Path
import re

import explain_revb_bin as raw

ROOT = raw.ROOT
CONTEXT = ROOT / "maps/maintenance/revb_function_context.json"
OUTLINE = [
    ("Boot", "Reset validates/seeds retained engine state, initializes CPU/board controls and establishes the normal scheduling path.", "$7100, $71C3, $74D3, $5BD0"),
    ("Engine events", "Reference and timer-output interrupts consume prepared fuel/timing state and maintain event histories. They can run between foreground operations.", "$74EA, $751B, $7875, $78D9"),
    ("Periodic admission", "The timer IRQ admits a foreground pass or records the retained pending observation when that work is busy.", "$793D, $7989"),
    ("Foreground schedule", "The admitted pass advances phase, runs the retained fast engine work, selects one background slot and resolves catch-up.", "$798C, $79E7, $7A44, $7A55"),
    ("Fuel", "Inputs and AFR/trim state feed pulse construction; cut/enrichment and packet accounting precede final pulse shaping and publication.", "$7D4B, $7FD8, $83B1, $84BC"),
    ("Idle air", "The admitted controller prepares target/error, decides capture and learning permission, composes internal air and converts it to a position request. Step service moves toward that request separately.", "$93D0, $9537, $9951, $99FB, $983D, $91A3"),
    ("Spark", "Admission and period/RPM preparation feed the base/correction sum, active DFCO gate, knock and limits, then service edits and output conversion/publication.", "$A466, $A700, $9F40, $AA33, $AADC, $AB44"),
    ("Slow producers", "Background slots refresh battery, BARO, temperature, permissions, diagnostics and retained spark/fuel factors for later consumers.", "$7AA6..$7B6C, $C583, $C96A, $E477"),
    ("ALDL", "SCI events receive/store requests or advance replies; scheduled work maintains sessions and edge-qualified service/clear requests.", "$F5E8, $F715, $F781, $F7EA"),
]
GLOSSARY = {
    "Target": "The value a controller is trying to reach, such as requested idle RPM.",
    "Published state": "A saved value that another scheduled routine or interrupt can later read.",
    "Gate / admission": "A test deciding whether a later operation is allowed to run.",
    "Hysteresis": "Different entry and release limits that prevent rapid state switching at one boundary.",
    "P / proportional air": "A temporary correction based on current RPM error, outside the deadband.",
    "Integral / baseline air": "A retained runtime starting point that qualified error observations can adjust.",
    "Feed-forward air": "Air added for a known condition such as cold start or A/C, without waiting for an RPM error.",
    "Follower air": "TPS-related air that can rise immediately and decay as the throttle closes; separate from learned baseline.",
    "Deadband": "The error range in which the selected corrective action is suppressed.",
    "Anti-windup": "Preventing integral movement farther into a command limit that cannot provide more correction in that direction.",
    "Internal air / Q8.8": "A software air-command word with 8 whole and 8 fractional bits; not measured airflow or motor steps.",
    "DFCO": "Deceleration fuel-cut state. Fuel cut and the DFCO spark subtraction have separate gates and owners.",
    "BLM": "Learned multiplicative pulse correction, neutral at 128.",
    "INT/P": "O2 integrator/proportional state converted to a signed additive pulse correction; not another BLM multiplier.",
    "Tail / continuation": "Code reached by a jump or fall-through; it can be shared by several paths rather than be a separate function.",
    "NOP / empty entry": "Deliberately retained padding or a return that preserves layout/call structure after old work was removed.",
}


def read_context():
    data = json.loads(CONTEXT.read_text())
    if data["image_sha256"] != raw.SHA:
        raise ValueError("Context identity does not match the reader image")
    for mapping in (data["by_source"], data["by_address"]):
        for key, value in mapping.items():
            if not value.get("title", "").strip() or not value.get("purpose", "").strip():
                raise ValueError("Empty functional context: " + key)
    return data


def context_entries(image, decoded, contexts):
    entries, stock = raw.source_entries(image, decoded)
    # Include a modified entry only with authored image-specific context. A
    # matching first opcode is not promoted into proof of a whole stock body.
    candidates = defaultdict(list)
    for path in sorted((ROOT / "pseudo-source/src").rglob("*.c")):
        match = re.search(r"/\*(.*?)\*/", path.read_text(), re.S)
        if match is None:
            continue
        for lo, hi in re.findall(r"\b([0-9A-Fa-f]{4})\s*\.\.\s*([0-9A-Fa-f]{4})\b", match[1]):
            lo, hi = int(lo, 16), int(hi, 16)
            if lo in decoded and hi > lo:
                candidates[lo].append((hi - lo, path))
    for pc, choices in candidates.items():
        path = min(choices, key=lambda v: (v[0], str(v[1])))[1]
        if pc not in entries:
            entries[pc] = (path.stem, "", path.relative_to(ROOT).as_posix())
    for address, context in contexts["by_address"].items():
        pc = int(address, 16)
        if pc not in decoded:
            raise ValueError("Functional boundary is not a decoded instruction: " + address)
        entries.setdefault(pc, (context["title"], "", "authored Rev B context"))
    resolved = {}
    for pc, (_, _, source) in entries.items():
        address = f"{pc:04X}"
        context = contexts["by_address"].get(address)
        if context is None:
            context = contexts["by_source"].get(Path(source).stem)
        if context is None:
            raise ValueError(f"No authored functional explanation for {address}: {source}")
        resolved[pc] = dict(context, source=source)
    return resolved, stock


def spans(instructions):
    result = []
    for instruction in instructions:
        if result and result[-1][1] == instruction.pc:
            result[-1][1] = instruction.next_pc
        else:
            result.append([instruction.pc, instruction.next_pc])
    return result


def partition(decoded, entries):
    """Assign every instruction once; do not turn intervening data into code."""
    groups = []
    for number, title, lo, hi, purpose in raw.CHAPTERS:
        current = None
        for pc, instruction in sorted(decoded.items()):
            if not lo <= pc < hi:
                continue
            if pc in entries or current is None:
                if pc not in entries:
                    raise ValueError(f"Chapter begins without functional context at {pc:04X}")
                current = dict(address=f"{pc:04X}", chapter=number,
                               chapter_title=title, chapter_purpose=purpose,
                               **entries[pc], instructions=[])
                groups.append(current)
            current["instructions"].append(instruction)
    pcs = [i.pc for g in groups for i in g["instructions"]]
    if len(pcs) != len(set(pcs)) or set(pcs) != set(decoded):
        raise AssertionError("Functional groups must cover the decoded image exactly once")
    return groups


def fixed_references(instructions):
    """Explicit fixed operands only, including their byte widths; not def-use."""
    reads, writes, indexed = set(), set(), []
    for instruction in instructions:
        access = instruction.access()
        if access is None:
            continue
        if access["address"] is None:
            indexed.append(f"{instruction.pc:04X}")
        else:
            item = (access["address"], access["width_bits"])
            if "R" in access["access"]:
                reads.add(item)
            if "W" in access["access"]:
                writes.add(item)
    return sorted(reads), sorted(writes), indexed


def make_groups(image):
    if len(image) != 65536 or hashlib.sha256(image).hexdigest() != raw.SHA:
        raise ValueError("Requires the exact released 64 KiB Rev B image")
    decoded, frontiers, roots = raw.sweep(image)
    contexts = read_context()
    entries, stock = context_entries(image, decoded, contexts)
    groups = partition(decoded, entries)
    names, _, _ = raw.role_maps()
    catalog, _ = raw.data_catalog(image, names)
    owner = {i.pc: g["address"] for g in groups for i in g["instructions"]}
    callers = defaultdict(list)
    writers = defaultdict(set)
    readers = defaultdict(set)
    for group in groups:
        instructions = group["instructions"]
        fixed_reads, fixed_writes, indexed = fixed_references(instructions)
        group["fixed_reads"] = [dict(address=f"{a:04X}", width_bits=w, role=names.get(a, "role unresolved")) for a, w in fixed_reads]
        group["fixed_writes"] = [dict(address=f"{a:04X}", width_bits=w, role=names.get(a, "role unresolved")) for a, w in fixed_writes]
        for a, width in fixed_reads:
            for byte in range(a, a + width // 8):
                readers[byte].add(group["address"])
        for a, width in fixed_writes:
            for byte in range(a, a + width // 8):
                writers[byte].add(group["address"])
        group["indexed_operations"] = indexed
        group["instruction_count"] = len(instructions)
        group["byte_count"] = sum(len(i.data) for i in instructions)
        group["instruction_spans"] = [dict(start=f"{a:04X}", end_exclusive=f"{z:05X}") for a, z in spans(instructions)]
        group["unchanged_stock_instruction_count"] = sum(image[i.pc:i.next_pc] == stock[i.pc:i.next_pc] for i in instructions)
        group["changed_from_stock"] = [f"{i.pc:04X}" for i in instructions if image[i.pc:i.next_pc] != stock[i.pc:i.next_pc]]
        group["calls"] = []
        group["cross_group_transfers"] = []
        for instruction in instructions:
            target = instruction.target
            if target is not None:
                edge = dict(site=f"{instruction.pc:04X}", target=f"{target:04X}", operation=instruction.op, group=owner.get(target))
                if instruction.op in ("JSR", "BSR"):
                    group["calls"].append(edge)
                    if target in owner:
                        callers[owner[target]].append(dict(edge, caller_group=group["address"]))
                elif target in owner and owner[target] != group["address"]:
                    group["cross_group_transfers"].append(edge)
            next_pc = instruction.next_pc
            if next_pc in owner and owner[next_pc] != group["address"] and instruction.op not in ("RTS", "RTI", "JMP", "BRA", "SWI", "WAI", "STOP"):
                label = "if call returns" if instruction.op in ("JSR", "BSR") else "fall-through"
                group["cross_group_transfers"].append(dict(site=f"{instruction.pc:04X}", target=f"{next_pc:04X}", operation=label, group=owner[next_pc]))
        # Table bases can be passed to callees in X/Y. List references without
        # claiming a whole-table footprint or assigning runtime pointer values.
        rom_refs = set(a for a, _ in fixed_reads if 0x4000 <= a < 0xFFC0)
        rom_refs.update(i.value for i in instructions if i.op in ("LDX", "LDY") and i.mode == "immediate" and 0x4000 <= i.value < 0xFFC0 and i.value not in decoded)
        group["rom_references"] = [dict(address=f"{a:04X}", role=names.get(a, "ROM data/table role unresolved")) for a in sorted(rom_refs)]
        group["calibration_views"] = [dict(address=c["address"], title=c["title"], status=c["status"], raw=c["raw"], units=c["units"], reviewed_values=c["verified_display_values"]) for c in catalog if any(int(c["address"], 16) <= a < int(c["address"], 16) + c["length"] for a in rom_refs)]
        group["root_entries"] = [f"{i.pc:04X}" for i in instructions if i.pc in roots]
    for group in groups:
        group["callers"] = callers[group["address"]]
        upstream, downstream = set(), set()
        for r in group["fixed_reads"]:
            for a in range(int(r["address"], 16), int(r["address"], 16) + r["width_bits"] // 8):
                upstream.update(writers[a])
        for r in group["fixed_writes"]:
            for a in range(int(r["address"], 16), int(r["address"], 16) + r["width_bits"] // 8):
                downstream.update(readers[a])
        group["other_fixed_writers"] = sorted(upstream - {group["address"]})
        group["other_fixed_readers"] = sorted(downstream - {group["address"]})
    coverage = dict(image_sha256=raw.SHA, instructions=len(decoded),
                    executable_bytes=sum(len(i.data) for i in decoded.values()),
                    functional_groups=len(groups), chapters=len(raw.CHAPTERS),
                    indexed_data_operations=sum(len(g["indexed_operations"]) for g in groups),
                    control_frontiers=frontiers, all_operations_assigned_once=True,
                    context_sha256=hashlib.sha256(CONTEXT.read_bytes()).hexdigest(),
                    relationship_scope="Static direct calls/transfers and explicit fixed memory operands, width-aware. Indexed/stack/callee/hardware effects are not a complete producer-consumer proof.",
                    interpretation_scope="Authored functional context applied to exact surviving instruction groups. Inherited roles and physical meanings retain their limits; not full state/history or truck validation.")
    return groups, coverage


def human_refs(rows):
    return "; ".join(f"${r['address']} ({r['width_bits']}-bit): {r['role']}" for r in rows) or "None identified from explicit fixed memory operands."


def intro(coverage):
    return f"""# Rev B — what the operation groups do

Exact BIN: `0.3.12_engine_only_manual_idle_revB.bin`  
SHA-256: `{raw.SHA}`

This is the functional layer above the instruction-by-instruction guide:
**{coverage['instructions']:,} instructions in {coverage['functional_groups']} explained groups**, across 13 chapters.
Read each group's **Function** paragraph first. Its inputs, saved results, calls,
continuations and expandable assembly keep the explanation tied to actual code.

The groups are reading units: some are complete routines, some are a stage or a
shared tail, and some deliberately return without doing former work. A group
with multiple branch paths does not execute every listed operation in order.
Address order is not execution order. Gaps between listed instruction spans are
not silently included as executable code.

Purpose paragraphs use maintained contracts and reviewed current-image context.
Exact instruction membership, bytes and destinations are mechanically checked.
This is not independent proof of every inherited name, all possible histories,
interrupt timing or physical hardware action. Uncertain physical identities stay
qualified. A stock-byte comparison supplies evidence, not automatic approval of
every factory description after a caller or input has changed.

The fixed-read/write lists describe explicit operands **inside the group**.
They omit implicit register/stack inputs, arbitrary indexed addresses and callees'
effects. Related-reader/writer links show shared fixed addresses, not a complete
last-writer, dependency, runtime-order or causality proof.

No firmware, calibration or XDF is changed. TS00 testing/fine-tuning of Rev B
remains the first active work item.

## How the parts fit together

| Part | Function in the overall program | Address anchors |
|---|---|---|
""" + "\n".join(f"| {a} | {b} | {c} |" for a, b, c in OUTLINE) + "\n\n## Plain-English terms\n\n" + "\n".join(f"- **{key}:** {value}" for key, value in GLOSSARY.items())


def write_outputs(out, image, groups, coverage):
    out.mkdir(parents=True, exist_ok=True)
    (out / "context_chapters").mkdir(exist_ok=True)
    by_address = {g["address"]: g for g in groups}
    chapters = []
    for number, title, _, _, purpose in raw.CHAPTERS:
        cards = []
        for g in (g for g in groups if g["chapter"] == number):
            count, total = g["unchanged_stock_instruction_count"], g["instruction_count"]
            lines = [f"\n<a id=\"g{g['address']}\"></a>\n\n## ${g['address']} — {g['title']}\n",
                     "**Function:** " + g["purpose"] + "\n",
                     f"**Code represented:** {total} instructions, {g['byte_count']} bytes. Listed spans (end exclusive): " + "; ".join(f"${r['start']}..${r['end_exclusive']}" for r in g["instruction_spans"]) + ".\n",
                     "**Reads here:** " + human_refs(g["fixed_reads"]) + "\n",
                     "**Saves/changes here:** " + human_refs(g["fixed_writes"]) + "\n"]
            if g.get("tuning"):
                lines.insert(2, "**Tuning connection / exact boundary:** " + g["tuning"] + "\n")
            if g["indexed_operations"]:
                lines.append(f"**Indexed memory:** {len(g['indexed_operations'])} operations require the caller/local pointer context; these are not guessed fixed variables.\n")
            if g["calls"]:
                lines.append("**Calls:** " + "; ".join(f"${e['site']} calls [${e['target']} — {by_address[e['group']]['title']}](#g{e['group']})" if e["group"] else f"${e['site']} calls ${e['target']} (external/unresolved body)" for e in g["calls"]) + ".\n")
            if g["cross_group_transfers"]:
                lines.append("**Continuations to other groups:** " + "; ".join(f"${e['site']} {e['operation']} → [${e['target']}](#g{e['group']})" for e in g["cross_group_transfers"]) + ".\n")
            if g["rom_references"]:
                lines.append("**ROM data/table references:** " + "; ".join(f"${r['address']}: {r['role']}" for r in g["rom_references"]) + ". These are referenced starts/operands, not a complete callee lookup footprint or certification of inherited units.\n")
            if g["callers"]:
                lines.append("**Called from:** " + "; ".join(f"[${e['site']}](#g{e['caller_group']})" for e in g["callers"]) + ". Tail jumps, fall-through and interrupts may also enter.\n")
            lines.append(f"**Evidence:** exact current-image instructions; {count}/{total} instruction starts byte-identical to the stock comparison. Context reference: `{g['source']}`. Changed starts are recorded in FUNCTIONAL_GROUPS.json; changed neighbors and callers can affect retained algorithms.\n")
            lines.append("<details><summary>Exact operations in this group</summary>\n\n```text\n" + "\n".join(f"{i.pc:04X}  {i.data.hex(' '):<14} {(i.op+' '+i.operand).strip()}" for i in g["instructions"]) + "\n```\n\n</details>\n")
            cards.append("\n".join(lines))
        text = f'<a id="context-chapter-{number}"></a>\n\n# {number} — {title}\n\n{purpose}\n' + "\n".join(cards)
        (out / "context_chapters" / f"{number}.md").write_text(text.replace("](#g", "](../FUNCTIONAL_GUIDE.md#g"))
        chapters.append(text)
    preface = intro(coverage)
    preface += "\n\n## Chapters\n\n" + "\n".join(f"- [{n} — {t}](#context-chapter-{n})" for n, t, *_ in raw.CHAPTERS)
    (out / "FUNCTIONAL_GUIDE.md").write_text(preface + "\n\n" + "\n\n".join(chapters) + "\n")
    serializable = []
    for g in groups:
        row = {k: v for k, v in g.items() if k != "instructions"}
        row["operations"] = [dict(address=f"{i.pc:04X}", bytes=i.data.hex(" "), operation=(i.op + " " + i.operand).strip()) for i in g["instructions"]]
        serializable.append(row)
    (out / "FUNCTIONAL_GROUPS.json").write_text(json.dumps(serializable, indent=2) + "\n")
    (out / "FUNCTIONAL_COVERAGE.json").write_text(json.dumps(coverage, indent=2) + "\n")
    raw.csvfile(out / "FUNCTIONAL_INDEX.csv", [dict(address=g["address"], chapter=g["chapter"], title=g["title"], function=g["purpose"], instructions=g["instruction_count"], bytes=g["byte_count"], source=g["source"]) for g in groups])
    write_html(out, groups, coverage)
    (out / "README.txt").write_text("""REV B FUNCTIONAL AND OPERATION GUIDES

Extract this ZIP, then open FUNCTIONAL_GUIDE.html in a browser.
This is the new context layer: groups of operations, their function, inputs,
saved state, related calls and exact assembly. Search an address or topic,
select a chapter, and expand details as needed. It works offline.

FUNCTIONAL_GUIDE.md contains the complete context text.
context_chapters/ contains 13 smaller context chapters.
FUNCTIONAL_GROUPS.json records every group, operation and static relationship.
FUNCTIONAL_INDEX.csv is the function/purpose index.
FUNCTIONAL_COVERAGE.json records image identity and group coverage.

FULL_GUIDE.html and FULL_GUIDE.md retain the earlier per-instruction explanations.
chapters/ splits that detailed instruction guide into 13 smaller files.
CALIBRATION_CATALOG.md and CALIBRATIONS.json record supplied XDF views/bytes.
OPERATIONS.csv has one row per instruction, with flags and direct references.
BYTE_LEDGER.csv accounts for every BIN byte, including unclassified regions.
FULL_HEX.txt reconstructs the exact image as text; it is not a flashable BIN.
VECTORS_AND_SLOTS.json records the vector/background-dispatcher words.
COVERAGE.json records the original instruction-reader coverage.
SHA256SUMS.txt records the files' hashes.

Groups can contain alternative branches and shared tails, not just independent
functions. Fixed operand relationships are not a complete runtime dependency
proof. Physical identities and inherited meanings retain stated limits.
No BIN, XDF or calibration changes. Rev B testing and fine-tuning stay first.
""")


def write_html(out, groups, coverage):
    esc = html.escape
    index = {g["address"]: g for g in groups}
    ids = {i.pc: g["address"] for g in groups for i in g["instructions"]}
    def link(address, label=None):
        pc = int(address, 16)
        owner = ids.get(pc, address if address in index else None)
        label = esc(label or "$" + address)
        return f'<a href="#g{owner}" data-address="{address}">{label}</a>' if owner else label
    def ref_table(g):
        rows = []
        for direction, key in (("Read", "fixed_reads"), ("Write/change", "fixed_writes")):
            rows.extend(f'<tr><td>{direction}</td><td>${r["address"]}</td><td>{r["width_bits"]}</td><td>{esc(r["role"])}</td></tr>' for r in g[key])
        return '<table><thead><tr><th>Access</th><th>Address</th><th>Bits</th><th>Maintained role</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table>' if rows else '<p>No explicit fixed memory operands here; registers/stack or callees can still carry state.</p>'
    sections = []
    for n, title, _, _, purpose in raw.CHAPTERS:
        cards = []
        for g in (g for g in groups if g["chapter"] == n):
            calls = '<p><b>Calls:</b> ' + '; '.join(link(e['target'], f"${e['site']} → ${e['target']} " + index[e['group']]['title']) if e['group'] else esc(f"${e['site']} → ${e['target']} external body") for e in g['calls']) + '.</p>' if g['calls'] else ''
            transfers = '<p><b>Other-group branches/jumps:</b> ' + '; '.join(link(e['target'], f"${e['site']} {e['operation']} → ${e['target']}") for e in g['cross_group_transfers']) + '.</p>' if g['cross_group_transfers'] else ''
            related = '<p>Other groups touching the same explicit fixed addresses (width-aware, no runtime-order claim):</p><p><b>Other writers of reads here:</b> ' + (', '.join(link(a) for a in g['other_fixed_writers']) or 'none identified') + '.</p><p><b>Other readers of writes here:</b> ' + (', '.join(link(a) for a in g['other_fixed_readers']) or 'none identified') + '.</p>'
            refs = '<p><b>ROM references:</b> ' + '; '.join(esc('$' + r['address'] + ': ' + r['role']) for r in g['rom_references']) + '. Referenced starts/operands only; inherited units and callee footprints remain qualified.</p>' if g['rom_references'] else ''
            if g['calibration_views']:
                refs += '<p><b>Supplied XDF views touching those references:</b></p><ul>' + ''.join('<li>$'+c['address']+' '+esc(c['title'])+(' — reviewed display: '+esc(', '.join(f'{v:g}' for v in c['reviewed_values']))+' '+esc(c['units']) if c['reviewed_values'] is not None else ' — inherited view; units/conversion retain qualifications')+'</li>' for c in g['calibration_views']) + '</ul>'
            spantext = '; '.join('$'+r['start']+'..$'+r['end_exclusive'] for r in g['instruction_spans'])
            evidence = f'<p>{g["instruction_count"]} instructions, {g["byte_count"]} bytes. Listed spans, end exclusive: {spantext}. {g["unchanged_stock_instruction_count"]}/{g["instruction_count"]} starts match stock instruction bytes.</p><p>Context reference: <code>{esc(g["source"])}</code>. Exact-byte membership and purpose interpretation are distinct evidence.</p>'
            operations = '\n'.join(f'{i.pc:04X}  {i.data.hex(" "):<14} {(i.op+" "+i.operand).strip()}' for i in g['instructions'])
            # Include precise membership in search so any contained instruction
            # address reveals the appropriate functional group, not a neighbor.
            search = esc(' '.join([g['title'], g['purpose'], g.get('tuning',''), operations, human_refs(g['fixed_reads']), human_refs(g['fixed_writes']), json.dumps(g['rom_references'])]).lower(), quote=True)
            tuning = '<p><b>Tuning connection / exact boundary:</b> '+esc(g['tuning'])+'</p>' if g.get('tuning') else ''
            cards.append(f'<section class="group" id="g{g["address"]}" data-search="{search}"><h3>${g["address"]} — {esc(g["title"])}</h3><p class="function"><b>Function:</b> {esc(g["purpose"])}</p>{tuning}{calls}{transfers}<details><summary>Inputs, saved results and relationships</summary>{ref_table(g)}<p>{len(g["indexed_operations"])} indexed data operations need caller/local pointer context. Fixed operands omit implicit register/stack and callee effects.</p>{refs}{related}</details><details><summary>Exact operations and evidence</summary>{evidence}<pre>{esc(operations)}</pre><p><a href="FULL_GUIDE.html#a{g["address"]}">Open instruction-by-instruction explanation</a></p></details></section>')
        sections.append(f'<article class="chapter" data-chapter="{n}"><h2>{n} — {esc(title)}</h2><p>{esc(purpose)}</p>' + ''.join(cards) + '</article>')
    options = '<option value="all">All chapters</option>' + ''.join(f'<option value="{n}">{n} — {esc(t)}</option>' for n, t, *_ in raw.CHAPTERS)
    outline = '<table><thead><tr><th>Part</th><th>Function</th><th>Anchors</th></tr></thead><tbody>' + ''.join('<tr><td>'+esc(a)+'</td><td>'+esc(b)+'</td><td>'+re.sub(r'\$([0-9A-F]{4})', lambda m:link(m[1]), esc(c))+'</td></tr>' for a,b,c in OUTLINE) + '</tbody></table>'
    glossary = '<dl>' + ''.join('<dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd>' for k,v in GLOSSARY.items()) + '</dl>'
    style = '''*{box-sizing:border-box}body{margin:0;background:#f1f3f5;color:#19252b;font:17px/1.6 system-ui,sans-serif}header,main,nav{max-width:1080px;margin:auto;padding:18px}header{background:#fff}nav{position:sticky;top:0;background:#e4edf1;z-index:2;border-bottom:1px solid #b3c3ca;display:flex;gap:10px;flex-wrap:wrap}input,select,button{font:inherit;padding:9px;border:1px solid #849ba5;border-radius:5px;min-width:0;max-width:100%}input{flex:1 1 220px}select{flex:1 1 220px}.group{background:#fff;border-left:4px solid #386c7a;border-radius:5px;margin:20px 0;padding:18px;scroll-margin-top:160px}h1{font-size:1.8rem}h2{font-size:1.5rem}h3{font-size:1.18rem;margin-top:0}.function{font-size:1.03rem}a{color:#145d7a;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#edf1f4;padding:12px;font:14px/1.55 ui-monospace,monospace}code{overflow-wrap:anywhere}details{border-top:1px solid #dce3e7;padding-top:10px;margin-top:13px}summary{cursor:pointer;color:#285e72}table{width:100%;border-collapse:collapse;font-size:.88rem;table-layout:fixed}td,th{padding:8px;vertical-align:top;text-align:left;border:1px solid #cbd4db;overflow-wrap:anywhere}dt{font-weight:bold}dd{margin:0 0 12px}.muted{color:#53636d;font-size:.9rem}.hidden{display:none!important}#status{flex-basis:100%}@media(max-width:560px){header,main,nav{padding:12px}.group{padding:13px}table{font-size:.78rem}td,th{padding:5px}}'''
    script = '''const q=document.querySelector('#search');
const pick=document.querySelector('#chapter');
const status=document.querySelector('#status');
const groups=[...document.querySelectorAll('.group')];
function apply(){
  const needle=q.value.trim().toLowerCase().replace(/^(?:\\$|0x)/,'');
  let shown=0;
  for(const chapter of document.querySelectorAll('.chapter')){
    const allowed=pick.value==='all'||pick.value===chapter.dataset.chapter;
    let any=false;
    for(const group of chapter.querySelectorAll('.group')){
      const hit=allowed&&(!needle||group.dataset.search.includes(needle));
      group.classList.toggle('hidden',!hit);
      if(hit){shown++;any=true;}
    }
    chapter.classList.toggle('hidden',!any);
  }
  status.textContent=shown+' functional groups shown. Clear search for surrounding context.';
}
let timer;
q.addEventListener('input',()=>{clearTimeout(timer);timer=setTimeout(apply,120);});
pick.addEventListener('change',apply);
document.querySelector('#clear').addEventListener('click',()=>{q.value='';pick.value='all';apply();});
document.addEventListener('click',event=>{
  const link=event.target.closest('a[href^="#g"]');
  if(!link)return;
  q.value='';pick.value='all';apply();
});
apply();
'''
    header = f'<h1>Rev B — what the operation groups do</h1><p>{coverage["instructions"]:,} instructions in <b>{coverage["functional_groups"]} functional reading groups</b>. Read each Function paragraph first; expand details to trace its inputs/results and exact operations.</p><p class="muted">Exact Rev B SHA-256: <code>{raw.SHA}</code>. Groups can contain alternative paths and shared tails; address order is not execution order. Purpose text is reviewed context, while instruction membership/bytes and static links are mechanically checked. Inherited roles and physical identities retain their qualifications. No BIN/XDF/calibration change; Rev B truck testing remains first.</p><details><summary>How the program fits together</summary>{outline}</details><details><summary>Plain-English terms and reading limits</summary>{glossary}<p>Fixed-address relationships omit arbitrary indexed, stack and callee effects and do not prove runtime order or causality. Stock-byte matching does not establish unchanged caller inputs, all-state equivalence, interrupt timing or physical hardware behavior. See the complete Markdown for scope notes.</p></details>'
    doc = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Rev B functional operation groups</title><style>'+style+'</style></head><body><header>'+header+'</header><nav><input id="search" type="search" aria-label="Search functional groups" placeholder="Address or function: 9A52, idle learning, BLM…"><select id="chapter" aria-label="Choose chapter">'+options+'</select><button id="clear" type="button">Show all</button><span id="status" class="muted"></span></nav><main>'+''.join(sections)+'</main><script>'+script+'</script></body></html>'
    (out / 'FUNCTIONAL_GUIDE.html').write_text(doc)


def build(image, output):
    # Guard identity and context completeness before writing any deliverable.
    groups, coverage = make_groups(image)
    raw.build(image, output)
    write_outputs(output, image, groups, coverage)
    (output / "SHA256SUMS.txt").write_text("".join(hashlib.sha256(p.read_bytes()).hexdigest()+"  "+p.relative_to(output).as_posix()+"\n" for p in sorted(output.rglob("*")) if p.is_file() and p.name != "SHA256SUMS.txt"))
    return coverage


def record_boundaries(image, path):
    groups, coverage = make_groups(image)
    def row(i):
        return dict(address=f"{i.pc:04X}", bytes=i.data.hex(" "), operation=(i.op + " " + i.operand).strip())
    evidence = dict(image_sha256=raw.SHA, context_sha256=coverage["context_sha256"],
                    scope="First and last instruction of each functional reading group plus selected calibration bytes; not a full executable BIN or all-state semantic proof.",
                    groups=[dict(address=g["address"], instructions=g["instruction_count"], first=row(g["instructions"][0]), last=row(g["instructions"][-1])) for g in groups],
                    calibration_excerpts={f"{a:04X}": image[a:z].hex() for a, z in ((0x9f00, 0x9f27), (0x50a8, 0x50aa), (0xff8a, 0xff8c))})
    path.write_text(json.dumps(evidence, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rom", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--record-boundaries", action="store_true", help="Also regenerate the committed compact boundary fixture from this exact image")
    args = parser.parse_args()
    image = args.rom.read_bytes()
    coverage = build(image, args.output)
    if args.record_boundaries:
        record_boundaries(image, ROOT / "maps/maintenance/revb_function_boundaries.json")
    assert args.rom.read_bytes() == image
    print(json.dumps(coverage, indent=2))
