import random
import unittest

from fatfinger.slips import PRESETS, roughen, slip

PROTECTED = ["`foo_bar()`", "https://example.com/x", "@alice", "#1234", "src/app.py", "2pm"]
DRAFT = "Check `foo_bar()` at https://example.com/x, ping @alice on #1234 and src/app.py before 2pm, I think it works."
VOWELS = "aeiou"


def only_slip(percent_key: str) -> dict[str, float]:
    """A preset that only rolls one keyboard slip, every time."""
    p = dict.fromkeys(PRESETS["sloppy"], 0)
    p[percent_key] = 100
    return p


class SlipTest(unittest.TestCase):
    def test_no_vowel_is_replaced_by_another_vowel(self) -> None:
        # A vowel for a nearby vowel changes the word rather than the spelling: this -> thus.
        p = only_slip("wrong_key_per_word_pct")
        words = ("this", "for", "not", "look", "minute", "because", "should", "about", "other")
        for word in words:
            for seed in range(100):
                out = slip(word, p, rng=random.Random(seed))
                with self.subTest(word=word, seed=seed, out=out):
                    self.assertEqual(len(out), len(word))
                    for was, now in zip(word, out):
                        self.assertFalse(was != now and was in VOWELS and now in VOWELS)

    def test_no_vowel_is_swapped_with_another_vowel(self) -> None:
        # Swapping two vowels is the same problem (read -> raed), even though it isn't a wrong key.
        p = only_slip("swapped_letters_per_word_pct")
        words = ("this", "read", "about", "quiet", "really", "theatre", "outside")
        for word in words:
            for seed in range(100):
                out = slip(word, p, rng=random.Random(seed))
                with self.subTest(word=word, seed=seed, out=out):
                    if out != word:
                        self.assertEqual([c for c in out if c in VOWELS], [c for c in word if c in VOWELS])

    def test_this_never_becomes_thus(self) -> None:
        for n in range(100):
            result = roughen(f"I think this works, we should ship it. Thanks {n}.", "sloppy")
            with self.subTest(n=n, result=result):
                self.assertNotIn("thus", result)


class RoughenTest(unittest.TestCase):
    def test_protected_tokens_survive(self) -> None:
        # Each draft hashes to its own seed, so varying the text gives a spread of rolls.
        for n in range(50):
            result = roughen(f"{DRAFT} Thanks again {n}", "sloppy")
            for token in PROTECTED:
                with self.subTest(n=n, token=token):
                    self.assertIn(token, result)

    def test_none_changes_nothing(self) -> None:
        self.assertEqual(roughen(DRAFT, "none"), DRAFT)

    def test_same_draft_same_result(self) -> None:
        for preset in PRESETS:
            with self.subTest(preset=preset):
                self.assertEqual(roughen(DRAFT, preset), roughen(DRAFT, preset))

    def test_sloppy_always_changes_short_text(self) -> None:
        for draft in ("Thanks, that works.", "Looks good to me.", "Sounds fine, merging now."):
            with self.subTest(draft=draft):
                self.assertNotEqual(roughen(draft, "sloppy"), draft)


if __name__ == "__main__":
    unittest.main()
