"""
네이버 금융 - 코스피/코스닥 상승종목 순위 스크래퍼
API 키, 증권 계좌 필요 없음. 공개 웹페이지만 읽음.

실행: python scrape_rising.py
결과: data/latest.json 에 저장 (GitHub Actions에서 자동 커밋)
"""
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime, timezone, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Referer": "https://finance.naver.com/sise/sise_rise.naver",
}

# sosok=0 코스피, sosok=1 코스닥
MARKETS = {"kospi": 0, "kosdaq": 1}


def fetch_market(sosok: int, pages: int = 1):
    """상승률 상위 종목을 pages 페이지만큼 가져온다 (페이지당 50종목)."""
    rows = []
    for page in range(1, pages + 1):
        url = f"https://finance.naver.com/sise/sise_rise.naver?sosok={sosok}&page={page}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = "euc-kr"
        soup = BeautifulSoup(resp.text, "html.parser")

        table = soup.select_one("table.type_2")
        if not table:
            break

        for tr in table.select("tr"):
            tds = tr.select("td")
            if len(tds) < 10:
                continue  # 헤더/광고 행 skip

            name_tag = tds[1].select_one("a")
            if not name_tag:
                continue

            name = name_tag.get_text(strip=True)
            code = name_tag.get("href", "").split("code=")[-1]
            price = tds[2].get_text(strip=True).replace(",", "")
            change_dir = tds[3].get_text(strip=True)  # 상한가/상승 등
            change_amt = tds[4].get_text(strip=True).replace(",", "")
            change_pct = tds[5].get_text(strip=True)
            volume = tds[6].get_text(strip=True).replace(",", "")

            rows.append({
                "name": name,
                "code": code,
                "price": price,
                "change_amt": change_amt,
                "change_pct": change_pct,
                "volume": volume,
                "status": change_dir,
            })

    return rows


def main():
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    result = {
        "updated_at": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "kospi": fetch_market(MARKETS["kospi"], pages=1),
        "kosdaq": fetch_market(MARKETS["kosdaq"], pages=1),
    }

    os.makedirs("data", exist_ok=True)
    with open("data/latest.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"저장 완료: KOSPI {len(result['kospi'])}종목, KOSDAQ {len(result['kosdaq'])}종목")


if __name__ == "__main__":
    main()
