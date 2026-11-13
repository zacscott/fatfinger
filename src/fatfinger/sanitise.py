"""Strip terminal escapes, hidden and control characters, odd spaces and lookalike letters from pasted text."""

import re

# Common Cyrillic and Greek letters that can masquerade as Latin letters.
CONFUSABLES = str.maketrans({
    "А": "A", "В": "B", "Е": "E", "К": "K", "М": "M", "Н": "H", "О": "O",
    "Р": "P", "С": "C", "Т": "T", "Х": "X", "а": "a", "е": "e", "о": "o",
    "р": "p", "с": "c", "у": "y", "х": "x", "і": "i", "ј": "j",
    "Α": "A", "Β": "B", "Ε": "E", "Ζ": "Z", "Η": "H", "Ι": "I", "Κ": "K",
    "Μ": "M", "Ν": "N", "Ο": "O", "Ρ": "P", "Τ": "T", "Υ": "Y", "Χ": "X",
    "α": "a", "ι": "i", "ο": "o", "ρ": "p", "υ": "u", "χ": "x",
})
SCRIPT_WORD = re.compile(r"[A-Za-z\u0370-\u03ff\u0400-\u052f]+")
TERMINAL_ESCAPE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07\x1b]*(?:\x07|\x1b\\))")
HIDDEN = re.compile(r"[\u00ad\u200b-\u200d\u2060\ufeff\ufe00-\ufe0f\U000e0000-\U000e007f]")
ODD_SPACE = re.compile(r"[\u00a0\u2002-\u200a\u202f\u205f\u3000]")
CONTROL = re.compile(r"[\x00-\x08\x0b-\x1f\x7f-\x9f]")


def demeta(text):
    """Normalize pasted text and remove hidden characters and terminal escapes."""
    text = TERMINAL_ESCAPE.sub("", text)
    text = HIDDEN.sub("", text)
    text = CONTROL.sub("", text)
    text = ODD_SPACE.sub(" ", text)

    def normalize_word(match):
        word = match[0]
        return word.translate(CONFUSABLES) if re.search(r"[A-Za-z]", word) else word

    return SCRIPT_WORD.sub(normalize_word, text)
