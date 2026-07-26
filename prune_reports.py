"""CLI entrypoint: delete reports older than N days."""

import argparse
import logging

from sentiment_scanner.report import prune_old_reports

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_MAX_AGE_DAYS = 14


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Delete sentiment reports older than N days.")
    parser.add_argument(
        "--max-age-days",
        type=int,
        default=DEFAULT_MAX_AGE_DAYS,
        help="Delete reports whose filename date is older than this many days.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    deleted = prune_old_reports(max_age_days=args.max_age_days)
    logger.info("Deleted %d report(s) older than %d days", len(deleted), args.max_age_days)


if __name__ == "__main__":
    main()
