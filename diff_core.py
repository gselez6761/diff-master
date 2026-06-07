"""Shared diff logic. Standard library only (difflib).

Splits two versions of a file into a sequence of "hunks":
  - equal     : identical in both, passes straight through
  - conflict  : differs between current and incoming. Sub-classified as
                  'added'   -> incoming has lines current doesn't
                  'removed' -> current has lines incoming dropped
                  'changed' -> both sides have lines, but different

The same hunk list feeds all three front-ends (HTML / CLI / markers).
"""

import difflib


def read_lines(path):
    """Read a file as a list of lines (without trailing newlines)."""
    with open(path, encoding="utf-8") as f:
        return f.read().split("\n")


def write_lines(path, lines):
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def classify(current, incoming):
    if not current:
        return "added"      # incoming introduced new lines
    if not incoming:
        return "removed"    # incoming dropped lines that current has
    return "changed"        # both sides present but different


def compute_hunks(current, incoming):
    """Return a list of hunk dicts describing how to turn current -> incoming."""
    sm = difflib.SequenceMatcher(None, current, incoming, autojunk=False)
    hunks = []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        cur = current[i1:i2]
        inc = incoming[j1:j2]
        if tag == "equal":
            hunks.append({"type": "equal", "lines": cur})
        else:
            hunks.append({
                "type": "conflict",
                "kind": classify(cur, inc),
                "current": cur,
                "incoming": inc,
            })
    return hunks


def default_choice(hunk):
    """Sensible default per conflict.

    Because the whole point of this tool is catching code the AI *dropped*,
    a 'removed' hunk defaults to keeping CURRENT. Everything else defaults to
    the new INCOMING text.
    """
    return "current" if hunk["kind"] == "removed" else "incoming"


def is_whitespace_only(hunk):
    """True if a conflict only involves blank/whitespace lines on both sides.

    Used to auto-resolve trivial blank-line additions/removals so the user
    isn't asked to approve them. Combined with default_choice (which keeps
    CURRENT for 'removed'), nothing meaningful is lost.
    """
    return all(not s.strip() for s in hunk["current"] + hunk["incoming"])


def resolve(hunk, choice):
    """Turn a (hunk, choice) into the lines that go in the merged output.

    choice is one of: 'current', 'incoming', 'both', 'none'.
    """
    if choice == "current":
        return list(hunk["current"])
    if choice == "incoming":
        return list(hunk["incoming"])
    if choice == "both":
        return list(hunk["current"]) + list(hunk["incoming"])
    if choice == "none":
        return []
    raise ValueError("unknown choice: %r" % choice)


def enclosing_def(lines, start):
    """Nearest `def`/`class` line above index `start` (exclusive), or None.

    Used to show which function/method a conflict lives inside, like the
    `@@ ... def foo():` header in a git diff.
    """
    for i in range(min(start, len(lines)) - 1, -1, -1):
        s = lines[i].lstrip()
        if s.startswith(("def ", "class ", "async def ")):
            return lines[i]
    return None


def stats(hunks):
    conflicts = [h for h in hunks if h["type"] == "conflict"]
    return {
        "conflicts": len(conflicts),
        "added": sum(1 for h in conflicts if h["kind"] == "added"),
        "removed": sum(1 for h in conflicts if h["kind"] == "removed"),
        "changed": sum(1 for h in conflicts if h["kind"] == "changed"),
    }
