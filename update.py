#!/usr/bin/env python3
"""Scrape Fortune Poker $3/$5/$10 NLH into data/history.json. Stdlib only."""

from __future__ import annotations

import json
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

BOARD_URL = "https://pokerwa.com/fortunepoker/index.php"
UA = "FortunePokerMonitor/1.0 (personal; polite ~10min; not affiliated)"
RETENTION_DAYS = 60
PACIFIC = ZoneInfo("America/Los_Angeles")

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "data" / "history.json"

IMG_RE = re.compile(r"<img\b[^>]*>", re.I)
ATTR_RE = re.compile(
    r"""\b([A-Za-z_:][-A-Za-z0-9_:.]*)\s*=\s*(?:"([^"]*)"|'([^']*)')"""
)
OVERLAY_RE = re.compile(r"DL2_WL_overlay_(OPEN|8plus|[0-9]+)(?:_|\.|$)", re.I)
BOARD_RE = re.compile(r"""class\s*=\s*["'][^"']*Poker(?:Table|List)""", re.I)


def _attrs(tag: str) -> dict[str, str]:
    found: dict[str, str] = {}
    for match in ATTR_RE.finditer(tag):
        key = match.group(1).lower()
        found[key] = match.group(2) if match.group(2) is not None else match.group(3)
    return found


def _overlay_count(token: str) -> int:
    token = token.upper()
    if token == "OPEN":
        return 0
    if token == "8PLUS":
        # ponytail: badge tops out at "8+". Ceiling is the filename; store 8 until the site shows an exact count.
        return 8
    return int(token)


def parse_board(html: str) -> tuple[int, int]:
    """Return (active $3/$5/$10 NLH tables, waitlist players)."""
    if not BOARD_RE.search(html):
        raise ValueError("board markup not recognized")

    tables = 0
    wait: int | None = None
    for tag in IMG_RE.findall(html):
        attrs = _attrs(tag)
        classes = set((attrs.get("class") or "").lower().split())
        src = attrs.get("src") or ""
        if "pokertable" in classes and "FP_3_5_10_NL" in src and "FP_3_5_10_NL_list" not in src:
            tables += 1
            continue
        if "pokerlist" in classes and "FP_3_5_10_NL_list" in tag:
            match = OVERLAY_RE.search(src) or OVERLAY_RE.search(tag)
            if not match:
                raise ValueError("waitlist overlay not recognized")
            count = _overlay_count(match.group(1))
            if wait is not None and wait != count:
                raise ValueError("conflicting waitlist overlays")
            wait = count
    return tables, 0 if wait is None else wait


def pacific_now() -> datetime:
    return datetime.now(PACIFIC)


def format_label(moment: datetime) -> str:
    hour = int(moment.strftime("%I"))
    ampm = moment.strftime("%p").lower()
    return f"{moment.strftime('%b')} {moment.day} {hour}:{moment.strftime('%M')}{ampm}"


def load_history(path: Path) -> list:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("history.json must be a JSON array")
    return data


def prune(rows: list, now: datetime | None = None) -> list:
    now = now or pacific_now()
    cutoff = now - timedelta(days=RETENTION_DAYS)
    kept = []
    for row in rows:
        ts = datetime.fromisoformat(row["ts"])
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=PACIFIC)
        if ts >= cutoff:
            kept.append(row)
    kept.sort(key=lambda row: row["ts"])
    return kept


def save_history(path: Path, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def fetch_board(url: str = BOARD_URL) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="replace")


def append_sample(html: str, path: Path = OUT, moment: datetime | None = None) -> dict:
    active, waiting = parse_board(html)
    moment = moment or pacific_now()
    rows = prune(load_history(path), moment)
    rows.append(
        {
            "ts": moment.isoformat(timespec="seconds"),
            "ts_label": format_label(moment),
            "active_tables": active,
            "waitlist_players": waiting,
        }
    )
    save_history(path, rows)
    return {
        "ok": True,
        "active_tables": active,
        "waitlist_players": waiting,
        "checked_pacific": format_label(moment),
        "samples": len(rows),
        "out": str(path),
    }


def emit(payload: dict) -> None:
    print(json.dumps(payload, separators=(",", ":")))


def _self_check() -> None:
    open_html = """
    <img class="PokerTable" src="https://www.pokerwa.com/images/icons/FP_4_8_w90px.png">
    <img class="PokerTable" src="https://www.pokerwa.com/images/icons/FP_3_5_10_NL_w90px.png">
    <img src="https://www.pokerwa.com/images/icons/FP_3_5_10_NL_w90px.png" class="PokerTable">
    <img class="PokerList" style="background:url(https://www.pokerwa.com/images/icons/FP_1_3_NL_list_v3_w65px.png);" src="https://www.pokerwa.com/images/icons/DL2_WL_overlay_5_w65px.png">
    <img class="PokerList" style="background:url(https://www.pokerwa.com/images/icons/FP_3_5_10_NL_list_w65px.png);" src="https://www.pokerwa.com/images/icons/DL2_WL_overlay_OPEN_w65px.png">
    """
    assert parse_board(open_html) == (2, 0)
    assert parse_board(open_html.replace("DL2_WL_overlay_OPEN", "DL2_WL_overlay_6")) == (2, 6)
    assert parse_board(open_html.replace("DL2_WL_overlay_OPEN", "DL2_WL_overlay_8plus")) == (2, 8)

    single = """
    <img class='PokerTable' src='https://x/FP_3_5_10_NL_w90px.png'>
    <img class='PokerList' style='background:url(https://x/FP_3_5_10_NL_list.png)' src='https://x/DL2_WL_overlay_3_w65px.png'>
    """
    assert parse_board(single) == (1, 3)
    assert parse_board(
        '<img class="PokerTable" src="https://www.pokerwa.com/images/icons/FP_1_3_NL_v2_w90px.png">'
    ) == (0, 0)

    try:
        parse_board("<html>no board</html>")
        raise AssertionError("expected markup error")
    except ValueError:
        pass

    try:
        parse_board(
            """
            <img class="PokerTable" src="FP_1_3.png">
            <img class="PokerList" style="background:url(FP_3_5_10_NL_list.png);" src="no-overlay.png">
            """
        )
        raise AssertionError("expected overlay error")
    except ValueError:
        pass

    moment = datetime(2026, 10, 13, 18, 47, tzinfo=PACIFIC)
    assert format_label(moment) == "Oct 13 6:47pm"
    assert format_label(datetime(2026, 10, 13, 12, 5, tzinfo=PACIFIC)) == "Oct 13 12:05pm"
    assert format_label(datetime(2026, 10, 13, 0, 5, tzinfo=PACIFIC)) == "Oct 13 12:05am"

    old = {
        "ts": (moment - timedelta(days=RETENTION_DAYS + 1)).isoformat(),
        "ts_label": "old",
        "active_tables": 1,
        "waitlist_players": 0,
    }
    edge = {
        "ts": (moment - timedelta(days=RETENTION_DAYS)).isoformat(),
        "ts_label": "edge",
        "active_tables": 1,
        "waitlist_players": 0,
    }
    fresh = {
        "ts": moment.isoformat(),
        "ts_label": "Oct 13 6:47pm",
        "active_tables": 2,
        "waitlist_players": 1,
    }
    assert prune([fresh, old, edge], moment) == [edge, fresh]


def main(argv: list[str]) -> int:
    if len(argv) > 1 or (len(argv) == 1 and argv[0] in ("-h", "--help")):
        print("usage: python3 update.py [saved-board.html]", file=sys.stderr)
        return 2
    if len(argv) == 1 and argv[0] == "--self-check":
        _self_check()
        emit({"ok": True, "self_check": True})
        return 0
    try:
        html = (
            Path(argv[0]).read_text(encoding="utf-8", errors="replace")
            if len(argv) == 1
            else fetch_board()
        )
        emit(append_sample(html))
        return 0
    except (OSError, urllib.error.URLError, ValueError, json.JSONDecodeError, KeyError) as exc:
        emit({"ok": False, "error": str(exc)})
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
