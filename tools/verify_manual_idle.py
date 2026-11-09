"""Run manual-idle C/HC11 tests and reproduce their committed witness summary."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
import test_manual_idle as tests


def verify():
    result = unittest.TextTestRunner(verbosity=2).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(tests.ManualIdle))
    if not result.wasSuccessful(): raise SystemExit(1)
    cls = tests.ManualIdle
    return dict(
        assembly_source_sha256=hashlib.sha256((ROOT / 'source/manual_idle/manual_idle.asm').read_bytes()).hexdigest(),
        c_source_sha256=hashlib.sha256((ROOT / 'source/manual_idle/manual_idle.c').read_bytes()).hexdigest(),
        differential_cases=cls.count,
        replacement_instructions_exercised=len(cls.pcs & set(tests.ASSEMBLY.instructions)),
        replacement_instructions=len(tests.ASSEMBLY.instructions),
        maximum_observed_bounded_cycles=cls.max_cycles,
        minimum_observed_bounded_sp=f'{cls.minimum_sp:04X}', tests=result.testsRun,
        scope='Native C versus exact emitted HC11, with independent admission/sign/decay/rail properties. Excerpt fixtures have no interrupts, physical I/O, or engine dynamics. Cycle maxima describe exercised fixtures, not WCET.')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    group = p.add_mutually_exclusive_group()
    group.add_argument('--write-report', action='store_true')
    group.add_argument('--check-recorded', action='store_true')
    args = p.parse_args()
    report = verify()
    path = ROOT / 'maps/maintenance/manual_idle_test_results.json'
    if args.write_report: path.write_text(json.dumps(report, indent=2) + '\n')
    if args.check_recorded and json.loads(path.read_text()) != report:
        raise SystemExit('Manual-idle witness summary is stale; review source/test changes and regenerate')
    print(json.dumps(report, indent=2))
