# Fortune Poker — $3/$5/$10 NLH monitor

Static page that charts active tables and the waitlist for Fortune Poker’s $3/$5/$10 NLH game.

This runs on GitHub only. Nothing needs to stay running on a laptop.

- Site: https://ajoros.github.io/poker-room-monitor/
- Scrape: GitHub Actions, about every 10 minutes, commits `data/history.json`
- Page: refetches that file about every 10 minutes

No npm, no bundler, no server. HTML + Chart.js from a CDN + `data/history.json`.

## Layout

```
├── .github/workflows/fortune-update.yml
├── data/history.json
├── index.html
├── update.py          # executed by Actions, not on your machine
├── sync-history.py    # optional JSONL merge
├── .gitignore
└── README.md
```

## How it updates

`.github/workflows/fortune-update.yml` runs on `*/10 * * * *` and on manual dispatch. On a GitHub-hosted runner it fetches `https://pokerwa.com/fortunepoker/index.php`, counts `$3/$5/$10` NLH tables and the waitlist from icon filenames, appends one sample, drops samples older than 60 days, and pushes `data/history.json` when it changed.

The chart shows the latest 60 days. GitHub’s cron can drift a few minutes.

Actions needs `contents: write` and permission to push commits. Pages deploys from `main` / root.

## Data

`data/history.json` is an array. The page headline uses the last element.

| Field | Meaning |
| --- | --- |
| `ts` | ISO-8601 with Pacific offset |
| `ts_label` | Short Pacific label (`Oct 13 6:47pm`) |
| `active_tables` | `$3/$5/$10` NLH tables on the board |
| `waitlist_players` | Waitlist size (`OPEN` on the site is 0) |

Counts come from image filenames. An active table is an `img.PokerTable` whose `src` contains `FP_3_5_10_NL`. The waitlist is a `PokerList` whose background is `FP_3_5_10_NL_list` plus a `DL2_WL_overlay_<N|OPEN>` badge. `fortunepokerroom.com` is a frameset; the scraper hits pokerwa directly.

## Knobs

| Location | Setting |
| --- | --- |
| `update.py` → `RETENTION_DAYS` | 60 |
| `index.html` → `HISTORY_DAYS` | Chart shows the latest 60 days |
| `update.py` → `UA` | User-Agent |
| `index.html` → `THRESHOLD` | Dashed line at 4 |
| `index.html` → `RELOAD_MS` | Client refetch, 10 minutes |

The threshold is visual only. No SMS.

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| Pages looks old | Hard-refresh. Confirm the Actions run committed `data/history.json`. |
| Actions run failed | Open the workflow log. Usually the board markup changed or pokerwa did not respond. |
| Schedule looks idle | GitHub cron can lag. The workflow is also runnable with “Run workflow”. |

Personal monitoring utility. Not affiliated with Fortune Poker.
