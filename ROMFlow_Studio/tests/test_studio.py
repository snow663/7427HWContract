import json, tempfile, unittest
from pathlib import Path
from studio.server import Workspace
from studio.graph import routine_graph, global_graph
from studio.mathtrace import math_traces

ROOT=Path(__file__).resolve().parents[1]
class StudioTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.ws=Workspace(Path(self.tmp.name))
    def tearDown(self):self.tmp.cleanup()
    def test_load_rooted_graph_and_calls(self):
        self.assertIn(0x8100,self.ws.an.routines)
        g=routine_graph(self.ws.an,0x8100)
        self.assertTrue(any(e['kind']=='call' and e['site']=='8106' for e in g['edges']))
        self.assertTrue(any(e['kind']=='jump' for e in g['edges']))
        gl=global_graph(self.ws.an)
        self.assertTrue(any(e['kind']=='call' and e['source']=='R8100' and e['target']=='R8400' for e in gl['edges']))
        self.assertTrue(any(e['kind'].startswith('slot') for e in gl['edges']))
    def test_annotation_roundtrip(self):
        self.ws.annotate('R:8100',dict(label='Main scheduler',group='Scheduler',notes='reviewed',color='#5ad4d2'))
        self.assertEqual(self.ws.summary()['routines'][0]['label'],'Main scheduler')
        ws2=Workspace(Path(self.tmp.name))
        self.assertEqual(ws2.meta['annotations']['R:8100']['group'],'Scheduler')
    def test_read_write_and_derived_math(self):
        info=self.ws.address_info('3022')
        self.assertTrue(any(x['pc']=='8103' and x['access']=='RW' for x in info['writers']))
        r=self.ws.routine('8100')
        self.assertTrue(any('mem8[$3022]' in x['math'] for x in r['instructions']))
        self.assertTrue(any(x['op']=='JSR' for x in r['instructions']))
    def test_table_values_and_scales_and_regions(self):
        self.ws.upsert_table(dict(label='Fixture ptrs',start='B200',rows=1,columns=3,width=2,scale=1,offset=0))
        t=self.ws.table_preview('T_B200')
        self.assertEqual([v['value'] for v in t['values'][0]],[0x8600,0x8610,0x8620])
        self.assertEqual(self.ws.classify(0xB200),'calibration/table (annotated)')
        self.ws.upsert_region(dict(start='B200',end='B205',type='embedded pointer table',label='Dispatcher'))
        self.assertEqual(self.ws.classify(0xB200),'embedded pointer table')
    def test_other_rom_auto_discovery_and_profile(self):
        self.ws.open_rom(ROOT/'examples'/'synthetic_B_32k_different_map.bin','generic')
        self.assertIn(0x9100,self.ws.an.routines)
        self.assertIn(0x9600,self.ws.an.routines)
        self.assertTrue(any(d['table']=='A300' for d in self.ws.an.dispatch))
        self.assertEqual(self.ws.domain(0x2E22),'external memory / IO (unknown)')
        self.ws.setup({'profile':'gm_7427_31'})
        self.assertEqual(self.ws.domain(0x3FCC),'GM external ASIC block (profile)')
        self.ws.meta['tables']=[]
        for t in json.loads((ROOT/'profiles'/'gm_7427_31.json').read_text())['table_hints']:self.ws.upsert_table(t)
        self.assertEqual(len(self.ws.meta['tables']),7)
    def test_invalid_address_and_bounds(self):
        with self.assertRaises(ValueError):self.ws.upsert_table(dict(start='FFF0',rows=2,columns=16,width=2))
        with self.assertRaises(ValueError):self.ws.upsert_region(dict(start='B200',end='A200',type='data'))
        with self.assertRaises(ValueError):self.ws.annotate('BROKEN',{})
    def test_hex_and_unknown_not_auto_calibrated(self):
        d=self.ws.hex_window('8100',5)
        self.assertEqual(d['cells'][0]['byte'],'CE')
        self.assertEqual(d['cells'][0]['classification'],'code (rooted)')
        self.assertIn('unclassified',self.ws.classify(0x5000))
        self.assertNotIn('calibration',self.ws.classify(0x5000))

if __name__=='__main__':unittest.main()

class PortableProjectTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.ws=Workspace(Path(self.tmp.name))
    def tearDown(self):self.tmp.cleanup()
    def test_roundtrip_includes_rom_metadata_and_view(self):
        import zipfile,io
        self.ws.annotate('R:8100',{'label':'Fuel main','group':'Fuel'})
        self.ws.upsert_table({'label':'VE table','start':'B200','rows':1,'columns':3,'width':2})
        self.ws.set_view({'mode':'routine','entry':'8100','expanded':['code','g_Fuel'],
                          'layouts':{'routine:8100':{'B8100':{'x':75.5,'y':120.25}}}})
        data=self.ws.portable_project()
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            self.assertEqual(set(z.namelist()),{'manifest.json','rom.bin','metadata.json'})
        tmp2=tempfile.TemporaryDirectory()
        try:
            restored=Workspace(Path(tmp2.name))
            restored.load_project(data)
            self.assertEqual(self.ws.raw,restored.raw)
            self.assertEqual(restored.meta['annotations']['R:8100']['label'],'Fuel main')
            self.assertEqual(restored.meta['tables'][0]['label'],'VE table')
            self.assertEqual(restored.meta['view']['layouts']['routine:8100']['B8100']['x'],75.5)
            self.assertEqual(restored.summary()['sha256'],self.ws.summary()['sha256'])
        finally:tmp2.cleanup()
    def test_invalid_project_rejected_without_changing_active(self):
        import zipfile,io
        data=self.ws.portable_project()
        original=self.ws.sha
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            manifest=json.loads(archive.read('manifest.json'))
            meta=archive.read('metadata.json')
            rom=bytearray(archive.read('rom.bin'))
        rom[100]^=1
        out=io.BytesIO()
        with zipfile.ZipFile(out,'w') as archive:
            archive.writestr('manifest.json',json.dumps(manifest))
            archive.writestr('rom.bin',rom)
            archive.writestr('metadata.json',meta)
        with self.assertRaises(ValueError):self.ws.load_project(out.getvalue())
        self.assertEqual(self.ws.sha,original)
    def test_workspace_reopen_after_process_restart(self):
        self.ws.annotate('I:8103',{'label':'timer mask bit'})
        revived=Workspace(Path(self.tmp.name))
        self.assertEqual(revived.sha,self.ws.sha)
        self.assertEqual(revived.meta['annotations']['I:8103']['label'],'timer mask bit')
