# diff_tool

Catch code an AI chat dropped, then merge what you want. **Python stdlib only —
no pip installs.** Same diff engine, two front-ends; pick whichever fits.

The workflow is your 3-file idea:

| file          | what it is                                  |
|---------------|---------------------------------------------|
| `current.py`  | your existing code                          |
| `incoming.py` | the version the AI pasted back              |
| `merge_*.py`  | one of the two tools below                  |
| → `merged.py` | the 4th file it produces                    |

Each conflict is auto-classified so dropped code is obvious:
- **removed** — incoming dropped lines you have (the failure mode you care about)
- **added** — incoming introduced new lines
- **changed** — both sides differ

Defaults protect you: a **removed** block defaults to *keep current*, so you
never lose code unless you explicitly say so.

## 1. Terminal — interactive
```
python merge_cli.py current.py incoming.py [merged.py]
```
Walks each conflict in the terminal (red current / green incoming), showing the
enclosing `def`/`class` it lives in, and prompts with a single keypress:
`c` current · `i` incoming · `b` both · `n` neither · `q` quit. Writes the
merged file at the end.

## 2. Conflict markers — edit like git/VSCode
```
python merge_markers.py current.py incoming.py [merged.py]   # generate
python merge_markers.py --clean merged.py                    # verify
```
Produces one file full of `<<<<<<< CURRENT / ======= / >>>>>>> INCOMING`
markers. Open in VSCode (you get the usual Accept Current/Incoming/Both
codelens), delete the sides you don't want, then run `--clean` to confirm no
markers were missed.

---
`current.py` / `incoming.py` are sample inputs — overwrite them with your own,
or pass any two paths as arguments.
