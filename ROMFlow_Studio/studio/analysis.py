#!/usr/bin/env python3
"""ROM-first 68HC11 analyzer. It never imports BMHM labels/locations to find code.

Outputs a cross-linked static site, CSV/JSON evidence, and DOT control flow. Routines
are rooted from vectors, optional entries, resolved calls and vetted dispatch tables.
Unproved byte ranges and indirect targets remain visibly unresolved.
"""
from __future__ import annotations
import argparse,csv,hashlib,html,json,re
from collections import defaultdict,deque,Counter
from dataclasses import dataclass
from pathlib import Path
from .decoder import decode,DecodeError,BRANCHES,TERMINALS

VECTOR_NAMES={0xFFD6:'SCI',0xFFD8:'SPI',0xFFDA:'PA_EDGE',0xFFDC:'PA_OVERFLOW',0xFFDE:'TIMER_OVERFLOW',0xFFE0:'TOC5',0xFFE2:'TOC4',0xFFE4:'TOC3',0xFFE6:'TOC2',0xFFE8:'TOC1',0xFFEA:'TIC3',0xFFEC:'TIC2',0xFFEE:'TIC1',0xFFF0:'RTI_TIMER',0xFFF2:'IRQ',0xFFF4:'XIRQ',0xFFF6:'SWI',0xFFF8:'ILLEGAL',0xFFFA:'COP',0xFFFC:'CLOCK',0xFFFE:'RESET'}
CALLS={'JSR','BSR'};COND=set(BRANCHES)-{'BRA','BRN'}|{'BRSET','BRCLR'}
END={'RTS','RTI','STOP'}
def hx(n):return f'{n:04X}' if n is not None else '?'
def num(s):return int(str(s).replace('$','0x'),0)
def safe(s):return html.escape(str(s),quote=True)
def dump_csv(path,rows,fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)

@dataclass
class Image:
    raw:bytes
    start:int
    def contains(self,a,n=1):return self.start<=a and a+n<=self.start+len(self.raw) and a+n<=0x10000
    def read(self,a,n=1):return self.raw[a-self.start:a-self.start+n] if self.contains(a,n) else b''
    def word(self,a):
        b=self.read(a,2);return int.from_bytes(b,'big') if len(b)==2 else None

class Analyzer:
    def __init__(self,image,entries,vector_scan=True,dispatch_spec=(),max_instructions=60000):
        self.img=image;self.entries=set(entries);self.entry_sources=defaultdict(set)
        for e in entries:self.entry_sources[e].add('explicit')
        self.vectors=[];self.instructions={};self.failures={};self.overlaps=[];self.dispatch=[];self.dispatch_candidates=[];self.max_instructions=max_instructions
        self.specs=[]
        for spec in dispatch_spec:
            parts=spec.split(':')
            if len(parts)!=2:raise ValueError('dispatch format ADDRESS:COUNT')
            addr,count=num(parts[0]),num(parts[1]);
            if count<1 or count>1024:raise ValueError('dispatch count must be 1..1024')
            self.specs.append((addr,count))
        if vector_scan:
            for va in range(0xFFC0,0x10000,2):
                if not image.contains(va,2):continue
                target=image.word(va)
                if target in {0,0xFFFF} or not image.contains(target):continue
                # A vector is an execution root only when its first opcode decodes.
                try:ins=decode(image.read,target)
                except DecodeError:continue
                source=VECTOR_NAMES.get(va,f'VECTOR_{va:04X}')
                self.vectors.append({'vector':hx(va),'name':source,'target':hx(target)})
                self.entries.add(target);self.entry_sources[target].add('vector:'+source)
    def scan(self):
        queue=deque(sorted(self.entries));seen_roots=set()
        while queue:
            root=queue.popleft()
            if root in seen_roots:continue
            seen_roots.add(root)
            if not self.img.contains(root):continue
            pending=[root];visited=set()
            while pending:
                pc=pending.pop()
                if pc in visited or not self.img.contains(pc):continue
                visited.add(pc)
                if pc not in self.instructions:
                    if len(self.instructions)>=self.max_instructions:raise RuntimeError('instruction limit reached')
                    try:ins=decode(self.img.read,pc)
                    except DecodeError as exc:self.failures[pc]=str(exc);continue
                    overlap=next((a for a,i in self.instructions.items() if a<pc<a+len(i.data)),None)
                    if overlap is not None:
                        self.overlaps.append((pc,overlap));continue
                    self.instructions[pc]=ins
                ins=self.instructions[pc]
                if ins.op in CALLS:
                    if ins.target is not None and self.img.contains(ins.target):
                        self.entries.add(ins.target);self.entry_sources[ins.target].add('call:'+hx(pc));queue.append(ins.target)
                    pending.append(ins.next_pc)
                elif ins.op in END:continue
                elif ins.op=='JMP':
                    if ins.target is not None:pending.append(ins.target)
                elif ins.op=='BRA':pending.append(ins.target)
                elif ins.op=='BRN':pending.append(ins.next_pc)
                elif ins.op in COND:pending.extend((ins.next_pc,ins.target))
                else:pending.append(ins.next_pc) # includes WAI and SWI continuation
        self.find_dispatchers()
        # Re-run only if vetted pointer roots add newly found reachable blocks.
        if any(a not in seen_roots for a in self.entries):
            extras=Analyzer(self.img,self.entries,False,(),self.max_instructions)
            extras.entry_sources=self.entry_sources;extras.scan()
            self.instructions.update(extras.instructions);self.failures.update(extras.failures);self.overlaps.extend(extras.overlaps)
        self.routines=self.find_routines()
        self.accesses=self.collect_accesses()
        self.calls=self.collect_calls()
        return self
    def find_dispatchers(self):
        """Find pointer arrays from instructions, not from a predefined GM memory map.

        This identifies the common indexed-table-then-indirect-control idiom:
        LDX #base ... [ABX/offset] ... LDX n,X ... JSR/JMP n,X.
        Independent pointer/entry plausibility checking is required. These are
        statically inferred *possible* flows, never dynamic execution proof.
        """
        load_sites=defaultdict(list)
        for pc,i in self.instructions.items():
            if i.op in {'LDX','LDY'} and i.mode=='immediate' and self.img.contains(i.value,6):load_sites[i.value].append(pc)
        candidates={addr:(sites,'pattern_candidate') for addr,sites in load_sites.items()}
        for a,n in self.specs:candidates[a]=(load_sites.get(a,[]),'manual')
        for addr,(sites,source) in sorted(candidates.items()):
            count=next((n for a,n in self.specs if a==addr),None)
            nearby_sinks=[]
            for site in sites:
                is_x=self.instructions[site].op=='LDX';kind='indexed_x' if is_x else 'indexed_y'
                between=[(pc,i) for pc,i in self.instructions.items() if site<pc<=site+32]
                between.sort()
                for pc,ins in between:
                    if ins.op in {'JSR','JMP'} and ins.mode==kind and ins.target is None:
                        if any(i.op in {'LDX','LDY'} and i.mode==kind for p,i in between if p<pc):
                            nearby_sinks.append(pc)
            def entry_looks_executable(target):
                if target in {0,0xFFFF} or not self.img.contains(target):return False
                if target in self.instructions:return True
                pc=target;has_control=False;has_nonfill=False
                for _ in range(12):
                    try:ins=decode(self.img.read,pc)
                    except DecodeError:return False
                    if not (ins.op=='STX' and ins.mode=='extended' and ins.value==0xFFFF):has_nonfill=True
                    if ins.op in {'RTS','RTI'}:return has_nonfill
                    if ins.op in {'JMP','BRA'}:
                        return ins.target is not None and self.img.contains(ins.target) and has_nonfill
                    if ins.op in {'SWI','STOP'}:return False
                    if ins.op in COND or ins.op in CALLS:has_control=True
                    pc=ins.next_pc
                return has_nonfill and has_control
            words=[]
            for j in range(count if count is not None else 32):
                v=self.img.word(addr+2*j)
                if v is None:break
                if count is None and (v in {0,0xFFFF} or not self.img.contains(v)):break
                if count is None and j>=3 and not entry_looks_executable(v):break
                words.append(v)
            if not words:continue
            rooted=sum(v in self.instructions for v in words)
            unique=len(set(words))
            plausible=sum(entry_looks_executable(v) for v in words)
            fraction=plausible/max(1,len(words))
            if count is not None:status='manual_confirmed_by_user'
            elif len(words)>=3 and unique>=3 and rooted>=3 and fraction>=0.75:status='auto_rooted_pointer_array'
            elif len(words)>=3 and unique>=3 and nearby_sinks and fraction>=0.90:status='auto_pattern_vetted'
            else:status='candidate_only'
            if status!='candidate_only' or nearby_sinks:
                self.dispatch_candidates.append(dict(table=hx(addr),slots=len(words),plausible=plausible,unique=unique,rooted=rooted,linked_sites=';'.join(hx(s) for s in sorted(set(nearby_sinks))),status=status))
            if status=='candidate_only':continue
            for index,target in enumerate(words):
                valid=self.img.contains(target)
                self.dispatch.append(dict(table=hx(addr),slot=index,target=hx(target),source=status,status='rooted' if target in self.instructions else 'inferred_entry' if valid else 'out_of_image',load_sites=';'.join(hx(x) for x in sites)))
                if valid:
                    self.entries.add(target);self.entry_sources[target].add(f'dispatch:{hx(addr)}[{index}]')
    def graph_edges(self,i):
        if i.op in END:return []
        if i.op in CALLS:return [(i.next_pc,'return_path')]
        if i.op=='JMP':return [(i.target,'jump')] if i.target is not None else []
        if i.op=='BRA':return [(i.target,'jump')]
        if i.op=='BRN':return [(i.next_pc,'fallthrough')]
        if i.op in COND:return [(i.target,'taken'),(i.next_pc,'not_taken')]
        return [(i.next_pc,'fallthrough')]
    def find_routines(self):
        # Distinguish entry-to-entry transfers from ordinary branch within one routine.
        results={}
        for entry in sorted(self.entries):
            if entry not in self.instructions:continue
            todo=[entry];seen=set();edges=[];exits=[]
            while todo:
                pc=todo.pop()
                if pc in seen:continue
                if pc not in self.instructions:
                    exits.append((pc,'unresolved'));continue
                if pc!=entry and pc in self.entries:
                    exits.append((pc,'tail_transfer'));continue
                seen.add(pc);ins=self.instructions[pc]
                if ins.op in CALLS:
                    edges.append((pc,ins.target,'call' if ins.target is not None else 'indirect_call'))
                    if ins.target is None:exits.append((pc,'indirect_call'))
                if ins.op in END:exits.append((pc,ins.op))
                if ins.op=='JMP' and ins.target is None:exits.append((pc,'indirect_jump'))
                for target,kind in self.graph_edges(ins):
                    edges.append((pc,target,kind))
                    if target not in self.instructions:
                        exits.append((pc,'unknown_target:'+hx(target)))
                    elif target!=entry and target in self.entries:
                        exits.append((pc,'tail_to:'+hx(target)))
                    else:todo.append(target)
            if not seen:continue
            sig=' '.join(self.instructions[a].op+':'+self.instructions[a].mode for a in sorted(seen))
            results[entry]=dict(entry=entry,pcs=seen,edges=edges,exits=sorted(set(exits)),signature=hashlib.sha256(sig.encode()).hexdigest()[:16],shape=sig.split(),sources=sorted(self.entry_sources[entry]))
        return results
    def collect_accesses(self):
        # Fixed point X/Y constants across reachable flows. Unknown at joins or calls.
        states={pc:None for pc in self.instructions};pending=deque()
        def combine(pc,s):
            if pc not in states:return
            if states[pc] is None:states[pc]=s;pending.append(pc)
            else:
                old=states[pc];new=tuple(old[i] if old[i]==s[i] else -1 for i in range(2))
                if new!=old:states[pc]=new;pending.append(pc)
        for pc in self.entries:combine(pc,(-1,-1))
        count=0
        while pending and count<500000:
            count+=1;pc=pending.popleft();s=list(states[pc]);i=self.instructions[pc]
            if i.op in {'LDX','LDY'}:
                k=0 if i.op=='LDX' else 1
                s[k]=i.value if i.mode=='immediate' else -1
            elif i.op in {'INX','DEX','INY','DEY'}:
                k=0 if i.op.endswith('X') else 1
                if s[k]>=0:s[k]=(s[k]+(1 if i.op.startswith('IN') else -1))&0xFFFF
            elif i.op in {'TSX','PULX','XGDX','ABX','TSY','PULY','XGDY','ABY'}:
                s[0 if i.op.endswith('X') else 1]=-1
            if i.op in CALLS:s=[-1,-1]
            for target,_ in self.graph_edges(i):combine(target,tuple(s))
        rows=[]
        for pc,i in sorted(self.instructions.items()):
            mem=i.access()
            if mem is None:continue
            state=states.get(pc) or (-1,-1)
            index=mem['index'];address=mem['address']
            if index:
                base=state[0 if index=='X' else 1]
                if base>=0:address=(base+mem['offset'])&0xFFFF;confidence='constant_index_propagation'
                else:confidence='unresolved_index'
            else:confidence='instruction_absolute'
            for width_offset in range(2 if mem['width_bits']==16 and address is not None else 1):
                target=((address+width_offset)&0xFFFF) if address is not None else None
                rows.append(dict(pc=hx(pc),instruction=i.op,operand=i.operand,access=mem['access'],width_bits=mem['width_bits'],address=hx(target),index=index,offset=hx(mem['offset']),mask=hx(mem['mask']),resolution=confidence,region='image' if target is not None and self.img.contains(target) else 'external' if target is not None else 'unknown',byte_lane=width_offset))
        return rows
    def collect_calls(self):
        rows=[]
        ownership=defaultdict(list)
        for root,r in self.routines.items():
            for pc in r['pcs']:ownership[pc].append(root)
        for pc,i in sorted(self.instructions.items()):
            if i.op in CALLS or i.op=='JMP' and i.target is None:
                rows.append(dict(pc=hx(pc),kind=i.op,target=hx(i.target),resolution='direct' if i.target is not None else 'indirect_unresolved',owners=';'.join(hx(r) for r in ownership.get(pc,[]))))
        return rows
    def orphan_candidates(self, max_results=100):
        """Unrooted opcode sweep only: candidates are NEVER promoted to established code."""
        claimed={a+j for a,i in self.instructions.items() for j in range(len(i.data))}
        claimed|={int(v['vector'],16)+n for v in self.vectors for n in (0,1)}
        for d in self.dispatch:
            a=int(d['table'],16)+2*d['slot'];claimed.update((a,a+1))
        # Unrooted probing is heuristic. Skip long uniform padding spans to avoid
        # millions of decodes in sparse ROM images. This does NOT mark FF bytes
        # invalid: an isolated FF still decodes as real STX extended.
        padding=bytearray(len(self.img.raw))
        for match in re.finditer(rb'\xFF{32,}|\x00{32,}', self.img.raw):
            padding[match.start():match.end()]=b'\x01'*(match.end()-match.start())
        candidates=[];last_end=-1
        for pc in range(self.img.start,self.img.start+len(self.img.raw)-10):
            if padding[pc-self.img.start] or pc in claimed or pc<last_end:continue
            cur=pc;decoded=[];terminated=False
            for step in range(24):
                if cur in claimed or not self.img.contains(cur) or any(cur+j in claimed for j in range(3)):
                    break
                try:i=decode(self.img.read,cur)
                except DecodeError:break
                if any(cur+j in claimed for j in range(len(i.data))):break
                decoded.append(i);cur+=len(i.data)
                if i.op in {'RTS','RTI'}:terminated=True;break
                if i.op in {'JMP','BRA','STOP','SWI'}:break
            if not terminated or len(decoded)<6:continue
            controls=sum(i.op in COND or i.op in CALLS for i in decoded)
            mem=sum(i.access() is not None for i in decoded)
            if controls<1 or mem<2:continue
            candidates.append(dict(start=hx(pc),end_exclusive=hx(cur),instructions=len(decoded),control_count=controls,memory_access_count=mem,terminator=decoded[-1].op,status='unrooted_candidate_unproven'))
            last_end=cur
            if len(candidates)>=max_results:break
        return candidates
    def hotspots(self):
        pages=defaultdict(lambda:Counter())
        for r in self.accesses:
            if r['address']=='?':continue
            addr=int(r['address'],16)
            page=addr>>8;pages[page][r['access']]+=1
        return [dict(page=f'{k:02X}xx',reads=v['R'],writes=v['W'],read_modify_write=v['RW'],note='address_cluster_only_no_hardware_type_inferred') for k,v in sorted(pages.items())]
    def unknown_spans(self):
        claimed={a+j for a,i in self.instructions.items() for j in range(len(i.data))}
        claimed|={int(v['vector'],16)+n for v in self.vectors for n in (0,1)}
        for d in self.dispatch:
            a=int(d['table'],16)+2*d['slot'];claimed.update((a,a+1))
        rows=[];start=None
        for pc in range(self.img.start,self.img.start+len(self.img.raw)+1):
            unknown=pc<self.img.start+len(self.img.raw) and pc not in claimed
            if unknown and start is None:start=pc
            if not unknown and start is not None:
                rows.append(dict(start=hx(start),end_exclusive=f'{pc:05X}',length=pc-start,status='unclassified_not_necessarily_data'))
                start=None
        return rows
    def serializable(self):
        owners=defaultdict(list)
        for root,r in self.routines.items():
            for pc in r['pcs']:owners[pc].append(root)
        return dict(image=dict(start=hx(self.img.start),end=hx(self.img.start+len(self.img.raw)-1),size=len(self.img.raw),sha256=hashlib.sha256(self.img.raw).hexdigest()),vectors=self.vectors,entries=[dict(address=hx(x),sources=sorted(self.entry_sources[x])) for x in sorted(self.entries)],routines=[dict(entry=hx(a),sources=r['sources'],instruction_count=len(r['pcs']),signature=r['signature'],shape=r['shape'],exits=[dict(pc=hx(p),type=k) for p,k in r['exits']],calls=[dict(pc=hx(pc),target=hx(t),type=kind) for pc,t,kind in r['edges'] if kind.startswith('call')]) for a,r in sorted(self.routines.items())],instructions=[dict(pc=hx(pc),bytes=i.data.hex(' ').upper(),op=i.op,operand=i.operand,owners=[hx(x) for x in owners.get(pc,[])]) for pc,i in sorted(self.instructions.items())],dispatch=self.dispatch,accesses=self.accesses,calls=self.calls,failures=[dict(pc=hx(p),error=e) for p,e in sorted(self.failures.items())],overlaps=[dict(pc=hx(p),existing_start=hx(s)) for p,s in self.overlaps],unknown_bytes=len(self.img.raw)-len(set(i.pc+j for i in self.instructions.values() for j in range(len(i.data))))-len(self.vectors)*2)

def render(an,out,comparison=None):
    out.mkdir(parents=True,exist_ok=True);data=an.serializable();(out/'analysis.json').write_text(json.dumps(data,indent=2)+'\n')
    dump_csv(out/'calls.csv',an.calls,['pc','kind','target','resolution','owners'])
    dump_csv(out/'dispatch.csv',an.dispatch,['table','slot','target','source','status','load_sites'])
    dump_csv(out/'dispatch_candidates.csv',an.dispatch_candidates,['table','slots','plausible','unique','rooted','linked_sites','status'])
    dump_csv(out/'memory_accesses.csv',an.accesses,['pc','instruction','operand','access','width_bits','address','index','offset','mask','resolution','region','byte_lane'])
    dump_csv(out/'vectors.csv',an.vectors,['vector','name','target'])
    dump_csv(out/'routines.csv',data['routines'],['entry','sources','instruction_count','signature'])
    dump_csv(out/'unresolved.csv',data['failures']+data['overlaps'],['pc','error','existing_start'])
    dump_csv(out/'access_hotspots.csv',an.hotspots(),['page','reads','writes','read_modify_write','note'])
    dump_csv(out/'unclassified_regions.csv',an.unknown_spans(),['start','end_exclusive','length','status'])
    dump_csv(out/'orphan_candidates.csv',an.orphan_candidates(),['start','end_exclusive','instructions','control_count','memory_access_count','terminator','status'])
    (out/'routines').mkdir(exist_ok=True);(out/'entry_exit').mkdir(exist_ok=True);(out/'graphs').mkdir(exist_ok=True);(out/'calls').mkdir(exist_ok=True);(out/'dispatch').mkdir(exist_ok=True);(out/'dispatch'/'sites').mkdir(exist_ok=True)
    css='''body{background:#111822;color:#dde6ed;font-family:system-ui,Arial,sans-serif;margin:1.4rem auto;max-width:1260px;padding:0 1rem}a{color:#7fd6ff}code,pre,td.mono{font:13px ui-monospace,Consolas,monospace}table{border-collapse:collapse;width:100%}th,td{padding:6px 10px;border-bottom:1px solid #34414f;text-align:left;vertical-align:top}th{position:sticky;top:0;background:#202c3a}tr:hover{background:#202c3a}.muted{color:#adbac7}input{background:#253344;color:#fff;border:1px solid #64778d;padding:10px;width:100%;box-sizing:border-box}.box{border:1px solid #354759;padding:16px;margin:15px 0;border-radius:8px}small{color:#b5c6d6}pre{overflow-x:auto}'''
    (out/'style.css').write_text(css)
    call_graph=['digraph rom_calls {','rankdir=LR; node [shape=box,fontname="monospace"];']
    for root,r in sorted(an.routines.items()):
        rid=hx(root)
        label=rid+'\n'+','.join(r['sources'][:2])
        call_graph.append(f'"{rid}" [label="{label}"];')
        for pc,target,kind in r['edges']:
            if kind.startswith('call') and target in an.routines:
                call_graph.append(f'"{rid}" -> "{hx(target)}" [label="{hx(pc)}"];')
    call_graph.append('}')
    (out/'callgraph.dot').write_text('\n'.join(call_graph)+'\n')
    # Every rooted call has an independent, linkable evidence page.
    for c in an.calls:
        p=c['pc'];target=c['target'];owners=c['owners'].split(';') if c['owners'] else []
        targetlink=f'<a href="../routines/{target}.html">${target}</a>' if target!='?' and int(target,16) in an.routines else '$'+target if target!='?' else 'unresolved'
        ownerlinks='; '.join(f'<a href="../routines/{x}.html">${x}</a>' for x in owners)
        callhtml=f'<meta charset="utf-8"><link rel="stylesheet" href="../style.css"><p><a href="../index.html">Index</a></p><h1>Call/transfer site ${p}</h1><p>Instruction: {safe(c["kind"])} · target: {targetlink} · resolution: {safe(c["resolution"])}</p><p>Owners: {ownerlinks}</p>'
        (out/'calls'/f'{p}.html').write_text(callhtml)
    sites=[]
    for c in an.calls:
        if c['resolution']!='indirect_unresolved':continue
        pc=int(c['pc'],16);possible=[]
        for a,i in an.instructions.items():
            if 0<pc-a<=40 and i.op in {'LDX','LDY'} and i.mode=='immediate' and an.img.contains(i.value):possible.append((a,i.value))
        guess=possible[-1][1] if possible else None
        table=hx(guess)
        status='heuristic_nearby_load_not_proven' if guess is not None else 'unknown'
        sites.append(dict(site=c['pc'],kind=c['kind'],candidate_table=table,confidence=status,owners=c['owners']))
    dump_csv(out/'dispatcher_sites.csv',sites,['site','kind','candidate_table','confidence','owners'])
    for site in sites:
        p=site['site'];table=site['candidate_table']
        matching=[d for d in an.dispatch if d['table']==table]
        slots=''.join(f'<tr><td>{d["slot"]}</td><td><a href="../../routines/{d["target"]}.html">${d["target"]}</a></td><td>{d["status"]}</td></tr>' for d in matching)
        body=f'<meta charset="utf-8"><link rel="stylesheet" href="../../style.css"><a href="../../index.html">Index</a><h1>Indirect {site["kind"]} at ${p}</h1><p>Candidate table: ${table}. {site["confidence"]}. This association is a proximity hint, not proof of an executing dispatch.</p><table><tr><th>Slot</th><th>Target</th><th>Evidence</th></tr>{slots}</table>'
        (out/'dispatch'/'sites'/f'{p}.html').write_text(body)
    for table,group in __import__('itertools').groupby(sorted(an.dispatch,key=lambda x:x['table']),key=lambda x:x['table']):
        rows=list(group)
        slots=''.join(f'<tr><td>{d["slot"]}</td><td><a href="../routines/{d["target"]}.html">${d["target"]}</a></td><td>{d["status"]}</td></tr>' for d in rows)
        (out/'dispatch'/f'{table}.html').write_text(f'<meta charset="utf-8"><link rel="stylesheet" href="../style.css"><a href="../index.html">Index</a><h1>Dispatch pointer table ${table}</h1><p>Discovery source: {safe(rows[0]["source"])} · load sites: {safe(rows[0]["load_sites"])}</p><table><tr><th>Slot</th><th>Target</th><th>Resolution</th></tr>{slots}</table>')
    for root,r in sorted(an.routines.items()):
        rid=hx(root)
        calls=[(pc,t,kind) for pc,t,kind in r['edges'] if kind.startswith('call')]
        incoming=[c for c in an.calls if c['target']==rid]
        pcs=sorted(r['pcs'])
        insrows='\n'.join(f'<tr><td class="mono"><a id="pc{hx(pc)}">${hx(pc)}</a></td><td class="mono">{an.instructions[pc].data.hex(" ").upper()}</td><td class="mono">{safe(an.instructions[pc].op)} {safe(an.instructions[pc].operand)}</td><td>{"; ".join(f"{kind} → ${hx(t)}" for src,t,kind in r["edges"] if src==pc)}</td></tr>' for pc in pcs)
        def routine_link(t):return f'<a href="{hx(t)}.html">${hx(t)}</a>' if t in an.routines else f'${hx(t)}'
        body=f'''<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="../style.css"><title>Routine ${rid}</title><p><a href="../index.html">Index</a> · <a href="../entry_exit/{rid}.html">Entry/exit evidence</a> · <a href="../graphs/{rid}.dot">DOT flow graph</a></p><h1>Routine ${rid}</h1><p class="muted">{len(pcs)} decoded instruction starts · SHA shape {r['signature']} · roots: {safe(', '.join(r['sources']))}</p><div class="box"><h3>Callers</h3><p>{'; '.join(safe(c['pc']) for c in incoming) or 'No rooted direct caller; vector/dispatch entry possible'}</p><h3>Calls</h3><p>{'; '.join(f'${hx(pc)} → {routine_link(t)}' for pc,t,_ in calls) or 'none'}</p><h3>Exit/transfer sites</h3><p>{'; '.join(f'${hx(p)} {safe(k)}' for p,k in r['exits']) or 'none proved'}</p></div><table><thead><tr><th>PC</th><th>bytes</th><th>instruction</th><th>control edge(s)</th></tr></thead><tbody>{insrows}</tbody></table>'''
        (out/'routines'/f'{rid}.html').write_text(body,encoding='utf-8')
        site=f'''<!doctype html><meta charset="utf-8"><link rel="stylesheet" href="../style.css"><p><a href="../index.html">Index</a> · <a href="../routines/{rid}.html">Routine</a></p><h1>Entry / exit ${rid}</h1><h2>Entry sources</h2><pre>{safe(chr(10).join(r['sources']))}</pre><h2>Direct incoming calls</h2><pre>{safe(chr(10).join(c['pc']+' '+c['kind'] for c in incoming)) or 'none'}</pre><h2>Calls out</h2><pre>{safe(chr(10).join(f'{hx(pc)} {kind} {hx(t)}' for pc,t,kind in calls)) or 'none'}</pre><h2>Exits / unresolved</h2><pre>{safe(chr(10).join(f'{hx(p)} {k}' for p,k in r['exits'])) or 'none'}</pre>'''
        (out/'entry_exit'/f'{rid}.html').write_text(site)
        dot=[f'digraph R_{rid} {{', 'rankdir=LR; node [shape=box,fontname="monospace"];']
        for pc in pcs:dot.append(f'"{hx(pc)}" [label="{hx(pc)} {an.instructions[pc].op}"];')
        for pc,t,kind in r['edges']:
            if t is not None:
                if t not in r['pcs']:dot.append(f'"{hx(t)}" [shape=oval,style=dashed];')
                dot.append(f'"{hx(pc)}" -> "{hx(t)}" [label="{kind}"];')
        dot.append('}');(out/'graphs'/f'{rid}.dot').write_text('\n'.join(dot)+'\n')
    cards='\n'.join(f'<tr><td><a href="routines/{hx(a)}.html">${hx(a)}</a></td><td>{len(r["pcs"])}</td><td>{safe(", ".join(r["sources"]))}</td><td>{len(r["exits"])}</td><td><a href="entry_exit/{hx(a)}.html">entry/exit</a></td><td><a href="graphs/{hx(a)}.dot">DOT</a></td></tr>' for a,r in sorted(an.routines.items()))
    index=f'''<!doctype html><meta charset="utf-8"><title>68HC11 ROM navigator</title><link rel="stylesheet" href="style.css"><h1>68HC11 ROM navigator</h1><p>ROM SHA-256: <code>{data['image']['sha256']}</code></p><p>{len(an.instructions)} decoded instruction starts · {len(an.routines)} routine entries · {len(an.calls)} call/jump sites · {len(an.dispatch)} dispatcher slots · {len(an.failures)} decode frontiers</p><div class="box"><b>Evidence downloads</b><p><a href="analysis.json">JSON</a> · <a href="callgraph.dot">Global call graph</a> · <a href="calls.csv">Call sites</a> · <a href="dispatch.csv">Dispatch slots</a> · <a href="dispatch_candidates.csv">Pointer candidates</a> · <a href="dispatcher_sites.csv">Indirect dispatch sites</a> · <a href="memory_accesses.csv">Memory accesses</a> · <a href="vectors.csv">Vectors</a> · <a href="unresolved.csv">Unresolved decoding</a> · <a href="orphan_candidates.csv">Unrooted candidates</a> · <a href="unclassified_regions.csv">Unknown ranges</a> · <a href="access_hotspots.csv">Address hotspots</a></p><p class="muted">Rooted flow only. Unvisited bytes are NOT automatically data. ROM-mapped read addresses are NOT automatically hardware. Indirect control flow requires confirmation.</p></div><input type="search" id="filter" oninput="for(let r of document.querySelectorAll('tbody tr'))r.hidden=!r.textContent.toLowerCase().includes(this.value.toLowerCase())" placeholder="Filter routines by address, entry source..."><table><thead><tr><th>Entry</th><th>Instructions</th><th>Provenance</th><th>Exits</th><th>Entry/exit</th><th>Graph</th></tr></thead><tbody>{cards}</tbody></table>'''
    (out/'index.html').write_text(index,encoding='utf-8')
    if comparison:
        prev=json.loads(Path(comparison).read_text());prevsig=defaultdict(list)
        for r in prev.get('routines',[]):prevsig[r['signature']].append(r['entry'])
        matches=[dict(new_entry=r['entry'],old_entries=prevsig[r['signature']],signature=r['signature'],match_type='opcode_mode_sequence_exact') for r in data['routines'] if prevsig[r['signature']]]
        dump_csv(out/'cross_rom_matches.csv',[dict(new_entry=m['new_entry'],old_entries=';'.join(m['old_entries']),signature=m['signature'],match_type=m['match_type']) for m in matches],['new_entry','old_entries','signature','match_type'])
        (out/'cross_rom_matches.json').write_text(json.dumps(matches,indent=2)+'\n')
        old=prev.get('routines',[])
        gram_index=defaultdict(set)
        for ix,r in enumerate(old):
            tok=r.get('shape',[])
            for g in set(zip(tok,tok[1:],tok[2:])):gram_index[g].add(ix)
        ranked=[]
        for r in data['routines']:
            tok=r.get('shape',[]);grams=set(zip(tok,tok[1:],tok[2:]))
            options=Counter()
            for g in grams:
                for ix in gram_index.get(g,()):options[ix]+=1
            scores=[]
            for ix,common in options.most_common(30):
                oldr=old[ix];other=oldr.get('shape',[])
                if len(other)>3*max(1,len(tok)) or len(tok)>3*max(1,len(other)):continue
                oldgrams=set(zip(other,other[1:],other[2:]))
                score=common/max(1,len(grams|oldgrams))
                if score>=0.3:scores.append((score,oldr['entry']))
            for score,old_entry in sorted(scores,reverse=True)[:3]:
                ranked.append(dict(new_entry=r['entry'],old_entry=old_entry,score=f'{score:.3f}',evidence='opcode_mode_3gram_Jaccard_only'))
        dump_csv(out/'cross_rom_ranked.csv',ranked,['new_entry','old_entry','score','evidence'])
    return data

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('rom',type=Path,help='raw ROM image, unchanged')
    p.add_argument('-o','--output',type=Path,required=True)
    p.add_argument('--load-address',type=lambda x:int(x,0),help='CPU address where file byte 0 maps; default 0 for 64K or top-aligned otherwise')
    p.add_argument('--entry',action='append',default=[],help='additional entry PC (hex 0x7100); repeatable')
    p.add_argument('--dispatch-table',action='append',default=[],help='verified 16-bit big-endian pointer table ADDRESS:COUNT; repeatable')
    p.add_argument('--no-vectors',action='store_true')
    p.add_argument('--compare',help='previous analysis.json for exact opcode+mode signature matches')
    a=p.parse_args(argv);raw=a.rom.read_bytes();start=a.load_address if a.load_address is not None else (0 if len(raw)==65536 else 65536-len(raw))
    if not raw or start<0 or start+len(raw)>65536: p.error('binary must occupy one contiguous region in 16-bit CPU address space')
    analyzer=Analyzer(Image(raw,start),[int(x,0) for x in a.entry],not a.no_vectors,a.dispatch_table).scan()
    report=render(analyzer,a.output,a.compare)
    print(f"{len(analyzer.instructions)} decoded PCs, {len(analyzer.routines)} entry views, {len(analyzer.dispatch)} dispatch slots, {len(analyzer.failures)} failures")
    print(f'Navigator: {a.output / "index.html"}')
    return report
if __name__=='__main__':main()
