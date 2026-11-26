"""Deterministic BMHM build engine and command-line interface."""
from __future__ import annotations

import argparse
import hashlib
import io
import json
from pathlib import Path
import re
import tempfile
from xml.etree import ElementTree as ET
from zipfile import ZipFile, ZipInfo

from manual_idle_asm import assemble

STOCK_SHA = '6188975246cf0042979f3a1694e3d43a2985a1452e7547a3b9e8a66d10e65004'
FEATURE = 0x400F
FEATURE_MASK = 0x08
CURVE = 0x46E4
CURVE_COUNT = 8
CURVE_TEMPERATURES = tuple(range(75, 111, 5))
HOOK = 0x7AA9
HOOK_STOCK = bytes.fromhex('BD CF 15')
NOP = 0x01
SPARK_HEADER = bytes([0, 0, 17])
SPARK_WIDTH = SPARK_HEADER[2]
SPARK_BLOCK_SIZE = len(SPARK_HEADER) + SPARK_WIDTH**2
# Symbol, display title, stock header address, and LDX immediate instruction address.
SPARK_TABLES = (
    ('spark_open', 'Open-throttle base spark', 0x4166, 0xA70C),
    ('spark_closed', 'Closed-throttle base spark', 0x428A, 0xA713),
)
# This inline site must fall through to the existing RTS at $7AAC.
INLINE_OPS = {'NOP', 'LDAA', 'LDAB', 'LDD', 'LDX', 'ADDA', 'ADDB', 'ANDA',
              'ANDB', 'ORAA', 'ORAB', 'EORA', 'EORB', 'CMPA', 'CMPB', 'CLRA', 'CLRB'}


def sha(image):
    return hashlib.sha256(image).hexdigest()


def load_stock(image):
    if len(image) == 0xc000:
        image = bytes([0xff]) * 0x4000 + image
    if len(image) != 0x10000 or sha(image) != STOCK_SHA:
        raise ValueError('Expected the exact BMHM $31 stock image (48 KiB mapped or 64 KiB padded).')
    return image


def defaults():
    return {'version': 1, 'burst_spark': 'stock', 'burst_curve': None,
            'slot_00': {'mode': 'stock', 'assembly': ''},
            'custom_assembly': '', 'tables': [], 'spark_layout': 'stock'}


def json_bytes(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + '\n').encode()


def byte_array(value, count, label):
    if (not isinstance(value, list) or len(value) != count or
            any(type(cell) is not int or not 0 <= cell <= 255 for cell in value)):
        raise ValueError(f'{label} requires {count} integer cells from 0 to 255.')
    return bytes(value)


def inline_code(source):
    if not source.strip():
        raise ValueError('Enter one or more inline instructions.')
    for number, line in enumerate(source.splitlines(), 1):
        code = line.partition(';')[0].strip()
        if not code:
            continue
        fields = code.split(None, 1)
        if fields[0].upper() not in INLINE_OPS or len(fields) > 1 and not fields[1].startswith('#'):
            raise ValueError(f'Inline line {number} requires an allowed register-only instruction or immediate operand.')
    with tempfile.TemporaryDirectory() as work:
        path = Path(work) / 'slot_00.asm'
        path.write_text(f'.org ${HOOK:04X}\n' + source, encoding='utf-8')
        assembly = assemble(path)
    length = len(assembly.memory)
    if not 1 <= length <= len(HOOK_STOCK) or set(assembly.memory) != set(range(HOOK, HOOK+length)):
        raise ValueError('Slot 00 inline assembly must fit the three existing call bytes.')
    return bytes(assembly.memory[a] for a in range(HOOK, HOOK+length)).ljust(len(HOOK_STOCK), bytes([NOP]))


def table_source(tables):
    if not isinstance(tables, list) or len(tables) > 16:
        raise ValueError('A project supports up to 16 custom tables.')
    lines = ['; Custom table source. Include only after assigning reviewed ROM space.']
    names = set()
    for table in tables:
        if not isinstance(table, dict) or set(table) != {'name', 'rows', 'cols', 'cells'}:
            raise ValueError('Each custom table needs a name, dimensions and cells.')
        name, rows, cols = table['name'], table['rows'], table['cols']
        if not isinstance(name, str) or not re.fullmatch(r'[A-Za-z][A-Za-z0-9_]{0,30}', name):
            raise ValueError('Table names must start with a letter and use up to 31 letters, digits or underscores.')
        symbol = name.upper()
        if symbol in names:
            raise ValueError(f'Duplicate table symbol {symbol}.')
        names.add(symbol)
        if type(rows) is not int or type(cols) is not int or not 1 <= rows <= 16 or not 1 <= cols <= 16:
            raise ValueError(f'{symbol} requires 1 to 16 rows and columns.')
        cells = byte_array(table['cells'], rows*cols, symbol)
        prefix = 'CFG_' + symbol
        lines.extend(['', f'{prefix}_ROWS EQU {rows}', f'{prefix}_COLS EQU {cols}',
                      f'{prefix}_STRIDE EQU {cols}', f'{prefix}_DATA:'])
        for row in range(rows):
            values = cells[row*cols:(row+1)*cols]
            lines.append('        FCB     ' + ','.join(f'${value:02X}' for value in values))
    return '\n'.join(lines) + '\n'


def spark_placements(original, layout):
    destinations = [table[2] for table in SPARK_TABLES]
    if layout == 'swap':
        destinations.reverse()
    placements = []
    for (symbol, title, address, reference), destination in zip(SPARK_TABLES, destinations):
        if original[address:address+len(SPARK_HEADER)] != SPARK_HEADER:
            raise ValueError(f'Unexpected stock header for {title}.')
        expected = b'\xCE' + address.to_bytes(2, 'big')
        if original[reference:reference+len(expected)] != expected:
            raise ValueError(f'Unexpected stock pointer instruction for {title}.')
        placements.append((symbol, title, address, destination, reference))
    return placements


def xdf_table(root, uid, title, address, x_labels, y_labels, x_units='', y_units=''):
    table = ET.SubElement(root, 'XDFTABLE', uniqueid=uid, vislevel='1', flags='0x0')
    ET.SubElement(table, 'CATEGORYMEM', index='0', category='1')
    ET.SubElement(table, 'title').text = title
    for name, labels, units in [('x', x_labels, x_units), ('y', y_labels, y_units)]:
        axis = ET.SubElement(table, 'XDFAXIS', id=name, uniqueid='0x0')
        ET.SubElement(axis, 'EMBEDDEDDATA', mmedelementsizebits='16',
                      mmedmajorstridebits='-32', mmedminorstridebits='0')
        ET.SubElement(axis, 'indexcount').text = str(len(labels))
        if units:
            ET.SubElement(axis, 'units').text = units
        ET.SubElement(axis, 'outputtype').text = '4'
        ET.SubElement(axis, 'datatype').text = '0'
        ET.SubElement(axis, 'unittype').text = '0'
        ET.SubElement(axis, 'DALINK', index='0')
        for index, label in enumerate(labels):
            ET.SubElement(axis, 'LABEL', index=str(index), value=str(label))
        ET.SubElement(ET.SubElement(axis, 'MATH', equation='X'), 'VAR', id='X')
    data = ET.SubElement(table, 'XDFAXIS', id='z')
    ET.SubElement(data, 'EMBEDDEDDATA', mmedaddress=f'0x{address:X}', mmedelementsizebits='8',
                  mmedrowcount=str(len(y_labels)), mmedcolcount=str(len(x_labels)),
                  mmedtypeflags='0x00', mmedmajorstridebits='0', mmedminorstridebits='0')
    ET.SubElement(data, 'units').text = 'Raw spark'
    ET.SubElement(data, 'outputtype').text = '1'
    ET.SubElement(data, 'min').text = '0'
    ET.SubElement(data, 'max').text = '255'
    ET.SubElement(ET.SubElement(data, 'MATH', equation='X'), 'VAR', id='X')


def make_xdf(image_hash, placements):
    root = ET.Element('XDFFORMAT', version='1.80')
    header = ET.SubElement(root, 'XDFHEADER')
    for key, value in [('flags', '0x1'), ('fileversion', '1.0'), ('deftitle', '7427 Configurator – BMHM spark'),
                       ('description', f'Full 64 KiB address space. Build SHA-256 {image_hash}.')]:
        ET.SubElement(header, key).text = value
    ET.SubElement(header, 'BASEOFFSET', offset='0', subtract='0')
    ET.SubElement(header, 'DEFAULTS', datasizeinbits='8', sigdigits='2', outputtype='1',
                  signed='0', lsbfirst='0', float='0')
    ET.SubElement(header, 'REGION', type='0xFFFFFFFF', startaddress='0x0', size='0x10000',
                  regionflags='0x0', regioncolor='0x0', name='Binary File', desc='Full 64 KiB image')
    ET.SubElement(header, 'CATEGORY', index='0x0', name='Configurator')
    xdf_table(root, '0x7427', 'Burst spark gain curve', CURVE, [0], CURVE_TEMPERATURES,
              y_units='Nominal coolant °C')
    coordinates = range(0, SPARK_WIDTH*16, 16)
    for index, (_, title, _, destination, _) in enumerate(placements, 1):
        xdf_table(root, f'0x{0x7427+index:X}', title, destination+len(SPARK_HEADER),
                  coordinates, coordinates, 'Load lookup coordinate', 'RPM lookup coordinate')
    ET.indent(root)
    return ET.tostring(root, encoding='utf-8', xml_declaration=True) + b'\n'


def build(stock, config):
    original = load_stock(stock)
    if isinstance(config, dict) and set(config) == set(defaults()) - {'spark_layout'}:
        config = config | {'spark_layout': 'stock'}
    if (not isinstance(config, dict) or type(config.get('version')) is not int or
            config['version'] != 1 or set(config) != set(defaults())):
        raise ValueError('Expected a complete configurator project, version 1.')
    mode, curve, hook = config['burst_spark'], config['burst_curve'], config['slot_00']
    draft, tables = config['custom_assembly'], config['tables']
    if mode not in ('stock', 'enabled', 'disabled'):
        raise ValueError('Invalid burst spark setting.')
    if not isinstance(hook, dict) or set(hook) != {'mode', 'assembly'} or hook['mode'] not in ('stock', 'remove', 'inline'):
        raise ValueError('Invalid Slot 00 hook configuration.')
    for source in (hook['assembly'], draft):
        if not isinstance(source, str) or len(source) > 16000:
            raise ValueError('Assembly must be text of at most 16,000 characters.')
    if config['spark_layout'] not in ('stock', 'swap'):
        raise ValueError('Invalid base spark table layout.')
    placements = spark_placements(original, config['spark_layout'])
    generated_tables = table_source(tables)
    if isinstance(curve, list) and len(curve) == 11:
        legacy = byte_array(curve, 11, 'Legacy burst spark curve')
        if legacy[CURVE_COUNT:] != original[CURVE+CURVE_COUNT:CURVE+11]:
            raise ValueError('This old project changes adjacent dynamic-spark bytes. Restore the factory curve and re-enter its first eight values.')
        curve = list(legacy[:CURVE_COUNT])
        config = config | {'burst_curve': curve}

    image = bytearray(original)
    changes = []
    def replace(address, data, reason):
        before = original[address:address+len(data)]
        if before != data:
            changes.append({'address': f'${address:04X}', 'before': before.hex(' ').upper(),
                            'after': data.hex(' ').upper(), 'reason': reason})
            image[address:address+len(data)] = data

    if mode != 'stock':
        value = (original[FEATURE] & ~FEATURE_MASK) | (FEATURE_MASK if mode == 'enabled' else 0)
        replace(FEATURE, bytes([value]), 'Factory burst spark enable bit')
    if curve is not None:
        replace(CURVE, byte_array(curve, CURVE_COUNT, 'Stock burst spark curve'), 'Stock burst spark gain cells')
    if original[HOOK:HOOK+len(HOOK_STOCK)+1] != HOOK_STOCK + b'\x39' or original[0xCF15] != 0x39:
        raise ValueError('Stock Slot 00 call or return bytes differ from the reviewed site.')
    if hook['mode'] == 'remove':
        replace(HOOK, bytes([NOP])*len(HOOK_STOCK), 'Remove Slot 00 call to the fixed RTS at $CF15')
    elif hook['mode'] == 'inline':
        replace(HOOK, inline_code(hook['assembly']), 'Slot 00 inline assembly before the stock RTS')
    relocations = []
    for symbol, title, source, destination, reference in placements:
        if source == destination:
            continue
        replace(destination, original[source:source+SPARK_BLOCK_SIZE], f'Relocate {title}')
        replace(reference+1, destination.to_bytes(2, 'big'), f'Update {title} LDX operand')
        relocations.append({'symbol': symbol, 'title': title, 'from': f'${source:04X}',
                            'to': f'${destination:04X}', 'size': SPARK_BLOCK_SIZE,
                            'operand_address': f'${reference+1:04X}',
                            'xdf_address': f'${destination+len(SPARK_HEADER):04X}'})
    checksum = sum(image[0x4008:]) & 0xffff
    replace(0x4006, checksum.to_bytes(2, 'big'), 'BMHM additive checksum')
    output = bytes(image)
    image_hash = sha(output)
    report = {'baseline_sha256': STOCK_SHA, 'image_sha256': image_hash, 'checksum': f'${checksum:04X}',
              'changed_bytes': sum(a!=b for a,b in zip(original, output)),
              'relocations': relocations, 'changes': sorted(changes, key=lambda row: row['address']),
              'draft_table_count': len(tables), 'draft_assembly': bool(draft.strip())}
    files = {'bmhm-configured.bin': output, 'bmhm-configured.xdf': make_xdf(image_hash, placements),
             'project.json': json_bytes(config), 'changes.json': json_bytes(report)}
    if draft.strip():
        files['draft/custom.asm'] = draft.encode('utf-8')
    if tables:
        files['draft/tables.inc'] = generated_tables.encode('utf-8')
    return report, files


def bundle(files):
    result = io.BytesIO()
    with ZipFile(result, 'w') as archive:
        for name, data in sorted(files.items()):
            archive.writestr(ZipInfo(name), data)
    return result.getvalue()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stock', type=Path)
    parser.add_argument('project', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    try:
        _, files = build(args.stock.read_bytes(), json.loads(args.project.read_text(encoding='utf-8')))
        args.output.write_bytes(bundle(files))
    except (OSError, ValueError) as exc:
        parser.exit(1, f'{exc}\n')


if __name__ == '__main__':
    main()
