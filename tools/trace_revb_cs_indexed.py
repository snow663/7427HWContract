"""Trace conservative current-image indexed write contexts; never writes a BIN."""
import sys,json,hashlib,argparse
from pathlib import Path
from collections import defaultdict
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from explain_revb_bin import SHA
from build_factory_state_flow import target_bytes
parser=argparse.ArgumentParser(description='Trace normal-return indexed write contexts in exact Rev B; run from the repository root.')
parser.add_argument('--rom',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
im=args.rom.read_bytes()
assert len(im)==65536 and hashlib.sha256(im).hexdigest()==SHA, 'Requires exact released Rev B'
from revb_access_flow import analyze_image
flow=analyze_image(im)
ins=flow['instructions'];functions=flow['functions'];summaries=flow['summaries']
effects=defaultdict(list);calls=[]
for e,s in summaries.items():
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
