import hashlib
from datetime import datetime, timezone
from urllib.parse import quote

import feedparser


async def fetch_google_news(company: dict) -> list[dict]:
    name = company["name"]
    code = company["code"]

    query = quote(f'"{name}"')
    url = f"https://news.google.com/rss/search?q={query}&hl=ja&gl=JP&ceid=JP:ja"

    feed = feedparser.parse(url)
    articles = []

    for entry in feed.entries[:20]:
        link = entry.get("link", "")
        if not link:
            continue
        article_id = f"gnews_{hashlib.md5(link.encode()).hexdigest()}"
        articles.append({
            "id": article_id,
            "company_name": name,
            "company_code": code,
            "title": entry.get("title", ""),
            "url": link,
            "published": entry.get("published", datetime.now(timezone.utc).isoformat()),
            "source": "Google News",
            "summary": "",
            "importance": "medium",
        })

    return articles
