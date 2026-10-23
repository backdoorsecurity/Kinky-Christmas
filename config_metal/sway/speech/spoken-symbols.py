#!/usr/bin/env python3
"""Replace spoken symbol names in a transcript.

Reads text on stdin and the map path as the first argument. A line in the
map is a spoken name, then the symbol. Names are whole words and match the capitalization in the map. A shorter
name does not win inside a longer one. A period glued to a matched name
is removed with it. Spaces next to an inserted symbol are removed, so the
symbol sits against the words around it.

Pass --keep-spaces to replace names and leave the characters around them.
On that path, a space or comma between digits is removed.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

LEFT = "\ue000"
RIGHT = "\ue001"


def load_map(path: Path) -> list[tuple[str, str]]:
    pairs: list[tuple[str, str]] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        name, symbol = line.rsplit(None, 1)
        name = " ".join(name.split())
        if not name or not symbol:
            continue
        pairs.append((name, symbol))
    pairs.sort(key=lambda item: len(item[0]), reverse=True)
    return pairs


def apply_symbols(text: str, pairs: list[tuple[str, str]], *, keep_spaces: bool = False) -> str:
    if not text or not pairs:
        return text
    by_name = {name: symbol for name, symbol in pairs}
    pattern = "|".join(re.escape(name) for name, _symbol in pairs)
    if keep_spaces:
        found = re.compile(rf"\b({pattern})\b")
        replaced = found.sub(lambda match: by_name[match.group(1)], text)
        return join_digits(replaced)
    # The name is matched as written. A period glued to that name is part of it.
    found = re.compile(rf"\b({pattern})\b\.?")

    def replace(match: re.Match[str]) -> str:
        return LEFT + by_name[match.group(1)] + RIGHT

    marked = found.sub(replace, text)
    # A period the model added is dropped. A period that is the symbol stays inside the markers.
    marked = drop_periods(marked)
    marked = re.sub(rf"[ \t]*{LEFT}", LEFT, marked)
    marked = re.sub(rf"{RIGHT}[ \t]*", RIGHT, marked)
    return marked.replace(LEFT, "").replace(RIGHT, "")


def join_digits(text: str) -> str:
    """Drop a space or comma that sits between digits."""
    return re.sub(r"(?<=\d)[,\s]+(?=\d)", "", text)


def drop_periods(marked: str) -> str:
    out: list[str] = []
    index = 0
    while index < len(marked):
        if marked.startswith(LEFT, index):
            end = marked.find(RIGHT, index)
            if end == -1:
                out.append(marked[index:])
                break
            out.append(marked[index : end + len(RIGHT)])
            index = end + len(RIGHT)
            continue
        if marked[index] != ".":
            out.append(marked[index])
        index += 1
    return "".join(out)


def main() -> None:
    args = sys.argv[1:]
    keep_spaces = False
    if "--keep-spaces" in args:
        keep_spaces = True
        args.remove("--keep-spaces")
    if len(args) != 1:
        print("usage: spoken-symbols.py [--keep-spaces] MAP", file=sys.stderr)
        raise SystemExit(2)
    pairs = load_map(Path(args[0]))
    sys.stdout.write(apply_symbols(sys.stdin.read(), pairs, keep_spaces=keep_spaces))


if __name__ == "__main__":
    main()
