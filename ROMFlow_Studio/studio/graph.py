"""Basic-block and global call/dispatcher graphs from decoded instructions."""
from __future__ import annotations
from collections import defaultdict
from .analysis import CALLS, COND, END

def hx(n):return f'{n:04X}' if n is not None else '?'

def routine_graph(an,entry):
    routine=an.routines.get(entry)
    if not routine:return {'nodes':[],'edges':[], 'boundaries':[]}
    pcs=set(routine['pcs']);ordered=sorted(pcs)
    boundaries={entry}
    for pc in ordered:
        ins=an.instructions[pc]
        edges=an.graph_edges(ins)
        for t,k in edges:
            if t in pcs and (k!='fallthrough' and k!='return_path'):boundaries.add(t)
        if ins.op in CALLS or ins.op in COND or ins.op in {'BRA','JMP'}:
            if ins.next_pc in pcs:boundaries.add(ins.next_pc)
    current=None;blocks=[]
    for pc in ordered:
        i=an.instructions[pc]
        if current is None or pc in boundaries or pc!=an.instructions[current[-1]].next_pc:
            current=[];blocks.append(current)
        current.append(pc)
        if i.op in END or i.op in CALLS or i.op in COND or i.op in {'BRA','JMP'}:current=None
    nodes=[];owner={}
    for seq in blocks:
        name=hx(seq[0]);block_lines=[]
        for pc in seq:
            ins=an.instructions[pc];block_lines.append(f'{hx(pc)}  {ins.op} {ins.operand}'.strip())
            owner[pc]=name
        nodes.append(dict(id=name,kind='block',address=name,label=f'${name}',lines=block_lines[:8],length=len(seq),detail=seq[-1],subtitle=f'{len(seq)} instruction'+('s' if len(seq)!=1 else '')))
    edges=[];externals={}
    for seq in blocks:
        last=an.instructions[seq[-1]];src=owner[seq[0]]
        for target,kind in an.graph_edges(last):
            if target is None:continue
            if target in owner:dest=owner[target]
            else:
                dest='X_'+hx(target)
                externals[dest]=dict(id=dest,kind='external',address=hx(target),label=f'${hx(target)}',subtitle='external / unresolved',lines=[])
            edges.append(dict(source=src,target=dest,kind=kind,site=hx(last.pc),proven=target in an.instructions))
        if last.op in CALLS:
            if last.target is None:dest=f'X_UNRES_{hx(last.pc)}';destname='indirect call'
            else:dest='X_'+hx(last.target);destname='$'+hx(last.target)
            externals[dest]=dict(id=dest,kind='call',address=hx(last.target),label=destname,subtitle='call target',lines=[])
            edges.append(dict(source=src,target=dest,kind='call',site=hx(last.pc),proven=last.target in an.routines))
        if last.op=='JMP' and last.target is None:
            dest=f'X_UNRES_{hx(last.pc)}';externals[dest]=dict(id=dest,kind='unresolved',address='?',label='indirect jump',subtitle='target unresolved',lines=[])
            edges.append(dict(source=src,target=dest,kind='indirect_jump',site=hx(last.pc),proven=False))
    nodes+=list(externals.values())
    return {'nodes':nodes,'edges':edges,'boundaries':[hx(x) for x in sorted(boundaries)],'entry':hx(entry),'mode':'routine'}

def global_graph(an):
    nodes=[];edges=[]
    for entry,r in sorted(an.routines.items()):
        nodes.append(dict(id='R'+hx(entry),kind='routine',address=hx(entry),label='$'+hx(entry),subtitle=f'{len(r["pcs"])} instructions',lines=[]))
    for c in an.calls:
        if c['target']=='?':continue
        for owner in c['owners'].split(';'):
            if owner and int(c['target'],16) in an.routines:
                edges.append(dict(source='R'+owner,target='R'+c['target'],kind='call',site=c['pc'],proven=True))
    for d in an.dispatch:
        did='T'+d['table']
        if not any(n['id']==did for n in nodes):nodes.append(dict(id=did,kind='dispatch',address=d['table'],label='TABLE $'+d['table'],subtitle='dispatch table',lines=[]))
        dest='R'+d['target']
        if int(d['target'],16) in an.routines:edges.append(dict(source=did,target=dest,kind='slot '+str(d['slot']),site=d['table'],proven=d['status']=='rooted'))
        for site in d['load_sites'].split(';'):
            if not site:continue
            for entry,r in an.routines.items():
                if int(site,16) in r['pcs']:
                    row=dict(source='R'+hx(entry),target=did,kind='dispatch use (candidate)',site=site,proven=False)
                    if row not in edges:edges.append(row)
    for v in an.vectors:
        vid='V'+v['vector'];dest='R'+v['target']
        nodes.append(dict(id=vid,kind='vector',address=v['vector'],label=v['name'],subtitle='$'+v['vector'],lines=[]))
        if int(v['target'],16) in an.routines:edges.append(dict(source=vid,target=dest,kind='vector',site=v['vector'],proven=True))
    return {'nodes':nodes,'edges':edges,'entry':'global','mode':'global'}
