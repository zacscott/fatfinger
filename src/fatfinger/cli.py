import sys
from typing import cast

from fatfinger import fatfinger
from fatfinger.slips import PRESETS, Preset


def main() -> None:
    preset = sys.argv[1] if len(sys.argv) > 1 else "mid"
    if preset not in PRESETS:
        sys.exit(f"usage: fatfinger [{'|'.join(PRESETS)}] < draft.txt")
    sys.stdout.write(fatfinger(sys.stdin.read(), cast(Preset, preset)))


if __name__ == "__main__":
    main()
