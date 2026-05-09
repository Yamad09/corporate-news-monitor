import asyncio
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sources.company_ir import fetch_company_ir
from sources.edinet import fetch_edinet
from sources.google_news import fetch_google_news
from sources.tdnet import fetch_tdnet
from notifier import send_email
from summarizer import summarize_articles

ROOT = Path(__file__).parent.parent
COMPANIES_FILE = ROOT / "companies.json"
SEEN_IDS_FILE = ROOT / "seen_ids.json"
RETENTION_DAYS = 30


def load_companies() -> list[dict]:
    return json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))


def load_seen_ids() -> dict[str, str]:
    if SEEN_IDS_FILE.exists():
        try:
            return json.loads(SEEN_IDS_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def save_seen_ids(seen_ids: dict[str, str]) -> None:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=RETENTION_DAYS)).isoformat()
    pruned = {k: v for k, v in seen_ids.items() if v >= cutoff}
    SEEN_IDS_FILE.write_text(
        json.dumps(pruned, ensure_ascii=False, indent=2), encoding="utf-8"
    )


async def fetch_all(company: dict) -> list[dict]:
    results = await asyncio.gather(
        fetch_google_news(company),
        fetch_edinet(company),
        fetch_tdnet(company),
        fetch_company_ir(company),
        return_exceptions=True,
    )
    articles = []
    for r in results:
        if isinstance(r, list):
            articles.extend(r)
        elif isinstance(r, Exception):
            print(f"[{company['name']}] fetch error: {r}")
    return articles


async def main() -> None:
    companies = load_companies()
    seen_ids = load_seen_ids()

    print(f"対象企業: {len(companies)}社")

    all_results = await asyncio.gather(*[fetch_all(c) for c in companies])
    all_articles = [a for articles in all_results for a in articles]

    print(f"取得件数（重複込み）: {len(all_articles)}件")

    new_articles = [a for a in all_articles if a["id"] not in seen_ids]

    if not new_articles:
        print("新着ニュースなし")
        return

    print(f"新着: {len(new_articles)}件 → 要約・送信します")

    new_articles = await summarize_articles(new_articles)
    send_email(new_articles)

    now = datetime.now(timezone.utc).isoformat()
    for a in new_articles:
        seen_ids[a["id"]] = now
    save_seen_ids(seen_ids)


if __name__ == "__main__":
    asyncio.run(main())
