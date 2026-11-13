"""Swap the characters a person can't type (em dashes, arrows, curly quotes, ...) for what they would type instead."""

import re

# Each character that can't be typed on a keyboard, and what a person would type instead.
TYPED = {
    # Quotes
    "‘": "'",
    "’": "'",
    "‚": "'",
    "‛": "'",
    "′": "'",  # ‘ ’ ‚ ‛ ′
    "“": '"',
    "”": '"',
    "„": '"',
    "‟": '"',
    "″": '"',  # “ ” „ ‟ ″
    "«": '"',
    "»": '"',  # « »
    # Dashes and hyphens (em and en dashes between words are handled in DASH below)
    "‐": "-",
    "‑": "-",
    "‒": "-",
    "−": "-",
    "⁃": "-",  # ‐ ‑ ‒ − ⁃
    # Arrows
    "→": "->",
    "←": "<-",
    "↔": "<->",
    "⇒": "=>",
    "⇐": "<=",
    "⇔": "<=>",  # → ← ↔ ⇒ ⇐ ⇔
    "⟶": "->",
    "⟵": "<-",
    "➔": "->",
    "➜": "->",  # ⟶ ⟵ ➔ ➜
    # Punctuation and symbols
    "…": "...",  # …
    "•": "-",
    "◦": "-",
    "‣": "-",
    "·": "-",  # • ◦ ‣ ·
    "×": "x",
    "÷": "/",  # × ÷
    "≤": "<=",
    "≥": ">=",
    "≠": "!=",
    "≈": "~",
    "±": "+/-",  # ≤ ≥ ≠ ≈ ±
    "§": "section ",  # §
    "™": "",
    "®": "",
    "©": "(c)",  # ™ ® ©

}
# An em or en dash (or a horizontal bar). Between numbers it's a range (2-3). Starting a
# line it's a bullet (- ). Anywhere else it's a break in the sentence, typed as a comma.
DASH = re.compile(
    r"(?<=\d)\s*([\u2013\u2014])\s*(?=\d)|^\s*[\u2013\u2014\u2015]+\s*|\s*[\u2013\u2014\u2015]+\s*"
)


def deslop(text):
    """Swap every character you can't type for what a person would type. Code is left alone."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
        if fenced or line.lstrip().startswith("```"):
            out.append(line)
            continue
        parts = re.split(r"(`[^`]*`)", line)
        out.append("".join(s if n % 2 else typed(s) for n, s in enumerate(parts)))
    return "\n".join(out)


def typed(text):
    """deslop for a stretch with no code in it."""

    def dash(m):
        if m[1]:
            return "-"
        if m.start() == 0:
            return "- "
        return "" if m.end() == len(text) or text[m.end()] in ".,;:!?" else ", "

    text = DASH.sub(dash, text)
    return text.translate(str.maketrans(TYPED))
