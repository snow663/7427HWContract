"""Trace conservative current-image indexed write contexts; never writes a BIN."""
import sys,json,hashlib,argparse
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from explain_revb_bin import sweep,SHA
from factory_rom_decode import successors
from factory_state_flow import analyze
from build_factory_state_flow import clear_override,target_bytes
parser=argparse.ArgumentParser(description='Trace normal-return indexed write contexts in exact Rev B; run from the repository root.')
parser.add_argument('--rom',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
im=args.rom.read_bytes()
assert len(im)==65536 and hashlib.sha256(im).hexdigest()==SHA, 'Requires exact released Rev B'
class ROM:
 def read(self,a,n):
  assert 0x4000<=a and a+n<=65536,(a,n)
  return im[a:a+n]
 def word(self,a):return int.from_bytes(self.read(a,2),'big')
rom=ROM();ins,frontiers,roots=sweep(im);table=[rom.word(0x7a85+2*i)for i in range(16)]
entries=set(roots)|{0x7100}|{i.target for i in ins.values()if i.op in ('JSR','BSR')and i.target in ins}
functions={}
for entry in sorted(entries):
 pending=[entry];local={}
 while pending:
  pc=pending.pop()
  if pc in local:continue
  local[pc]=ins[pc];pending.extend(t for t,_ in successors(ins[pc])if t in ins)
 functions[entry]=local
graph={e:{i.target for i in f.values()if i.op in ('JSR','BSR')and i.target in entries}for e,f in functions.items()}
for e,f in functions.items():
 if 0x7a4f in f:graph[e].update(table)
order=[];active=set();done=set()
def visit(e):
 if e in active:raise ValueError(f'Recursion {e:04X}')
 if e in done:return
 active.add(e)
 for x in sorted(graph[e]):visit(x)
 active.remove(e);done.add(e);order.append(e)
for e in sorted(entries):visit(e)
summaries={};effects=defaultdict(list);calls=[]
for e in order:
 s=analyze(rom,e,functions[e],summaries,table,clear_override);summaries[e]=s
 for effect in s.effects.values():
  if 'W' not in effect.access:continue
  resolved=target_bytes(effect)
  if resolved&{0x103d,0x303d,0x305c,0x305d,0x305e,0x305f,0x303c,0x303f}:
   effects[effect.pc].append({'entry':f'{e:04X}','expression':effect.address.text(),'target_bytes':[f'{a:04X}'for a in sorted(resolved)],'via':effect.via})
 for pc,(dest,binding)in s.calls.items():
  if dest.singleton()==0xcc7c:calls.append({'entry':f'{e:04X}','pc':f'{pc:04X}','X':binding['X'].text()})
local_indexed=defaultdict(set)
for e,s in summaries.items():
 for effect in s.local.values():
  if effect.pc in ins and ins[effect.pc].access()and ins[effect.pc].access()['address']is None and 'W'in effect.access:
   local_indexed[effect.pc].add(effect.address.text())
report={'image_sha256':SHA,'functions_analyzed':len(functions),'config_target_may_writes':{f'{p:04X}':r for p,r in sorted(effects.items())},'initializer_calls':calls,'indexed_write_contexts':{f'{p:04X}':sorted(v)for p,v in sorted(local_indexed.items())},'scope':'Conservative abstract normal-return effects; fixed and bounded destinations only. Unknown/formal indexed pointers, interrupts, stack corruption and hardware aliases remain qualified.'}
args.output.write_text(json.dumps(report,indent=2)+'\n')
assert args.rom.read_bytes()==im
print(json.dumps({'functions':len(functions),'register_writer_sites':list(report['config_target_may_writes']),'indexed_write_sites':len(local_indexed),'initializer_calls':calls}))
