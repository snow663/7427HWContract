"""Local-only ROMFlow Studio server; stdlib Python, no external services."""
from __future__ import annotations
import argparse, base64, csv, hashlib, io, json, re, threading, webbrowser, zipfile
from datetime import datetime, timezone
from collections import Counter, defaultdict
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import parse_qs, urlsplit
from .analysis import Image, Analyzer, COND, CALLS, END
from .graph import routine_graph, global_graph
from .mathtrace import math_traces

ROOT=Path(__file__).resolve().parents[1]
STATIC=ROOT/'static'
SAMPLES=ROOT/'examples'
PROFILE_FILE=ROOT/'profiles'/'gm_7427_31.json'
MAX_BODY=750_000
PROJECT_FORMAT='ROMFlowStudioProject'
PROJECT_SCHEMA=1
MAX_PROJECT_ARCHIVE=400_000
MAX_PROJECT_METADATA=250_000

def hexaddr(value):
    if isinstance(value,int):return f'{value&0xffff:04X}'
    txt=str(value).strip().upper().replace('$','').replace('0X','')
    if not re.fullmatch('[0-9A-F]{1,4}',txt):raise ValueError('Expected a 16-bit hexadecimal address')
    return f'{int(txt,16):04X}'

def parsehex(value):return int(hexaddr(value),16)
def js(x):return json.dumps(x,indent=2,ensure_ascii=False)+'\n'
def atomic_json(path,obj):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(js(obj),encoding='utf-8');temp.replace(path)

def starter_meta(profile='generic'):
    return dict(version=3,profile=profile,annotations={},tables=[],regions=[],zones=[],entries=[],dispatch_tables=[],groups=['Startup','Fuel','Spark','IAC','SCI / ALDL','Diagnostics','Scheduler','Calibration','Unsorted'],view={})

def validate_project_meta(meta):
    """Validate saved-state shape before it can affect the active workspace."""
    if not isinstance(meta,dict) or meta.get('profile','generic') not in ('generic','gm_7427_31'):
        raise ValueError('Invalid project metadata or hardware profile')
    defaults=starter_meta(meta.get('profile','generic'))
    defaults.update(meta)
    for key in ('annotations','view'):
        if not isinstance(defaults[key],dict):raise ValueError('Invalid '+key)
    for key in ('tables','regions','zones','entries','dispatch_tables','groups'):
        if not isinstance(defaults[key],list) or len(defaults[key])>10000:raise ValueError('Invalid '+key)
    if len(js(defaults).encode('utf-8'))>MAX_PROJECT_METADATA:raise ValueError('Metadata too large')
    if 'load_address' in defaults:parsehex(defaults['load_address'])
    if len(defaults['view'].get('layouts',{}))>1000:raise ValueError('Excessive graph layouts')
    return defaults

class Workspace:
    def __init__(self,data_dir=None):
        self.root=Path(data_dir or ROOT/'workspace').resolve();self.root.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock();self.an=None;self.filename='';self.meta=None;self.raw=None
        self.rom_path=None;self.summary_cache=None
        active=self.root/'active.json'
        if active.exists():
            try:
                obj=json.loads(active.read_text());p=(self.root/obj['relative_rom']).resolve()
                if p.is_file() and p.is_relative_to(self.root):self.open_rom(p,obj.get('profile','generic'),restore=True)
            except (ValueError,KeyError,OSError,IndexError):pass
        if self.an is None:self.open_rom(SAMPLES/'synthetic_A_64k.bin', 'generic')

    def save_meta(self):atomic_json(self.root/'projects'/self.sha[:20]/'annotations.json',self.meta)
    @property
    def sha(self):return hashlib.sha256(self.raw).hexdigest()
    def open_rom(self,path,profile='generic',restore=False):
        with self.lock:
            self.raw=Path(path).read_bytes()
            if not 1<=len(self.raw)<=65536:raise ValueError('ROM must be 1-65536 bytes')
            self.filename=Path(path).name
            project_dir=self.root/'projects'/self.sha[:20]
            project_dir.mkdir(parents=True,exist_ok=True)
            self.rom_path=project_dir/self.filename
            if Path(path).resolve()!=self.rom_path.resolve():self.rom_path.write_bytes(self.raw)
            mp=project_dir/'annotations.json'
            self.meta=validate_project_meta(json.loads(mp.read_text())) if mp.exists() else starter_meta(profile)
            if not mp.exists():self.save_meta()
            self.analyze()
            atomic_json(self.root/'active.json',{'relative_rom':str(self.rom_path.relative_to(self.root)),'profile':self.meta['profile']})
            return self.summary()
    def analyze(self):
        with self.lock:
            raw=self.raw
            load=int(self.meta.get('load_address',0 if len(raw)==65536 else 65536-len(raw)))
            if load<0 or load+len(raw)>65536:raise ValueError('ROM mapping exceeds CPU address space')
            entries=[parsehex(x) for x in self.meta['entries']]
            specs=[f'{hexaddr(d["address"])}:{int(d["count"])}' for d in self.meta['dispatch_tables']]
            self.an=Analyzer(Image(raw,load),entries,True,specs).scan()
            self.summary_cache=None
    def zones(self):
        base=json.loads(PROFILE_FILE.read_text())['zones'] if self.meta['profile']=='gm_7427_31' else []
        return base+self.meta.get('zones',[])
    def domain(self,addr):
        if addr is None:return 'unresolved'
        for z in reversed(self.zones()):
            if parsehex(z['start'])<=addr<=parsehex(z['end']):return z['name']
        if addr in self.an.instructions:return 'executable code'
        if self.an.img.contains(addr):return 'mapped ROM/image (unclassified)'
        return 'external memory / IO (unknown)'
    def classify(self,addr):
        for region in reversed(self.meta['regions']):
            if parsehex(region['start'])<=addr<=parsehex(region['end']):return region['type']
        for table in self.meta['tables']:
            count=int(table['rows'])*int(table['columns'])*int(table['width'])
            if parsehex(table['start'])<=addr<parsehex(table['start'])+count:return 'calibration/table (annotated)'
        for pc,ins in self.an.instructions.items():
            if pc<=addr<pc+len(ins.data):return 'code (rooted)'
        for d in self.an.dispatch:
            a=int(d['table'],16)+2*d['slot']
            if a<=addr<a+2:return 'dispatch word (inferred)'
        for v in self.an.vectors:
            a=int(v['vector'],16)
            if a<=addr<a+2:return 'interrupt vector'
        return 'unclassified — not necessarily data'
    def summary(self):
        if self.summary_cache is not None:return self.summary_cache
        a=self.an
        routines=[]
        for addr,r in sorted(a.routines.items()):
            key=f'R:{addr:04X}';ann=self.meta['annotations'].get(key,{})
            routines.append(dict(entry=f'{addr:04X}',label=ann.get('label',f'Routine ${addr:04X}'),group=ann.get('group','Unsorted'),color=ann.get('color',''),category=ann.get('category',''),count=len(r['pcs']),sources=r['sources'],exits=len(r['exits'])))
        d=dict(rom=self.filename,sha256=self.sha,start=f'{a.img.start:04X}',length=len(self.raw),routines=routines,vectors=a.vectors,dispatch=a.dispatch,dispatch_candidates=a.dispatch_candidates,unknown_spans=a.unknown_spans()[:250],orphan_candidates=a.orphan_candidates(80),counts=dict(instructions=len(a.instructions),routines=len(a.routines),reads=sum(x['access']=='R' for x in a.accesses),writes=sum(x['access']=='W' for x in a.accesses),rmw=sum(x['access']=='RW' for x in a.accesses),dispatch=len(a.dispatch),decode_failures=len(a.failures)),meta=self.meta,zones=self.zones())
        self.summary_cache=d;return d

    def set_view(self,view):
        if not isinstance(view,dict):raise ValueError('Invalid view state')
        candidate=dict(self.meta['view'])
        for k in ('entry','mode','tab','hexStart','expanded','layouts','transforms'):
            if k in view:candidate[k]=view[k]
        if len(js(candidate))>160_000:raise ValueError('View state is too large')
        self.meta['view']=candidate
        self.save_meta();self.summary_cache=None
        return {'ok':True}

    def portable_project(self):
        """Self-contained .romflow archive; analysis is regenerated on import."""
        manifest={'format':PROJECT_FORMAT,'schema':PROJECT_SCHEMA,
                  'rom_name':self.filename,'sha256':self.sha,'rom_size':len(self.raw),
                  'image_start':f'{self.an.img.start:04X}',
                  'created_utc':datetime.now(timezone.utc).isoformat(),
                  'members':['manifest.json','rom.bin','metadata.json']}
        stream=io.BytesIO()
        with zipfile.ZipFile(stream,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7) as archive:
            archive.writestr('manifest.json',js(manifest))
            archive.writestr('rom.bin',self.raw)
            archive.writestr('metadata.json',js(self.meta))
        return stream.getvalue()

    def load_project(self,data):
        """Validate before replacing saved state. No paths from the ZIP are extracted."""
        if len(data)>MAX_PROJECT_ARCHIVE:raise ValueError('Project archive is too large')
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                names=set(archive.namelist())
                if names!={'manifest.json','rom.bin','metadata.json'} or len(archive.infolist())!=3:
                    raise ValueError('Unrecognized project archive contents')
                for item in archive.infolist():
                    if item.file_size>MAX_PROJECT_METADATA:raise ValueError('Project member exceeds size limit')
                manifest=json.loads(archive.read('manifest.json'))
                meta=validate_project_meta(json.loads(archive.read('metadata.json')))
                rom=archive.read('rom.bin')
        except (zipfile.BadZipFile,UnicodeDecodeError,json.JSONDecodeError) as exc:
            raise ValueError('Invalid or damaged .romflow project') from exc
        if manifest.get('format')!=PROJECT_FORMAT or manifest.get('schema')!=PROJECT_SCHEMA:
            raise ValueError('Unsupported project format/version')
        if not 1<=len(rom)<=65536 or len(rom)!=manifest.get('rom_size'):
            raise ValueError('ROM size does not match project manifest')
        if hashlib.sha256(rom).hexdigest()!=manifest.get('sha256'):
            raise ValueError('ROM hash differs from saved project manifest')
        if not isinstance(manifest.get('rom_name'),str):raise ValueError('Missing ROM name')
        rom_name=Path(manifest['rom_name'].replace('\\','/')).name
        if not rom_name or len(rom_name)>120 or rom_name.startswith('.'):
            raise ValueError('Invalid saved ROM filename')
        start=parsehex(manifest.get('image_start','0000'))
        if start+len(rom)>0x10000:raise ValueError('Project ROM mapping exceeds 64KiB')
        if 'load_address' in meta and parsehex(meta['load_address'])!=start:
            raise ValueError('Project ROM mapping disagrees with metadata')
        meta['load_address']=start
        # Commit the validated state into a per-ROM workspace only after parsing succeeds.
        folder=self.root/'projects'/manifest['sha256'][:20]
        folder.mkdir(parents=True,exist_ok=True)
        image_path=folder/rom_name
        image_path.write_bytes(rom)
        atomic_json(folder/'annotations.json',meta)
        return self.open_rom(image_path,meta['profile'])
    def routine(self,entry):
        e=parsehex(entry);r=self.an.routines.get(e)
        if not r:raise ValueError('Routine not rooted; add an explicit entry first')
        g=routine_graph(self.an,e)
        access=defaultdict(list)
        for item in self.an.accesses:
            try:pc=int(item['pc'],16)
            except ValueError:continue
            if pc in r['pcs']:
                a=None if item['address']=='?' else int(item['address'],16)
                access[item['pc']].append({**item,'domain':self.domain(a)})
        trace={t['pc']:t for t in math_traces(self.an,r['pcs'],set(int(x,16) for x in g['boundaries']))}
        items=[]
        for pc in sorted(r['pcs']):
            i=self.an.instructions[pc];h=f'{pc:04X}'
            items.append(dict(pc=h,bytes=i.data.hex(' ').upper(),op=i.op,mode=i.mode,operand=i.operand,target=f'{i.target:04X}' if i.target is not None else '?',annotation=self.meta['annotations'].get('I:'+h,{}),accesses=access[h],math=trace[h]['formula'],effects=trace[h]['effects']))
        return dict(entry=f'{e:04X}',label=self.meta['annotations'].get(f'R:{e:04X}',{}).get('label',f'Routine ${e:04X}'),sources=r['sources'],signature=r['signature'],exits=[dict(pc=f'{pc:04X}',type=t) for pc,t in r['exits']],instructions=items,graph=g)
    def hex_window(self,start,count=256):
        a=parsehex(start);count=max(1,min(1024,int(count)))
        cells=[]
        for addr in range(a,min(a+count,65536)):
            b=self.an.img.read(addr)
            cells.append(dict(address=f'{addr:04X}',byte=b.hex().upper() if b else '--',classification=self.classify(addr),domain=self.domain(addr)))
        return {'start':f'{a:04X}','cells':cells}
    def address_info(self,addr):
        a=parsehex(addr);ha=f'{a:04X}'
        uses=[{**x,'domain':self.domain(a)} for x in self.an.accesses if x['address']==ha]
        owner=[f'{pc:04X}' for pc,i in self.an.instructions.items() if pc<=a<pc+len(i.data)]
        ins=self.an.instructions.get(a)
        references=[{'pc':f'{i.pc:04X}','kind':i.op} for i in self.an.instructions.values() if i.target==a]
        b=self.an.img.read(a,16)
        return dict(address=ha,classification=self.classify(a),domain=self.domain(a),bytes=b.hex(' ').upper(),instruction=dict(op=ins.op,operand=ins.operand,bytes=ins.data.hex(' ').upper()) if ins else None,within_instructions=owner,readers=[x for x in uses if x['access']=='R'],writers=[x for x in uses if x['access'] in ('W','RW')],control_references=references,annotation=self.meta['annotations'].get('A:'+ha,{}))
    def access_list(self,query):
        kind=query.get('kind','all').upper();q=query.get('q','').lower();domain=query.get('domain','all')
        rows=[]
        for x in self.an.accesses:
            if kind!='ALL' and x['access']!=kind:continue
            a=None if x['address']=='?' else int(x['address'],16)
            d=self.domain(a)
            if domain!='all' and domain.lower() not in d.lower():continue
            row={**x,'domain':d, 'site_note':self.meta['annotations'].get('I:'+x['pc'],{}).get('label',''), 'target_note':self.meta['annotations'].get('A:'+x['address'],{}).get('label','') if a is not None else ''}
            if q and q not in json.dumps(row).lower():continue
            rows.append(row)
        return {'count':len(rows),'rows':rows[:2000],'truncated':len(rows)>2000}
    def rom_references(self):
        """Heuristic candidates only: resolved reads to image bytes not claimed as code."""
        counts=Counter()
        for x in self.an.accesses:
            if x['access'] not in ('R','RW') or x['address']=='?':continue
            a=int(x['address'],16)
            if self.an.img.contains(a) and not a in self.an.instructions and not any(parsehex(z['start'])<=a<=parsehex(z['end']) and 'RAM' in z['name'].upper() for z in self.zones()):counts[a]+=1
        return [{'address':f'{a:04X}','reads':count,'domain':self.domain(a),'classification':self.classify(a)} for a,count in counts.most_common(200)]
    def table_preview(self,table_id):
        t=next((i for i in self.meta['tables'] if i['id']==table_id),None)
        if t is None:raise ValueError('Table not found')
        start=parsehex(t['start']);rows=int(t['rows']);columns=int(t['columns']);width=int(t['width'])
        if rows<1 or columns<1 or rows*columns>8192:raise ValueError('Invalid table dimensions')
        signed=bool(t.get('signed'));scale=float(t.get('scale',1));offset=float(t.get('offset',0));endian=t.get('endian','big')
        values=[]
        for r in range(rows):
            line=[]
            for c in range(columns):
                addr=start+(r*columns+c)*width;buf=self.an.img.read(addr,width)
                if len(buf)!=width:line.append({'address':f'{addr:04X}','raw':None,'value':None});continue
                raw=int.from_bytes(buf,endian,signed=signed)
                line.append(dict(address=f'{addr:04X}',hex=buf.hex().upper(),raw=raw,value=round(raw*scale+offset,5)))
            values.append(line)
        ref=[]
        end=start+rows*columns*width
        for x in self.an.accesses:
            if x['address']!='?':
                a=int(x['address'],16)
                if start<=a<end:ref.append({**x})
        return {'definition':t,'values':values,'references':ref[:200], 'references_truncated':len(ref)>200}
    def annotate(self,key,value):
        if not re.fullmatch(r'[RIA]:[0-9A-F]{4}',key):raise ValueError('Annotation key must be R:1234, I:1234, or A:1234')
        if not isinstance(value,dict):raise ValueError('Annotation must be an object')
        clean={k:str(v)[:5000] for k,v in value.items() if k in {'label','notes','group','color','category','confidence','math','flags'}}
        if clean:self.meta['annotations'][key]=clean
        else:self.meta['annotations'].pop(key,None)
        self.save_meta();self.summary_cache=None
        return {'key':key,'annotation':clean}
    def upsert_table(self,obj):
        if not isinstance(obj,dict):raise ValueError('Invalid table')
        t={
            'id':str(obj.get('id','') or ('T_'+hexaddr(obj['start'])))[:64],
            'label':str(obj.get('label','New table'))[:160],
            'start':hexaddr(obj.get('start','4000')),
            'rows':int(obj.get('rows',1)), 'columns':int(obj.get('columns',16)),
            'width':int(obj.get('width',1)), 'endian':str(obj.get('endian','big')),
            'signed':bool(obj.get('signed',False)), 'scale':float(obj.get('scale',1)),
            'offset':float(obj.get('offset',0)), 'units':str(obj.get('units',''))[:60],
            'notes':str(obj.get('notes',''))[:3000], 'group':str(obj.get('group','Calibration'))[:80],
            'source':str(obj.get('source','user_defined'))[:160],
            'row_labels':str(obj.get('row_labels',''))[:2000],
            'column_labels':str(obj.get('column_labels',''))[:2000],
            'bits':str(obj.get('bits',''))[:2000],
        }
        if t['width'] not in (1,2,4) or t['endian'] not in ('big','little') or t['rows']<1 or t['columns']<1 or t['rows']*t['columns']>8192 or parsehex(t['start'])+t['rows']*t['columns']*t['width']>0x10000:raise ValueError('Invalid table dimensions/address')
        self.meta['tables']=[x for x in self.meta['tables'] if x['id']!=t['id']]+[t]
        self.save_meta();self.summary_cache=None
        return self.table_preview(t['id'])
    def upsert_region(self,obj):
        t=dict(id=str(obj.get('id') or f'Z_{hexaddr(obj["start"])}')[:64],start=hexaddr(obj['start']),end=hexaddr(obj['end']),type=str(obj.get('type','data'))[:80],label=str(obj.get('label',''))[:120],color=str(obj.get('color',''))[:32],group=str(obj.get('group','Unsorted'))[:80],notes=str(obj.get('notes',''))[:3000])
        if parsehex(t['end'])<parsehex(t['start']):raise ValueError('Region end precedes start')
        self.meta['regions']=[x for x in self.meta['regions'] if x['id']!=t['id']]+[t]
        self.save_meta();self.summary_cache=None;return t
    def setup(self,change):
        if 'profile' in change:
            p=change['profile'];
            if p not in ('generic','gm_7427_31'):raise ValueError('Unrecognized profile')
            self.meta['profile']=p
        if 'entries' in change:self.meta['entries']=list(dict.fromkeys(hexaddr(x) for x in change['entries']))[:1024]
        if 'dispatch_tables' in change:
            self.meta['dispatch_tables']=[dict(address=hexaddr(x['address']),count=int(x['count'])) for x in change['dispatch_tables']]
        if 'load_address' in change:
            load=parsehex(change['load_address'])
            if load+len(self.raw)>65536:raise ValueError('Image exceeds address range')
            self.meta['load_address']=load
        if 'zones' in change:
            zones=[]
            for z in change['zones']:
                zones.append({'name':str(z['name'])[:80],'start':hexaddr(z['start']),'end':hexaddr(z['end'])})
            self.meta['zones']=zones
        self.save_meta();self.analyze();return self.summary()

class Handler(BaseHTTPRequestHandler):
    server_version='ROMFlowStudio/0.2'
    def log_message(self,fmt,*args):pass
    def respond(self,payload,status=200,ctype='application/json; charset=utf-8',filename=None):
        if isinstance(payload,(dict,list)):body=js(payload).encode()
        elif isinstance(payload,str):body=payload.encode()
        else:body=payload
        self.send_response(status);self.send_header('Content-Type',ctype);self.send_header('Content-Length',str(len(body)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
        self.end_headers();self.wfile.write(body)
    def do_GET(self):
        try:self.get_route()
        except (ValueError,IndexError,KeyError) as exc:self.respond({'error':str(exc)},400)
        except Exception as exc:self.respond({'error':type(exc).__name__+': '+str(exc)},500)
    def do_POST(self):
        try:
            ln=int(self.headers.get('Content-Length',0))
            if not 0<ln<=MAX_BODY:raise ValueError('Request too large or empty')
            inp=json.loads(self.rfile.read(ln))
            self.post_route(urlsplit(self.path).path,inp)
        except (ValueError,IndexError,KeyError) as exc:self.respond({'error':str(exc)},400)
        except Exception as exc:self.respond({'error':type(exc).__name__+': '+str(exc)},500)
    @property
    def ws(self):return self.server.workspace
    def get_route(self):
        url=urlsplit(self.path);path=url.path;query={k:v[0] for k,v in parse_qs(url.query).items()}
        with self.ws.lock:
            if path=='/api/state':return self.respond(self.ws.summary())
            if path=='/api/graph':return self.respond(global_graph(self.ws.an) if query.get('mode')=='global' else routine_graph(self.ws.an,parsehex(query.get('entry','8100'))))
            if path=='/api/routine':return self.respond(self.ws.routine(query['entry']))
            if path=='/api/hex':return self.respond(self.ws.hex_window(query.get('start','4000'),int(query.get('count',256))))
            if path=='/api/address':return self.respond(self.ws.address_info(query['address']))
            if path=='/api/accesses':return self.respond(self.ws.access_list(query))
            if path=='/api/rom-reads':return self.respond(self.ws.rom_references())
            if path=='/api/table':return self.respond(self.ws.table_preview(query['id']))
            if path=='/api/save-project':
                filename='ROMFlow_'+self.ws.sha[:12]+'.romflow'
                return self.respond(self.ws.portable_project(),ctype='application/octet-stream',filename=filename)
            if path=='/api/projects':
                rows=[]
                for folder in sorted((self.ws.root/'projects').glob('*')):
                    mp=folder/'annotations.json'
                    if mp.exists():
                        roms=[x for x in folder.iterdir() if x.is_file() and x.name!='annotations.json']
                        if roms:rows.append({'sha_prefix':folder.name,'rom':roms[0].name,'active':folder.name==self.ws.sha[:20]})
                return self.respond(rows)
            if path=='/api/export':
                obj={'format':'ROMFlowStudioProject','rom_sha256':self.ws.sha,'rom_name':self.ws.filename,'image_start':f'{self.ws.an.img.start:04X}','annotations':self.ws.meta,'analysis':self.ws.an.serializable()}
                return self.respond(js(obj),ctype='application/json; charset=utf-8',filename='ROMFlow_'+self.ws.sha[:12]+'_project.json')
            if path=='/api/export-zip':
                bio=io.BytesIO();a=self.ws.an
                with zipfile.ZipFile(bio,'w',zipfile.ZIP_DEFLATED) as z:
                    z.writestr('project.json',js({'sha256':self.ws.sha,'name':self.ws.filename,'metadata':self.ws.meta}))
                    z.writestr('analysis.json',js(a.serializable()))
                    z.writestr('memory_accesses.csv',self.csv_string(a.accesses))
                    z.writestr('calls.csv',self.csv_string(a.calls))
                    z.writestr('vectors.csv',self.csv_string(a.vectors))
                    z.writestr('dispatch.csv',self.csv_string(a.dispatch))
                    for e in sorted(a.routines):z.writestr(f'routines/{e:04X}.json',js(self.ws.routine(f'{e:04X}')))
                    for t in self.ws.meta['tables']:z.writestr(f'tables/{t["id"]}.json',js(self.ws.table_preview(t['id'])))
                return self.respond(bio.getvalue(),ctype='application/zip',filename='ROMFlow_'+self.ws.sha[:12]+'_reports.zip')
        static={'/':'index.html','/app.js':'app.js','/style.css':'style.css','/favicon.svg':'favicon.svg'}
        if path not in static:return self.respond({'error':'not found'},404)
        file=STATIC/static[path];mime={'html':'text/html','js':'application/javascript','css':'text/css','svg':'image/svg+xml'}[file.suffix[1:]]
        return self.respond(file.read_bytes(),ctype=mime+'; charset=utf-8')
    def csv_string(self,rows):
        if not rows:return ''
        fields=list(dict.fromkeys(k for r in rows for k in r))
        buff=io.StringIO();w=csv.DictWriter(buff,fields);w.writeheader();w.writerows(rows);return buff.getvalue()
    def post_route(self,path,inp):
        with self.ws.lock:
            if path=='/api/rom':
                name=Path(str(inp.get('name','uploaded.bin'))).name
                if not name.lower().endswith(('.bin','.rom','.img')):name+='.bin'
                data=base64.b64decode(inp['data_b64'],validate=True)
                if len(data)>65536 or len(data)<1:raise ValueError('Binary must contain 1-65536 bytes')
                target=self.ws.root/'uploads'/hashlib.sha256(data).hexdigest()[:16]/name
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
                response=self.ws.open_rom(target,inp.get('profile','generic'))
                if inp.get('load_address') is not None:response=self.ws.setup({'load_address':inp['load_address']})
                return self.respond(response)
            if path=='/api/load-project':
                data=base64.b64decode(inp['data_b64'],validate=True)
                return self.respond(self.ws.load_project(data))
            if path=='/api/reopen':
                sha_prefix=str(inp['sha_prefix'])
                if not re.fullmatch('[0-9a-f]{20}',sha_prefix):raise ValueError('Invalid workspace reference')
                folder=self.ws.root/'projects'/sha_prefix
                roms=[x for x in folder.iterdir() if x.is_file() and x.name!='annotations.json'] if folder.is_dir() else []
                if not roms:raise ValueError('Workspace no longer exists')
                return self.respond(self.ws.open_rom(roms[0]))
            if path=='/api/view':return self.respond(self.ws.set_view(inp))
            if path=='/api/annotation':return self.respond(self.ws.annotate(inp['key'],inp.get('value',{})))
            if path=='/api/table':return self.respond(self.ws.upsert_table(inp))
            if path=='/api/table/delete':
                self.ws.meta['tables']=[t for t in self.ws.meta['tables'] if t['id']!=inp['id']]
                self.ws.save_meta();self.ws.summary_cache=None;return self.respond({'ok':True})
            if path=='/api/region':return self.respond(self.ws.upsert_region(inp))
            if path=='/api/region/delete':
                self.ws.meta['regions']=[t for t in self.ws.meta['regions'] if t['id']!=inp['id']]
                self.ws.save_meta();self.ws.summary_cache=None;return self.respond({'ok':True})
            if path=='/api/setup':return self.respond(self.ws.setup(inp))
            if path=='/api/hints':
                if self.ws.meta['profile']!='gm_7427_31':raise ValueError('Select 7427/$31 profile first')
                hints=json.loads(PROFILE_FILE.read_text())['table_hints']
                existing={t['id'] for t in self.ws.meta['tables']}
                for t in hints:
                    if t['id'] not in existing:self.ws.upsert_table(t)
                return self.respond(self.ws.summary())
            if path=='/api/project/import':
                d=inp.get('annotations',inp.get('metadata'))
                if not isinstance(d,dict):raise ValueError('Project metadata missing')
                if inp.get('rom_sha256') and inp['rom_sha256']!=self.ws.sha:raise ValueError('ROM SHA-256 differs; import explicitly requires same ROM')
                for k in ('annotations','tables','regions','groups'):
                    if k in d:self.ws.meta[k]=d[k]
                self.ws.save_meta();self.ws.summary_cache=None;return self.respond(self.ws.summary())
        return self.respond({'error':'not found'},404)

def main(argv=None):
    ap=argparse.ArgumentParser(description='ROMFlow Studio — local interactive 68HC11 ROM workbench')
    ap.add_argument('--port',type=int,default=8765);ap.add_argument('--host',default='127.0.0.1')
    ap.add_argument('--data-dir',type=Path);ap.add_argument('--no-browser',action='store_true')
    ap.add_argument('--rom',type=Path);ap.add_argument('--project',type=Path,help='Open a saved .romflow project')
    ap.add_argument('--profile',choices=['generic','gm_7427_31'],default='generic')
    args=ap.parse_args(argv)
    if args.host not in ('127.0.0.1','localhost','::1'):ap.error('The workbench binds to loopback only')
    ws=Workspace(args.data_dir)
    if args.rom and args.project:ap.error('Choose either --rom or --project')
    if args.rom:ws.open_rom(args.rom,args.profile)
    if args.project:ws.load_project(args.project.read_bytes())
    server=ThreadingHTTPServer((args.host,args.port),Handler)
    server.workspace=ws
    url=f'http://127.0.0.1:{server.server_port}/'
    print(f'ROMFlow Studio: {url}');print('Local-only, no network dependencies. Press Ctrl+C to exit.')
    if not args.no_browser:threading.Timer(.6,lambda:webbrowser.open(url)).start()
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()

if __name__=='__main__':main()
