import unittest

from fatfinger.slips import PRESETS, roughen

PROTECTED = ["`foo_bar()`", "https://example.com/x", "@alice", "#1234", "src/app.py", "2pm"]
DRAFT = "Check `foo_bar()` at https://example.com/x, ping @alice on #1234 and src/app.py before 2pm, I think it works."


class RoughenTest(unittest.TestCase):
    def test_protected_tokens_survive(self):
        # Each draft hashes to its own seed, so varying the text gives a spread of rolls.
        for n in range(50):
            result = roughen(f"{DRAFT} Thanks again {n}", "sloppy")
            for token in PROTECTED:
                with self.subTest(n=n, token=token):
                    self.assertIn(token, result)

    def test_none_changes_nothing(self):
        self.assertEqual(roughen(DRAFT, "none"), DRAFT)

    def test_same_draft_same_result(self):
        for preset in PRESETS:
            with self.subTest(preset=preset):
                self.assertEqual(roughen(DRAFT, preset), roughen(DRAFT, preset))

    def test_sloppy_always_changes_short_text(self):
        for draft in ("Thanks, that works.", "Looks good to me.", "Sounds fine, merging now."):
            with self.subTest(draft=draft):
                self.assertNotEqual(roughen(draft, "sloppy"), draft)


if __name__ == "__main__":
    unittest.main()
