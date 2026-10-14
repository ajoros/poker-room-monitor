# Fortune Poker — $3/$5/$10 NLH monitor

Static page that charts active tables and the waitlist for Fortune Poker’s $3/$5/$10 NLH game.

Local use first. GitHub Pages is below, after this looks right on your machine.

No npm, no bundler, no production server. HTML + Chart.js from a CDN + `data/history.json`.

## Layout

```
├── .github/workflows/fortune-update.yml   # later: scrape about every 10 min
├── data/history.json
├── index.html
├── update.py
├── sync-history.py                         # optional JSONL merge
├── .gitignore
└── README.md
```

## Local

Python 3.10+ (stdlib only) and a browser.

```bash
python3 update.py
python3 -m http.server 8765
```

Open [http://127.0.0.1:8765/](http://127.0.0.1:8765/) on the same computer that is running the server.

`update.py` fetches `https://pokerwa.com/fortunepoker/index.php`, counts `$3/$5/$10` NLH tables and the waitlist from icon filenames, appends one sample, and drops samples older than 90 days.

Offline / fixture mode:

```bash
python3 update.py /path/to/saved-board.html
```

Success looks like:

```json
{"ok":true,"active_tables":2,"waitlist_players":6,"checked_pacific":"Oct 13 7:41pm","samples":1,"out":".../data/history.json"}
```

`file://` breaks `fetch()`. Use the local server. Edit `index.html` and hard-refresh.

Optional, if you also keep a `.jsonl` of the same objects:

```bash
python3 sync-history.py path/to/samples.jsonl
```

Merges into `data/history.json` and dedupes by `ts`.

## Data

`data/history.json` is an array. The page headline uses the last element.

| Field | Meaning |
| --- | --- |
| `ts` | ISO-8601 with Pacific offset |
| `ts_label` | Short Pacific label (`Oct 13 6:47pm`) |
| `active_tables` | `$3/$5/$10` NLH tables on the board |
| `waitlist_players` | Waitlist size (`OPEN` on the site is 0) |

Counts come from image filenames. An active table is an `img.PokerTable` whose `src` contains `FP_3_5_10_NL`. The waitlist is a `PokerList` whose background is `FP_3_5_10_NL_list` plus a `DL2_WL_overlay_<N|OPEN>` badge. `fortunepokerroom.com` is a frameset; the scraper hits pokerwa directly. Poll about every 10 minutes.

## Knobs

| Location | Setting |
| --- | --- |
| `update.py` → `RETENTION_DAYS` | 90 |
| `update.py` → `UA` | User-Agent |
| `index.html` → `THRESHOLD` | Dashed line at 4 |
| `index.html` → `RELOAD_MS` | Client refetch, 10 minutes |

The threshold is visual only. No SMS.

## GitHub Pages (after local is solid)

Push `main`, then Settings → Pages → Deploy from branch `main` / root. The workflow in `.github/workflows/fortune-update.yml` scrapes on a 10-minute cron and commits `data/history.json`. The page already fetches `data/history.json?t=` plus the current time, so visitors pick up a new file without an HTML redeploy. Cron can drift a few minutes. Actions needs `contents: write` and permission to push commits.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| `127.0.0.1` refused | Start `python3 -m http.server 8765` on that machine. |
| Chart empty / fetch error | Use `http://127.0.0.1:8765/`, not `file://`. Confirm `data/history.json` exists. |
| `update.py` → `ok: false` | Network blocked, or the board markup changed. |
| Pages looks old | Hard-refresh. Confirm Actions committed `data/history.json` and Pages uses the repo root. |

Personal monitoring utility. Not affiliated with Fortune Poker.
