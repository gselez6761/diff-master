"""Conflict-marker merge file (git / VSCode style).

Usage:
    python merge_markers.py current.py incoming.py [merged.py]   # write markers
    python merge_markers.py --clean merged.py                    # validate result

Phase 1 (default): emits a single file where every differing block is wrapped
in git-style markers:

    <<<<<<< CURRENT
    ...your existing lines...
    =======
    ...incoming AI lines...
    >>>>>>> INCOMING

Open it in VSCode (it shows the same Accept Current / Incoming / Both
codelens as a real git conflict) or any editor, delete the side(s) and markers
you don't want, and save.

Phase 2 (--clean): scans the edited file and errors if any markers remain, so
you can be sure you didn't miss one before using the result.
"""

import sys

import diff_core

CUR = "<<<<<<< CURRENT"
MID = "======="
INC = ">>>>>>> INCOMING"
MARKERS = (CUR, MID, INC, "<<<<<<<", ">>>>>>>")


def build_markers(current_path, incoming_path, out_path):
    current = diff_core.read_lines(current_path)
    incoming = diff_core.read_lines(incoming_path)
    hunks = diff_core.compute_hunks(current, incoming)

    out = []
    auto = 0
    marked = []
    for h in hunks:
        if h["type"] == "equal":
            out.extend(h["lines"])
            continue
        if diff_core.is_whitespace_only(h):
            # Blank-line-only change: resolve silently, no marker emitted.
            out.extend(diff_core.resolve(h, diff_core.default_choice(h)))
            auto += 1
            continue
        marked.append(h)
        out.append(CUR)
        out.extend(h["current"])
        out.append(MID)
        out.extend(h["incoming"])
        out.append(INC)

    diff_core.write_lines(out_path, out)
    s = diff_core.stats(marked)
    print("Wrote %s" % out_path)
    print("  %d conflict block(s)  (added %d, removed %d, changed %d)"
          % (s["conflicts"], s["added"], s["removed"], s["changed"]))
    if auto:
        print("  %d blank-line change(s) auto-resolved." % auto)
    if s["conflicts"]:
        print("Edit the file to keep the side(s) you want, then run:")
        print("  python merge_markers.py --clean %s" % out_path)
    return 0


def clean_check(path):
    leftover = []
    for n, line in enumerate(diff_core.read_lines(path), 1):
        stripped = line.strip()
        if stripped.startswith("<<<<<<<") or stripped.startswith(">>>>>>>") \
           or stripped == MID:
            leftover.append((n, line))
    if leftover:
        print("%d unresolved marker(s) still in %s:" % (len(leftover), path))
        for n, line in leftover:
            print("  line %d: %s" % (n, line))
        return 1
    print("No markers left — %s is clean." % path)
    return 0


def main(argv):
    if len(argv) >= 3 and argv[1] == "--clean":
        return clean_check(argv[2])
    if len(argv) < 3:
        print(__doc__)
        return 1
    current_path, incoming_path = argv[1], argv[2]
    out_path = argv[3] if len(argv) > 3 else "merged.py"
    return build_markers(current_path, incoming_path, out_path)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
