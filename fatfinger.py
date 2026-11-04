#!/usr/bin/env python3
"""
Make a clean draft read like it was typed: swap out characters you can't type
(em dashes, arrows, curly quotes, ...), then add keyboard slips.

  fatfinger [none|clean|mid|sloppy] < draft.txt

Prints the result, ready to send. Code, links, mentions, refs, numbers,
paths and identifiers are never touched, and names only ever get a held shift.
`none` only swaps the characters and adds no slips.
"""
import hashlib
import random
import re
import sys

# How sloppy each preset is. Every *_pct is a percentage chance of that thing
# happening, per word, contraction, mark, sentence or line as the name says.
# The rates are for a short chat message. Longer text gets proportionally fewer
# (see HALF_RATE_WORDS), so a letter isn't corrupted and a novel is near spotless.
PRESETS = {
    "clean": {
        # Keyboard slips, each rolled per word. A word gets at most one, the first
        # word of a line never gets one, and two slipped words are never side by side.
        "swapped_letters_per_word_pct": 0.5,  # the -> hte
        "extra_key_per_word_pct": 0.25,  # obviously -> obviopusly
        "wrong_key_per_word_pct": 0.25,  # change -> chsnge
        "missed_key_per_word_pct": 0.25,  # think -> thnk
        "doubled_key_per_word_pct": 0.25,  # really -> reallly, tomorrow -> tomorow
        "held_shift_per_capital_word_pct": 0,  # Like -> LIke (the only slip a capitalised word gets)
        "max_typos_per_line": 1,
        "at_least_one_change": False,  # roll again when nothing changed (text up to HALF_RATE_WORDS only)
        # Everything else.
        "lowercase_sentence_start_pct": 0,
        "drop_apostrophe_per_contraction_pct": 10,
        "punctuation_neighbour_per_mark_pct": 0,  # don't -> don;t, fine, but -> fine. but
        "drop_final_full_stop_per_line_pct": 0,
        "space_before_question_mark_per_line_pct": 0,
        "double_space_per_line_pct": 1,
        "missed_space_per_line_pct": 0.5,
        "early_space_per_line_pct": 0.5,  # the problem -> th eproblem
    },
    "mid": {
        "swapped_letters_per_word_pct": 5,
        "extra_key_per_word_pct": 3,
        "wrong_key_per_word_pct": 3,
        "missed_key_per_word_pct": 3,
        "doubled_key_per_word_pct": 2,
        "held_shift_per_capital_word_pct": 1,
        "max_typos_per_line": 2,
        "at_least_one_change": True,
        "lowercase_sentence_start_pct": 25,
        "drop_apostrophe_per_contraction_pct": 20,
        "punctuation_neighbour_per_mark_pct": 3,
        "drop_final_full_stop_per_line_pct": 20,
        "space_before_question_mark_per_line_pct": 25,
        "double_space_per_line_pct": 5,
        "missed_space_per_line_pct": 5,
        "early_space_per_line_pct": 5,
    },
    "sloppy": {
        "swapped_letters_per_word_pct": 8,
        "extra_key_per_word_pct": 8,
        "wrong_key_per_word_pct": 5,
        "missed_key_per_word_pct": 8,
        "doubled_key_per_word_pct": 8,
        "held_shift_per_capital_word_pct": 5,
        "max_typos_per_line": 8,
        "at_least_one_change": True,
        "lowercase_sentence_start_pct": 50,
        "drop_apostrophe_per_contraction_pct": 70,
        "punctuation_neighbour_per_mark_pct": 25,
        "drop_final_full_stop_per_line_pct": 70,
        "space_before_question_mark_per_line_pct": 70,
        "double_space_per_line_pct": 20,
        "missed_space_per_line_pct": 20,
        "early_space_per_line_pct": 20,
    },
}
# No slips at all, only the character swaps. For documents people come back to.
PRESETS["none"] = {key: 0 for key in PRESETS["clean"]}

# Copied through as-is: `code`, URLs, @mentions, #/! refs, anything with a digit, slash,
# underscore, bracket, = or dot in it, camelCase and ALLCAPS.
PROTECTED = re.compile(
    r"(`[^`]*`|\S+://\S+|[@#!]\w\S*|\S*[\d/\\_()\[\]<>{}=]\S*|\w+\.\w\S*|\b\w*[a-z][A-Z]\w*\b|\b[A-Z]{2,}\w*\b)"
)
WORD = re.compile(r"(?<![\w'])[A-Za-z]{3,}(?![\w'])")
ANY_WORD = re.compile(r"[A-Za-z']+")
CONTRACTION = re.compile(r"\b\w+'(?:t|m|ll|ve|d)\b|\b(?:it|that|what|there)'s\b", re.I)
ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]

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
    # Spaces that look like a space but aren't one
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    " ": " ",
    "　": " ",
    # Invisible characters (the zero-width joiner stays, emoji need it)
    "​": "",
    "‌": "",
    "⁠": "",
    "﻿": "",
    "­": "",
}
# An em or en dash (or a horizontal bar). Between numbers it's a range (2-3). Starting a
# line it's a bullet (- ). Anywhere else it's a break in the sentence, typed as a comma.
DASH = re.compile(
    r"(?<=\d)\s*([\u2013\u2014])\s*(?=\d)|^\s*[\u2013\u2014\u2015]+\s*|\s*[\u2013\u2014\u2015]+\s*"
)

# Every *_pct is scaled by length on a smooth curve: 1 / (1 + (words / HALF_RATE_WORDS) ** FALLOFF).
# With 150 and 1.5: 20 words 95%, 60 words 80%, 150 words 50%, 300 words 26%,
# 1,000 words 6%, a 100,000-word novel effectively 0.
HALF_RATE_WORDS = 150
FALLOFF = 1.5


def chance(rng, percent):
    """True percent% of the time."""
    return rng.random() * 100 < percent


def near(c):
    """The keys either side of c on its QWERTY row."""
    row = next((r for r in ROWS if c.lower() in r), "")
    i = row.find(c.lower())
    return [row[j] for j in (i - 1, i + 1) if i >= 0 and 0 <= j < len(row)]


def slip(w, p, rng):
    """At most one slip, each kind rolled on its own chance. Capitalised words only get a held shift."""
    if w[0].isupper():
        if w[1:].islower() and chance(rng, p["held_shift_per_capital_word_pct"]):
            return w[0] + w[1].upper() + w[2:]
        return w
    i = rng.randrange(1, len(w) - 1)
    keys = near(w[i])
    if chance(rng, p["swapped_letters_per_word_pct"]) and w[i] != w[i + 1]:
        return w[:i] + w[i + 1] + w[i] + w[i + 2:]
    if keys and chance(rng, p["extra_key_per_word_pct"]):
        return w[: i + 1] + rng.choice(keys) + w[i + 1 :]
    if keys and chance(rng, p["wrong_key_per_word_pct"]):
        return w[:i] + rng.choice(keys) + w[i + 1 :]
    if chance(rng, p["missed_key_per_word_pct"]):
        return w[:i] + w[i + 1 :]
    if chance(rng, p["doubled_key_per_word_pct"]):
        double = re.search(r"([a-z])\1", w)
        if double:  # a double letter loses one
            return w[: double.start()] + w[double.start() + 1 :]
        return w[: i + 1] + w[i] + w[i + 1 :]  # a stuck key types one twice
    return w


def rough(text, p, rng, start, end, left):
    """Rough up a stretch with nothing protected in it. left holds what the line can still take."""
    pieces, pos = [], 0
    for m in WORD.finditer(text):
        left["word"] += len(ANY_WORD.findall(text[pos : m.start()]))
        new = m[0]
        # Never the line's first word, never right after another slipped word.
        if (
            left["slips"] > 0
            and left["word"] > 0
            and left["word"] - left["last_slip"] > 1
        ):
            new = slip(m[0], p, rng)
            if new != m[0]:
                left["slips"] -= 1
                left["last_slip"] = left["word"]
        pieces.append(text[pos : m.start()] + new)
        left["word"] += 1
        pos = m.end()
    left["word"] += len(ANY_WORD.findall(text[pos:]))
    text = "".join(pieces) + text[pos:]

    def contraction(m):
        if chance(rng, p["drop_apostrophe_per_contraction_pct"]):
            return m[0].replace("'", "")
        if chance(rng, p["punctuation_neighbour_per_mark_pct"]):
            return m[0].replace("'", ";")
        return m[0]

    text = CONTRACTION.sub(contraction, text)
    text = re.sub(
        (r"(^|[.!?]\s+)" if start else r"([.!?]\s+)") + r"([A-Z])(?=[a-z'\s])",
        lambda m: (
            m[1] + m[2].lower()
            if chance(rng, p["lowercase_sentence_start_pct"])
            else m[0]
        ),
        text,
    )
    text = re.sub(
        r"(?<=[a-z]),(?= [a-z])",
        lambda m: "." if chance(rng, p["punctuation_neighbour_per_mark_pct"]) else ",",
        text,
    )
    if left["qspace"] and re.search(r"[A-Za-z]\?", text):
        text, left["qspace"] = re.sub(r"(?<=[A-Za-z])\?", " ?", text, count=1), False
    spaces = [m.start() for m in re.finditer(r"(?<=[a-z,]) (?=[a-z])", text)]
    if left["dspace"] and spaces:
        at, left["dspace"] = rng.choice(spaces), False
        text = text[:at] + " " + text[at:]
    spaces = [m.start() for m in re.finditer(r"(?<=[a-z]) (?=[a-z])", text)]
    if left["nospace"] and spaces:
        at, left["nospace"] = rng.choice(spaces), False
        text = text[:at] + text[at + 1:]
    spaces = [m.start() for m in re.finditer(r"(?<=[a-z]{3}) (?=[a-z]{2})", text)]
    if left["earlyspace"] and spaces:
        at, left["earlyspace"] = rng.choice(spaces), False
        text = text[: at - 1] + " " + text[at - 1] + text[at + 1 :]
    if (
        end
        and chance(rng, p["drop_final_full_stop_per_line_pct"])
        and re.search(r"[^.]\.$", text)
    ):
        text = text[:-1]
    return text


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


def fatfinger(text, preset="mid"):
    """Deslop text, then rough it up with a preset. The same draft always gives the same result."""
    text = deslop(text)
    p = dict(PRESETS[preset])
    scale = 1 / (1 + (len(ANY_WORD.findall(text)) / HALF_RATE_WORDS) ** FALLOFF)
    for key in p:
        if key.endswith("_pct"):
            p[key] *= scale
    # Long text is allowed to come through untouched.
    must_change = p["at_least_one_change"] and scale >= 0.5
    seed = hashlib.sha256(text.encode()).hexdigest()
    for attempt in range(20):
        out = rough_lines(text, p, random.Random(f"{seed}{attempt}"))
        if out != text or not must_change:
            break
    return out


def rough_lines(text, p, rng):
    """One pass over every line, skipping code fences, quotes and indented lines."""
    out, fenced = [], False
    for line in text.split("\n"):
        if line.lstrip().startswith("```"):
            fenced = not fenced
            out.append(line)
            continue
        if fenced or line.lstrip().startswith(">") or line.startswith(("    ", "\t")):
            out.append(line)
            continue
        parts = PROTECTED.split(line)
        left = {
            "slips": p["max_typos_per_line"],
            "word": 0,
            "last_slip": -2,
            "qspace": chance(rng, p["space_before_question_mark_per_line_pct"]),
            "dspace": chance(rng, p["double_space_per_line_pct"]),
            "nospace": chance(rng, p["missed_space_per_line_pct"]),
            "earlyspace": chance(rng, p["early_space_per_line_pct"]),
        }
        rebuilt = []
        for n, s in enumerate(parts):
            if n % 2:
                rebuilt.append(s)
                left["word"] += 1
            else:
                rebuilt.append(rough(s, p, rng, n == 0, n == len(parts) - 1, left))
        out.append("".join(rebuilt))
    return "\n".join(out)


def main():
    preset = sys.argv[1] if len(sys.argv) > 1 else "mid"
    if preset not in PRESETS:
        sys.exit(f"usage: fatfinger [{'|'.join(PRESETS)}] < draft.txt")
    sys.stdout.write(fatfinger(sys.stdin.read(), preset))


if __name__ == "__main__":
    main()

