"""Report generation and persistence."""

import logging
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

REPORTS_DIR = Path(__file__).resolve().parent.parent / "reports"
REPORT_DATE_PATTERN = re.compile(r"-(\d{8})\.md$")


def summarize_sentiments(analyzed_articles: list[dict]) -> dict:
    summary = {"Positive": 0, "Negative": 0, "Neutral": 0}
    for article in analyzed_articles:
        summary[article["sentiment"]] += 1
    return summary


def build_report(keyword: str, analyzed_articles: list[dict]) -> str:
    """Render a markdown report summarizing sentiment across analyzed articles."""
    total = len(analyzed_articles)
    summary = summarize_sentiments(analyzed_articles)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    lines = [
        f"# Sentiment Report: {keyword}",
        f"Generated: {generated_at}",
        f"Total articles analyzed: {total}",
        "",
        "## Summary",
    ]
    for label, count in summary.items():
        percent = (count / total * 100) if total else 0.0
        lines.append(f"- {label}: {count} ({percent:.2f}%)")

    lines.append("")
    lines.append("## Articles")
    for idx, article in enumerate(analyzed_articles, start=1):
        lines.extend(
            [
                f"### {idx}. {article['title']}",
                f"- Link: {article['link']}",
                f"- Published: {article['published']}",
                f"- Sentiment: {article['sentiment']} (confidence: {article['confidence']:.2f})",
                "",
            ]
        )

    return "\n".join(lines)


def save_report(keyword: str, content: str, reports_dir: Path = REPORTS_DIR) -> Path:
    """Write the report to reports/{keyword}-{yyyymmdd}.md and return its path."""
    reports_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    safe_keyword = keyword.strip().lower().replace(" ", "_")
    report_path = reports_dir / f"{safe_keyword}-{date_str}.md"
    report_path.write_text(content, encoding="utf-8")
    logger.info("Report saved to %s", report_path)
    return report_path


def prune_old_reports(reports_dir: Path = REPORTS_DIR, max_age_days: int = 14) -> list[Path]:
    """Delete reports whose filename date is older than max_age_days. Returns the deleted paths.

    Uses the yyyymmdd encoded in the filename rather than file mtime, since checkout
    tools (e.g. actions/checkout) reset mtimes to the checkout time, not the original date.
    """
    if not reports_dir.exists():
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    deleted = []

    for report_path in sorted(reports_dir.glob("*.md")):
        match = REPORT_DATE_PATTERN.search(report_path.name)
        if not match:
            continue

        report_date = datetime.strptime(match.group(1), "%Y%m%d").replace(tzinfo=timezone.utc)
        if report_date < cutoff:
            report_path.unlink()
            deleted.append(report_path)
            logger.info("Deleted old report: %s", report_path)

    return deleted
