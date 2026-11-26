import json
import os
from pathlib import Path
import unittest
from xml.etree import ElementTree as ET

from configurator import (CURVE, FEATURE, HOOK, SPARK_BLOCK_SIZE, SPARK_TABLES, STOCK_SHA,
                          build, bundle, defaults, inline_code, load_stock, spark_placements, spark_table_info, table_source)


class SourceTests(unittest.TestCase):
    def test_inline_assembly_and_padding(self):
        self.assertEqual(inline_code('LDAA #$42'), bytes.fromhex('86 42 01'))
        self.assertEqual(inline_code('LDD #$1234'), bytes.fromhex('CC 12 34'))
        for rejected in ('', 'RTS', 'JMP $4000', 'LDAA $50', 'LDAA #256', 'LDD #0\nNOP'):
            with self.subTest(rejected=rejected), self.assertRaises(ValueError):
                inline_code(rejected)

    def test_custom_table_geometry(self):
        table = {'name': 'mix', 'rows': 2, 'cols': 3, 'cells': list(range(6))}
        source = table_source([table])
        self.assertIn('CFG_MIX_ROWS EQU 2', source)
        self.assertIn('CFG_MIX_COLS EQU 3', source)
        self.assertIn('CFG_MIX_STRIDE EQU 3', source)
        self.assertIn('FCB     $03,$04,$05', source)
        with self.assertRaises(ValueError):
            table_source([table, table | {'name': 'MIX'}])
        with self.assertRaises(ValueError):
            table_source([table | {'cols': 4}])

    def test_wrong_baseline_is_refused(self):
        with self.assertRaises(ValueError):
            load_stock(bytes(0x10000))


@unittest.skipUnless(os.getenv('BMHM_STOCK_BIN'), 'set BMHM_STOCK_BIN for factory builds')
class StockTests(unittest.TestCase):
    def setUp(self):
        self.stock = load_stock(Path(os.environ['BMHM_STOCK_BIN']).read_bytes())

    def test_stock_and_mapped_image_are_identical(self):
        report, files = build(self.stock, defaults())
        self.assertEqual(report['image_sha256'], STOCK_SHA)
        self.assertEqual(report['changed_bytes'], 0)
        self.assertEqual(files['bmhm-configured.bin'], self.stock)
        self.assertEqual(bundle(files), bundle(build(self.stock[0x4000:], defaults())[1]))

    def test_spark_swap_relocates_tables_references_and_xdf(self):
        project = defaults() | {'spark_layout': 'swap'}
        report, files = build(self.stock, project)
        image = files['bmhm-configured.bin']
        xdf = ET.fromstring(files['bmhm-configured.xdf'])
        allowed = set()
        for index, (symbol, title, source, reference) in enumerate(SPARK_TABLES):
            destination = SPARK_TABLES[1-index][2]
            self.assertEqual(image[destination:destination+SPARK_BLOCK_SIZE],
                             self.stock[source:source+SPARK_BLOCK_SIZE])
            self.assertEqual(image[reference:reference+3], b'\xCE' + destination.to_bytes(2, 'big'))
            moved = report['relocations'][index]
            self.assertEqual((moved['symbol'], moved['from'], moved['to']),
                             (symbol, f'${source:04X}', f'${destination:04X}'))
            table = next(item for item in xdf.findall('XDFTABLE') if item.findtext('title') == title)
            data = table.find(".//XDFAXIS[@id='z']/EMBEDDEDDATA")
            self.assertEqual(int(data.get('mmedaddress'), 16), destination+3)
            self.assertEqual((data.get('mmedrowcount'), data.get('mmedcolcount')), ('17', '17'))
            allowed.update(range(destination, destination+SPARK_BLOCK_SIZE))
            allowed.update((reference+1, reference+2))
        changed = {address for address, (before, after) in enumerate(zip(self.stock, image)) if before != after}
        self.assertLessEqual(changed, allowed)
        self.assertEqual(image[0x43AE:0x43B2], self.stock[0x43AE:0x43B2])
        self.assertEqual(image[0x4006:0x4008], (sum(image[0x4008:]) & 65535).to_bytes(2, 'big'))
        self.assertEqual(bundle(files), bundle(build(self.stock, project)[1]))

    def test_stock_layout_compatibility_and_reference_validation(self):
        legacy = defaults()
        del legacy['spark_grids']
        self.assertEqual(build(self.stock, legacy), build(self.stock, defaults()))
        del legacy['spark_layout']
        self.assertEqual(build(self.stock, legacy), build(self.stock, defaults()))
        with self.assertRaisesRegex(ValueError, 'layout'):
            build(self.stock, defaults() | {'spark_layout': 'grow'})
        corrupt = bytearray(self.stock)
        corrupt[SPARK_TABLES[0][3]+1] ^= 1
        with self.assertRaisesRegex(ValueError, 'pointer instruction'):
            spark_placements(corrupt, 'swap')

    def test_base_spark_edits_follow_table_identity(self):
        tables = spark_table_info(self.stock)
        grids = {}
        for table in tables:
            grids[table['symbol']] = table['cells'].copy()
        grids['spark_open'][17*4+8] ^= 1
        grids['spark_closed'][-1] ^= 1
        for layout in ('stock', 'swap'):
            with self.subTest(layout=layout):
                project = defaults() | {'spark_layout': layout, 'spark_grids': grids}
                report, files = build(self.stock, project)
                baseline = build(self.stock, defaults() | {'spark_layout': layout})[1]['bmhm-configured.bin']
                image = files['bmhm-configured.bin']
                expected_edits = set()
                for index, offset in enumerate((17*4+8, 17*17-1)):
                    symbol = tables[index]['symbol']
                    destination = SPARK_TABLES[index if layout == 'stock' else 1-index][2]
                    data = destination + 3
                    self.assertEqual(image[destination:data], bytes((0, 0, 17)))
                    self.assertEqual(image[data:data+17*17], bytes(grids[symbol]))
                    expected_edits.add(data+offset)
                    row, column = divmod(offset, 17)
                    self.assertEqual(report['spark_edits'][index], {
                        'symbol': symbol, 'title': tables[index]['title'],
                        'cells': [{'address': f'${data+offset:04X}', 'rpm': 16*row, 'load': 16*column,
                                   'before': tables[index]['cells'][offset], 'after': grids[symbol][offset]}],
                    })
                actual_edits = {a for a, (old, new) in enumerate(zip(baseline, image)) if old != new}
                self.assertEqual(actual_edits - {0x4006, 0x4007}, expected_edits)
                self.assertEqual(int.from_bytes(image[0x4006:0x4008], 'big'), sum(image[0x4008:]) & 65535)
                reconstructed = bytearray(image)
                for change in report['changes']:
                    start = int(change['address'][1:], 16)
                    original = bytes.fromhex(change['before'])
                    reconstructed[start:start+len(original)] = original
                self.assertEqual(reconstructed, self.stock)

    def test_invalid_spark_grids_are_rejected(self):
        grids = defaults()['spark_grids']
        for bad in ([0]*288, [0]*288 + [256], [0]*288 + [True], [0]*288 + [None]):
            with self.subTest(length=len(bad), last=bad[-1]), self.assertRaisesRegex(ValueError, 'integer cells'):
                build(self.stock, defaults() | {'spark_grids': grids | {'spark_open': bad}})
        with self.assertRaisesRegex(ValueError, 'grid settings'):
            build(self.stock, defaults() | {'spark_grids': {'spark_other': None}})

    def test_legacy_curve_projects_preserve_dynamic_spark(self):
        old_curve = list(range(8)) + list(self.stock[CURVE+8:CURVE+11])
        project = defaults() | {'burst_curve': old_curve}
        _, files = build(self.stock, project)
        self.assertEqual(files['bmhm-configured.bin'][CURVE+8:CURVE+11], bytes(old_curve[8:]))
        self.assertEqual(json.loads(files['project.json'])['burst_curve'], old_curve[:8])
        with self.assertRaisesRegex(ValueError, 'dynamic-spark'):
            build(self.stock, project | {'burst_curve': old_curve[:10] + [old_curve[10] ^ 1]})

    def test_mixed_edits_and_reproducibility(self):
        project = defaults() | {
            'burst_spark': 'enabled', 'burst_curve': list(range(8)),
            'slot_00': {'mode': 'remove', 'assembly': ''},
            'tables': [{'name':'test', 'rows':1, 'cols':2, 'cells':[1,2]}],
            'custom_assembly': 'Example:\n        RTS\n',
        }
        report, files = build(self.stock, project)
        image = files['bmhm-configured.bin']
        self.assertEqual(image[FEATURE], self.stock[FEATURE] | 8)
        self.assertEqual(image[CURVE:CURVE+8], bytes(range(8)))
        self.assertEqual(image[HOOK:HOOK+4], bytes.fromhex('01 01 01 39'))
        self.assertEqual(int.from_bytes(image[0x4006:0x4008], 'big'), sum(image[0x4008:]) & 65535)
        allowed = {FEATURE, HOOK, HOOK+1, HOOK+2, 0x4006, 0x4007, *range(CURVE, CURVE+8)}
        changed = {a for a in range(len(image)) if self.stock[a] != image[a]}
        self.assertLessEqual(changed, allowed)
        self.assertEqual(len(changed), report['changed_bytes'])
        self.assertIn('draft/custom.asm', files)
        self.assertIn('draft/tables.inc', files)
        self.assertEqual(bundle(files), bundle(build(self.stock, project)[1]))
        data = ET.fromstring(files['bmhm-configured.xdf']).find(".//XDFAXIS[@id='z']/EMBEDDEDDATA")
        self.assertEqual(int(data.attrib['mmedaddress'], 0), CURVE)
        self.assertEqual(int(data.attrib['mmedrowcount']), 8)

        restore = bytearray(image)
        for change in report['changes']:
            address = int(change['address'][1:], 16)
            before = bytes.fromhex(change['before'])
            restore[address:address+len(before)] = before
        self.assertEqual(restore, self.stock)


if __name__ == '__main__':
    unittest.main()
