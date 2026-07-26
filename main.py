"""CLI entrypoint: fetch news for a keyword, score it with FinBERT, write a report."""

import argparse
import logging
import os
import time

from sentiment_scanner.analyzer import analyze_sentiment
from sentiment_scanner.fetcher import fetch_news
from sentiment_scanner.report import build_report, save_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_KEYWORD = "gold"
DEFAULT_NUM_ARTICLES_PER_QUERY = 10


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch news and run FinBERT sentiment analysis on a keyword.")
    parser.add_argument(
        "keyword",
        nargs="?",
        default=os.environ.get("SENTIMENT_KEYWORD", DEFAULT_KEYWORD),
        help="Search keyword, e.g. 'gold', 'nasdaq', 'tesla'. Falls back to SENTIMENT_KEYWORD env var.",
    )
    parser.add_argument(
        "--num-articles-per-query",
        type=int,
        default=int(os.environ.get("SENTIMENT_NUM_ARTICLES_PER_QUERY", DEFAULT_NUM_ARTICLES_PER_QUERY)),
        help="Number of articles to fetch per finance-flavored query variant (7 variants are queried).",
    )
    return parser.parse_args()


def analyze_articles(articles: list[dict]) -> list[dict]:
    """Attach a FinBERT sentiment label and confidence to each article."""
    analyzed = []
    for article in articles:
        text = f"{article['title']} {article['content']}".strip()
        result = analyze_sentiment(text)
        analyzed.append({**article, "sentiment": result.label, "confidence": result.confidence})
    return analyzed


def run(keyword: str, num_articles_per_query: int) -> None:
    run_start = time.perf_counter()

    logger.info("Fetching news for keyword=%s", keyword)
    fetch_start = time.perf_counter()
    articles = fetch_news(keyword, num_articles_per_query)
    fetch_elapsed = time.perf_counter() - fetch_start
    logger.info("Fetched %d unique articles in %.1fs", len(articles), fetch_elapsed)
    if not articles:
        logger.warning("No articles found for keyword=%s", keyword)

    analyze_start = time.perf_counter()
    analyzed_articles = analyze_articles(articles)
    analyze_elapsed = time.perf_counter() - analyze_start
    logger.info("Analyzed %d articles in %.1fs", len(analyzed_articles), analyze_elapsed)

    report_content = build_report(keyword, analyzed_articles)
    report_path = save_report(keyword, report_content)

    total_elapsed = time.perf_counter() - run_start
    logger.info("Report written to %s", report_path)
    logger.info(
        "Done in %.1fs total (fetch %.1fs, analyze %.1fs)",
        total_elapsed,
        fetch_elapsed,
        analyze_elapsed,
    )


def main() -> None:
    args = parse_args()
    run(args.keyword, args.num_articles_per_query)


if __name__ == "__main__":
    main()
