import json
import os

import anthropic


async def summarize_articles(articles: list[dict]) -> list[dict]:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key or not articles:
        return articles

    client = anthropic.AsyncAnthropic(api_key=api_key)

    items = "\n\n".join(
        f"[{i + 1}] 企業: {a['company_name']}({a['company_code']}) | 情報源: {a['source']}\n"
        f"タイトル: {a['title']}"
        for i, a in enumerate(articles)
    )

    prompt = f"""以下のニュース・開示情報を分析してください。
各記事について：
1. 50文字以内の日本語要約
2. 重要度（high/medium/low）
   - high: 決算発表・M&A・重大訴訟・行政処分・経営陣変更・業績修正など企業価値直結
   - medium: 新製品・提携・事業展開など
   - low: 一般業界ニュース・軽微な情報

以下のJSON形式のみで回答（余計なテキスト不要）：
{{"results": [{{"index": 1, "summary": "...", "importance": "high"}}]}}

記事リスト:
{items}"""

    try:
        resp = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2048,
            messages=[{"role": "user", "content": prompt}],
        )
        data = json.loads(resp.content[0].text)
        for item in data.get("results", []):
            idx = item["index"] - 1
            if 0 <= idx < len(articles):
                articles[idx]["summary"] = item.get("summary", "")
                articles[idx]["importance"] = item.get("importance", "medium")
    except Exception as e:
        print(f"要約エラー（スキップして続行）: {e}")

    return articles
