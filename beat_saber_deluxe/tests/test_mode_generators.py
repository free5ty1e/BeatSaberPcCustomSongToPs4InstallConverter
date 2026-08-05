import unittest
from tools.full_custom_song_pipeline import _generate_no_arrows, _generate_one_saber, _generate_90_degree

class TestModeGenerators(unittest.TestCase):
    def test_generate_no_arrows(self):
        data = {"_colorNotes": [{"_cutDirection": 1}]}
        gen = _generate_no_arrows(data)
        self.assertEqual(gen["_colorNotes"][0]["_cutDirection"], 8)

    def test_generate_one_saber(self):
        data = {"_colorNotes": [{"_cutDirection": 1}]}
        gen = _generate_one_saber(data)
        self.assertEqual(gen, data)

    def test_generate_90_degree(self):
        data = {"_colorNotes": [{"_cutDirection": 1}]}
        gen = _generate_90_degree(data)
        self.assertEqual(gen, data)

if __name__ == '__main__':
    unittest.main()
