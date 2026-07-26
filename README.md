# News Sentiment Scanner

Fetches recent news for a keyword, scores each article with FinBERT
(`yiyanghkust/finbert-tone`), and writes a markdown report to `reports/`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python main.py gold
python main.py "nasdaq" --num-articles-per-query 15
python main.py tesla
```

- Positional `keyword` — search term (e.g. `gold`, `nasdaq`, `tesla`). Falls back to the
  `SENTIMENT_KEYWORD` env var, then defaults to `gold`.
- `--num-articles-per-query` — number of articles to fetch per query variant. Falls back to
  `SENTIMENT_NUM_ARTICLES_PER_QUERY`, then defaults to `10`.

Each keyword is expanded into 7 finance-flavored queries (`"{keyword} market"`,
`"{keyword} price"`, `"{keyword} news"`, `"{keyword} trends"`, `"{keyword} analysis"`,
`"{keyword} forecast"`, `"{keyword} investment"`) so results skew toward market news
instead of unrelated hits (e.g. Olympic medals for "gold"). Results are deduplicated
by article link before scoring.

Each run writes `reports/{keyword}-{yyyymmdd}.md` with a sentiment summary
(Positive/Negative/Neutral breakdown) and per-article detail.

## Scheduled runs

`.github/workflows/sentiment-scan.yml` runs the scan daily via cron and
commits the resulting report back to `reports/`. Trigger it manually with a
custom keyword via the Actions tab (`workflow_dispatch` input `keyword`), or
edit the cron schedule / default keyword in the workflow file.
