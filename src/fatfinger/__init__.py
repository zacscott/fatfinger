"""
Make a clean draft read like it was typed: swap out characters you can't type
(em dashes, arrows, curly quotes, ...), then add keyboard slips.

  fatfinger [none|clean|mid|sloppy] < draft.txt

Prints the result, ready to send. Code, links, mentions, refs, numbers,
paths and identifiers are protected from keyboard slips, and names only ever get a held shift.
`none` only swaps the characters and adds no slips.
"""

from fatfinger.sanitise import demeta
from fatfinger.slips import roughen
from fatfinger.typeable import deslop

__all__ = ["fatfinger"]


def fatfinger(text, preset="mid"):
    """Clean pasted text, then rough it up with a preset. The same draft always gives the same result."""
    return roughen(deslop(demeta(text)), preset)
