import unittest

from fatfinger import fatfinger


class FatfingerTest(unittest.TestCase):
    def test_all_presets_clean_before_typing(self) -> None:
        for preset in ("none", "clean", "mid", "sloppy"):
            with self.subTest(preset=preset):
                result = fatfinger("Hello​!", preset)
                self.assertNotIn("​", result)


if __name__ == "__main__":
    unittest.main()
