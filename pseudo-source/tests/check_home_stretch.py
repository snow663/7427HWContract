#!/usr/bin/env python3
"""Fast source-only gate; does not establish ROM-wide or target equivalence."""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    manifest = json.loads((ROOT / 'reference/home_stretch_manifest.json').read_text())
    rows = list(csv.DictReader((ROOT / 'routine_index.csv').open(newline='')))
    names = {row['routine']: row for row in rows}
    require(len(names) == len(rows), 'Duplicate public routines')
    require(len({row['file'] for row in rows}) == len(rows), 'Duplicate source-file ownership')
    counts = Counter(row['status'] for row in rows)
    require(len(rows) == manifest['inventory']['indexed'], 'Routine inventory drift')
    for key in ('implemented_outline', 'implemented_algorithm', 'dependency_boundary'):
        require(counts[key] == manifest['inventory'][key], 'Inventory drift: ' + key)
    require(set(counts) == {'implemented_outline', 'implemented_algorithm', 'dependency_boundary'}, 'Unknown classification')
    actual = {name for name, row in names.items() if row['status'] == 'dependency_boundary'}
    require(actual == set(manifest['boundary_routines']), 'Dependency boundary ledger drift')
    for index in range(16):
        name = 'pcm_slot_%02x' % index
        require(name in names and names[name]['status'] != 'dependency_boundary',
                'Slow slot is missing/not resident: ' + name)

    fuel = (ROOT / 'src/fuel/fuel_control.c').read_text()
    slot1 = (ROOT / 'src/slots/slot_01.c').read_text()
    require(all(s in fuel for s in (
        'if(pcm->platform->enable_resident_fuel_cycle)',
        'if(!pcm->platform->bind_fuel_ram_owners)',
        'return pcm_fuel_cycle(pcm)',
        'SYS_RUN(pcm_fuel_ignition(pcm))',
        'SYS_RUN(pcm_fuel_inputs(pcm))',
        'SYS_RUN(pcm_fuel_calculate(pcm))',
        'return pcm_fuel_schedule(pcm)')),
        'Fuel root default/research policy has changed')
    require(all(s in slot1 for s in (
        'if(pcm->platform->enable_resident_slow_slots)',
        'return pcm_tcc_non_electronic(pcm)',
        'SYS_RUN(pcm_transmission_baro(pcm))',
        'return pcm_tcc_nonelectronic(pcm)')),
        'Slot01 default/research policy has changed')
    hooks = manifest['optional_hooks']
    require(len(hooks) == 8 and set(hooks) == {
        '1800', '1803', '1806', '1809', '180C', '180F', '1812', '1815'},
        'Optional-call ledger drift')
    require(all(hooks[k]['policy'] == 'unresolved' for k in hooks),
            'Module status cannot close without a reviewed target ABI')
    require((ROOT / 'reference/home_stretch_readiness.md').is_file(),
            'Missing target-port handoff')
    print('%d indexed routines: %d outlines + %d algorithms + %d boundaries; '
          '16 slow slots; two canonical default paths; eight optional hooks tracked.' %
          (len(rows), counts['implemented_outline'], counts['implemented_algorithm'],
           counts['dependency_boundary']))


if __name__ == '__main__':
    main()
