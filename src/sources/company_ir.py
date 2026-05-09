import hashlib
from datetime import datetime, timezone

import feedparser


async def fetch_company_ir(company: dict) -> list[dict]:
    ir_rss_url = company.get("ir_rss_url", "").strip()
    if not ir_rss_url:
        return []

    feed = feedparser.parse(ir_rss_url)
    articles = []

    for entry in feed.entries[:10]:
        link = entry.get("link", "")
        if not link:
            continue
        article_id = f"ir_{hashlib.md5(link.encode()).hexdigest()}"
        articles.append({
            "id": article_id,
            "company_name": company["name"],
            "company_code": company["code"],
            "title": f"【企業IR】{entry.get('title', '')}",
            "url": link,
            "published": entry.get("published", datetime.now(timezone.utc).isoformat()),
            "source": f"企業IR ({company['name']})",
            "summary": "",
            "importance": "high",
        })

    return articles
