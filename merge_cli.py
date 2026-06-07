"""Interactive terminal merge.

Usage:
    python merge_cli.py current.py incoming.py [merged.py]

Walks each differing block, shows CURRENT (red) vs INCOMING (green), and asks
you to choose. Writes the merged 4th file at the end. Standard library only.

Per-hunk keys:
    c  keep current      i  take incoming     b  keep both
    n  skip both         q  quit without writing
"""

import sys

import diff_core


def getch():
    """Read a single keypress without waiting for Enter.

    Uses termios/tty on a real terminal; falls back to line-based input()
    (e.g. when stdin is piped) so scripted runs still work.
    """
    try:
        import termios, tty
    except ImportError:
        termios = None
    if termios is None or not sys.stdin.isatty():
        line = sys.stdin.readline()
        return line[:1].lower() if line else "q"
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)
    if ch in ("\r", "\n"):      # Enter -> signal "use default"
        return ""
    if ch == "\x03":            # Ctrl-C
        raise KeyboardInterrupt
    return ch.lower()


# ANSI colors; disabled automatically when output isn't a terminal.
_TTY = sys.stdout.isatty()
def _c(code, s):
    return "\033[%sm%s\033[0m" % (code, s) if _TTY else s
RED   = lambda s: _c("31", s)
GREEN = lambda s: _c("32", s)
YEL   = lambda s: _c("33", s)
DIM   = lambda s: _c("2", s)
BOLD  = lambda s: _c("1", s)


def show_context(ctx, block):
    """Print the enclosing def/class header above a hunk side, e.g.
        def method():
            ...
    Skipped when there's no enclosing def, or when the def is already the
    first line of the block itself (no point repeating it).
    """
    if not ctx:
        return
    if block and block[0].strip() == ctx.strip():
        return
    indent = ctx[:len(ctx) - len(ctx.lstrip())]
    print("  " + DIM(ctx))
    print("  " + DIM(indent + "    ..."))


def show_block(lines, color, prefix):
    if not lines:
        print("    " + DIM("(empty)"))
        return
    for ln in lines:
        print(color(prefix + ln))


def prompt(hunk, idx, total, cur_ctx, inc_ctx):
    kind = hunk["kind"]
    note = {"added": "incoming ADDED new lines",
            "removed": "incoming DROPPED these lines",
            "changed": "both sides differ"}[kind]
    print()
    print(BOLD("── Conflict %d/%d  [%s]  %s" % (idx, total, kind.upper(), note)))
    print(DIM("<<<<<<< CURRENT"))
    show_context(cur_ctx, hunk["current"])
    show_block(hunk["current"], RED, "- ")
    print(DIM("======="))
    show_context(inc_ctx, hunk["incoming"])
    show_block(hunk["incoming"], GREEN, "+ ")
    print(DIM(">>>>>>> INCOMING"))

    default = diff_core.default_choice(hunk)
    dkey = {"current": "c", "incoming": "i"}[default]
    label = {"c": "current", "i": "incoming", "b": "both", "n": "none"}
    while True:
        sys.stdout.write("  [c]urrent / [i]ncoming / [b]oth / [n]one / [q]uit "
                         "(default %s): " % dkey)
        sys.stdout.flush()
        ans = getch()
        if ans == "":
            ans = dkey
        print(ans)                       # echo the key, since raw mode hides it
        if ans == "q":
            print("Aborted, nothing written.")
            sys.exit(0)
        if ans in label:
            return label[ans]
        print("  ? press c, i, b, n, or q")


def main(argv):
    if len(argv) < 3:
        print(__doc__)
        return 1
    current_path, incoming_path = argv[1], argv[2]
    out_path = argv[3] if len(argv) > 3 else "merged.py"

    current = diff_core.read_lines(current_path)
    incoming = diff_core.read_lines(incoming_path)
    hunks = diff_core.compute_hunks(current, incoming)
    total = sum(1 for h in hunks
                if h["type"] == "conflict" and not diff_core.is_whitespace_only(h))

    any_conflict = any(h["type"] == "conflict" for h in hunks)
    if not any_conflict:
        print("Files are identical — nothing to merge.")
        diff_core.write_lines(out_path, current)
        print("Wrote %s" % out_path)
        return 0

    if total == 0:
        print("Only blank-line differences — auto-resolved, nothing to approve.")
    else:
        print("%d conflict(s) to resolve.\n" % total)
    out = []
    idx = 0
    cur_pos = 0   # line index into current
    inc_pos = 0   # line index into incoming
    for h in hunks:
        if h["type"] == "equal":
            out.extend(h["lines"])
            cur_pos += len(h["lines"])
            inc_pos += len(h["lines"])
            continue
        if diff_core.is_whitespace_only(h):
            # Blank-line-only change: resolve silently with the safe default.
            out.extend(diff_core.resolve(h, diff_core.default_choice(h)))
            cur_pos += len(h["current"])
            inc_pos += len(h["incoming"])
            continue
        idx += 1
        cur_ctx = diff_core.enclosing_def(current, cur_pos)
        inc_ctx = diff_core.enclosing_def(incoming, inc_pos)
        choice = prompt(h, idx, total, cur_ctx, inc_ctx)
        out.extend(diff_core.resolve(h, choice))
        cur_pos += len(h["current"])
        inc_pos += len(h["incoming"])

    diff_core.write_lines(out_path, out)
    print()
    print(GREEN("Wrote %s (%d lines)." % (out_path, len(out))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
