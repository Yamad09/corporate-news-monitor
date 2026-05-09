from datetime import date, datetime, timedelta, timezone

import httpx

EDINET_API = "https://api.edinet-fsa.go.jp/api/v2"
EDINET_DOC_URL = (
    "https://disclosure.edinet-fsa.go.jp/E01EW/BLMainController.jsp"
    "?uji.verb=W1E62071DetailInfo&uji.bean=ee.W1E62071.W1E62071DtlBean"
    "&TID=W1E62071&PID=W1E62071&SESSIONKEY=&lgKbn=2&dcdFlg=0"
    "&iflg=0&dispKbn=1&docID={doc_id}"
)


def _matches(company: dict, doc: dict) -> bool:
    code = company["code"]
    name = company["name"]
    sec_code = doc.get("secCode") or ""
    filer_name = doc.get("filerName") or ""
    return (
        (sec_code and (sec_code[:4] == code or sec_code == code + "0"))
        or name in filer_name
    )


async def fetch_edinet(company: dict) -> list[dict]:
    articles = []
    async with httpx.AsyncClient(timeout=30) as client:
        for delta in range(2):
            target_date = (date.today() - timedelta(days=delta)).isoformat()
            try:
                resp = await client.get(
                    f"{EDINET_API}/documents.json",
                    params={"date": target_date, "type": 2},
                )
                resp.raise_for_status()
                data = resp.json()
            except Exception as e:
                print(f"EDINET fetch error ({target_date}): {e}")
                continue

            for doc in data.get("results", []):
                if not _matches(company, doc):
                    continue
                doc_id = doc.get("docID", "")
                if not doc_id:
                    continue
                articles.append({
                    "id": f"edinet_{doc_id}",
                    "company_name": company["name"],
                    "company_code": company["code"],
                    "title": f"【EDINET】{doc.get('docDescription', '')}",
                    "url": EDINET_DOC_URL.format(doc_id=doc_id),
                    "published": doc.get(
                        "submitDateTime", datetime.now(timezone.utc).isoformat()
                    ),
                    "source": "EDINET",
                    "summary": "",
                    "importance": "high",
                })

    return articles
