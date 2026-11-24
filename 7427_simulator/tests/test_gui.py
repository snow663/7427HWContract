import unittest
from sim7427.gui import Workbench, number

class GuiSmokeTest(unittest.TestCase):
    def test_import_and_number_parser_without_display(self):
        self.assertTrue(callable(Workbench))
        self.assertEqual(number("$3FCE"),0x3FCE)
        self.assertEqual(number("0x3000"),0x3000)
        self.assertEqual(number("4096"),4096)

if __name__=="__main__":
    unittest.main()
