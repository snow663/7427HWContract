"""Generate a whole-image plain-English reader for exact Rev B; never writes a BIN.

Every rooted instruction is decoded from the actual image. Semantic address
names are reference metadata, not proof that every inherited label is correct.
Local flag provenance is reset at control-flow joins and opaque calls.
"""
from __future__ import annotations
import argparse, csv, hashlib, html, io, json, re, textwrap
from collections import Counter, defaultdict
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
import xml.etree.ElementTree as ET
from factory_rom_decode import decode, WORDS
from trace_manual_idle import sweep
from manual_idle_asm import assemble

ROOT=Path(__file__).resolve().parents[1]
SHA='e75fa886318f477c3c95001740ded92f5b2f40692a3aa82b67d4249cf943fdb1'
ISA='https://www.nxp.com/docs/en/reference-manual/M68HC11ERG.pdf'
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
CHAPTERS=[
 ('01','Reset, interrupts and main scheduling',0x7100,0x7aa6,'Reset reaches 7100 through the reset vector/trap entry. This area sets up CPU state, initializes outputs and RAM, handles reference/timer interrupts, and repeatedly admits the main engine work and 16 background slots.'),
 ('02','Scheduled engine work and input preparation',0x7aa6,0x7d4b,'The dispatcher calls the slot entries here. Retained slot work acquires or prepares engine inputs and state. Removed transmission/emissions slots can be immediate returns. A returning slot is a real operation, not missing documentation.'),
 ('03','Fuel calculation, injection and oxygen feedback',0x7d4b,0x8eb4,'Follow admission, cranking versus running, transient enrichment, VE/base pulse, trims, fuel cut, packet delivery and the O2/BLM controller. BLM is multiplicative; INT/P is converted to a signed additive pulse correction. A zero at one intermediate stage does not by itself prove final fuel cut.'),
 ('04','Retained engine input and housekeeping paths',0x8eb4,0x91a3,'These retained address slices perform engine input/housekeeping work around the former shared engine/transmission allocation. The exact surviving calls and stores below govern this modified image.'),
 ('05','IAC driver and the new single idle controller',0x91a3,0xa466,'The actuator guard, service and motor-conversion paths remain. The replacement uses one target, one runtime learned baseline, bounded P/I, cold/start air and a TPS follower. The new deceleration-spark gate is allocated inside the vacated strategy area, so address order alone does not imply idle-controller ownership.'),
 ('06','Spark command and output construction',0xa466,0xaca7,'Build the single base-table command, environmental/startup/knock terms, deceleration correction, signed limits, service edits and output timing. A limit before service edits is not necessarily the final possible limit. The disconnected old idle/transient spark block is not decoded as live code.'),
 ('07','Other retained middle-ROM helpers',0xaca7,0xc900,'Only rooted surviving instructions are listed. Large retired transmission allocations in this address range are accounted for by the byte ledger rather than translated into fictitious instructions.'),
 ('08','Sensors, environmental terms and knock learning',0xc900,0xe2fb,'This area includes coolant/MAT and other retained acquisition, environmental calculations, A/C inputs and adaptive knock work. Indexed table accesses use caller-supplied coordinates; they are not fixed RAM variables simply because a pointer is visible.'),
 ('09','Startup fuel, background acquisition and permissions',0xe2fb,0xf245,'Retained slow work includes injector offset, startup enrichment, coolant-dependent admission and engine/service preparation. Existing startup and deceleration owners can share state; a shared word must not be relabeled as belonging to only one path.'),
 ('10','ADC, retained-memory and numeric helpers',0xf245,0xf5e8,'These helpers multiplex/read ADC channels, reset or clamp retained state, manipulate board state, and perform fixed-point lags, interpolation, division and multiplication. Register input/output and rounding order matter.'),
 ('11','ALDL, service, traps and exceptional paths',0xf5e8,0xfc45,'Serial polling, receive/transmit IRQ work and session/service handling live here, together with exceptional vector targets. Normal data can be fetched through ROM-held RAM-address pointers. A diagnostic/trap entry being reachable in a static graph does not mean it occurs in normal driving.'),
 ('12','High-ROM custom fuel-policy and classifier hooks',0xfc45,0xffc0,'Most of this address area is conversion/calibration data. The live instructions here are the custom open-loop policy, BLM/INT hooks, target-relative fuel idle classifier and related retained hooks. Data bytes between them are not instructions.'),
 ('13','Relocated engine-only helpers',0x4000,0x7100,'These executable helpers occupy former low-ROM calibration space. They normalize TPS and retain selected engine/board housekeeping after the engine-only separation. They must not be exposed as editable calibration tables.')]

CUSTOM={
 0x5bd0:('Engine-only initialization and output cleanup','Clear the removed subsystem states and initialize the retained output/register shadows. Existing board-write identities remain subject to the hardware contract.'),
 0x5c8a:('Retained slow O2 filter','Filter the O2 input through the retained gain and publish its word state.'),
 0x5c9a:('Engine TPS normalization','Round the learned zero, subtract it from raw TPS with a zero floor, apply the normalization gain, saturate, and return normalized TPS in A. The caller publishes 01D9.'),
 0x5cbb:('TPS-zero learning guard','Qualify or update the learned TPS-zero word without restoring the removed transmission consumer.'),
 0x5cd0:('Retained engine service sequence','Call the retained engine input/service routines in their existing order.'),
 0x7100:('Reset and boot setup','Set the stack and initial CPU/register mapping, establish startup state and continue through engine/board initialization into the scheduler.'),
 0x74ea:('Reference-event interrupt','Service an engine reference event. Event timing, crank/run state and fuel/spark publication share state with normal scheduled work.'),
 0x793d:('Timer interrupt','Service periodic timer work and publish its shared scheduling state before returning from the interrupt.'),
 0x7d4b:('Main fuel task','Update ignition/input state, authorize calculation, choose crank/running behavior and construct/deliver the fuel command.'),
 0x91a3:('IAC actuator step service','Apply the retained voltage/admission checks, position/direction/phase logic and ordered actuator-shadow writes.'),
 0x920e:('Retained auxiliary IAC output flags','Update the retained auxiliary actuator/converter flags. The removed Park/Drive learning strategy is separate.'),
 0x93d0:('Main IAC admission and homing/service guard','Preserve actuator homing/service conditions and admit the single controller at its retained scheduling phase.'),
 0x983d:('Air-command to IAC-position conversion','Apply the retained BARO and auxiliary-output treatment, then map the air coordinate to the software IAC position target.'),
 0x9411:('Stopped/cranking idle setup','Initialize the single controller, calculate the common target, compose starting air and enter the retained air-to-position converter.'),
 0x9537:('Running idle controller','Ensure initialization, update the target/follower/start-air fade, classify capture, calculate P/I and compose the requested air command.'),
 0x989c:('Single idle initialization','Seed the one integral word, clear follower/history state, load startup-air timing and mark the controller initialized. Learning does not persist across this reset.'),
 0x98e3:('Common requested idle speed','Look up the FF60 curve using native coolant index0283, slew a falling request and publish the target and stall boundary. Service override is a separate branch.'),
 0x9913:('Throttle follower','Calculate air from TPS above the closed-throttle band, cap the result and decay the retained follower when the new demand falls.'),
 0x9951:('Proportional and integral idle correction','Apply deadband, bounds, qualification and freeze/anti-windup gates. Closed-throttle overspeed P can shed air before capture; learning remains gated.'),
 0x99fb:('Compose idle air and IAC-change fuel enrichment','Combine bounded baseline, cold/start/A/C/P/stall terms, publish pre-follower air-change enrichment, add follower, and continue to the retained converter.'),
 0x9e99:('Background idle target publisher','Publish the same single-controller target through the retained background entry.'),
 0xa2b0:('Retired slow idle strategy entry','Return immediately. The old slow Park/Drive strategy does not run here.'),
 0x9f40:('Rev B deceleration-spark gate','Apply the old DFCO subtraction only during active fuel cut above idle target plus the shared margin. Otherwise clear the saved subtraction/latch without clearing the startup-shared word.'),
 0xa466:('Main spark task','Prepare load and timing inputs, select the retained normal/alternate path, build the command and publish the required output sequence.'),
 0xf436:('16-bit lag helper','Apply a word-state lag using its existing fixed-point and rounding order.'),
 0xf459:('Byte-input lag helper','Apply a byte input/gain to a retained fractional word state. The high byte and fractional remainder remain distinct.'),
 0xf4b6:('Scaled one-dimensional lookup','Preserve the input registers required by this ABI, load the coordinate scale from the table header and interpolate between neighboring bytes.'),
 0xf4bd:('Offset/clamped one-dimensional lookup','Subtract the input offset with a zero floor, then enter the ordinary 16-knot-coordinate interpolation helper.'),
 0xf4c1:('One-dimensional interpolation','Use the byte coordinate to select two neighboring knots, preserve the sign of their difference and apply the existing integer rounding.'),
 0xf4de:('Two-dimensional interpolation','Use the supplied table header and two coordinates to interpolate the byte surface. Header arithmetic and endpoint neighbors are significant.'),
 0xff2e:('Custom load/TPS PE admission helper','Test the custom load threshold or return the TPS comparison used by the PE caller.'),
 0xff40:('Custom OL policy gate','The global OL bit takes precedence; the closed-throttle bit uses TPS<=FF8B without an RPM-capture check. Normal CL admission continues when neither policy forces OL.'),
 0xfec0:('Global-OL BLM substitution','Select neutral multiplicative BLM when the global OL flag is set; otherwise retain the selected learned value.'),
 0xfee0:('Global-OL INT-derived correction handling','Clear the signed additive correction under global OL; otherwise retain the normal signed INT/P encoding.'),
 0xfef8:('Target-relative fuel idle classification','Apply separate entry/retention TPS limits and requested-RPM-relative hysteresis, then enter the retained idle-AFR or off-idle continuation.')}

NOTES={
 0x9a44:'Save the current pre-follower air command for later restoration.',
 0x9a47:'Subtract the previous pre-follower command to obtain the air-command change.',
 0x9a4a:'If the command decreased, go to the zero-enrichment path at $9A6F.',
 0x9a4c:'Save the whole-unit part of the positive air-command increase.',
 0x9a4f:'Load normalized TPS. This is the throttle input, not the air-command change.',
 0x9a52:'Compare normalized TPS with the IAC-change enrichment cutoff at $50A9.',
 0x9a55:'If TPS is at or above the cutoff, take the zero-enrichment path.',
 0x9a57:'Restore the whole-unit air-command increase after the TPS comparison.',
 0x9a5a:'Compare the increase with the minimum normalized air-command change at $50A8.',
 0x9a5d:'If the increase is below that minimum, take the zero-enrichment path.',
 0x9a67:'Point X to the retained IAC-change enrichment lookup header.',
 0x9a6a:'Look up the IAC-change fuel term using the scaled positive command change.',
 0x9a6f:'Select zero IAC-change enrichment.',
 0x9a70:'Publish the IAC-change enrichment byte at $087F.',
 0x84bc:'Load the corrected base pulse width from $024E before final synchronous shaping.',
 0x84cd:'Compare the nonzero pulse with $0100; only shorter pulses enter the short-pulse lookup.',
 0x84d6:'Select the short-pulse added-correction table. The synchronous path uses it regardless of the async shaping option.',
 0x84de:'Add the lookup correction to the original corrected pulse width.',
 0x84e1:'Subtract the short-pulse bias word. This is subtraction, not addition.',
 0x84e9:'Compare the shaped pulse with the synchronous minimum threshold at $496D.',
 0x84ef:'Mark the pulse as requiring the synchronous replacement.',
 0x84f2:'Load the replacement pulse from $496F; this is distinct from the comparison threshold.',
 0x84f5:'Publish the selected pulse before the voltage-dependent byte offset is added.',
 0x8508:'Publish the final timer-pulse word after the offset and the existing $7FFF limit.',
 0x855a:'Select the same short-pulse table for the option-qualified asynchronous path.',
 0x8564:'Subtract the shared short-pulse bias in the asynchronous helper.',
 0x8569:'On asynchronous subtraction borrow, select zero rather than the synchronous replacement.',
 0xf888:'Read an indirect data-source pointer from this descriptor. For the discussed channel, the word at $5216 points to RAM $024A.',
 0xf8dc:'Fetch the byte at the selected source address for the serial reply; this reads data, it does not set the requested AFR.',
 0x7f95:'Compare normalized TPS with shared closed-throttle limit $FF8B, not the old $48DA VE threshold.',
 0x7fa4:'Compare the coarse RPM coordinate with raw $48 (nominally 1800 RPM).',
 0x7faa:'Select the main VE table header at $49D5.',
 0x7fbd:'Select the lower-RPM closed-throttle VE table header at $4A88; IAC capture is not tested here.',
 0xaafe:'Compare normalized TPS with the shared low-TPS threshold used to select the DFCO spark floor.',
 0xab03:'Load the signed DFCO lower-angle bound from $4148.',
 0xab0e:'Load the signed normal lower-angle bound from $4146.',
 0xab17:'Apply the selected signed lower-angle bound. Later service edits can still change the command.',
 0xc9bc:'Publish the native coolant lookup index: coolant byte minus16, floored at0 and capped at192.',
 0x98a0:'Seed the single runtime integral word with zero fractional byte.',
 0x98ed:'Interpolate the common requested-idle RPM curve using native coolant index $0283.',
 0x98fd:'Publish the common requested idle-RPM coordinate at $0857.',
 0x9916:'Subtract the IAC release-TPS threshold to establish the follower closed-throttle band.',
 0x9f40:'If fuel-cut flag $0046.3 is clear, go to the Rev B spark-cleanup path.',
}

ROLE_OVERRIDES={0x4eb6:'minimum battery-voltage sample for IAC operation',0x004c:'shared IAC/output shadow; former transmission role removed',0x50a8:'minimum normalized air-command increase for IAC AE',0x50a9:'normalized-TPS cutoff for IAC-change AE',0x4971:'shared short-pulse subtraction word',0x496d:'synchronous minimum-pulse comparison threshold',0x496f:'synchronous replacement pulse',0x5216:'ALDL source-address pointer for commanded AFR',0x48da:'shared low-TPS threshold for filter/BLM/spark-floor consumers',0xff8b:'shared fuel-idle/VE/optional-OL normalized-TPS limit',0x4146:'signed normal lower spark-angle bound',0x4148:'signed DFCO lower spark-angle bound'}

def read_workbook(path):
    result={}
    with ZipFile(path)as z:
        strings=[''.join(s.itertext())for s in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',NS)]
        for n,s in enumerate(ET.fromstring(z.read('xl/workbook.xml')).findall('m:sheets/m:sheet',NS),1):
            rows=[]
            for row in ET.fromstring(z.read(f'xl/worksheets/sheet{n}.xml')).findall('.//m:sheetData/m:row',NS)[1:]:
                v=['','','']
                for c in row.findall('m:c',NS):
                    k=ord(c.get('r')[0])-65;t=c.find('m:v',NS)
                    if k<3:v[k]=strings[int(t.text)]if c.get('t')=='s'else(t.text if t is not None else '')
                if v[0].startswith('$'):rows.append(v)
            result[s.get('name')]=rows
    return result


def role_maps():
    names={};bits={};sources=[]
    for filename in('7427_Address_Register_0.3.12.xlsx','7427_Write_Register_0.3.12.xlsx'):
        for sheet,rows in read_workbook(ROOT/filename).items():
            for address,oem,current in rows:
                a,*b=address[1:].split('.');key=int(a,16)
                name=current if current and current!='omitted'else oem
                if current=='omitted':name+=' (retired operational role; reset/shared access may remain)'
                if b:bits.setdefault((key,int(b[0])),name)
                else:names.setdefault(key,name)
        sources.append(dict(path=filename,sha256=hashlib.sha256((ROOT/filename).read_bytes()).hexdigest()))
    names.update(ROLE_OVERRIDES)
    return names,bits,sources


def short(text,limit=110):
    return text if len(text)<=limit else text[:limit-1]+'…'


class English:
    def __init__(self,names,bits):self.names=names;self.bits=bits;self.reset()
    def reset(self):
        self.reg={x:x for x in('A','B','D','X','Y','SP')};self.ptr={};self.flags={};self.last=None
    def name(self,a):return f'${a:04X}'+(' ('+self.names[a]+')'if a in self.names else' (role unresolved)')
    def operand(self,i):
        if i.mode=='immediate':return f'{i.value} (hex ${i.value:X})'
        if i.mode.startswith('indexed_'):
            r=i.mode[-1].upper()
            if r in self.ptr:return self.name((self.ptr[r]+i.value)&65535)+f' through {r}+{i.value}'
            return f'the memory location {i.value} byte(s) beyond the address in {r}'
        return self.name(i.value)if i.value is not None else''
    def label(self,i):
        if i.mode=='immediate':return f'${i.value:X}'
        if i.mode.startswith('indexed_'):
            r=i.mode[-1].upper()
            if r not in self.ptr:return f'memory at {r}+{i.value}'
            a=(self.ptr[r]+i.value)&65535
        else:a=i.value
        return short(self.names.get(a,f'memory ${a:04X}'),75)
    def nz(self,value,clear_c=False):
        self.flags['Z']=(f'{value} is zero',f'{value} is nonzero')
        self.flags['N']=(f'the high/sign bit of {value} is set',f'the high/sign bit of {value} is clear')
        self.flags.pop('signed',None);self.flags['V']=('signed overflow is set','signed overflow is clear')
        if clear_c:self.flags['C']=('carry/borrow is set','carry/borrow is clear')
    def setreg(self,r,value):
        self.reg[r]=short(value,95)
        if r=='D':
            self.reg['A']='high byte of '+short(value,65);self.reg['B']='low byte of '+short(value,65)
        elif r in('A','B'):self.reg['D']='word D (A followed by B)'
    def compare(self,left,right):
        self.flags={'C':(f'{left} is below {right} (unsigned)',f'{left} is at least {right} (unsigned)'),
                    'Z':(f'{left} equals {right}',f'{left} differs from {right}'),
                    'N':(f'the high/sign bit of {left} minus {right} is set',f'the high/sign bit of {left} minus {right} is clear'),
                    'signed':(left,right)}
    def describe(self,i):
        op=i.op;arg=self.operand(i);label=self.label(i)if i.value is not None else'';text=''
        if op.startswith('LD'):
            r={'LDAA':'A','LDAB':'B','LDD':'D','LDX':'X','LDY':'Y','LDS':'SP'}[op]
            text=f'Load {arg} into '+('word 'if r in('D','X','Y','SP')else'byte ')+r+'.'
            self.setreg(r,label);self.nz(label)
            if r in('X','Y'):
                if i.mode=='immediate':self.ptr[r]=i.value
                else:self.ptr.pop(r,None)
        elif op in('STAA','STAB','STD','STX','STY','STS'):
            r={'STAA':'A','STAB':'B','STD':'D','STX':'X','STY':'Y','STS':'SP'}[op]
            text=f'Store {self.reg[r]} from {r} into {arg}.'
            if r in('D','X','Y','SP'):text+=' Store the high byte first and the low byte at the next address.'
            self.nz(self.reg[r])
        elif op in('CMPA','CMPB','CPD','CPX','CPY','CBA'):
            r={'CMPA':'A','CMPB':'B','CPD':'D','CPX':'X','CPY':'Y','CBA':'A'}[op]
            right=self.reg['B']if op=='CBA'else label;left=self.reg[r]
            text=f'Compare {left} with {right}, updating the result flags without changing either value.'
            self.compare(left,right)
        elif op in('BRSET','BRCLR','BSET','BCLR'):
            labels=[]
            if i.mode in('direct','extended'):
                labels=[self.bits.get((i.value,n),f'bit{n}')for n in range(8)if i.mask&(1<<n)]
            mask=f'bits selected by mask ${i.mask:02X}'+(' ['+'; '.join(labels)+']'if labels else'')
            if op.startswith('BR'):
                state='all set'if op=='BRSET'else'all clear'
                text=f'If {mask} in {arg} are {state}, continue at ${i.target:04X}; otherwise continue at ${i.next_pc:04X}. This test leaves the condition flags unchanged.'
            else:
                text=f"{'Set'if op=='BSET'else'Clear'} {mask} in {arg}, preserving every unselected bit."
                self.nz('the updated byte')
        elif op.startswith('B')and op not in('BITA','BITB','BSR'):
            if op=='BRA':text=f'Continue unconditionally at ${i.target:04X}.'
            elif op=='BRN':text=f'Do not take this branch; continue at ${i.next_pc:04X}.'
            else:
                defaults={'BCC':'carry/borrow is clear','BCS':'carry/borrow is set','BEQ':'the zero flag is set','BNE':'the zero flag is clear','BMI':'the sign bit is set','BPL':'the sign bit is clear','BHI':'carry and zero are both clear (unsigned higher)','BLS':'carry or zero is set (unsigned lower or equal)','BLT':'N differs from V (signed less)','BGE':'N equals V (signed at least)','BGT':'Z is clear and N equals V (signed greater)','BLE':'Z is set or N differs from V (signed at most)','BVC':'the overflow flag is clear','BVS':'the overflow flag is set'}
                condition=defaults[op]
                key={'BCC':('C',1),'BCS':('C',0),'BEQ':('Z',0),'BNE':('Z',1),'BMI':('N',0),'BPL':('N',1)}.get(op)
                if key and key[0]in self.flags:condition=self.flags[key[0]][key[1]]
                if 'signed'in self.flags:
                    a,b=self.flags['signed'];relations={'BLT':'less than','BGE':'at least','BGT':'greater than','BLE':'at most'}
                    if op in relations:condition=f'{a} is {relations[op]} {b} using a signed comparison'
                    if op=='BHI':condition=f'{a} is greater than {b} (unsigned)'
                    if op=='BLS':condition=f'{a} is at most {b} (unsigned)'
                text=f'If {condition}, continue at ${i.target:04X}; otherwise continue at ${i.next_pc:04X}.'
        elif op in('JMP','JSR','BSR'):
            target=i.target if i.target is not None else i.value
            dest=arg if i.mode.startswith('indexed_')else f'${target:04X}'
            if op=='JMP':text=f'Continue at {dest} without saving a subroutine return address.'
            else:
                text=f'Call {dest}, saving ${i.next_pc:04X} as the return address.'
                if target in CUSTOM:text+=' '+CUSTOM[target][0]+'.'
                if target in(0xf4b6,0xf4bd,0xf4c1,0xf4de)and'X'in self.ptr:text+=' Table pointer on entry: '+self.name(self.ptr['X'])+'.'
                self.reg={x:x for x in self.reg};self.ptr={};self.flags={}
        elif op in('RTS','RTI'):
            text='Return to the caller using the address saved on the stack.'if op=='RTS'else'Restore the saved CPU interrupt frame and resume the interrupted code, including its saved condition flags.'
        elif op in('CLRA','CLRB','CLR'):
            r=op[-1]if op!='CLR'else None;dest=r if r else arg
            text=f'Set {dest} to zero. Clear carry and overflow; set the zero result flag.'
            if r:self.setreg(r,'zero')
            self.nz('zero');self.flags['C']=('carry is set','carry is clear')
        elif op in('TSTA','TSTB','TST'):
            value=self.reg[op[-1]]if op!='TST'else label
            text=f'Test whether {value} is zero or has its high/sign bit set, without changing it. Clear carry and overflow.'
            self.nz(value);self.flags['C']=('carry is set','carry is clear')
        elif op in('BITA','BITB'):
            r=op[-1];text=f'Test which bits of {self.reg[r]} overlap {arg}; keep {r} unchanged and update the zero/sign result.'
            self.nz(f'the selected bits of {self.reg[r]}')
        elif op in('ANDA','ANDB','ORAA','ORAB','EORA','EORB'):
            r=op[-1];action='Keep only bits also set in'if op.startswith('AND')else'Set bits selected by'if op.startswith('ORA')else'Toggle bits selected by'
            text=f'{action} {arg} in byte {r} ({self.reg[r]}).'
            self.setreg(r,f'updated {r} bits');self.nz(self.reg[r])
        elif op in('ADDA','ADDB','ADDD','ADCA','ADCB','SUBA','SUBB','SUBD','SBCA','SBA','ABA'):
            r='A'if op in('SBA','ABA')else op[-1];right=self.reg['B']if op in('SBA','ABA')else label
            add=op.startswith(('ADD','ADC'))or op=='ABA';with_c=op.startswith(('ADC','SBC'))
            before=self.reg[r];width=16 if r=='D' else 8
            text=f"{'Add'if add else'Subtract'} {right}"+(f" and the previous {'carry'if add else'borrow'}"if with_c else'')+f" {'to'if add else'from'} {before} in {r}. Keep the {width}-bit result; "
            text+=('carry records overflow beyond the width.'if add else'carry records an unsigned borrow.')
            self.setreg(r,f'updated {r} result');self.nz(self.reg[r]);self.flags['C']=(f'the {width}-bit '+('addition overflowed'if add else'subtraction needed a borrow'),f'the {width}-bit '+('addition fit without carry'if add else'subtraction did not need a borrow'))
        elif op=='MUL':
            text=f'Multiply unsigned byte A ({self.reg["A"]}) by unsigned byte B ({self.reg["B"]}); keep the full 16-bit product in D. Carry receives product bit7 for subsequent rounding.'
            self.setreg('D','the product');self.flags['C']=('product bit7 is set (rounding carry)','product bit7 is clear');self.flags.pop('signed',None)
        elif op in('IDIV','FDIV'):
            text=('Divide unsigned D by X; put the integer quotient in X and remainder in D.'if op=='IDIV'else'Divide the unsigned fraction represented by D by X: normal quotient is (D shifted left16)/X in X, with the remainder in D.')+' Zero divisor or an overflowing fractional quotient must be interpreted through the divide flags.'
            self.reg['X']='division quotient';self.setreg('D','division remainder');self.ptr.pop('X',None);self.flags={}
        elif op in('ASL','ASLA','ASLB','ASLD','LSRA','LSRB','LSRD','ASRA','ASRB','LSR','ASR','ROL','ROR','ROLA','ROLB','RORA','RORB'):
            mem=op in('ASL','LSR','ASR','ROL','ROR');r=None if mem else op[-1];dest=arg if mem else r
            left=op.startswith(('ASL','ROL'));rotate=op.startswith(('ROL','ROR'));signed=op.startswith('ASR')
            if rotate:text=f'Rotate {dest} one bit '+('left'if left else'right')+' through the carry bit; the outgoing bit becomes the new carry.'
            elif left:text=f'Shift {dest} left one bit (double it within its stored width); the outgoing high bit becomes carry.'
            else:text=f'Shift {dest} right one bit; '+('preserve the sign bit for signed halving'if signed else'insert zero at the high end for unsigned halving')+' and copy the outgoing low bit to carry.'
            if r:self.setreg(r,f'shifted {r}')
            self.nz(f'the shifted {dest}');self.flags['C']=(f'the bit shifted out of {dest} was1',f'the bit shifted out of {dest} was0')
        elif op in('INC','DEC','INCA','INCB','DECA','DECB','INX','INY','DEX','DEY','INS','DES'):
            r={'INX':'X','INY':'Y','DEX':'X','DEY':'Y','INS':'SP','DES':'SP'}.get(op)
            if not r and op not in('INC','DEC'):r=op[-1]
            dest=r or arg;plus=op.startswith('IN')
            text=f"{'Increase'if plus else'Decrease'} {dest} by one, wrapping within its stored width."
            if r:self.setreg(r,f'updated {r}')
            if r in('X','Y'):
                if r in self.ptr:self.ptr[r]=(self.ptr[r]+(1 if plus else-1))&65535
                self.flags['Z']=(f'{r} is zero',f'{r} is nonzero');self.flags.pop('signed',None)
            elif r!='SP':self.nz(f'the updated {dest}')
        elif op in('COMA','COMB','NEGA','NEGB','NEG','COM'):
            r=op[-1]if op[-1]in'AB'else None;dest=r or arg
            text=(f'Invert every bit of {dest}.'if op.startswith('COM')else f'Negate {dest} using two\'s-complement subtraction from zero.')
            if r:self.setreg(r,f'updated {r}')
            self.nz(f'the updated {dest}');self.flags.pop('C',None)
        elif op.startswith(('PSH','PUL')):
            r=op[-1];text=(f'Push {r} onto the CPU stack to preserve it.'if op.startswith('PSH')else f'Pull the saved value from the CPU stack into {r}.')+' This does not change the condition flags.'
            if op.startswith('PUL'):
                self.setreg(r,f'restored {r}');self.ptr.pop(r,None)
        elif op in('TAB','TBA'):
            src,dst=('A','B')if op=='TAB'else('B','A');text=f'Copy byte {src} ({self.reg[src]}) into {dst}; update zero/sign and clear overflow.'
            value=self.reg[src];self.setreg(dst,value);self.nz(value)
        elif op in('TSX','TSY','TXS','TYS'):
            r='X'if'X'in op else'Y';text=f'Point {r} at the first saved stack byte (SP+1).'if op.startswith('TS')else f'Set SP to {r}-1, establishing the stack position from {r}.'
            text+=' Condition flags are unchanged.';self.ptr.pop(r,None)
            if op.startswith('TS'):self.setreg(r,'stack address SP+1')
        elif op in('ABX','ABY'):
            r=op[-1];text=f'Add unsigned byte B ({self.reg["B"]}) to word register {r}, wrapping at16 bits; preserve condition flags.';self.ptr.pop(r,None);self.setreg(r,f'indexed {r} address')
        elif op in('XGDX','XGDY'):
            r=op[-1];text=f'Exchange the 16-bit values in D and {r}, preserving condition flags.';self.ptr.pop(r,None);a=self.reg[r];self.reg[r]=self.reg['D'];self.setreg('D',a)
        elif op in('SEI','CLI'):
            text='Set the I mask to block maskable IRQ admission; other interrupt classes have separate rules.'if op=='SEI'else'Clear the I mask to allow maskable IRQ admission; other masks and pending-source rules still apply.'
        elif op=='SEC':text='Set carry. The following carry test or add/subtract consumes this explicit condition.';self.flags['C']=('carry is set','carry is clear')
        elif op=='TAP':text='Copy byte A into the condition-code register, changing result flags and the writable interrupt/STOP masks.';self.flags={}
        elif op=='SWI':text='Enter the software-interrupt path after saving the CPU context; this is an exception transfer, not a normal subroutine return.';self.flags={}
        elif op=='WAI':text='Save the CPU context and wait for an interrupt to resume processing.';self.flags={}
        elif op=='STOP':text='Request low-power STOP; the condition-code STOP-disable bit determines whether the CPU can enter that state.';self.flags={}
        elif op=='NOP':text='Perform no data operation and continue. This byte can occupy a deliberately bypassed former operation.'
        else:raise AssertionError('No English semantics for '+op)
        self.last=i
        return NOTES.get(i.pc,text)


def flag_effect(op):
    if op in ('CLR','CLRA','CLRB'):return 'N=0, Z=1, V=0, C=0; other flags preserved.'
    if op in ('TST','TSTA','TSTB'):return 'N/Z follow tested value; V=0 and C=0.'
    if op in ('MUL',):return 'Only C changes: product bit7 supplies rounding carry.'
    if op in ('INX','INY','DEX','DEY'):return 'Only Z changes; other condition flags are preserved.'
    if op in ('CLI','SEI'):return 'I='+('0 (maskable IRQs allowed).' if op=='CLI' else '1 (maskable IRQs masked).')
    if op=='SEC':return 'C=1; other flags preserved.'
    if op=='TAP':return 'Writable condition-code bits are taken from A; X-mask writes have HC11 restrictions.'
    if op=='RTI':return 'Restore the saved condition-code register with the interrupt frame.'
    if op=='SWI':return 'Save context, set I and use the software-interrupt vector.'
    if op in ('IDIV','FDIV'):return 'Division updates quotient-zero/error status; zero-divisor and fractional-overflow cases require the ISA divide rules.'
    if op.startswith(('LD','ST')) and op not in ('STOP',):return 'N/Z follow transferred value; V=0; C is preserved.'
    if op in ('BSET','BCLR','BITA','BITB','ANDA','ANDB','ORAA','ORAB','EORA','EORB','TAB','TBA'):return 'N/Z follow the byte result/test; V=0; C is preserved.'
    if op in ('COMA','COMB','COM'):return 'N/Z follow result; V=0; C=1.'
    if op in ('INC','DEC','INCA','INCB','DECA','DECB'):return 'N/Z/V update; C is preserved.'
    if op in ('ASL','ASLA','ASLB','ASLD','LSR','LSRA','LSRB','LSRD','ASR','ASRA','ASRB','ROL','ROR','ROLA','ROLB','RORA','RORB','NEGA','NEGB','NEG'):return 'N/Z/V/C update for the shift or negation; other flags preserved.'
    if op in ('CMPA','CMPB','CPD','CPX','CPY','CBA','SUBA','SUBB','SUBD','SBCA','SBA'):return 'N/Z/V/C record subtraction/comparison; a set C means unsigned borrow.'
    if op in ('ADDA','ADDB','ADDD','ADCA','ADCB','ABA'):return 'N/Z/V/C update; 8-bit additions also update H for BCD support.'
    return 'Condition flags preserved.'


def source_entries(image,decoded):
    entries={};e=json.loads((ROOT/'maps/structure/bmhm_ownership_rom_evidence.json').read_text());stock=bytearray(65536)
    for r in e['byte_ranges']:
        a=int(r['start'],16);raw=bytes.fromhex(r['bytes_hex']);stock[a:a+len(raw)]=raw
    candidates=defaultdict(list)
    for f in sorted((ROOT/'pseudo-source/src').rglob('*.c')):
        s=f.read_text();comment=re.search(r'/\*(.*?)\*/',s,re.S)
        if not comment:continue
        for a,z in re.findall(r'\b([0-9A-Fa-f]{4})\s*\.\.\s*([0-9A-Fa-f]{4})\b',comment.group(1)):
            pc=int(a,16)
            if pc in decoded and image[pc:decoded[pc].next_pc]==stock[pc:decoded[pc].next_pc]:
                candidates[pc].append((int(z,16)-pc,f,comment.group(1)))
    for pc,options in candidates.items():
        _,f,comment=min(options,key=lambda v:v[0]);title=f.stem.replace('_',' ').capitalize()
        entries[pc]=(title,'Stock-source topic hint: '+short(' '.join(comment.split()),300)+'. The exact Rev B operations below take precedence.',f.relative_to(ROOT).as_posix())
    calls={i.target for i in decoded.values()if i.op in('JSR','BSR')and i.target is not None}
    for pc in calls:
        if pc in decoded:entries.setdefault(pc,(f'Retained helper at ${pc:04X}','Follow the input loads before each call and the output stores after it; no more specific semantic name is asserted.',''))
    for pc,(title,purpose)in CUSTOM.items():
        if pc in decoded:entries[pc]=(title,purpose,'custom/reviewed context')
    for a in range(0x7a85,0x7aa5,2):
        pc=int.from_bytes(image[a:a+2],'big')
        if pc in decoded:entries.setdefault(pc,(f'Background slot {(a-0x7a85)//2:X}',f'Dispatch-table entry at ${a:04X}. This slot executes only under the retained dispatcher admission.',''))
    return entries,stock


def data_catalog(image,names):
    root=ET.parse(ROOT/'definitions/7427_0.3.12_Manual_Idle_RevB.xdf').getroot();items=[];covered=set()
    for p in root:
        if p.tag not in('XDFCONSTANT','XDFTABLE','XDFFLAG'):continue
        e=p.find("XDFAXIS[@id='z']/EMBEDDEDDATA")if p.tag=='XDFTABLE'else p.find('EMBEDDEDDATA')
        if e is None or e.get('mmedaddress')is None:continue
        a=int(e.get('mmedaddress'),0);width=int(e.get('mmedelementsizebits','8'))//8
        count=int(e.get('mmedrowcount','1'))*int(e.get('mmedcolcount','1'));length=width*count
        m=p.find("XDFAXIS[@id='z']/MATH")if p.tag=='XDFTABLE'else p.find('MATH')
        units=p.findtext("XDFAXIS[@id='z']/units",'')if p.tag=='XDFTABLE'else p.findtext('units','')
        item=dict(address=f'{a:04X}',title=p.findtext('title',''),kind=p.tag,width_bytes=width,elements=count,length=length,units=units,equation=m.get('equation','')if m is not None else'',mask=p.findtext('mask',''),raw=image[a:a+length].hex(' '),role=names.get(a,''),status='reviewed custom calibration'if 0x9f00<=a<0x9f27 or a in(0xff60,0xff8a,0xff8b,0x4152)else'inherited XDF display metadata; not blanket unit certification')
        item['rows']=int(e.get('mmedrowcount','1'));item['columns']=int(e.get('mmedcolcount','1'))
        item['axes']={axis:dict(units=p.findtext(f"XDFAXIS[@id='{axis}']/units",''),labels=[n.get('value','') for n in p.findall(f"XDFAXIS[@id='{axis}']/LABEL")]) for axis in ('x','y')} if p.tag=='XDFTABLE' else {}
        item['verified_display_values']=None
        if 0x9f00<=a<0x9f27 or a in (0xff60,0xff8a,0xff8b,0x4152,0x4146,0x4148,0x4169):
            from verify_custom_xdf import arithmetic
            flags=int(e.get('mmedtypeflags','0'),0)
            values=[]
            for offset in range(0,length,width):
                variables={'X':int.from_bytes(image[a+offset:a+offset+width],'big',signed=bool(flags&1))}
                for var in m.findall('VAR'):
                    if var.get('type')=='address':variables[var.get('id')]=image[int(var.get('address'),0)]
                values.append(arithmetic(m.get('equation'),variables))
            item['verified_display_values']=values
        items.append(item);covered.update(range(a,a+length))
    return items,covered


def byte_ledger(image,decoded,cal,stock):
    classes=['File padding below ROM; not runtime RAM contents']*0x4000+['Unclassified non-rooted ROM byte']*0xc000
    for a in range(0x4000,65536):
        if image[a]==255:classes[a]='FF-valued non-rooted byte; no execution inferred'
    for row in csv.DictReader((ROOT/'maps/structure/factory_global_regions.csv').open()):
        if row['classification']!='data_or_declared_tail':continue
        lo,hi=int(row['start'],16),int(row['end_exclusive'],16)
        if image[lo:hi]==stock[lo:hi]:
            for a in range(lo,hi):classes[a]='Retained OEM data layout: '+row['evidence_role']
    for a in cal:
        if 0x4000<=a<65536:classes[a]='XDF-described data/flag byte (inherited or reviewed as catalogued)'
    for a in range(0x7a85,0x7aa5):classes[a]='16-entry background dispatcher pointer table'
    for a in range(0xffc0,65536):classes[a]='Reserved/interrupt vector word data'
    for pc,i in decoded.items():
        for a in range(pc,i.next_pc):classes[a]='Rooted executable instruction bytes'
    runs=[];lo=0
    for a in range(1,65537):
        if a==65536 or classes[a]!=classes[lo]:
            runs.append(dict(start=f'{lo:04X}',end_exclusive=f'{a:05X}',bytes=a-lo,classification=classes[lo]));lo=a
    assert sum(r['bytes']for r in runs)==65536
    return classes,runs


def build(image,output):
    if len(image)!=65536 or hashlib.sha256(image).hexdigest()!=SHA:raise ValueError('Requires exact 64 KiB Rev B; refusing a guessed image')
    decoded,frontiers,roots=sweep(image);assert len(decoded)==6449
    names,bits,source_hashes=role_maps();entries,stock=source_entries(image,decoded)
    catalog,cal=data_catalog(image,names);classes,ledger=byte_ledger(image,decoded,cal,stock)
    output.mkdir(parents=True,exist_ok=True);(output/'chapters').mkdir(exist_ok=True)
    leaders=set(entries)|set(roots)
    for i in decoded.values():
        if i.target in decoded:leaders.add(i.target)
        if i.op in('JSR','BSR','BRSET','BRCLR')or i.mode=='relative':leaders.add(i.next_pc)
    translator=English(names,bits);operations=[];prev=None
    for pc,i in sorted(decoded.items()):
        if pc in leaders or prev!=pc:translator.reset()
        english=translator.describe(i);assert english and 'No English semantics'not in english
        operations.append(dict(address=f'{pc:04X}',bytes=i.data.hex(' '),operation=(i.op+' '+i.operand).strip(),explanation=english,flag_effect=flag_effect(i.op),access=i.access()['access'] if i.access() else '',width_bits=i.access()['width_bits'] if i.access() else '',target=f'{i.target:04X}'if i.target is not None else'',direct_reference=f'{i.value:04X}'if i.access()and i.access()['address']is not None else''))
        prev=i.next_pc
    groups=[]
    for number,title,lo,hi,purpose in CHAPTERS:
        ops=[r for r in operations if lo<=int(r['address'],16)<hi]
        if not ops:continue
        sections=[];current=None
        for row in ops:
            pc=int(row['address'],16)
            if current is None or pc in entries:
                topic,summary,source=entries.get(pc,(f'Continued address slice at ${pc:04X}','Follow the branches and calls shown below; this address span is a reading section, not proof of an independent function.',''))
                current=dict(address=row['address'],title=topic,summary=summary,source=source,operations=[]);sections.append(current)
            current['operations'].append(row)
        groups.append(dict(number=number,title=title,purpose=purpose,sections=sections,count=len(ops)))
    assert sum(g['count']for g in groups)==len(decoded)
    opcode_counts=dict(sorted(Counter(i.op for i in decoded.values()).items()))
    metadata=dict(image_sha256=SHA,image_bytes=65536,instructions=len(decoded),executable_bytes=sum(len(i.data)for i in decoded.values()),root_entries=[f'{a:04X}'for a in roots],control_frontiers=frontiers,indexed_data_instructions=sum(bool(i.access()and i.access()['address']is None)for i in decoded.values()),reading_sections=sum(len(g['sections'])for g in groups),calibration_displays=len(catalog),byte_ledger_total=sum(r['bytes']for r in ledger),byte_classes=dict(sorted(Counter(classes).items())),opcode_counts=opcode_counts,reference_inputs=source_hashes,isa_reference=ISA,reviewed_pc_notes=sum(pc in NOTES for pc in decoded),scope='Complete per-instruction explanation of rooted static code and full 65536-byte accounting. Automatic ISA/address-role explanations with reviewed context; not an independently hand-proved semantic reconstruction or physical execution trace of every routine.')
    write_outputs(output,image,operations,groups,catalog,ledger,metadata,names)
    return metadata


def write_outputs(out,image,ops,groups,catalog,ledger,meta,names):
    intro=f'''# Rev B: whole-image operation-by-operation guide

Exact image: `0.3.12_engine_only_manual_idle_revB.bin`  
SHA-256: `{SHA}`  
{meta['instructions']:,} rooted instructions; {meta['reading_sections']} address reading sections; {len(catalog)} XDF displays; all 65,536 file bytes accounted for.

## Read this first

This is the full address-by-address reader for the supplied Rev B. Each rooted
instruction appears once, with its exact bytes, opcode and a plain-English
explanation. Sections are address slices with routine/topic context. Shared tails
and jumps can cross section boundaries; the headings do not invent independent
functions. Use the search in FULL_GUIDE.html or find an address in this Markdown.

Instruction decoding and branch destinations come from the exact image.
Operation meanings use the HC11 instruction reference and maintained address
roles; context-specific comments supplement them. Inherited names are not blanket
semantic proof. Unresolved indexed addresses are explicitly described as pointer
accesses rather than guessed fixed variables. A flag explanation only follows a
known local producer; joins/calls discard uncertain local provenance. A conditional
branch lists both the taken and fall-through addresses.

This is a static walkthrough, not a prediction that every listed path occurs on
the truck, a cycle-accurate trace, or hand verification of every routine's purpose.
No BIN, calibration, XDF or runtime behavior was changed. Rev B truck testing and
fine-tuning remain the first work item.

## Execution order and registers

Reset vector at FFFE points to {int.from_bytes(image[0xfffe:],'big'):04X}; its
entry reaches boot at7100. Boot initializes the machine and enters the main
scheduler. Engine-reference/timer/serial interrupts can interrupt foreground work
when their masks and sources permit. The main dispatcher selects among16 slots
through words at7A85..7AA4. Numeric ROM address order is not execution order.

- A and B are byte working registers; D is their combined word, A high then B low.
- X/Y hold word values or addresses. `offset,X` reads/writes memory at X+offset.
- SP points to the CPU stack; calls save return addresses and interrupt frames
  save more state. File padding below4000 is not the RAM's startup contents.
- Carry can mean addition overflow, subtraction borrow, a shifted-out bit or
  rounding status, depending on its producer. Equality is the zero flag.
- Signed and unsigned comparisons differ. A 16-bit FFEE can mean -18 in a
  signed angle comparison. Addition/shift results can wrap before later clamps.
- SEI/CLI change the maskable IRQ I bit; they do not respectively disable/enable
  every possible interrupt source. RTI restores the saved interrupt context.
- Word memory is big-endian: the high byte is at the named address.

## Confirmed label distinctions used in this guide

50A9 is a normalized-TPS cutoff;50A8 is a positive air-command-change threshold.
Percent of normalized air-command scale is a valid display for50A8, but is not
measured airflow percent. Short-pulse4979 is added and4971 subtracted; both sync
and option-qualified async paths use them.496D is a threshold and496F a replacement.
5216 is a logging source pointer, not an AFR target.4146/4148 are signed angle
floors before later service edits. BLM is multiplicative; INT/P is additive PW.
Air units in the new controller are internal coordinates, not physical IAC steps.
The coolant lookup coordinate0283 is not degrees Celsius. Its normal producer
subtracts16 from the effective coolant byte and limits the result to0..192;
the higher generic curve knots are not all active independent tuning points.

## Contents

'''
    toc=''.join(f"- [{g['number']} — {g['title']}](#chapter-{g['number']}) ({g['count']} operations)\n"for g in groups)
    toc+='- [Calibration and pointer catalog](#calibration-catalog)\n- [Whole-file byte ledger](#byte-ledger)\n- [Vectors and dispatcher](#vectors)\n- [Scope and evidence](#scope)\n'
    code_addresses={r['address'] for r in ops}
    full=[intro,toc];html_sections=[]
    for g in groups:
        md=[f"<a id=\"chapter-{g['number']}\"></a>\n\n# {g['number']} — {g['title']}\n\n{g['purpose']}\n"]
        cards=[]
        for s in g['sections']:
            md.append(f"\n## ${s['address']} — {s['title']}\n\n{s['summary']}\n")
            if s['source']:md.append(f"\nContext reference: `{s['source']}`.\n")
            refs=sorted({r['direct_reference']for r in s['operations']if r['direct_reference']})
            if refs:
                for direction,title in [('R','Reads'),('W','Writes')]:
                    selected=sorted({r['direct_reference'] for r in s['operations'] if r['direct_reference'] and direction in r['access']})
                    if selected:md.append('\n'+title+': '+'; '.join('$'+a+' '+names.get(int(a,16),'unresolved role') for a in selected)+'.\n')
            card=[]
            for row in s['operations']:
                md.append(f"\n<a id=\"a{row['address']}\"></a>\n\n```text\n{row['address']}  {row['operation']}    [{row['bytes']}]\n```\n{row['explanation']}\n\nFlags: {row['flag_effect']}\n")
                sentence=html.escape(row['explanation'])
                sentence=re.sub(r'\$([0-9A-F]{4})',lambda m:(f'<a href="#a{m[1]}">${m[1]}</a>' if m[1] in code_addresses else m[0]),sentence)
                card.append(f'<div class="operation" id="a{row["address"]}"><code>{row["address"]}  {html.escape(row["operation"])}</code><span class="bytes">{row["bytes"]}</span><p>{sentence}</p><small class="muted">Flags: {html.escape(row["flag_effect"])}</small></div>')
            cards.append(f'<section class="routine"><h3>${s["address"]} — {html.escape(s["title"])}</h3><p class="summary">{html.escape(s["summary"])}</p>'+''.join(card)+'</section>')
        text='\n'.join(md);(out/'chapters'/f'{g["number"]}.md').write_text(text);full.append(text)
        html_sections.append(f'<article class="chapter" data-chapter="{g["number"]}"><h2>{g["number"]} — {html.escape(g["title"])}</h2><p>{html.escape(g["purpose"])}</p>'+''.join(cards)+'</article>')
    catmd=['\n<a id="calibration-catalog"></a>\n\n# Calibration and pointer catalog\n\nNames, axes and conversion formulas below are the supplied XDF views. The status field distinguishes reviewed custom data from inherited metadata. Aliases can share bytes; six flow-rate displays at4D92 are not six independent parameters. This catalog does not promote the XDF display into semantic proof. All raw bytes are included.\n']
    cathtml=[]
    for index,r in enumerate(catalog):
        text=f"\n## ${r['address']} — {r['title']}\n\n{r['status']}. {r['kind']}; {r['elements']} element(s), {r['width_bytes']} byte(s) each. Display units: {r['units'] or 'not supplied'}; formula: `{r['equation'] or 'flag/mask'}`; mask: `{r['mask'] or 'not applicable'}`.\n\n"
        if r['role']:text+='Maintained role: '+r['role']+'.\n\n'
        if r['axes']:
            text+=f"Shape: {r['rows']} rows × {r['columns']} columns. Supplied axis labels (inherited unless noted):\n\n"
            for axis,axisdata in r['axes'].items():text+=axis.upper()+' '+axisdata['units']+': '+', '.join(axisdata['labels'])+'.\n\n'
        if r['verified_display_values'] is not None:text+='Reviewed display values: '+', '.join(f'{v:g}' for v in r['verified_display_values'])+'.\n\n'
        text+='Raw bytes:\n\n```text\n'+ '\n'.join(textwrap.wrap(r['raw'],95))+'\n```\n';catmd.append(text)
        cathtml.append(f'<section class="datum"><h3>${r["address"]} — {html.escape(r["title"])}</h3><p>{html.escape(r["status"])}. {r["elements"]} elements × {r["width_bytes"]} bytes. Units: {html.escape(r["units"])}. Formula: <code>{html.escape(r["equation"])}</code></p><p>{html.escape(r["role"])}</p><pre>{html.escape(r["raw"])}</pre></section>')
    full.append('\n'.join(catmd));(out/'CALIBRATION_CATALOG.md').write_text('\n'.join(catmd))
    ledgermd=['\n<a id="byte-ledger"></a>\n\n# Whole-file byte ledger\n\nEnd addresses are exclusive. Every one of the65,536 bytes belongs to exactly one row. FF is also a legal opcode: an FF-valued run outside rooted code is not automatically a proved non-executable erase. Retained OEM data layout is reused only where the entire recorded region is byte-identical. Unclassified means the evidence does not justify a stronger data/code label.\n\n| Start | End exclusive | Bytes | Classification |\n|---|---|---:|---|\n']
    ledgermd.extend(f"| {r['start']} | {r['end_exclusive']} | {r['bytes']} | {r['classification']} |\n"for r in ledger);full.append(''.join(ledgermd))
    vectors=[]
    for a in range(0xffc0,65536,2):vectors.append(dict(address=f'{a:04X}',target=f'{int.from_bytes(image[a:a+2],"big"):04X}',role=names.get(a,'reserved/vector identity not separately named')))
    slots=[dict(slot=f'{(a-0x7a85)//2:X}',address=f'{a:04X}',target=f'{int.from_bytes(image[a:a+2],"big"):04X}')for a in range(0x7a85,0x7aa5,2)]
    full.append('\n<a id="vectors"></a>\n\n# Vectors and dispatcher\n\n```json\n'+json.dumps(dict(vectors=vectors,slots=slots),indent=2)+'\n```\n')
    scope=f'''\n<a id="scope"></a>\n\n# Scope, provenance and verification

All {meta['instructions']} rooted instruction starts are decoded and explained,
with no missing opcode handler. This is structural reachability, not proof every
branch can occur. {meta['indexed_data_instructions']} indexed data operations need
caller/runtime pointer context. The rooted sweep currently reports
{len(meta['control_frontiers'])} unresolved control-transfer frontiers; that does
not close every possible RAM upload or hardware-triggered behavior outside this
fixed image/model. Non-rooted bytes are accounted for without guessed opcodes.

Inputs: exact Rev B, maintained non-OEM read/write role workbooks, unchanged
stock-source topic comments, manual-idle assembly symbols, supplied Rev B XDF,
reviewed byte-ledger layout and the retained image-specific trace evidence.
ISA reference: {ISA} (instruction/condition-code tables, pages12–20).
CPU semantics are explanatory rules, not a certification of the emulator.
Reads and writes occur in the listed order; shared state can change between
instructions. A role name describes the loaded snapshot, not a new hidden read.
The 4EB6 wording corrects an earlier coolant-name error: the actual input is
the battery-voltage sample, consistent with the inherited XDF voltage label.

The reset/interrupt schedule, IAC, spark and fuel contracts in7427HWContract
supply additional background. Inherited address names and physical port/ASIC
identities retain their documented limits. Generic indexed bytes are not given
invented fixed meanings. High-level headings are context hints unless explicitly
reviewed; instruction explanations are not a substitute for full state/history
and hardware validation. This guide changes documentation only.
'''
    full.append(scope)
    (out/'FULL_GUIDE.md').write_text('\n'.join(full))
    csvfile(out/'OPERATIONS.csv',ops);csvfile(out/'BYTE_LEDGER.csv',ledger)
    (out/'CALIBRATIONS.json').write_text(json.dumps(catalog,indent=2)+'\n')
    (out/'COVERAGE.json').write_text(json.dumps(meta,indent=2)+'\n')
    (out/'VECTORS_AND_SLOTS.json').write_text(json.dumps(dict(vectors=vectors,slots=slots),indent=2)+'\n')
    dump='\n'.join(f'{a:04X}  '+image[a:a+16].hex(' ')for a in range(0,65536,16))+'\n';(out/'FULL_HEX.txt').write_text(dump)
    htmlwrite(out,groups,html_sections,cathtml,ledger,meta,intro)
    readme='''REV B OPERATION-BY-OPERATION GUIDE

Start with FULL_GUIDE.html: extract the ZIP, then open this self-contained file
in a browser. Search an address (9A52, $9A52 or 0x9A52), variable or topic.
Select a chapter to narrow the view. Linked code destinations clear the search
and chapter filter so their surrounding code can be read. No network is needed.

FULL_GUIDE.md: complete Markdown version with reading notes and provenance.
chapters/: 13 smaller Markdown files containing the executable walkthrough.
OPERATIONS.csv: one row per decoded instruction, including flags and references.
CALIBRATION_CATALOG.md: raw data, axes and supplied XDF display information.
CALIBRATIONS.json: structured version of the calibration/pointer catalog.
BYTE_LEDGER.csv: every file byte accounted for, including unknown regions.
FULL_HEX.txt: exact image as hexadecimal text; this is not a flashable BIN.
VECTORS_AND_SLOTS.json: raw vector and background-dispatcher pointer words.
COVERAGE.json: exact image/reference identities, counts and limits.
SHA256SUMS.txt: SHA-256 hashes of the files in this package.

This is an automatic instruction/address-role reader with reviewed context,
not independent hand verification of every routine or physical truck testing.
Inherited names and conversions retain their qualifications. Unknowns are marked.
No firmware changes are included. Rev B testing and fine-tuning stay first.
'''
    (out/'README.txt').write_text(readme)
    manifest={p.relative_to(out).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()for p in sorted(out.rglob('*'))if p.is_file()and p.name!='SHA256SUMS.txt'}
    (out/'SHA256SUMS.txt').write_text(''.join(v+'  '+k+'\n'for k,v in manifest.items()))


def csvfile(path,rows):
    with path.open('w',newline='')as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)


def htmlwrite(out,groups,sections,cathtml,ledger,meta,intro):
    css='''body{font:16px/1.55 system-ui,sans-serif;color:#202830;margin:0;background:#f6f7f9}header,main{max-width:1080px;margin:auto;padding:20px}h1{font-size:1.8rem}h2{font-size:1.45rem}h3{font-size:1.15rem}nav{position:sticky;top:0;background:#fff;border-block:1px solid #ccd4dd;z-index:3;padding:10px;display:flex;gap:8px;flex-wrap:wrap}input,select{font:inherit;padding:8px;max-width:100%;box-sizing:border-box}input{flex:1;min-width:180px}select{width:310px}a{color:#135a8c}code{font-family:ui-monospace,monospace;font-size:.92rem}.routine,.datum{background:white;border:1px solid #dce2e8;border-radius:7px;padding:16px;margin:18px 0}.summary{color:#435463}.operation{padding:10px 0;border-top:1px solid #e8edf1;scroll-margin-top:140px}.operation>code{display:block;font-weight:650}.bytes{color:#637183;font:12px monospace}.operation p{margin:4px 0;overflow-wrap:anywhere}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f2f4f7;padding:10px}table{border-collapse:collapse;width:100%;font-size:.9rem}td,th{padding:6px;text-align:left;border-bottom:1px solid #dde3e9;overflow-wrap:anywhere}.muted{color:#526575}.hidden{display:none!important}.jump{display:flex;flex-wrap:wrap;gap:10px}.datum{scroll-margin-top:140px}@media(max-width:600px){header,main{padding:12px}nav{gap:5px}select{width:100%}.routine,.datum{padding:12px}.operation p{font-size:16px}}'''
    options='<option value="all">All executable chapters</option>'+''.join(f'<option value="{g["number"]}">{g["number"]} {html.escape(g["title"])}</option>'for g in groups)+'<option value="data">Calibration catalog</option><option value="ledger">Whole-file ledger</option>'
    le='<article class="chapter" data-chapter="ledger"><h2>Whole-file ledger</h2><p>All 65,536 bytes; end addresses are exclusive. Unclassified bytes are not guessed instructions.</p><table><thead><tr><th>Start</th><th>End</th><th>Bytes</th><th>Classification</th></tr></thead><tbody>'+''.join(f'<tr><td>{r["start"]}</td><td>{r["end_exclusive"]}</td><td>{r["bytes"]}</td><td>{html.escape(r["classification"])}</td></tr>'for r in ledger)+'</tbody></table></article>'
    script=r'''const q=document.querySelector('#search');
const pick=document.querySelector('#chapter');
const status=document.querySelector('#status');
const sections=[...document.querySelectorAll('.routine,.datum')];
for(const section of sections){
  section.dataset.search=section.textContent.toLowerCase();
  section.dataset.topic=[...section.querySelectorAll('h3,.summary')].map(x=>x.textContent).join(' ').toLowerCase();
  for(const op of section.querySelectorAll('.operation'))op.dataset.search=op.textContent.toLowerCase();
}
function apply(){
  const needle=q.value.trim().toLowerCase().replace(/^(?:\$|0x)/,'');
  let shown=0;
  for(const chapter of document.querySelectorAll('.chapter')){
    const allow=pick.value==='all'?!['data','ledger'].includes(chapter.dataset.chapter):chapter.dataset.chapter===pick.value;
    chapter.classList.toggle('hidden',!allow);
    if(!allow)continue;
    for(const section of chapter.querySelectorAll('.routine,.datum')){
      const ops=[...section.querySelectorAll('.operation')];
      if(ops.length){
        let any=false;
        for(const op of ops){
          const hit=!needle||op.dataset.search.includes(needle)||section.dataset.topic.includes(needle);
          op.classList.toggle('hidden',!hit);
          if(hit){shown++;any=true;}
        }
        section.classList.toggle('hidden',!any);
      }else{
        section.classList.toggle('hidden',!!needle&&!section.dataset.search.includes(needle));
      }
    }
  }
  status.textContent=shown+' operations shown. Clear search to restore surrounding code.';
}
let delay;
q.addEventListener('input',()=>{clearTimeout(delay);delay=setTimeout(apply,140);});
pick.addEventListener('change',apply);
document.addEventListener('click',event=>{
  const link=event.target.closest('a[href^="#a"]');
  if(!link)return;
  q.value='';pick.value='all';apply();
});
apply();
'''
    introhtml='<p><strong>Exact Rev B:</strong> '+SHA+'</p><p>'+f'{meta["instructions"]:,} operations, {meta["reading_sections"]} reading sections, {meta["calibration_displays"]} supplied XDF displays, all 65,536 bytes accounted for.'+'</p><p>Every rooted instruction has exact bytes and a plain-English explanation. A/B are byte working registers; D is their combined word. X/Y are address/value registers. Use the linked targets to follow calls and branches. Sections are reading slices, including shared tails, rather than guaranteed standalone functions.</p><p class="muted">Static reachability and reference-based explanations are not a physical execution trace or an independent proof of every inherited name. Indexed memory can depend on runtime pointers. Known uncertain roles remain marked. Calibration units retain inherited qualifications. No BIN/XDF/calibration was changed. The Markdown version contains the full reading notes, vectors, provenance and scope.</p>'
    document='<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>Rev B whole-image operation guide</title><style>'+css+'</style></head><body><header><h1>Rev B operation-by-operation</h1>'+introhtml+'</header><nav><input id="search" type="search" placeholder="Address or topic: 9A52, TPS, IAC, fuel…" aria-label="Search operations"><select id="chapter" aria-label="Select chapter">'+options+'</select><span id="status" class="muted"></span></nav><main>'+''.join(sections)+'<article class="chapter" data-chapter="data"><h2>Calibration and pointer catalog</h2><p>These are the supplied XDF displays, not blanket semantic certification. Aliases can share the same bytes.</p>'+''.join(cathtml)+'</article>'+le+'</main><script>'+script+'</script></body></html>'
    (out/'FULL_GUIDE.html').write_text(document)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    original=a.rom.read_bytes();metadata=build(original,a.output);assert a.rom.read_bytes()==original
    print(json.dumps({k:metadata[k]for k in('instructions','reading_sections','executable_bytes','calibration_displays','byte_ledger_total','indexed_data_instructions')},indent=2))
