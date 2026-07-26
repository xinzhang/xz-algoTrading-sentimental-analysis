"""News retrieval via Google News RSS."""

import logging
from urllib.parse import quote

import feedparser
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (compatible; NewsSentimentScanner/1.0)"
REQUEST_TIMEOUT_SECONDS = 10

# Broadens a bare keyword (e.g. "gold") into finance-flavored queries so results
# skew toward market news instead of unrelated hits (Olympic medals, "Gold Coast", etc.).
QUERY_TEMPLATES = [
    "{keyword} market",
    "{keyword} price",
    "{keyword} news",
    "{keyword} trends",
    "{keyword} analysis",
    "{keyword} forecast",
    "{keyword} investment",
]


def build_queries(keyword: str) -> list[str]:
    return [template.format(keyword=keyword) for template in QUERY_TEMPLATES]


def build_rss_url(query: str) -> str:
    return f"https://news.google.com/rss/search?q={quote(query)}"


def fetch_article_content(url: str) -> str:
    """Best-effort scrape of an article's paragraph text. Returns "" on failure."""
    try:
        response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Failed to fetch article content from %s: %s", url, exc)
        return ""

    soup = BeautifulSoup(response.text, "html.parser")
    paragraphs = soup.find_all("p")
    return " ".join(p.get_text() for p in paragraphs).strip()


def fetch_rss_feed(query: str) -> feedparser.FeedParserDict:
    """Fetch the RSS feed body via requests (bundles its own CA certs) and hand it to feedparser."""
    response = requests.get(build_rss_url(query), timeout=REQUEST_TIMEOUT_SECONDS, headers={"User-Agent": USER_AGENT})
    response.raise_for_status()
    return feedparser.parse(response.content)


def fetch_articles_for_query(query: str, num_articles: int) -> list[dict]:
    """Fetch and enrich the top articles for a single search query."""
    feed = fetch_rss_feed(query)

    articles = []
    for entry in feed.entries[:num_articles]:
        link = entry.get("link", "")
        articles.append(
            {
                "title": entry.get("title", ""),
                "link": link,
                "published": entry.get("published", ""),
                "content": fetch_article_content(link) if link else "",
            }
        )
    return articles


def fetch_news(keyword: str, num_articles_per_query: int = 10) -> list[dict]:
    """Fetch news across finance-flavored query variants of a keyword, deduplicated by link."""
    seen_links = set()
    articles = []

    for query in build_queries(keyword):
        logger.info("Fetching news for query=%r", query)
        for article in fetch_articles_for_query(query, num_articles_per_query):
            link = article["link"]
            if link and link in seen_links:
                continue
            if link:
                seen_links.add(link)
            articles.append(article)

    return articles
