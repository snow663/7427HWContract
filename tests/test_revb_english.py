"""Reader coverage and safety of local explanatory flag/pointer provenance."""
import json
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from explain_revb_bin import English,flag_effect,build,SHA
from factory_rom_decode import decode


def inst(raw,pc=0x7000):
    b=bytes.fromhex(raw);return decode(lambda a,n:b[a-pc:a-pc+n],pc)


class EnglishReader(unittest.TestCase):
    def test_every_present_mnemonic_has_an_explanation(self):
        data=json.loads((ROOT/'maps/maintenance/revb_operation_examples.json').read_text())
        self.assertEqual(data['image_sha256'],SHA);self.assertEqual(len(data['examples']),112)
        for op,row in data['examples'].items():
            i=inst(row['bytes'],int(row['address'],16));self.assertEqual(i.op,op)
            text=English({},{}).describe(i);self.assertTrue(text.strip(),op)
            self.assertNotIn('No English semantics',text)

    def test_pull_and_stack_address_transfer_preserve_compare(self):
        e=English({0x1d9:'normalized TPS',0x50a9:'TPS cutoff'}, {})
        e.describe(inst('B6 01 D9'));e.describe(inst('B1 50 A9'))
        e.describe(inst('32'));e.describe(inst('30'))
        self.assertIn('normalized TPS is at least TPS cutoff',e.describe(inst('24 01')))
        self.assertIn('preserved',flag_effect('TSX'))

    def test_clear_does_not_keep_an_old_borrow_explanation(self):
        e=English({0x50a9:'TPS cutoff'},{});e.describe(inst('B1 50 A9'));e.describe(inst('5F'))
        text=e.describe(inst('24 01'))
        self.assertNotIn('TPS cutoff',text);self.assertIn('C=0',flag_effect('CLRB'))

    def test_test_instruction_clears_carry(self):
        self.assertIn('C=0',flag_effect('TSTA'))

    def test_index_increment_changes_zero_only(self):
        e=English({0x50a9:'TPS cutoff'},{});e.describe(inst('B1 50 A9'));e.describe(inst('08'))
        self.assertIn('TPS cutoff',e.describe(inst('24 01')))
        self.assertIn('X is nonzero',e.describe(inst('26 01')))
        self.assertIn('Only Z',flag_effect('INX'))

    def test_unknown_call_discards_pointer_and_flag_context(self):
        e=English({0x50a9:'TPS cutoff'},{});e.describe(inst('CE 50 A9'));e.describe(inst('B1 50 A9'))
        e.describe(inst('BD 81 00'))
        self.assertNotIn('TPS cutoff',e.describe(inst('24 01')))
        self.assertIn('address in X',e.describe(inst('A6 00')))

    def test_bit_branches_require_all_selected_bits(self):
        e=English({},{});self.assertIn('all set',e.describe(inst('12 42 03 01')))
        self.assertIn('all clear',e.describe(inst('13 42 03 01')))

    def test_indexed_load_follows_known_pointer_only_locally(self):
        e=English({0x50a9:'TPS cutoff'},{});e.describe(inst('CE 50 A8'))
        self.assertIn('$50A9',e.describe(inst('A6 01')))
        e.reset();self.assertNotIn('$50A9',e.describe(inst('A6 01')))

    def test_signed_and_unsigned_branches_are_distinct(self):
        e=English({},{});e.describe(inst('1A B3 01 EE'))
        self.assertIn('signed comparison',e.describe(inst('2D 01')))
        self.assertIn('unsigned',e.describe(inst('25 01')))

    def test_wrong_image_is_not_guessed(self):
        with self.assertRaises(ValueError):build(bytes(65536),Path('/tmp/not_created_revb_reader'))

    def test_reviewed_enrichment_comment_is_input_specific(self):
        e=English({},{});self.assertIn('normalized TPS',e.describe(inst('B6 01 D9',0x9a4f)))
        self.assertIn('air-command',e.describe(inst('B1 50 A8',0x9a5a)))


if __name__=='__main__':unittest.main(verbosity=2)
