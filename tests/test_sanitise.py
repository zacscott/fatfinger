import unittest

from fatfinger.sanitise import demeta


class DemetaTest(unittest.TestCase):
    def test_hidden_unicode_and_confusables(self) -> None:
        text = "pаypal​‌‍⁠﻿­️\U000e0001\U000e007f"
        self.assertEqual(demeta(text), "paypal")

    def test_odd_spaces(self) -> None:
        spaces = " " + "".join(chr(code) for code in range(0x2002, 0x200B)) + "  　"
        self.assertEqual(demeta("one" + spaces + "two"), "one" + " " * len(spaces) + "two")

    def test_terminal_controls(self) -> None:
        text = "\x1b]8;;https://example.com\x07\x1b[31mhello\x1b[0m\x1b]8;;\x07\x00"
        self.assertEqual(demeta(text), "hello")

    def test_other_scripts_and_line_structure(self) -> None:
        self.assertEqual(demeta("Привет κόσμε\nhello\tworld"), "Привет κόσμε\nhello\tworld")


if __name__ == "__main__":
    unittest.main()
