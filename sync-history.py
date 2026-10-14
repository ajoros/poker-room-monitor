#!/usr/bin/env python3
"""Merge a JSONL of board samples into data/history.json. Dedupe by ts."""

from __future__ import annotations

import json
import sys
from pathlib import Path

from update import OUT, load_history, prune, save_history


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: python3 sync-history.py FILE.jsonl", file=sys.stderr)
        return 2
    incoming = []
    for line_no, line in enumerate(Path(argv[0]).read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        if not isinstance(row, dict) or "ts" not in row:
            raise ValueError(f"line {line_no}: expected an object with ts")
        incoming.append(row)
    by_ts = {row["ts"]: row for row in load_history(OUT)}
    for row in incoming:
        by_ts[row["ts"]] = row
    rows = prune(list(by_ts.values()))
    save_history(OUT, rows)
    print(json.dumps({"ok": True, "samples": len(rows), "out": str(OUT)}, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except (OSError, ValueError, json.JSONDecodeError, KeyError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, separators=(",", ":")))
        raise SystemExit(1)
