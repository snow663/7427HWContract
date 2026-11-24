"""Replay scoped Rev B CS, ALDL and shadow-store evidence without a private BIN."""
import sys,json,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import verify_revb_xdf_labels as witness
from explain_revb_bin import SHA
import csv
from factory_rom_decode import decode
parser=argparse.ArgumentParser(description='Bounded current-ROM instruction witnesses; no physical hardware modeling.')
group=parser.add_mutually_exclusive_group(required=True)
group.add_argument('--rom',type=Path)
group.add_argument('--check-recorded',action='store_true')
parser.add_argument('--output',type=Path)
args=parser.parse_args()
DATA=ROOT/'maps/maintenance/revb_cs_decode'
if args.rom:
 im=args.rom.read_bytes();assert len(im)==65536 and hashlib.sha256(im).hexdigest()==SHA
else:
 evidence=json.loads((DATA/'EVIDENCE.json').read_text())
 assert evidence['image_sha256']==SHA
 im=bytearray(65536)
 for span in evidence['spans']:
  lo,hi=int(span['start'],16),int(span['end_exclusive'],16)
  data=bytes.fromhex(span['bytes']);assert len(data)==hi-lo
  im[lo:hi]=data
 # Recorded scope is deliberately local: this does not rerun the complete
 # 132-entry abstract scan or establish the hash of the absent full image.
 assert im[0x7100:0x710d]==bytes.fromhex('8e03ffce10008603a73dce3000')
 assert im[0x71c6:0x71cd]==bytes.fromhex('b6303f810b2705')
 assert im[0xf3ed]==0x39

class Record(witness.Memory):
 def write8(self,a,v):
  a&=65535;v&=255;self.writes.append((a,v));self.mem[a]=v
witness.Memory=Record
m,c,pcs=witness.execute(im,0x7100,{0x710a});assert(0x103d,3)in m.writes
init={'entry':'7100','stop':'710A','writes':[{'address':f'{a:04X}','value':f'{v:02X}'}for a,v in m.writes if a>=0x1000]}
m,c,pcs=witness.execute(im,0xcc7c,{0xccc0},x=0x3000)
expected={0x305c:0,0x303c:0x15,0x305d:0xac,0x305f:0xcb,0x305e:0}
for a,v in expected.items():assert(a,v)in m.writes
setup={'entry':'CC7C','X':'3000','stop':'CCC0','writes':[{'address':f'{a:04X}','value':f'{v:02X}'}for a,v in m.writes if a>=0x3000]}
cases=[]
for mode in(0,8):
 for x in (0x0fff,0x1000,0x1001,0x17ff,0x1800,0x1fff,0x2000,0x2fff,0x3000,0x305f,0x3060,0x37ff,0x3800,0x3fc0,0x3fff,0x4000,0xffff):
  b=witness.fresh(im);b[0x50]=mode
  m,c,pcs=witness.execute(b,0xf8b8,{0xf8ca,0xf8dc},x=x)
  expected_x=x&0xcfff if 0x1000<=x<=0x3fff and not mode else x
  assert c.s.x==expected_x
  cases.append({'encoded':f'{x:04X}','RAM0050_3':bool(mode),'actual_cpu_address':f'{c.s.x:04X}','word_source':c.s.pc==0xf8ca})
b=witness.fresh(im);b[0x4b]=0x90;b[0x4c]=0x1c;b[0x4e]=0xa5;b[0x3060]=0x65;b[0x3064]=0x26
m,c,pcs=witness.execute(b,0xf400,{0xf41f})
assert m.mem[0x3060]==0x90 and m.mem[0x4b]==0xf5 and m.mem[0x3062]==0x1c and m.mem[0x4d]==0x26 and m.mem[0x3067]==0xa5
shadow={'entry':'F400','stop':'F41F','board_writes':[{'address':f'{a:04X}','value':f'{v:02X}'}for a,v in m.writes if a>=0x3000],'final_ram':{f'{a:04X}':f'{m.mem[a]:02X}'for a in(0x4b,0x4d)}}
bit_cases=[]
for flag in(0,128):
 b=witness.fresh(im);b[0x72]=flag;witness.put(b,0x3ffc,0xa55a)
 m,c,pcs=witness.execute(b,0xf3ee,{0xf400})
 expected=(0xa55a&~8) if flag else(0xa55a|8)
 assert witness.word(m.mem,0x3ffc)==expected
 bit_cases.append({'RAM0072':f'{flag:02X}','initial_word':'A55A','result_word':f'{expected:04X}'})
report={'image_sha256':SHA,'init':init,'cpu_setup':setup,'aldl_address_cases':cases,'shadow_flush':shadow,'shared_word_bit_cases':bit_cases,'scope':'Executes actual emitted HC11 instructions against a controlled byte-memory fixture. Does not model physical INIT relocation, chip-select pins, EEPROM, peripheral response or board aliases.'}
if args.output:
 args.output.write_text(json.dumps(report,indent=2)+'\n')
else:
 assert report==json.loads((DATA/'EXECUTION_WITNESSES.json').read_text()), 'Stale instruction witnesses'
if args.rom:assert args.rom.read_bytes()==im
# Match each extracted store to an actual fixture transaction and decoded opcode.
with (DATA/'CS_EN_WRITES.csv').open(newline='')as stream:
 for row in csv.DictReader(stream):
  pc=int(row['pc'],16);i=decode(lambda a,n:im[a:a+n],pc)
  assert i.data.hex(' ')==row['bytes'] and (i.op+' '+i.operand)==row['operation']
  writes=report['init']['writes']if pc==0x7108 else report['cpu_setup']['writes']
  assert {'address':row['address'],'value':row['value']}in writes

with (DATA/'ADDRESS_WINDOWS.csv').open(newline='')as stream:
 for row in csv.DictReader(stream):
  assert int(row['end'],16)-int(row['start'],16)+1==int(row['size_bytes'])
next_address=0
with (DATA/'EFFECTIVE_EXPECTED_MAP.csv').open(newline='')as stream:
 for row in csv.DictReader(stream):
  assert int(row['start'],16)==next_address
  next_address=int(row['end'],16)+1
  assert next_address-int(row['start'],16)==int(row['size_bytes'])
  assert row['assumption']
assert next_address==65536
with (DATA/'ALDL_ADDRESS_MAPPING.csv').open(newline='')as stream:
 for row in csv.DictReader(stream):
  selected=[c for c in cases if c['encoded']==row['encoded']]
  assert len(selected)==2
  for case in selected:
   expected=row['with_0050_bit3_set']if case['RAM0050_3']else row['normal_cpu_address']
   assert case['actual_cpu_address']==expected
scan=json.loads((DATA/'INDEXED_SCAN.json').read_text())
assert scan['image_sha256']==SHA
assert set(scan['config_target_may_writes'])=={'7108','CC89','CCA3','CCA7','CCAB','CCAF'}
assert scan['initializer_calls'] and all(c['X']=='$3000'for c in scan['initializer_calls'])
print('INIT/setup,34 ALDL address cases,board-shadow publication and2 shared-word bit cases passed; no physical-device inference.')
