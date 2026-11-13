# fatfinger

Your AI writes flawlessly, you don't.

`fatfinger` takes a clean AI draft and gives it the human touch.

## Install

```bash
uv tool install https://github.com/zacscott/fatfinger.git
```

OR

```bash
uvx --from https://github.com/zacscott/fatfinger.git fatfinger
```

## Use

```bash
echo "Looks good to me. Approved!" | fatfinger
```

```
Looks goood to me. approved!
```

| Preset | Sounds like |
|---|---|
| `clean` | Talking to the CEO |
| `mid` | Talking to the team (default) |
| `sloppy` | Typing on your phone while walking to the car park |


Pasted text is cleaned before the preset runs: invisible Unicode characters,
Unicode tag characters, variation selectors, terminal control sequences and
common Greek/Cyrillic lookalikes inside Latin words are removed or normalized.
This works on text passed through stdin; it does not inspect file metadata or
parse HTML clipboard attributes. Removing variation selectors and zero-width
joiners can change emoji presentation.
