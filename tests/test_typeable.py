import unittest

from fatfinger.typeable import deslop


class DeslopTest(unittest.TestCase):
    def test_dashes(self) -> None:
        self.assertEqual(deslop("pages 2–3"), "pages 2-3")
        self.assertEqual(deslop("— a bullet"), "- a bullet")
        self.assertEqual(deslop("good — approved"), "good, approved")
        self.assertEqual(deslop("the end —."), "the end.")

    def test_arrows_quotes_and_ellipsis(self) -> None:
        self.assertEqual(deslop("a → b ⇒ c"), "a -> b => c")
        self.assertEqual(deslop("it’s “quoted” …"), "it's \"quoted\" ...")

    def test_code_is_left_alone(self) -> None:
        self.assertEqual(deslop("see `a — b` here"), "see `a — b` here")
        fenced = "```\nx — “y”\n```"
        self.assertEqual(deslop(fenced), fenced)


if __name__ == "__main__":
    unittest.main()
