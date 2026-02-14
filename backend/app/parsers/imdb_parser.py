import json
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.imdb.com"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def parse_top_250(limit: int = 1000) -> List[Dict]:
    """Пример парсинга таблицы Top 250 (для учебных целей).
    Перед использованием проверь robots.txt и правила сайта.
    """
    url = f"{BASE_URL}/chart/top/"
    resp = requests.get(url, headers=HEADERS, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    rows = soup.select("table tbody tr")

    items: List[Dict] = []
    for row in rows:
        title_col = row.select_one("td.titleColumn a")
        year_span = row.select_one("td.titleColumn span.secondaryInfo")
        rating_strong = row.select_one("td.imdbRating strong")

        if not title_col:
            continue

        title = title_col.get_text(strip=True)
        url_rel = title_col.get("href") or ""
        url_full = BASE_URL + url_rel.split("?")[0]

        year = None
        if year_span and year_span.get_text(strip=True).startswith("("):
            try:
                year = int(year_span.get_text(strip=True).strip("()"))
            except ValueError:
                pass

        rating = None
        if rating_strong:
            try:
                rating = float(rating_strong.get_text(strip=True))
            except ValueError:
                pass

        items.append(
            {
                "title": title,
                "original_title": None,
                "year": year,
                "type": "movie",
                "description": None,
                "rating": rating,
                "genres": [],
                "countries": [],
                "url": url_full,
            }
        )

        if len(items) >= limit:
            break

    return items


if __name__ == "__main__":
    data = parse_top_250(limit=1000)
    with open("data/imdb.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
