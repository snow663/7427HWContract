"""Extract current Rev B relocation/chip-select operands and qualified address maps."""
import sys,json,csv,hashlib,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from explain_revb_bin import sweep,SHA
from factory_rom_decode import decode

parser=argparse.ArgumentParser(description='Extract exact Rev B CS writes, address windows and shadow paths; run from repository root.')
parser.add_argument('--rom',type=Path,required=True)
parser.add_argument('--output-dir',type=Path,required=True)
args=parser.parse_args();out=args.output_dir
out.mkdir(parents=True,exist_ok=True)
image=args.rom.read_bytes()
assert len(image)==65536 and hashlib.sha256(image).hexdigest()==SHA
ins,frontiers,roots=sweep(image)
# These are actual current-image spans, not HAC text operands.
assert image[0x7100:0x710d]==bytes.fromhex('8e03ffce10008603a73dce3000')
assert image[0x71c6:0x71cd]==bytes.fromhex('b6303f810b2705')
rows=[]
rows.append(dict(pc='7108',bytes=ins[0x7108].data.hex(' '),operation='STAA $3D,X',address='103D',value='03',register='INIT',meaning='RAM page 0; CPU-register page 3',context='X=1000 from7103; A=03 from7106'))
a=b=None;x=0x3000
for pc,i in sorted(ins.items()):
 if not 0xcc7c<=pc<0xccc1:continue
 if i.op=='CLRA':a=0
 elif i.op=='LDAA'and i.mode=='immediate':a=i.value
 elif i.op=='LDAB'and i.mode=='immediate':b=i.value
 elif i.op in ('LDX','PULX','INX','DEX','ABX','XGDX'):raise AssertionError('Initializer no longer preserves X')
 elif i.op=='STAA':
  address=(x+i.value)&65535 if i.mode=='indexed_x'else i.value
  if address in (0x305c,0x305d,0x305e,0x305f,0x303c):
   name,meaning={0x305c:('CSSTRH','All four programmed stretch fields zero'),0x305d:('CSCTL','IO1/IO2/program enabled; GEN priority; program size64K'),0x305e:('CSGADR','General-select base0000'),0x305f:('CSGSIZ','GEN8K; active-low/address-valid; IO1/IO2 address-valid'),0x303c:('HPRIO','IRV bit4 set; write mode bits have normal-mode restrictions')}[address]
   rows.append(dict(pc=f'{pc:04X}',bytes=i.data.hex(' '),operation=(i.op+' '+i.operand),address=f'{address:04X}',value=f'{a:02X}',register=name,meaning=meaning,context='Caller711C establishes X=3000; straight-line immediate A'))
assert [(r['address'],r['value'])for r in rows]==[('103D','03'),('305C','00'),('303C','15'),('305D','AC'),('305F','CB'),('305E','00')]
def savecsv(name,items):
 with(out/name).open('w',newline='')as f:
  w=csv.DictWriter(f,fieldnames=list(items[0]),lineterminator='\n');w.writeheader();w.writerows(items)
savecsv('CS_EN_WRITES.csv',rows)
windows=[
 dict(resource='Internal RAM',start='0000',end='03FF',size_bytes=1024,enable='INIT.RAM=0',scope='F1-compatible internal resource'),
 dict(resource='Internal CPU registers',start='3000',end='305F',size_bytes=96,enable='INIT.REG=3',scope='Moved from1000..105F; not duplicated'),
 dict(resource='CSGEN nominal',start='0000',end='1FFF',size_bytes=8192,enable='CSGSIZ.GSIZE=3',scope='External selection; internal resources can override; fitted backing unknown'),
 dict(resource='CSIO1',start='3060',end='37FF',size_bytes=1952,enable='CSCTL.IO1EN=1',scope='External I/O selection'),
 dict(resource='CSIO2',start='3800',end='3FFF',size_bytes=2048,enable='CSCTL.IO2EN=1',scope='External I/O selection'),
 dict(resource='CSPROG nominal',start='0000',end='FFFF',size_bytes=65536,enable='CSCTL.PCSEN=1 PSIZ=0',scope='Selection before internal/IO/general precedence; not proof of64K fitted ROM'),
 dict(resource='Expected internal EEPROM overlay',start='0E00',end='0FFF',size_bytes=512,enable='Only if CONFIG live value0B and standard F1 EEPROM implemented',scope='Firmware compares against0B; it does not program CONFIG or capture its actual response in this BIN'),
 dict(resource='Program selection remainder1',start='2000',end='2FFF',size_bytes=4096,enable='From above decode and expected internal map',scope='Bus-select inference; backing response unknown'),
 dict(resource='Program selection remainder2',start='4000',end='FFFF',size_bytes=49152,enable='From above decode and expected internal map',scope='Supplied ROM code/calibration address region; physical chip wiring separate'),
]
savecsv('ADDRESS_WINDOWS.csv',windows)
effective=[
 dict(start='0000',end='03FF',size_bytes=1024,resource='Internal RAM'),
 dict(start='0400',end='0DFF',size_bytes=2560,resource='External GEN selection; backing unknown'),
 dict(start='0E00',end='0FFF',size_bytes=512,resource='Conditional internal EEPROM'),
 dict(start='1000',end='1FFF',size_bytes=4096,resource='External GEN selection; backing unknown'),
 dict(start='2000',end='2FFF',size_bytes=4096,resource='Program selection; backing unknown'),
 dict(start='3000',end='305F',size_bytes=96,resource='Internal CPU registers'),
 dict(start='3060',end='37FF',size_bytes=1952,resource='External IO1 selection'),
 dict(start='3800',end='3FFF',size_bytes=2048,resource='External IO2 selection'),
 dict(start='4000',end='FFFF',size_bytes=49152,resource='Program selection; supplied code/calibration/vector region'),
]
next_address=0
for row in effective:
 assert int(row['start'],16)==next_address
 next_address=int(row['end'],16)+1
 assert next_address-int(row['start'],16)==row['size_bytes']
 row['assumption']='Standard F1 internal resources and CONFIG live value0B; not a measured physical inventory'
assert next_address==65536
savecsv('EFFECTIVE_EXPECTED_MAP.csv',effective)
shadows=[
 dict(ram_source='004B bits90',target='3060 bits90',pc='F405/F407/F409',width_bits=8,operation='Masked output request;3060 input bits6F merged back into004B atF40C/F40D',category='Software shadow flush, not CPU remapping'),
 dict(ram_source='004C',target='3062',pc='F40F/F411',width_bits=8,operation='Full-byte shadow copy; retained IAC phase/enable fields share the byte',category='Software shadow flush, physical pin polarity separate'),
 dict(ram_source='004E',target='3067',pc='F419/F41B',width_bits=8,operation='Full-byte output shadow copy',category='Software shadow flush'),
 dict(ram_source='004D (destination)',target='3064 (source)',pc='F414/F417',width_bits=8,operation='Hardware sample copied back into RAM; reverse direction',category='Input mirror'),
 dict(ram_source='0072 bit7',target='3FFD bit3 within word3FFC',pc='F3F5/F3F7/F3FB/F3FD',width_bits=16,operation='Read-modify-write shared word; low-byte bit3 set when RAM bit7 clear, cleared when set',category='Derived shared hardware bit, not full-word RAM mirror'),
]
savecsv('SOFTWARE_SHADOWS.csv',shadows)
aldl=[]
for requested in (0x1000,0x1800,0x3000,0x3060,0x3fc0,0x4000):
 normal=requested&0xcfff if 0x1000<=requested<=0x3fff else requested
 aldl.append(dict(encoded=f'{requested:04X}',normal_cpu_address=f'{normal:04X}',with_0050_bit3_set=f'{requested:04X}',kind='Software reply address transform atF8C7; not physical address alias'))
savecsv('ALDL_ADDRESS_MAPPING.csv',aldl)
spans=[(0x7100,0x712b),(0x71c3,0x71d2),(0xcc7c,0xccc1),(0xf3ed,0xf420),(0xf8b8,0xf8de),(0xf5cf,0xf5dc)]
evidence={'image_sha256':SHA,'image_bytes':len(image),'rooted_instructions':len(ins),'control_frontiers':frontiers,'register_writes':rows,'config_compare':{'read_pc':'71C6','address':'303F','compare_pc':'71C9','expected':'0B','actual_live_value':'Not present in BIN; compared at runtime'},'spans':[{'start':f'{a:04X}','end_exclusive':f'{z:04X}','bytes':image[a:z].hex(' ')}for a,z in spans],'source':'Exact Rev B image; NXP MC68HC11F1 technical data sections4.2/4.3/4.5 for conditional decode interpretation','reference':'https://www.nxp.com/docs/en/data-sheet/MC68HC11F1.pdf','scope':'CPU decode and instruction/software-shadow extraction; board-level aliases/device population not inferred.'}
(out/'EVIDENCE.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('6 relocation/CS/visibility writes,9 nominal/conditional range rows,9 expected-map regions,5 software shadow paths,6 ALDL examples extracted from exact Rev B.')

assert args.rom.read_bytes()==image
