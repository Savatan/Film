import json
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.kinopoisk.ru"
HEADERS = {"User-Agent": "Mozilla/5.0"}


def parse_popular(limit: int = 1000) -> List[Dict]:
    """Упрощённый пример парсинга популярных фильмов с Кинопоиска.
    Структура страниц может меняться, селекторы нужно будет подправить.
    Обязательно проверь robots.txt перед использованием.
    """
    items: List[Dict] = []
    page = 1

    while len(items) < limit:
        url = f"{BASE_URL}/lists/movies/popular/?page={page}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        cards = soup.select("div.styles_root__ti07r") or []
        if not cards:
            break

        for card in cards:
            title_el = card.select_one("a.styles_root__wgbNq")
            if not title_el:
                continue
            title = title_el.get_text(strip=True)
            url_rel = title_el.get("href") or ""
            url_full = BASE_URL + url_rel

            year = None
            year_el = card.select_one("span.styles_year__T57gn")
            if year_el:
                try:
                    year = int(year_el.get_text(strip=True)[:4])
                except ValueError:
                    pass

            rating = None
            rating_el = card.select_one("span.styles_kinopoiskValue__9qXjg")
            if rating_el:
                try:
                    rating = float(rating_el.get_text(strip=True).replace(",", "."))
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

        page += 1

    return items


if __name__ == "__main__":
    data = parse_popular(limit=1000)
    with open("data/kinopoisk.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
