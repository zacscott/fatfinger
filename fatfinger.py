#!/usr/bin/env python3
"""
Add keyboard slips to a clean draft so it reads like it was typed.

  fatfinger [pro|mid|sloppy] < draft.txt

Prints the result, ready to send. Code, links, mentions, refs, numbers,
paths and identifiers are never touched, and names only ever get a held shift.
"""
import hashlib, random, re, sys

# How sloppy each preset is. Every number is a percentage chance, except
# max_typos_per_line. Typos are per word, the rest per sentence or line.
PRESETS = {
    "pro": {
        "typo": 1,
        "max_typos_per_line": 1,
        "lowercase_sentence_start": 0,
        "drop_apostrophe": 40,
        "drop_final_full_stop": 0,
        "space_before_question_mark": 0,
        "double_space": 2,
        "missed_space": 1,
    },
    "mid": {
        "typo": 5,
        "max_typos_per_line": 1,
        "lowercase_sentence_start": 30,
        "drop_apostrophe": 60,
        "drop_final_full_stop": 70,
        "space_before_question_mark": 25,
        "double_space": 5,
        "missed_space": 5,
    },
    "sloppy": {
        "typo": 20,
        "max_typos_per_line": 3,
        "lowercase_sentence_start": 50,
        "drop_apostrophe": 80,
        "drop_final_full_stop": 80,
        "space_before_question_mark": 25,
        "double_space": 20,
        "missed_space": 20,
    },
}

# Copied through as-is: `code`, URLs, @mentions, #/! refs, anything with a digit, slash,
# underscore, bracket, = or dot in it, camelCase and ALLCAPS.
PROTECTED = re.compile(
    r"(`[^`]*`|\S+://\S+|[@#!]\w\S*|\S*[\d/\\_()\[\]<>{}=]\S*|\w+\.\w\S*|\b\w*[a-z][A-Z]\w*\b|\b[A-Z]{2,}\w*\b)"
)
WORD = re.compile(r"(?<![\w'])[A-Za-z]{3,}(?![\w'])")
CONTRACTION = re.compile(r"\b\w+'(?:t|m|ll|ve|d)\b|\b(?:it|that|what|there)'s\b", re.I)
ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm"]


def chance(rng, percent):
    """True percent% of the time."""
    return rng.random() * 100 < percent


def near(c):
    """The keys either side of c on its QWERTY row."""
    row = next((r for r in ROWS if c.lower() in r), "")
    i = row.find(c.lower())
    return [row[j] for j in (i - 1, i + 1) if i >= 0 and 0 <= j < len(row)]


def slip(w, rng):
    """One slip: swapped letters (hte), extra key (obviopusly), wrong key, or held shift (LIke)."""
    if w[0].isupper():
        return w[0] + w[1].upper() + w[2:] if w[1:].islower() else w
    i = rng.randrange(1, len(w) - 1)
    kind = rng.choice("sssseeew")
    if kind == "s" and w[i] != w[i + 1]:
        return w[:i] + w[i + 1] + w[i] + w[i + 2:]
    if near(w[i]):
        return w[:i + (kind == "e")] + rng.choice(near(w[i])) + w[i + 1:]
    return w


def rough(text, p, rng, start, end, left):
    """Rough up a stretch with nothing protected in it. left holds what the line can still take."""

    def hit(m):
        if left["slips"] <= 0 or not chance(rng, p["typo"]):
            return m[0]
        new = slip(m[0], rng)
        if new != m[0]:
            left["slips"] -= 1
        return new

    text = WORD.sub(hit, text)
    text = CONTRACTION.sub(lambda m: m[0].replace("'", "") if chance(rng, p["drop_apostrophe"]) else m[0], text)
    text = re.sub(
        (r"(^|[.!?]\s+)" if start else r"([.!?]\s+)") + r"([A-Z])(?=[a-z'\s])",
        lambda m: m[1] + m[2].lower() if chance(rng, p["lowercase_sentence_start"]) else m[0],
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
    if end and chance(rng, p["drop_final_full_stop"]) and re.search(r"[^.]\.$", text):
        text = text[:-1]
    return text


def fatfinger(text, preset="mid"):
    """Rough up text with a preset. The same draft always gives the same result."""
    p = PRESETS[preset]
    rng = random.Random(hashlib.sha256(text.encode()).hexdigest())
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
            "qspace": chance(rng, p["space_before_question_mark"]),
            "dspace": chance(rng, p["double_space"]),
            "nospace": chance(rng, p["missed_space"]),
        }
        out.append("".join(
            s if n % 2 else rough(s, p, rng, n == 0, n == len(parts) - 1, left) for n, s in enumerate(parts)
        ))
    return "\n".join(out)


def main():
    preset = sys.argv[1] if len(sys.argv) > 1 else "mid"
    if preset not in PRESETS:
        sys.exit(f"usage: fatfinger [{'|'.join(PRESETS)}] < draft.txt")
    sys.stdout.write(fatfinger(sys.stdin.read(), preset))


if __name__ == "__main__":
    main()

