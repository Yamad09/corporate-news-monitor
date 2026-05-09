from datetime import date, datetime, timedelta, timezone
from urllib.parse import urljoin

import httpx
from bs4 import BeautifulSoup

TDNET_BASE = "https://www.release.tdnet.info"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


async def _fetch_list_page(client: httpx.AsyncClient, date_str: str, session: int) -> list[dict] | None:
    url = f"{TDNET_BASE}/inbs/I_list_{session:03d}_{date_str}.html"
    try:
        resp = await client.get(url, headers=HEADERS)
        if resp.status_code == 404:
            return None
        resp.raise_for_status()
        return resp
    except Exception:
        return None


async def fetch_tdnet(company: dict) -> list[dict]:
    code = company["code"]
    articles = []

    async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
        for delta in range(2):
            date_str = (date.today() - timedelta(days=delta)).strftime("%Y%m%d")

            for session in range(1, 8):
                resp = await _fetch_list_page(client, date_str, session)
                if resp is None:
                    break

                soup = BeautifulSoup(resp.text, "lxml")
                for row in soup.find_all("tr"):
                    cells = row.find_all("td")
                    if not cells:
                        continue

                    # security code column: match exact 4-digit code
                    row_has_code = any(
                        c.get_text(strip=True) == code for c in cells
                    )
                    if not row_has_code:
                        continue

                    link_tag = row.find("a")
                    if not link_tag:
                        continue

                    title = link_tag.get_text(strip=True)
                    href = link_tag.get("href", "")
                    full_url = urljoin(TDNET_BASE + "/inbs/", href) if href else TDNET_BASE

                    articles.append({
                        "id": f"tdnet_{abs(hash(full_url))}",
                        "company_name": company["name"],
                        "company_code": code,
                        "title": f"【適時開示】{title}",
                        "url": full_url,
                        "published": f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}",
                        "source": "TDnet（適時開示）",
                        "summary": "",
                        "importance": "high",
                    })

    # deduplicate within this function
    seen = set()
    unique = []
    for a in articles:
        if a["id"] not in seen:
            seen.add(a["id"])
            unique.append(a)
    return unique
