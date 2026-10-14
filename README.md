# Fortune Poker — $3/$5/$10 NLH

A static chart of open $1/$3 and $3/$5/$10 no-limit hold’em tables at Fortune Poker, and how many players are on each waitlist.

GitHub Actions checks the public board about every 10 minutes and appends a sample to `data/history.json`. GitHub Pages hosts the page. The page reloads that file on its own, so the chart stays current without a server. Samples older than 60 days are dropped.

The site is plain HTML plus Chart.js from a CDN. There is no build step and no backend.

Not affiliated with Fortune Poker.
